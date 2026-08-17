"""export_inference_model.py — Export the Phase-1 inference model.

Phase 1 does NOT select the final classifier (that is Phase 2 evaluation).
For the phase-1 API gate we need one saved baseline supervised model that
``/api/predict`` loads. We promote the strongest Phase-1 baseline on the
RANDOM experiment (trained on in-distribution data) to a stable path.

Current choice (2026-08-09): XGBoost multiclass, random experiment
  weighted-F1 0.9987, macro-F1 0.8877 on random/test.

Artifacts written to ml/artifacts/inference/:
  - model.joblib          the promoted classifier (canonical int classes)
  - model_metadata.json   provenance + expected inputs/outputs
  - feature_order.json    exact canonical feature order for the API
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib

from ml.preprocessing.preprocess import CANONICAL_FEATURE_COLUMNS, FEATURE_COUNT
from ml.preprocessing.labels import FAMILY_MAP, INT_TO_LABEL, CANONICAL_LABELS

ROOT = Path(__file__).resolve().parents[2]
BASELINES = ROOT / "ml" / "artifacts" / "baselines"
INFERENCE = ROOT / "ml" / "artifacts" / "inference"

EXPERIMENT = "random"
MODEL = "xgb"
TASK = "multiclass"
SOURCE = BASELINES / f"{EXPERIMENT}_{MODEL}_{TASK}.joblib"


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(f"{SOURCE} not found; run train_baseline first")
    INFERENCE.mkdir(parents=True, exist_ok=True)

    dst = INFERENCE / "model.joblib"
    shutil.copyfile(SOURCE, dst)

    classes = [INT_TO_LABEL[i] for i in range(len(INT_TO_LABEL))]
    metadata = {
        "model": f"{MODEL}-{TASK}",
        "experiment": EXPERIMENT,
        "dataset": "lacg030175/CICIDS2017",
        "revision": "d071fd53782d9ca7cdc15173b8ceb858fea04628",
        "trained_on": "dev_random_train.parquet (300k class-aware subset)",
        "feature_count": FEATURE_COUNT,
        "feature_order": CANONICAL_FEATURE_COLUMNS,
        "classes": classes,
        "family_map": FAMILY_MAP,
        "phase": "phase-1-baseline",
        "note": "Provisional Phase-1 baseline; final model selection in Phase 2.",
        "source_artifact": SOURCE.name,
    }
    (INFERENCE / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (INFERENCE / "feature_order.json").write_text(
        json.dumps(CANONICAL_FEATURE_COLUMNS, indent=2), encoding="utf-8"
    )
    print(f"promoted {SOURCE.name} -> {dst}")
    print(f"classes: {classes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
