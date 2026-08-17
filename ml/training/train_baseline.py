"""train_baseline.py — Train Phase-1 ML baselines (LR / RF / XGBoost).

Runs two DISTINCT experiments (PRD §26):
  - random:  train on dev subset built from random/train, evaluate on random/test.
  - temporal: train on dev subset built from temporal/train (Mon–Thu),
              evaluate on temporal/test (Fri).

For each experiment, for each model, trains binary and multiclass classifiers.
Logistic Regression is scaled (scaler fit on TRAIN only); RF/XGBoost are NOT
standardised (DATA_ML_CONTRACT §13).

Models are kept deliberately simple (no large hyperparameter search).
Reproducible: fixed seed, fixed dev subsets, exact model params recorded.

Persists, per model, under ml/artifacts/baselines/:
  - {model}_binary.joblib / {model}_multiclass.joblib
  - metrics JSON (evaluation/evaluation/baseline_metrics_{exp}_{model}_*.json)

NOTE: For the temporal experiment the multiclass TRAIN set contains only the
12 Monday–Thursday classes, while temporal/test contains 4 classes (BENIGN,
PortScan, DDoS, Bot). PortScan/DDoS/Bot are therefore UNSEEN during temporal
multiclass training. This is the intended harder generalisation evaluation
(PRD §26B) — do not force the final runtime model to use this artifact.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ml.evaluation.metrics import evaluate_binary, evaluate_multiclass
from ml.preprocessing.labels import CANONICAL_LABELS, INT_TO_LABEL, decode_label
from ml.preprocessing.preprocess import fit_scaler, preprocess_frame
from ml.preprocessing.subset import load_dev_subset
from ml.preprocessing.dataset import LoadConfig, load_split

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"
BASELINES = ARTIFACTS / "baselines"
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"

SEED = 42

# Dev subset source per experiment (config, split) used to TRAIN the baseline.
# The dev subsets were materialised by ml/preprocessing/subset.py.
DEV_SUBSET_PATHS = {
    "random": ROOT / "data" / "processed" / "dev_random_train.parquet",
    "temporal": ROOT / "data" / "processed" / "dev_temporal_train.parquet",
}

# Full test set source per experiment (config, split).
TEST_SPLITS = {
    "random": LoadConfig(config="random", split="test"),
    "temporal": LoadConfig(config="temporal", split="test"),
}


def build_model(name: str):
    """Return a fresh, simple model instance (per PRD §32)."""
    if name == "lr":
        return LogisticRegression(max_iter=1000, random_state=SEED, n_jobs=-1)
    if name == "rf":
        return RandomForestClassifier(
            n_estimators=100, random_state=SEED, n_jobs=-1, class_weight="balanced"
        )
    if name == "xgb":
        return XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=SEED,
            n_jobs=-1,
            tree_method="hist",
            verbosity=0,
        )
    raise ValueError(f"unknown model {name}")


def run_experiment(experiment: str, models: list[str]) -> dict:
    """Train and evaluate baselines for one experiment. Returns result dict."""
    print(f"\n===== Experiment: {experiment} =====")

    dev_path = DEV_SUBSET_PATHS[experiment]
    if not dev_path.exists():
        raise FileNotFoundError(
            f"Dev subset missing: {dev_path}. Build it first with "
            f"ml/preprocessing/subset.py (build_dev_subset)."
        )
    train_df = load_dev_subset(str(dev_path))
    test_df = load_split(TEST_SPLITS[experiment])

    print(f"train frame: {train_df.shape}  test frame: {test_df.shape}")

    # Preprocess train (raw features; scaling deferred to model family).
    train_raw = preprocess_frame(train_df, scale=False)
    test_raw = preprocess_frame(test_df, scale=False)

    # Train/test must share the identical class set for multiclass evaluation.
    # Multiclass: encode canonical labels; temporal test may contain classes
    # unseen in train — handled by aligning labels.
    train_classes = sorted(set(train_raw.labels))
    test_classes = sorted(set(test_raw.labels))
    print(f"train classes ({len(train_classes)}): {train_classes}")
    print(f"test classes ({len(test_classes)}): {test_classes}")

    # Binary: BENIGN=0 vs attack=1. Unseen attack classes are still "attack".
    results: dict = {"experiment": experiment, "train_rows": int(train_df.shape[0]),
                     "test_rows": int(test_df.shape[0]),
                     "train_classes": train_classes, "test_classes": test_classes,
                     "models": {}}

    for model_name in models:
        print(f"\n--- {experiment} / {model_name} ---")
        mres = {"model": model_name, "binary": {}, "multiclass": {}}

        # ---- Binary ----
        y_tr, y_te = train_raw.y_binary, test_raw.y_binary
        if model_name == "lr":
            scaler = fit_scaler(train_raw.X)
            clf = build_model(model_name)
            t0 = time.time()
            clf.fit(scaler.transform(train_raw.X), y_tr)
            tr_time = time.time() - t0
            X_te = scaler.transform(test_raw.X)
        else:
            scaler = None
            clf = build_model(model_name)
            t0 = time.time()
            clf.fit(train_raw.X, y_tr)
            tr_time = time.time() - t0
            X_te = test_raw.X

        t0 = time.time()
        y_pred = clf.predict(X_te)
        inf_time = time.time() - t0

        y_prob = None
        if hasattr(clf, "predict_proba"):
            y_prob = clf.predict_proba(X_te)[:, 1]
        mres["binary"] = {
            **evaluate_binary(y_te, y_pred, y_prob),
            "train_time_s": round(tr_time, 3),
            "inference_time_s": round(inf_time, 3),
            "scaler_fit": model_name == "lr",
        }
        _save_model(clf, scaler, experiment, model_name, "binary")
        print(f"binary: acc={mres['binary']['accuracy']:.4f} "
              f"F1={mres['binary']['f1']:.4f} AUC={mres['binary']['roc_auc']}")

        # ---- Multiclass ----
        y_tr_m, y_te_m = train_raw.y_multiclass, test_raw.y_multiclass
        # XGBoost requires contiguous class ids 0..k-1. When train lacks some
        # canonical classes (temporal train has only 12 of 15), remap the
        # classes present in train to a contiguous range, train, then map
        # predictions back to canonical integer ids for evaluation.
        train_orig_classes = sorted(set(y_tr_m.tolist()))
        remap = {orig: new for new, orig in enumerate(train_orig_classes)}
        unmap = {new: orig for orig, new in remap.items()}
        y_tr_m_fit = np.array([remap[int(v)] for v in y_tr_m], dtype="int64")
        if model_name == "lr":
            scaler = fit_scaler(train_raw.X)
            clf = build_model(model_name)
            t0 = time.time()
            clf.fit(scaler.transform(train_raw.X), y_tr_m_fit)
            tr_time = time.time() - t0
            X_te = scaler.transform(test_raw.X)
        else:
            scaler = None
            clf = build_model(model_name)
            t0 = time.time()
            clf.fit(train_raw.X, y_tr_m_fit)
            tr_time = time.time() - t0
            X_te = test_raw.X

        t0 = time.time()
        y_pred_m = clf.predict(X_te)
        inf_time = time.time() - t0
        y_pred_m = np.array([unmap[int(v)] for v in y_pred_m], dtype="int64")

        mres["multiclass"] = {
            **evaluate_multiclass(y_te_m, y_pred_m, CANONICAL_LABELS),
            "train_time_s": round(tr_time, 3),
            "inference_time_s": round(inf_time, 3),
            "scaler_fit": model_name == "lr",
        }
        _save_model(clf, scaler, experiment, model_name, "multiclass")
        print(f"multiclass: acc={mres['multiclass']['accuracy']:.4f} "
              f"macroF1={mres['multiclass']['macro_f1']:.4f} "
              f"wF1={mres['multiclass']['weighted_f1']:.4f}")

        results["models"][model_name] = mres

    _save_metrics(experiment, results)
    return results


def _save_model(clf, scaler, experiment, model_name, task):
    BASELINES.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, BASELINES / f"{experiment}_{model_name}_{task}.joblib")
    if scaler is not None:
        joblib.dump(scaler, BASELINES / f"{experiment}_{model_name}_{task}_scaler.joblib")


def _save_metrics(experiment, results):
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = EVAL_DIR / f"baseline_metrics_{experiment}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"wrote {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Train Phase-1 baselines")
    ap.add_argument("--experiments", nargs="+", default=["random", "temporal"],
                    choices=["random", "temporal"])
    ap.add_argument("--models", nargs="+", default=["lr", "rf", "xgb"],
                    choices=["lr", "rf", "xgb"])
    args = ap.parse_args()

    for exp in args.experiments:
        run_experiment(exp, args.models)
    print("\nBaseline training complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
