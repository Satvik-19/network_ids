"""train_isolation_forest.py — Train + calibrate the Phase-2 anomaly detector.

Protocol (PRD §34, §47):
  - IsolationForest fit on BENIGN training traffic ONLY (no scaling,
    DATA_ML_CONTRACT §13).
  - Threshold calibrated on a held-out validation set, NEVER on the reported
    test set.
  - The raw ``decision_function`` value is the anomaly_score semantic
    (lower = more abnormal). It is NOT a 0-1 probability.
  - Reported anomaly metrics are computed on a DISJOINT test half so that no
    threshold is tuned on the reported set.

Data split used (verified disjoint):
  - Fit:      benign rows of data/processed/dev_random_train.parquet
              (88,314 rows, drawn from random/train).
  - Calibrate: random_3way/validation (282,788 rows; stratified slice of the
              random partition that is disjoint from random/train).
  - Report:   random_3way/test (282,788 rows; the other 10% slice, disjoint
              from the calibration set).

Outputs:
  - ml/artifacts/isolation_forest.joblib          (runtime artifact)
  - ml/artifacts/isolation_forest_metadata.json   (provenance + params)
  - ml/evaluation/results/anomaly_calibration_random.json
  - ml/evaluation/results/anomaly_evaluation_random.json
  - config/config.yaml                            (calibrated anomaly_threshold)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.preprocess import CANONICAL_FEATURE_COLUMNS, FEATURE_COUNT, preprocess_frame
from ml.preprocessing.subset import load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"
SEED = 42

DEV_SUBSET = ROOT / "data" / "processed" / "dev_random_train.parquet"
CAL_SPLIT = LoadConfig(config="random_3way", split="validation")
TST_SPLIT = LoadConfig(config="random_3way", split="test")

IF_PARAMS = {
    "n_estimators": 200,
    "max_samples": "auto",
    "contamination": "auto",
    "random_state": SEED,
    "n_jobs": -1,
}


def _scores_by_class(df, clf):
    raw = preprocess_frame(df, scale=False)
    scores = clf.decision_function(raw.X)
    benign_mask = raw.y_binary == 0
    return scores, benign_mask, raw


def calibrate_threshold(scores, benign_mask, max_fpr: float = 0.05) -> dict:
    """Sweep thresholds; pick the threshold with best F1 subject to FPR <= max_fpr.

    Pure max-F1 over-prioritises recall when attacks dominate the calibration
    set (e.g. Friday in the temporal experiment), yielding an unusable FPR.
    Constraining FPR first keeps the detector deployable at a bounded false
    alarm rate (PRD §57, DEC-00X). Threshold is NEVER tuned on the reported set.
    """
    order = np.argsort(scores)
    s = scores[order]
    b = benign_mask[order]
    n_benign = int(np.sum(b))
    grid = np.linspace(float(s.min()), float(s.max()), 200)
    best = None
    sweep = []
    for t in grid:
        anomalous = s < t
        tp = int(np.sum((~b) & anomalous))
        fp = int(np.sum(b & anomalous))
        fn = int(np.sum((~b) & ~anomalous))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        fpr = fp / n_benign if n_benign else 0.0
        sweep.append({
            "threshold": round(float(t), 6),
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "fpr": round(fpr, 6),
            "n_flagged": int(np.sum(anomalous)),
        })
        if fpr <= max_fpr and (best is None or f1 > best["f1"]):
            best = sweep[-1]
    if best is None:
        best = max(sweep, key=lambda e: e["f1"])
    return {"best_threshold": best, "sweep": sweep}


def _eval_at(scores, benign_mask, threshold) -> dict:
    anomalous = scores < threshold
    tp = int(np.sum((~benign_mask) & anomalous))
    fp = int(np.sum(benign_mask & anomalous))
    fn = int(np.sum((~benign_mask) & ~anomalous))
    tn = int(np.sum(benign_mask & ~anomalous))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "threshold": float(threshold),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "fpr": round(fpr, 6),
        "n_flows": int(len(scores)),
    }


def main() -> int:
    # ---- Fit on benign training only ----
    train_df = load_dev_subset(str(DEV_SUBSET))
    train_raw = preprocess_frame(train_df, scale=False)
    benign = train_raw.y_binary == 0
    X_benign = train_raw.X[benign]
    print(f"fit IF on {X_benign.shape[0]} benign rows (of {len(train_raw.X)})")

    clf = IsolationForest(**IF_PARAMS)
    t0 = time.time()
    clf.fit(X_benign)
    fit_time = time.time() - t0
    print(f"fit: {fit_time:.1f}s")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, ARTIFACTS / "isolation_forest.joblib")
    meta = {
        "model": "IsolationForest",
        "phase": "phase-2-final",
        "trained_on": "benign rows of dev_random_train.parquet "
                      f"({X_benign.shape[0]} rows, seed {SEED})",
        "params": IF_PARAMS,
        "feature_count": FEATURE_COUNT,
        "feature_order": CANONICAL_FEATURE_COLUMNS,
        "score_semantics": "raw decision_function; lower = more abnormal; "
                           "anomalous when score < anomaly_threshold. "
                           "Not a 0-1 probability.",
        "no_scaling": True,
        "fit_time_s": round(fit_time, 3),
    }
    (ARTIFACTS / "isolation_forest_metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"wrote ml/artifacts/isolation_forest.joblib")

    # ---- Calibrate threshold on random_3way/validation ----
    cal_df = load_split(CAL_SPLIT)
    cal_scores, cal_benign, _ = _scores_by_class(cal_df, clf)
    print(f"calibration set: {cal_df.shape[0]} rows")
    max_fpr = 0.05
    calib = calibrate_threshold(cal_scores, cal_benign, max_fpr=max_fpr)
    threshold = calib["best_threshold"]["threshold"]
    print(f"calibrated anomaly_threshold = {threshold:.4f} "
          f"(F1={calib['best_threshold']['f1']:.4f}, "
          f"FPR={calib['best_threshold']['fpr']:.4f}, max_fpr={max_fpr})")

    # ---- Report on the disjoint random_3way/test ----
    tst_df = load_split(TST_SPLIT)
    tst_scores, tst_benign, tst_raw = _scores_by_class(tst_df, clf)
    eval_metrics = _eval_at(tst_scores, tst_benign, threshold)
    print(f"reported (random_3way/test): precision={eval_metrics['precision']:.4f} "
          f"recall={eval_metrics['recall']:.4f} F1={eval_metrics['f1']:.4f} "
          f"FPR={eval_metrics['fpr']:.4f}")

    # Score distributions (PRD §47)
    benign_scores = tst_scores[tst_benign]
    attack_scores = tst_scores[~tst_benign]
    distributions = {
        "benign": {
            "min": round(float(benign_scores.min()), 6),
            "p25": round(float(np.percentile(benign_scores, 25)), 6),
            "p50": round(float(np.percentile(benign_scores, 50)), 6),
            "p75": round(float(np.percentile(benign_scores, 75)), 6),
            "max": round(float(benign_scores.max()), 6),
        },
        "attack": {
            "min": round(float(attack_scores.min()), 6),
            "p25": round(float(np.percentile(attack_scores, 25)), 6),
            "p50": round(float(np.percentile(attack_scores, 50)), 6),
            "p75": round(float(np.percentile(attack_scores, 75)), 6),
            "max": round(float(attack_scores.max()), 6),
        },
    }
    print(f"benign score p50={distributions['benign']['p50']}  "
          f"attack score p50={distributions['attack']['p50']}")

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    calib_out = {
        "experiment": "random",
        "fit_on": "benign dev_random_train rows",
        "calibration_set": "random_3way/validation",
        "reported_set": "random_3way/test",
        "calibration_criterion": "max F1 subject to FPR <= 5% on random_3way/validation",
        "max_fpr": 0.05,
        "best": calib["best_threshold"],
        "n_sweep_points": len(calib["sweep"]),
        "sweep": calib["sweep"],
    }
    (EVAL_DIR / "anomaly_calibration_random.json").write_text(
        json.dumps(calib_out, indent=2), encoding="utf-8"
    )

    eval_out = {
        "experiment": "random",
        "reported_set": "random_3way/test",
        "threshold": eval_metrics["threshold"],
        "metrics": eval_metrics,
        "score_distributions": distributions,
    }
    (EVAL_DIR / "anomaly_evaluation_random.json").write_text(
        json.dumps(eval_out, indent=2), encoding="utf-8"
    )
    print(f"wrote anomaly_calibration_random.json + anomaly_evaluation_random.json")

    # ---- Update config.yaml anomaly_threshold ----
    _update_config_threshold(threshold)
    return 0


def _update_config_threshold(threshold: float) -> None:
    """Atomically replace the anomaly_threshold placeholder in config.yaml."""
    cfg_path = ROOT / "config" / "config.yaml"
    lines = cfg_path.read_text(encoding="utf-8").splitlines(keepends=True)
    out = []
    replaced = False
    for line in lines:
        if line.strip().startswith("anomaly_threshold:"):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}anomaly_threshold: {threshold:.4f}  # calibrated "
                       f"{__import__('datetime').date.today().isoformat()} "
                       f"(random_3way/validation, FPR<=5%)\n")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        raise RuntimeError("anomaly_threshold not found in config.yaml")
    new_text = "".join(out)
    data = new_text.encode("utf-8")
    tmp = cfg_path.with_suffix(cfg_path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(cfg_path)
    check = cfg_path.read_text(encoding="utf-8")
    assert "anomaly_threshold:" in check and cfg_path.exists()
    print(f"updated config/config.yaml anomaly_threshold -> {threshold:.4f}")


if __name__ == "__main__":
    raise SystemExit(main())
