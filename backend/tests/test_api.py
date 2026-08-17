"""Tests for the Phase-2 FastAPI contract (backend/app).

Run: python -m pytest backend/tests -q
Uses FastAPI TestClient; requires the final Phase-2 artifacts
(ml/artifacts/supervised_model.joblib + isolation_forest.joblib + config).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.preprocess import preprocess_frame

from backend.app.main import app


def _to_request(df, flow_id):
    res = preprocess_frame(df, scale=False)
    return {
        "flow_id": flow_id,
        "features": {
            col: float(v)
            for col, v in zip(res.columns, res.X[0].tolist())
        },
    }


@pytest.fixture(scope="module")
def client():
    from backend.app.db.database import init_db

    init_db()  # ensure tables exist even if lifespan is not triggered
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def sample_flow():
    """One real row from random/test converted to the request shape."""
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    return _to_request(df, "test-flow-1")


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["feature_count"] == 77
    assert body["phase"] == "phase-2"


def test_predict_phase2_contract(client, sample_flow):
    r = client.post("/api/predict", json=sample_flow)
    assert r.status_code == 200
    body = r.json()
    assert body["classification"] in {
        "BENIGN", "KNOWN_ATTACK", "UNKNOWN_SUSPICIOUS"
    }
    assert body["label"]
    assert body["family"]
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["anomaly_score"], float)
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert 0.0 <= body["risk_score"] <= 100.0
    # SHAP top features present for every flow (PRD §12)
    assert len(body["top_features"]) == 5
    for tf in body["top_features"]:
        assert tf["feature"]
        assert isinstance(tf["shap_value"], float)
        assert tf["direction"] in {"pushes_towards", "pushes_against"}
    assert body["model_name"] and body["model_version"]
    assert isinstance(body["prediction_id"], int)
    # BENIGN flows must be classified BENIGN with label BENIGN.
    if body["classification"] == "BENIGN":
        assert body["label"] == "BENIGN"
        assert body["family"] == "BENIGN"


def test_predict_missing_feature(client, sample_flow):
    bad = {
        "flow_id": "bad",
        "features": dict(list(sample_flow["features"].items())[:10]),
    }
    r = client.post("/api/predict", json=bad)
    assert r.status_code == 422


def test_predict_extra_feature(client, sample_flow):
    bad = dict(sample_flow)
    bad["features"]["not_a_feature"] = 1.0
    r = client.post("/api/predict", json=bad)
    assert r.status_code == 422
