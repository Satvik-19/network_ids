"""select_supervised.py — Phase-2 final supervised model selection.

Light tuning of Random Forest vs XGBoost (PRD §32, §33). Avoids large
hyperparameter searches (PRD §58 "light tuning").

Selection criteria (PRD §33) — NOT accuracy alone:
  - macro F1, weighted F1
  - per-class recall
  - false-positive behaviour (binary FP rate on BENIGN test rows)
  - temporal generalisation (temporal experiment metrics)
  - inference cost (predict_proba wall time on the full test split)

Models:
  - RandomForestClassifier: class_weight="balanced", n_estimators/max_depth
    variants.
  - XGBClassifier: tree_method="hist", subsample=0.8, colsample_bytree=0.8,
    n_estimators/max_depth/learning_rate variants.

Two distinct experiments (PRD §26): random and temporal. Each experiment trains
binary + multiclass for every variant on its dev subset and evaluates on the
full test split.

Persists, per experiment, to
ml/evaluation/results/supervised_selection_{experiment}.json
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from xgboost import XGBClassifier

from ml.evaluation.metrics import evaluate_binary, evaluate_multiclass
from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.labels import CANONICAL_LABELS, decode_label
from ml.preprocessing.preprocess import preprocess_frame
from ml.preprocessing.subset import load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"
SEED = 42

DEV_SUBSET_PATHS = {
    "random": ROOT / "data" / "processed" / "dev_random_train.parquet",
    "temporal": ROOT / "data" / "processed" / "dev_temporal_train.parquet",
}
TEST_SPLITS = {
    "random": LoadConfig(config="random", split="test"),
    "temporal": LoadConfig(config="temporal", split="test"),
}


def build_variants() -> dict:
    """Small light-tuning grid. Keys are stable variant names."""
    return {
        "rf_baseline": {
            "family": "rf",
            "params": {"n_estimators": 100, "class_weight": "balanced"},
        },
        "rf_200": {
            "family": "rf",
            "params": {"n_estimators": 200, "class_weight": "balanced"},
        },
        "rf_depth": {
            "family": "rf",
            "params": {"n_estimators": 100, "max_depth": 20, "class_weight": "balanced"},
        },
        "xgb_baseline": {
            "family": "xgb",
            "params": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            },
        },
        "xgb_200": {
            "family": "xgb",
            "params": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            },
        },
        "xgb_lr": {
            "family": "xgb",
            "params": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.3,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            },
        },
    }


def make_classifier(family: str, params: dict):
    params = dict(params)
    if family == "rf":
        return RandomForestClassifier(random_state=SEED, n_jobs=-1, **params)
    if family == "xgb":
        return XGBClassifier(
            random_state=SEED,
            n_jobs=-1,
            tree_method="hist",
            verbosity=0,
            **params,
        )
    raise ValueError(f"unknown family {family}")


def _contiguous_fit(clf, X, y_multiclass):
    """Remap training classes to a contiguous range (handles temporal subset
    where only 12 of 15 classes are present). Returns (clf, remap, unmap)."""
    train_orig = sorted(set(int(v) for v in y_multiclass))
    remap = {orig: new for new, orig in enumerate(train_orig)}
    unmap = {new: orig for orig, new in remap.items()}
    y_fit = np.array([remap[int(v)] for v in y_multiclass], dtype="int64")
    clf.fit(X, y_fit)
    return clf, remap, unmap


def _binary_fp(y_true_bin, y_pred_bin) -> dict:
    """FP behaviour from a binary confusion matrix (BENIGN=0, attack=1)."""
    tn, fp, fn, tp = confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1]).ravel()
    benign_total = tn + fp
    return {
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn),
        "fp_rate": float(fp / benign_total) if benign_total else None,
    }


def run_experiment(experiment: str, variants: dict) -> dict:
    print(f"\n===== Supervised selection / {experiment} =====")
    train_df = load_dev_subset(str(DEV_SUBSET_PATHS[experiment]))
    test_df = load_split(TEST_SPLITS[experiment])
    print(f"train frame: {train_df.shape}  test frame: {test_df.shape}")

    train_raw = preprocess_frame(train_df, scale=False)
    test_raw = preprocess_frame(test_df, scale=False)
    train_classes = sorted(set(train_raw.labels))
    test_classes = sorted(set(test_raw.labels))
    print(f"train classes ({len(train_classes)}), test classes ({len(test_classes)})")

    results: dict = {
        "experiment": experiment,
        "seed": SEED,
        "train_rows": int(train_df.shape[0]),
        "test_rows": int(test_df.shape[0]),
        "train_classes": train_classes,
        "test_classes": test_classes,
        "criterion": "macro/weighted F1, per-class recall, FP behaviour, "
                     "temporal generalisation, inference cost (PRD §33)",
        "variants": {},
    }

    for name, v in variants.items():
        print(f"\n--- {experiment} / {name} ---")
        mres = {"family": v["family"], "params": v["params"], "binary": {}, "multiclass": {}}

        # ---- Binary ----
        clf = make_classifier(v["family"], v["params"])
        t0 = time.time()
        clf.fit(train_raw.X, train_raw.y_binary)
        tr_time = time.time() - t0
        t0 = time.time()
        y_pred = clf.predict(test_raw.X)
        inf_time = time.time() - t0
        y_prob = clf.predict_proba(test_raw.X)[:, 1] if hasattr(clf, "predict_proba") else None
        mres["binary"] = {
            **evaluate_binary(test_raw.y_binary, y_pred, y_prob),
            **{"fp_behaviour": _binary_fp(test_raw.y_binary, y_pred)},
            "train_time_s": round(tr_time, 3),
            "inference_time_s": round(inf_time, 3),
        }
        print(f"  binary: acc={mres['binary']['accuracy']:.4f} "
              f"f1={mres['binary']['f1']:.4f} "
              f"fp_rate={mres['binary']['fp_behaviour']['fp_rate']:.5f} "
              f"inf={mres['binary']['inference_time_s']}s")

        # ---- Multiclass ----
        clf = make_classifier(v["family"], v["params"])
        t0 = time.time()
        clf, remap, unmap = _contiguous_fit(clf, train_raw.X, train_raw.y_multiclass)
        tr_time = time.time() - t0
        t0 = time.time()
        y_pred_m = clf.predict(test_raw.X)
        inf_time = time.time() - t0
        y_pred_m = np.array([unmap[int(x)] for x in y_pred_m], dtype="int64")
        mres["multiclass"] = {
            **evaluate_multiclass(test_raw.y_multiclass, y_pred_m, CANONICAL_LABELS),
            "train_time_s": round(tr_time, 3),
            "inference_time_s": round(inf_time, 3),
        }
        print(f"  multiclass: acc={mres['multiclass']['accuracy']:.4f} "
              f"macroF1={mres['multiclass']['macro_f1']:.4f} "
              f"wF1={mres['multiclass']['weighted_f1']:.4f} "
              f"inf={mres['multiclass']['inference_time_s']}s")

        results["variants"][name] = mres

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = EVAL_DIR / f"supervised_selection_{experiment}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"wrote {path}")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-2 supervised model selection")
    ap.add_argument("--experiments", nargs="+", default=["random", "temporal"],
                    choices=["random", "temporal"])
    args = ap.parse_args()
    variants = build_variants()
    for exp in args.experiments:
        run_experiment(exp, variants)
    print("\nSupervised selection complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
