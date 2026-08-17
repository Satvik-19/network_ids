"""Tests for the Phase-2 SHAP local explanations + benign baselines.

Requires the FINAL artifacts (supervised_model.joblib, benign_baselines.json).
Run: python -m pytest ml/tests/test_shap.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.preprocess import CANONICAL_FEATURE_COLUMNS, preprocess_frame

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"


@pytest.fixture(scope="module")
def X_row():
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    return preprocess_frame(df, scale=False).X[0]


def test_shap_returns_top_features(X_row):
    from ml.hybrid.shap_explainer import ShapExplainer

    ex = ShapExplainer(ARTIFACTS)
    out = ex.explain(X_row, top_k=5)
    assert out["predicted_class"]
    assert len(out["top_features"]) == 5
    assert out["n_features_explained"] == 77
    for tf in out["top_features"]:
        assert tf["feature"] in CANONICAL_FEATURE_COLUMNS
        assert isinstance(tf["shap_value"], float)
        assert tf["direction"] in {"pushes_towards", "pushes_against"}


def test_shap_topk_ordering(X_row):
    from ml.hybrid.shap_explainer import ShapExplainer

    ex = ShapExplainer(ARTIFACTS)
    out = ex.explain(X_row, top_k=5)
    vals = [abs(tf["shap_value"]) for tf in out["top_features"]]
    assert vals == sorted(vals, reverse=True)


def test_shap_additivity_across_all_classes(X_row):
    # DEC-009: native TreeSHAP must satisfy
    #   sum(contributions) + bias == raw margin  for EVERY class 0..14.
    import joblib
    import xgboost as xgb

    model = joblib.load(ARTIFACTS / "supervised_model.joblib")
    dmat = xgb.DMatrix(np.asarray(X_row, dtype="float64").reshape(1, -1))
    contrib = model.get_booster().predict(dmat, pred_contribs=True)
    margin = model.get_booster().predict(dmat, output_margin=True)
    # contrib: (1, n_classes, n_features+1); margin: (1, n_classes)
    n_classes = margin.shape[1]
    assert contrib.shape[1] == n_classes
    bias = contrib[0, :, -1]
    sums = contrib[0, :, :-1].sum(axis=1)
    assert np.allclose(bias + sums, margin[0], atol=1e-4)


def test_shap_explainer_uses_predicted_class(X_row):
    # Top features must be ranked by the PREDICTED class's contributions.
    import joblib
    import xgboost as xgb

    from ml.hybrid.shap_explainer import ShapExplainer
    from ml.preprocessing.labels import INT_TO_LABEL

    model = joblib.load(ARTIFACTS / "supervised_model.joblib")
    proba = model.predict_proba(np.asarray(X_row, dtype="float64").reshape(1, -1))[0]
    pred_idx = int(np.argmax(proba))
    expected_class = INT_TO_LABEL[int(model.classes_[pred_idx])]

    out = ShapExplainer(ARTIFACTS).explain(X_row, top_k=5)
    assert out["predicted_class"] == expected_class

    dmat = xgb.DMatrix(np.asarray(X_row, dtype="float64").reshape(1, -1))
    contrib = model.get_booster().predict(dmat, pred_contribs=True)
    class_sv = contrib[0, pred_idx, :-1]
    top_vals = [abs(tf["shap_value"]) for tf in out["top_features"]]
    expected = sorted(np.abs(class_sv), reverse=True)[:5]
    assert np.allclose(top_vals, expected, atol=1e-6)


def test_benign_baselines_artifact():
    path = ARTIFACTS / "benign_baselines.json"
    assert path.exists(), "run ml/hybrid/baselines.py first"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["n_benign_flows"] > 0
    assert data["feature_count"] == len(data["baselines"])
    for f, stats in data["baselines"].items():
        assert f in CANONICAL_FEATURE_COLUMNS
        assert {"median", "mean", "p25", "p75", "std", "n"} <= set(stats)
