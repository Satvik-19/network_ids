"""train_final_supervised.py — Train and export the Phase-2 final supervised model.

The Phase-2 selection (ml/training/select_supervised.py) chose XGBoost
(n_estimators=200, max_depth=6, learning_rate=0.1) on the RANDOM experiment:
macro-F1 0.8898, weighted-F1 0.9988, binary FP rate 0.00143 on random/test
and the best per-class recall on rare classes (Web Attacks, Infiltration).

This script retrains that exact variant on the same dev_random_train subset
(seed 42) and writes the FINAL runtime artifact:

  ml/artifacts/supervised_model.joblib
  ml/artifacts/supervised_model_metadata.json

It then evaluates on random/test and persists
ml/evaluation/results/final_supervised_random.json.

Multiclass model only (the API derives label/family from it; binary is a
derived view). The model is trained on the full 15-class canonical label
encoding (0..14), so classes_ == list(range(15)).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
from xgboost import XGBClassifier

from ml.evaluation.metrics import evaluate_multiclass
from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.labels import CANONICAL_LABELS
from ml.preprocessing.preprocess import CANONICAL_FEATURE_COLUMNS, FEATURE_COUNT, preprocess_frame
from ml.preprocessing.subset import load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"
SEED = 42

DEV_SUBSET = ROOT / "data" / "processed" / "dev_random_train.parquet"
TEST_SPLIT = LoadConfig(config="random", split="test")

MODEL_PARAMS = {
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


def main() -> int:
    if not DEV_SUBSET.exists():
        raise FileNotFoundError(f"{DEV_SUBSET} missing; build dev subsets first")

    train_df = load_dev_subset(str(DEV_SUBSET))
    test_df = load_split(TEST_SPLIT)
    print(f"train: {train_df.shape}  test: {test_df.shape}")

    train_raw = preprocess_frame(train_df, scale=False)
    test_raw = preprocess_frame(test_df, scale=False)

    clf = XGBClassifier(**MODEL_PARAMS)
    t0 = time.time()
    clf.fit(train_raw.X, train_raw.y_multiclass)
    train_time = time.time() - t0
    assert list(clf.classes_) == list(range(15)), clf.classes_
    print(f"fit: {train_time:.1f}s")

    t0 = time.time()
    y_pred = clf.predict(test_raw.X)
    inf_time = time.time() - t0
    y_pred = np.array([int(x) for x in y_pred], dtype="int64")
    metrics = evaluate_multiclass(test_raw.y_multiclass, y_pred, CANONICAL_LABELS)
    metrics["train_time_s"] = round(train_time, 3)
    metrics["inference_time_s"] = round(inf_time, 3)
    print(f"random/test: acc={metrics['accuracy']:.4f} "
          f"macroF1={metrics['macro_f1']:.4f} wF1={metrics['weighted_f1']:.4f}")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACTS / "supervised_model.joblib"
    joblib.dump(clf, model_path)

    metadata = {
        "model": "xgb-multiclass",
        "variant": "xgb_200",
        "task": "multiclass",
        "phase": "phase-2-final",
        "dataset": "lacg030175/CICIDS2017",
        "revision": "d071fd53782d9ca7cdc15173b8ceb858fea04628",
        "trained_on": "dev_random_train.parquet (300k class-aware subset, seed 42)",
        "experiment": "random",
        "params": MODEL_PARAMS,
        "feature_count": FEATURE_COUNT,
        "feature_order": CANONICAL_FEATURE_COLUMNS,
        "classes": CANONICAL_LABELS,
        "selection_evidence": "select_supervised.py: macro-F1 0.8898, wF1 0.9988, "
                              "FP rate 0.00143 on random/test (PRD §33)",
        "random_test_metrics": {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
        },
        "source_selection_script": "ml/training/select_supervised.py",
    }
    meta_path = ARTIFACTS / "supervised_model_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"wrote {model_path}")
    print(f"wrote {meta_path}")

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "experiment": "random",
        "test_split": "random/test",
        "model": "xgb_200",
        "metrics": metrics,
        "metadata_ref": str(meta_path.relative_to(ROOT)),
    }
    rpath = EVAL_DIR / "final_supervised_random.json"
    rpath.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {rpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
