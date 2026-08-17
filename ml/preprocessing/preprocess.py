"""preprocess.py — Deterministic Phase-1 preprocessing pipeline.

Transforms a raw CICIDS2017 DataFrame (80 cols) into canonical model input.

Operations (deterministic; no test-data leakage):
1. Column validation: assert the expected raw columns exist.
2. Duplicate-column cleanup: drop ``Fwd Header Length.1`` (keeps
   ``Fwd Header Length``). Verified bit-for-bit identical on all canonical
   partitions (BUG-001).
3. Non-finite handling: replace inf with NaN, then fill NaN with a
   deterministic value (0.0). Observed data has zero NaN/inf on the
   canonical partitions; the fill is a safety net so model input is always
   finite.
4. Label normalisation (raw -> canonical) and family mapping.
5. Canonical feature ordering per ``feature_schema.json``.
6. Optional scaling for Logistic Regression — scaler fitted on TRAIN ONLY.

The pipeline is stateless except for an optional fitted StandardScaler.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ml.preprocessing.labels import (
    binary_target,
    encode_label,
    family_for,
    normalize_label,
)

# Raw schema facts (verified 2026-08-09). Single source for the loader path.
RAW_FEATURE_COLUMNS: List[str] = [
    "Destination Port", "Flow Duration", "Total Fwd Packets",
    "Total Backward Packets", "Total Length of Fwd Packets",
    "Total Length of Bwd Packets", "Fwd Packet Length Max",
    "Fwd Packet Length Min", "Fwd Packet Length Mean",
    "Fwd Packet Length Std", "Bwd Packet Length Max",
    "Bwd Packet Length Min", "Bwd Packet Length Mean",
    "Bwd Packet Length Std", "Flow Bytes/s", "Flow Packets/s",
    "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max",
    "Fwd IAT Min", "Bwd IAT Total", "Bwd IAT Mean", "Bwd IAT Std",
    "Bwd IAT Max", "Bwd IAT Min", "Fwd PSH Flags", "Bwd PSH Flags",
    "Fwd URG Flags", "Bwd URG Flags", "Fwd Header Length",
    "Bwd Header Length", "Fwd Packets/s", "Bwd Packets/s",
    "Min Packet Length", "Max Packet Length", "Packet Length Mean",
    "Packet Length Std", "Packet Length Variance", "FIN Flag Count",
    "SYN Flag Count", "RST Flag Count", "PSH Flag Count", "ACK Flag Count",
    "URG Flag Count", "CWE Flag Count", "ECE Flag Count", "Down/Up Ratio",
    "Average Packet Size", "Avg Fwd Segment Size", "Avg Bwd Segment Size",
    "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk", "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate",
    "Subflow Fwd Packets", "Subflow Fwd Bytes", "Subflow Bwd Packets",
    "Subflow Bwd Bytes", "Init_Win_bytes_forward",
    "Init_Win_bytes_backward", "act_data_pkt_fwd", "min_seg_size_forward",
    "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min",
]

# Column duplicated by the CICFlowMeter pipeline (verified identical).
DUPLICATE_COLUMNS = {"Fwd Header Length.1": "Fwd Header Length"}

LABEL_COLUMN = "Label"
BINARY_COLUMN = "label"

# Canonical feature columns = raw features minus the dropped duplicate.
CANONICAL_FEATURE_COLUMNS: List[str] = [
    c for c in RAW_FEATURE_COLUMNS if c not in DUPLICATE_COLUMNS
]
FEATURE_COUNT = len(CANONICAL_FEATURE_COLUMNS)  # 77


def build_feature_schema() -> dict:
    """Build the canonical feature schema dict (persisted as feature_schema.json)."""
    return {
        "version": "1.0",
        "dataset": "lacg030175/CICIDS2017",
        "revision": "d071fd53782d9ca7cdc15173b8ceb858fea04628",
        "feature_count": FEATURE_COUNT,
        "features": [
            {"name": c, "index": i, "dtype": "float64"}
            for i, c in enumerate(CANONICAL_FEATURE_COLUMNS)
        ],
        "dropped_features": [
            {
                "name": drop,
                "reason": "Bit-for-bit duplicate of " + keep,
            }
            for drop, keep in DUPLICATE_COLUMNS.items()
        ],
        "target_columns": {"multiclass": "Label", "binary": "label"},
    }


@dataclass
class PreprocessingResult:
    """Output of the pipeline for a single frame."""

    X: np.ndarray                    # (n, 77) float64 canonical features
    y_multiclass: np.ndarray         # (n,) int encoded canonical labels
    y_binary: np.ndarray             # (n,) 0/1
    labels: List[str]                # (n,) canonical label strings
    families: List[str]              # (n,) family strings
    columns: List[str] = field(default_factory=lambda: list(CANONICAL_FEATURE_COLUMNS))

    @property
    def shape(self) -> tuple:
        return self.X.shape


def _validate_raw_columns(df: pd.DataFrame) -> None:
    missing = [c for c in RAW_FEATURE_COLUMNS + [LABEL_COLUMN, BINARY_COLUMN]
               if c not in df.columns]
    if missing:
        raise ValueError(f"Raw frame missing columns: {missing}")


def clean_numeric(X: pd.DataFrame, fill_value: float = 0.0) -> pd.DataFrame:
    """Deterministic non-finite handling on the canonical feature columns."""
    X = X[CANONICAL_FEATURE_COLUMNS].copy()
    # Replace inf/-inf with NaN, then fill with a constant (no fitted state).
    X = X.replace([np.inf, -np.inf], np.nan)
    if X.isna().any().any():
        X = X.fillna(fill_value)
    return X.astype("float64")


def preprocess_frame(
    df: pd.DataFrame,
    *,
    scale: bool = False,
    scaler: Optional[StandardScaler] = None,
) -> PreprocessingResult:
    """Run the full deterministic pipeline on one DataFrame.

    scale=True requires a fitted scaler (fit on training data only).
    """
    _validate_raw_columns(df)

    # Duplicate-column cleanup: drop Fwd Header Length.1.
    df = df.drop(columns=[c for c in DUPLICATE_COLUMNS if c in df.columns])

    X = clean_numeric(df)
    if scale:
        if scaler is None:
            raise ValueError(
                "scale=True requires a scaler fitted on training data only."
            )
        # Transform the array, not the DataFrame, so the fitted (feature-name-
        # free) scaler does not emit the sklearn "X has feature names, but
        # StandardScaler was fitted without feature names" UserWarning. Column
        # order is guaranteed canonical by clean_numeric(), so values are
        # identical either way (A6).
        X_arr = scaler.transform(X.to_numpy())
    else:
        X_arr = X.to_numpy()

    labels = [normalize_label(s) for s in df[LABEL_COLUMN].tolist()]
    y_multi = np.array([encode_label(l) for l in labels], dtype="int64")
    y_bin = np.array([binary_target(l) for l in labels], dtype="int64")
    families = [family_for(l) for l in labels]

    return PreprocessingResult(
        X=X_arr,
        y_multiclass=y_multi,
        y_binary=y_bin,
        labels=labels,
        families=families,
    )


def fit_scaler(X_train: np.ndarray) -> StandardScaler:
    """Fit a StandardScaler on training features only (no leakage)."""
    scaler = StandardScaler()
    scaler.fit(X_train)
    return scaler
