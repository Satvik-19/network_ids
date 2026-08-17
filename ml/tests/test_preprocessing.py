"""Tests for ml.preprocessing (Phase-1 gate).

Run: python -m pytest ml/tests -q
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from ml.preprocessing.labels import (
    CANONICAL_LABELS,
    FAMILY_MAP,
    LABEL_TO_INT,
    INT_TO_LABEL,
    decode_label,
    encode_label,
    normalize_label,
)
from ml.preprocessing.preprocess import (
    CANONICAL_FEATURE_COLUMNS,
    DUPLICATE_COLUMNS,
    FEATURE_COUNT,
    RAW_FEATURE_COLUMNS,
    build_feature_schema,
    clean_numeric,
    fit_scaler,
    preprocess_frame,
)
from ml.preprocessing.subset import build_dev_subset, load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"
PROCESSED = ROOT / "data" / "processed"


def _tiny_frame() -> pd.DataFrame:
    """Deterministic tiny frame exercising the duplicate + infinite cases."""
    rng = np.random.RandomState(0)
    rows = 50
    data = rng.rand(rows, len(RAW_FEATURE_COLUMNS)) * 100
    df = pd.DataFrame(data, columns=RAW_FEATURE_COLUMNS)
    df["Fwd Header Length.1"] = df["Fwd Header Length"].copy()
    df["Label"] = ["BENIGN"] * 25 + ["DDoS"] * 25
    df["label"] = [0] * 25 + [1] * 25
    df.loc[0, "Fwd Header Length"] = np.inf
    df.loc[1, "Fwd Header Length"] = np.nan
    df.loc[2, "Fwd Header Length"] = -np.inf
    df.loc[0, "Fwd Header Length.1"] = df.loc[0, "Fwd Header Length"]
    df.loc[1, "Fwd Header Length.1"] = df.loc[1, "Fwd Header Length"]
    df.loc[2, "Fwd Header Length.1"] = df.loc[2, "Fwd Header Length"]
    return df


class TestLabels:
    def test_fifteen_canonical_labels(self):
        assert len(CANONICAL_LABELS) == 15
        assert CANONICAL_LABELS == sorted(CANONICAL_LABELS)

    def test_normalise_replacement_char(self):
        assert normalize_label("Web Attack \ufffd Brute Force") == "Web Attack - Brute Force"
        assert normalize_label("Web Attack \ufffd Sql Injection") == "Web Attack - Sql Injection"
        assert normalize_label("Web Attack \ufffd XSS") == "Web Attack - XSS"
        assert normalize_label("BENIGN") == "BENIGN"

    def test_int_roundtrip(self):
        for label in CANONICAL_LABELS:
            assert INT_TO_LABEL[LABEL_TO_INT[label]] == label

    def test_family_map(self):
        assert FAMILY_MAP["BENIGN"] == "BENIGN"
        assert FAMILY_MAP["DDoS"] == "Denial of Service"
        assert FAMILY_MAP["PortScan"] == "Reconnaissance"


class TestPreprocess:
    def test_raw_feature_count(self):
        assert len(RAW_FEATURE_COLUMNS) == 77
        assert len(CANONICAL_FEATURE_COLUMNS) == FEATURE_COUNT == 77

    def test_duplicate_dropped_not_kept(self):
        assert "Fwd Header Length.1" in DUPLICATE_COLUMNS
        assert "Fwd Header Length.1" not in CANONICAL_FEATURE_COLUMNS
        assert "Fwd Header Length" in CANONICAL_FEATURE_COLUMNS

    def test_no_canonical_duplicates(self):
        assert len(CANONICAL_FEATURE_COLUMNS) == len(set(CANONICAL_FEATURE_COLUMNS))

    def test_clean_numeric_replaces_nonfinite(self):
        df = _tiny_frame()
        out = clean_numeric(df[RAW_FEATURE_COLUMNS])
        assert np.isfinite(out.to_numpy()).all()

    def test_preprocess_frame_consistent(self):
        df = _tiny_frame()
        res = preprocess_frame(df, scale=False)
        assert res.X.shape == (50, FEATURE_COUNT)
        assert np.isfinite(res.X).all()
        assert res.columns == CANONICAL_FEATURE_COLUMNS
        assert set(res.labels) <= set(CANONICAL_LABELS)

    def test_preprocess_frame_scaled_consistent(self):
        df = _tiny_frame()
        scaler = fit_scaler(preprocess_frame(df, scale=False).X)
        res = preprocess_frame(df, scale=True, scaler=scaler)
        assert res.X.shape == (50, FEATURE_COUNT)
        assert np.isfinite(res.X).all()
        assert res.columns == CANONICAL_FEATURE_COLUMNS

    def test_feature_schema_matches_artifact(self):
        schema = json.loads((ARTIFACTS / "feature_schema.json").read_text(encoding="utf-8"))
        assert schema["version"] == "1.0"
        names = [c["name"] for c in schema["features"]]
        assert names == CANONICAL_FEATURE_COLUMNS
        assert len(schema["features"]) == FEATURE_COUNT
        assert all(c["dtype"] == "float64" for c in schema["features"])


class TestSubset:
    @pytest.mark.skipif(
        not (PROCESSED / "dev_random_train.parquet").exists(),
        reason="dev subset not materialised",
    )
    def test_materialised_dev_subset_matches_contract(self):
        df = load_dev_subset(str(PROCESSED / "dev_random_train.parquet"))
        assert df.shape[1] == 80
        meta = json.loads(
            (PROCESSED / "dev_random_train.parquet.meta.json").read_text(encoding="utf-8")
        )
        assert meta["target"] == 300_000
        assert len(df) == meta["total_after"]
        # All 15 classes retained
        labels = set(df["Label"].map(normalize_label))
        assert labels == set(CANONICAL_LABELS)

    def test_sampling_reproducible(self, tmp_path):
        p1 = tmp_path / "s1"
        p2 = tmp_path / "s2"
        build_dev_subset(config="random", split="train", out_path=str(p1 / "a.parquet"),
                         target=200_000, per_class_cap=1000, cap_floor=100, seed=42)
        build_dev_subset(config="random", split="train", out_path=str(p2 / "b.parquet"),
                         target=200_000, per_class_cap=1000, cap_floor=100, seed=42)
        a = load_dev_subset(str(p1 / "a.parquet"))
        b = load_dev_subset(str(p2 / "b.parquet"))
        assert (a.sort_values("label").reset_index(drop=True).equals(
            b.sort_values("label").reset_index(drop=True)))
