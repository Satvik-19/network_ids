from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.predict import HealthResponse
import backend.app.api.predict as predict_api


def test_health_distinguishes_inference_failure(monkeypatch):
    def missing():
        raise RuntimeError("internal artifact path must not leak")

    monkeypatch.setattr(predict_api, "get_predictor", missing)
    with TestClient(app) as client:
        body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["model_loaded"] is False
    assert body["readiness"] == "unavailable"
    assert "artifact" in body["message"].lower()
    assert "internal artifact path" not in body["message"]
    assert HealthResponse(**body).model_dump()["readiness"] == "unavailable"


def test_health_ready_has_no_error_message(monkeypatch):
    class Predictor:
        feature_order = list(range(77))

    monkeypatch.setattr(predict_api, "get_predictor", Predictor)
    with TestClient(app) as client:
        body = client.get("/api/health").json()
    assert body["readiness"] == "ready" and body["model_loaded"] is True
    assert body["feature_count"] == 77
    assert body["message"] is None
    assert HealthResponse(**body).model_dump()["readiness"] == "ready"
