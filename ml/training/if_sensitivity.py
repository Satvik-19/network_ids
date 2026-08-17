"""if_sensitivity.py — IsolationForest sensitivity + threshold trade-off audit.

Phase-2 closure audit (2026-08-09): checks whether the deployed IsolationForest
config is robust to light hyperparameter variation under a FIXED, leakage-free
methodology. No test labels are used for any choice: thresholds are calibrated
on validation splits only, every experiment fixes random_state=42, and the
calibration criterion (max F1 subject to FPR <= max_fpr) is identical to the
deployed training script.

Two protocols (PRD 26 — random and temporal must stay distinct experiments):

  Part A  RANDOM (known-malicious recall): fit on benign rows of
          dev_random_train.parquet, calibrate on random_3way/validation,
          report on random_3way/test.
  Part B  TEMPORAL (unseen recall): fit on benign rows of
          dev_temporal_train.parquet, calibrate on temporal_3way/validation,
          report on temporal_3way/test (Friday). Unseen classes: Bot, DDoS,
          PortScan. Wording is "unseen behaviour", never "zero-day".

Configs (vary n_estimators / max_samples / max_features only, seed 42 fixed):
  1. if_200_auto_1.0  n_estimators=200 max_samples="auto" max_features=1.0   (deployed)
  2. if_400_auto_1.0  n_estimators=400 max_samples="auto" max_features=1.0
  3. if_200_256_1.0   n_estimators=200 max_samples=256    max_features=1.0
  4. if_200_auto_0.5  n_estimators=200 max_samples="auto" max_features=0.5

A threshold trade-off table is emitted for the DEPLOYED config on the temporal
(unknown/unseen) protocol so the reader can see FPR <-> recall behaviour for
the unseen classes directly.

Outputs:
  - ml/evaluation/results/if_sensitivity.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.labels import decode_label
from ml.preprocessing.preprocess import preprocess_frame
from ml.preprocessing.subset import load_dev_subset
from ml.training.train_isolation_forest import _eval_at, calibrate_threshold

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"
SEED = 42
MAX_FPR = 0.05

RANDOM = {
    "dev": ROOT / "data" / "processed" / "dev_random_train.parquet",
    "cal": LoadConfig(config="random_3way", split="validation"),
    "tst": LoadConfig(config="random_3way", split="test"),
}
TEMPORAL = {
    "dev": ROOT / "data" / "processed" / "dev_temporal_train.parquet",
    "cal": LoadConfig(config="temporal_3way", split="validation"),
    "tst": LoadConfig(config="temporal_3way", split="test"),
}

CONFIGS = {
    "if_200_auto_1.0": {"n_estimators": 200, "max_samples": "auto", "max_features": 1.0},
    "if_400_auto_1.0": {"n_estimators": 400, "max_samples": "auto", "max_features": 1.0},
    "if_200_256_1.0": {"n_estimators": 200, "max_samples": 256, "max_features": 1.0},
    "if_200_auto_0.5": {"n_estimators": 200, "max_samples": "auto", "max_features": 0.5},
}

UNSEEN_CLASSES = ["Bot", "DDoS", "PortScan"]


def _make_if(params: dict) -> IsolationForest:
    return IsolationForest(
        contamination="auto",
        random_state=SEED,
        n_jobs=-1,
        **dict(params),
    )


def _fit_benign(protocol: dict):
    df = load_dev_subset(str(protocol["dev"]))
    raw = preprocess_frame(df, scale=False)
    benign = raw.y_binary == 0
    return raw.X[benign], int(benign.sum())


def _per_class_recall(tst_raw, scores, threshold):
    labels = [decode_label(int(l)) for l in tst_raw.y_multiclass]
    flagged = scores < threshold
    out = {}
    for cls in sorted(set(labels)):
        m = np.array([l == cls for l in labels])
        if m.sum() == 0:
            continue
        out[cls] = {
            "n": int(m.sum()),
            "recall": round(float(flagged[m].mean()), 6),
        }
    return out


def run_protocol(protocol: dict, params: dict, per_class: bool = False) -> dict:
    clf = _make_if(params)
    X_benign, n_benign = _fit_benign(protocol)
    t0 = time.time()
    clf.fit(X_benign)
    fit_time = time.time() - t0

    cal_df = load_split(protocol["cal"])
    cal_raw = preprocess_frame(cal_df, scale=False)
    cal_scores = clf.decision_function(cal_raw.X)
    cal_benign = cal_raw.y_binary == 0
    calib = calibrate_threshold(cal_scores, cal_benign, max_fpr=MAX_FPR)
    threshold = calib["best_threshold"]["threshold"]

    tst_df = load_split(protocol["tst"])
    tst_raw = preprocess_frame(tst_df, scale=False)
    t0 = time.time()
    tst_scores = clf.decision_function(tst_raw.X)
    inf_time = time.time() - t0
    tst_benign = tst_raw.y_binary == 0
    ev = _eval_at(tst_scores, tst_benign, threshold)

    res = {
        "threshold": threshold,
        "calibration": {
            "f1": calib["best_threshold"]["f1"],
            "fpr": calib["best_threshold"]["fpr"],
            "max_fpr": MAX_FPR,
        },
        "evaluation": ev,
        "fit_time_s": round(fit_time, 2),
        "inference_time_s": round(inf_time, 3),
        "fit_benign_rows": n_benign,
    }
    if per_class:
        res["per_class_recall"] = _per_class_recall(tst_raw, tst_scores, threshold)
    return res


def _tradeoff_table(tst_raw, tst_scores, tst_benign):
    """Threshold trade-off table for the DEPLOYED config (temporal protocol)."""
    order = np.argsort(tst_scores)
    s = tst_scores[order]
    b = tst_benign[order]
    n_benign = int(np.sum(b))
    labels = np.array([decode_label(int(l)) for l in tst_raw.y_multiclass])[order]
    unseen_mask = np.isin(labels, UNSEEN_CLASSES)
    rows = []
    grid = np.linspace(float(s.min()), float(s.max()), 40)
    for t in grid:
        anomalous = s < t
        tp = int(np.sum((~b) & anomalous))
        fp = int(np.sum(b & anomalous))
        fn = int(np.sum((~b) & ~anomalous))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        fpr = fp / n_benign if n_benign else 0.0
        unseen_recall = float(np.sum(unseen_mask & anomalous) / max(1, int(np.sum(unseen_mask))))
        rows.append({
            "threshold": round(float(t), 6),
            "benign_fpr": round(fpr, 6),
            "attack_recall": round(recall, 6),
            "unseen_recall": round(unseen_recall, 6),
            "precision": round(precision, 6),
            "f1": round(f1, 6),
        })
    return rows


def main() -> int:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "audit": "Phase-2 IF sensitivity (2026-08-09)",
        "methodology_fixed": {
            "seed": SEED,
            "calibration_criterion": f"max F1 subject to FPR <= {MAX_FPR} "
                                     "on the validation split (never the test set)",
            "wording": "unseen behaviour / unknown anomaly simulation",
        "protocols": ["random (known-malicious recall)",
                      "temporal (unseen recall, Friday)"],
        "note_max_samples_auto": "sklearn IsolationForest max_samples='auto' "
                                 "resolves to min(256, n_samples); with fits on "
                                 "88,314 and 202,353 benign rows this equals 256, "
                                 "so configs if_200_auto_1.0 and if_200_256_1.0 "
                                 "are the same model (an intentional protocol "
                                 "determinism check).",
        },
        "configs": {},
    }

    for name, params in CONFIGS.items():
        print(f"\n=== {name} ===")
        rand = run_protocol(RANDOM, params, per_class=False)
        temp = run_protocol(TEMPORAL, params, per_class=True)
        out["configs"][name] = {
            "params": params,
            "random": rand,
            "temporal": temp,
        }
        print(f"  random:  thr={rand['threshold']:.4f} testFPR={rand['evaluation']['fpr']:.4f} "
              f"recall={rand['evaluation']['recall']:.4f} F1={rand['evaluation']['f1']:.4f} "
              f"inf={rand['inference_time_s']}s")
        print(f"  temporal:thr={temp['threshold']:.4f} testFPR={temp['evaluation']['fpr']:.4f} "
              f"recall={temp['evaluation']['recall']:.4f} F1={temp['evaluation']['f1']:.4f} "
              f"unseen recall={temp['per_class_recall'].get('DDoS', {}).get('recall')}")

    # Trade-off table for the DEPLOYED config on the temporal (unseen) protocol.
    print("\n=== threshold trade-off table (deployed config, temporal/Friday) ===")
    deployed = CONFIGS["if_200_auto_1.0"]
    clf = _make_if(deployed)
    X_benign, _ = _fit_benign(TEMPORAL)
    clf.fit(X_benign)
    tst_df = load_split(TEMPORAL["tst"])
    tst_raw = preprocess_frame(tst_df, scale=False)
    tst_scores = clf.decision_function(tst_raw.X)
    tst_benign = tst_raw.y_binary == 0
    table = _tradeoff_table(tst_raw, tst_scores, tst_benign)
    out["threshold_tradeoff_table_deployed_temporal"] = table
    header = f"{'threshold':>10s} {'benign_FPR':>10s} {'attack_rec':>10s} {'unseen_rec':>10s} {'F1':>8s}"
    print(header)
    for r in table:
        print(f"{r['threshold']:10.4f} {r['benign_fpr']:10.4f} {r['attack_recall']:10.4f} "
              f"{r['unseen_recall']:10.4f} {r['f1']:8.4f}")

    path = EVAL_DIR / "if_sensitivity.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
