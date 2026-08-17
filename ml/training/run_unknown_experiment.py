"""run_unknown_experiment.py — Unknown / unseen anomaly simulation (PRD §46 Option B).

Wording is ALWAYS "unseen / unknown anomaly simulation" — never "zero-day
detection" (PRD §46, §64.3).

Design (Option B — temporal unseen classes):
  - Supervised: train the selected XGBoost variant (xgb_200 params) on
    dev_temporal_train.parquet (Mon–Thu, 12 classes). PortScan/DDoS/Bot are
    ABSENT from training by construction (temporal/train has only 12 classes).
  - Anomaly: IsolationForest fit on BENIGN rows of dev_temporal_train only.
  - Threshold: calibrated on temporal_3way/validation (first half of Friday)
    using the same max-F1 protocol as the random experiment. Reported metrics
    are on temporal_3way/test (second half of Friday), DISJOINT from the
    calibration set (no test tuning).
  - Hybrid: deterministic PRD §10 layer (supervised confidence -> anomaly ->
    benign) applied to Friday flows.

Outputs:
  - ml/evaluation/results/unknown_experiment_temporal.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

from ml.evaluation.metrics import evaluate_multiclass
from ml.hybrid.decision import HybridThresholds, hybrid_decision
from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.labels import CANONICAL_LABELS, decode_label
from ml.preprocessing.preprocess import preprocess_frame
from ml.preprocessing.subset import load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"
SEED = 42

DEV_SUBSET = ROOT / "data" / "processed" / "dev_temporal_train.parquet"
CAL_SPLIT = LoadConfig(config="temporal_3way", split="validation")
TST_SPLIT = LoadConfig(config="temporal_3way", split="test")

SUP_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": SEED,
    "n_jobs": -1,
    "tree_method": "hist",
    "verbosity": 0,
}
IF_PARAMS = {
    "n_estimators": 200,
    "max_samples": "auto",
    "contamination": "auto",
    "random_state": SEED,
    "n_jobs": -1,
}


def _fit_supervised(train_raw):
    train_orig = sorted(set(int(v) for v in train_raw.y_multiclass))
    remap = {o: n for n, o in enumerate(train_orig)}
    unmap = {n: o for o, n in remap.items()}
    y_fit = np.array([remap[int(v)] for v in train_raw.y_multiclass], dtype="int64")
    clf = XGBClassifier(**SUP_PARAMS)
    clf.fit(train_raw.X, y_fit)
    return clf, unmap


def _fit_if_benign(train_raw):
    benign = train_raw.y_binary == 0
    clf = IsolationForest(**IF_PARAMS)
    clf.fit(train_raw.X[benign])
    return clf, int(benign.sum())


def _calibrate(scores, benign_mask, max_fpr: float = 0.05):
    """Best F1 subject to FPR <= max_fpr (same criterion as random experiment)."""
    order = np.argsort(scores)
    s = scores[order]
    b = benign_mask[order]
    n_benign = int(np.sum(b))
    grid = np.linspace(float(s.min()), float(s.max()), 200)
    best = None
    for t in grid:
        anomalous = s < t
        tp = int(np.sum((~b) & anomalous))
        fp = int(np.sum(b & anomalous))
        fn = int(np.sum((~b) & ~anomalous))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        fpr = fp / n_benign if n_benign else 0.0
        entry = {
            "threshold": round(float(t), 6),
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "fpr": round(fpr, 6),
        }
        if fpr <= max_fpr and (best is None or f1 > best["f1"]):
            best = entry
    return best


def _hybrid(label_code, confidence, anomaly_score, threshold, conf_threshold):
    """Deterministic PRD §10 hybrid for one flow (predicted label).

    Delegates to ml.hybrid.decision.hybrid_decision — the single source of
    truth. label_code is the SUPERVISED PREDICTED label, never the
    ground-truth label. A high-confidence BENIGN prediction is still rescued
    by a suspicious anomaly signal (UNKNOWN_SUSPICIOUS).
    """
    label = decode_label(int(label_code))
    return hybrid_decision(
        confidence=confidence,
        label=label,
        anomaly_score=anomaly_score,
        thresholds=HybridThresholds(
            known_confidence_threshold=conf_threshold,
            anomaly_threshold=threshold,
        ),
    )


def main() -> int:
    train_df = load_dev_subset(str(DEV_SUBSET))
    train_raw = preprocess_frame(train_df, scale=False)

    clf, unmap = _fit_supervised(train_raw)
    print(f"temporal supervised fit (12 classes, Mon-Thu)")

    if_clf, n_benign = _fit_if_benign(train_raw)
    print(f"temporal IF fit on {n_benign} benign rows")

    # Calibrate temporal IF threshold on temporal_3way/validation (Fri half A)
    cal_df = load_split(CAL_SPLIT)
    cal_raw = preprocess_frame(cal_df, scale=False)
    cal_scores = if_clf.decision_function(cal_raw.X)
    cal_benign = cal_raw.y_binary == 0
    calib = _calibrate(cal_scores, cal_benign, max_fpr=0.05)
    threshold = calib["threshold"]
    print(f"temporal IF threshold = {threshold:.4f} (F1={calib['f1']:.4f}, FPR={calib['fpr']:.4f})")

    # Report on temporal_3way/test (Fri half B) — disjoint from calibration
    tst_df = load_split(TST_SPLIT)
    tst_raw = preprocess_frame(tst_df, scale=False)

    y_prob = clf.predict_proba(tst_raw.X)
    sup_idx = np.argmax(y_prob, axis=1)
    y_pred_codes = np.array([unmap[int(i)] for i in sup_idx])
    y_pred_labels = [decode_label(int(c)) for c in y_pred_codes]
    confidence = y_prob[np.arange(len(y_prob)), sup_idx]

    anomaly_scores = if_clf.decision_function(tst_raw.X)

    # Multiclass supervised metrics on the 4 Friday classes (with unseen gap)
    sup_metrics = evaluate_multiclass(tst_raw.y_multiclass, y_pred_codes, CANONICAL_LABELS)

    # Per-class anomaly flagged rate + hybrid outcome (vectorized).
    # Hybrid uses the SUPERVISED PREDICTED label + confidence (PRD §10), never
    # the ground-truth label.
    test_labels = [decode_label(int(c)) for c in tst_raw.y_multiclass]
    hybrid_out = np.array([
        _hybrid(y_pred_codes[i], confidence[i], anomaly_scores[i],
                threshold, 0.75)
        for i in range(len(tst_raw.y_multiclass))
    ], dtype="object")
    per_class = {}
    for lbl in sorted(set(test_labels)):
        m = np.array([x == lbl for x in test_labels])
        a = anomaly_scores[m]
        flagged = float(np.mean(a < threshold))
        outs = {}
        for o in sorted(set(hybrid_out[m])):
            outs[o] = int(np.sum(hybrid_out[m] == o))
        pred_dist = {}
        for p in sorted(set(np.array(y_pred_labels)[m])):
            pred_dist[p] = int(np.sum(np.array(y_pred_labels)[m] == p))
        per_class[lbl] = {
            "n": int(m.sum()),
            "anomaly_p50": round(float(np.median(a)), 4),
            "pct_flagged_anomalous": round(flagged, 4),
            "hybrid_outcomes": outs,
            "supervised_predicted_labels": pred_dist,
        }
        print(f"{lbl:16s} n={int(m.sum()):>6d} flagged%={flagged:.3f} "
              f"outcomes={outs}")

    # Aggregate anomaly metrics on test (attacks = all non-BENIGN)
    tst_benign = tst_raw.y_binary == 0
    anomalous = anomaly_scores < threshold
    tp = int(np.sum((~tst_benign) & anomalous))
    fp = int(np.sum(tst_benign & anomalous))
    fn = int(np.sum((~tst_benign) & ~anomalous))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / int(np.sum(tst_benign)) if int(np.sum(tst_benign)) else 0.0

    result = {
        "experiment": "temporal (Option B, PRD §46)",
        "wording": "unseen / unknown anomaly simulation (NOT zero-day detection)",
        "train_set": "dev_temporal_train.parquet (Mon-Thu, 12 classes, 300k)",
        "test_set": "temporal_3way/test (Friday second half)",
        "calibration_set": "temporal_3way/validation (Friday first half)",
        "unseen_classes": ["Bot", "DDoS", "PortScan"],
        "supervised": {"model": "xgb_200", "multiclass_metrics": {
            "accuracy": sup_metrics["accuracy"],
            "macro_f1": sup_metrics["macro_f1"],
            "weighted_f1": sup_metrics["weighted_f1"],
        }},
        "anomaly": {
            "model": "IsolationForest (fit benign Mon-Thu only)",
            "threshold": threshold,
            "calibration_criterion": "best F1 subject to FPR <= 5% on temporal_3way/validation",
            "metrics": {
                "precision": round(precision, 6),
                "recall": round(recall, 6),
                "f1": round(f1, 6),
                "fpr": round(fpr, 6),
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
            },
        },
        "per_class": per_class,
    }
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = EVAL_DIR / "unknown_experiment_temporal.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    print(f"anomaly on Friday test: precision={precision:.4f} recall={recall:.4f} "
          f"F1={f1:.4f} FPR={fpr:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
