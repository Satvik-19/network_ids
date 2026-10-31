"""test_replay_api.py — Phase-3 API contract for replay + incidents.

FastAPI TestClient against the real ASGI app. The replay dependency is
overridden with a stub predictor + temp scenario fixtures (same sandboxed DB
the incidents API reads), so tests are fast and deterministic and never load
the real model.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.api.replay import get_replay_service
from backend.app.db.database import SessionLocal, init_db
from backend.app.main import app

BENIGN = 0.0
ATTACK = 1.0
SCAN = 2.0


class StubPredictor:
    model_name = "stub-model"
    model_version = "test"

    def predict(self, features: dict, *, with_shap: bool = True) -> dict:
        code = int(features["f0"])
        if code == BENIGN:
            cls, fam, lab, risk, lvl = "BENIGN", "BENIGN", "BENIGN", 5.0, "LOW"
        elif code == SCAN:
            cls, fam, lab, risk, lvl = "KNOWN_ATTACK", "Reconnaissance", "PortScan", 50.0, "MEDIUM"
        else:
            cls, fam, lab, risk, lvl = "KNOWN_ATTACK", "Denial of Service", "DoS Hulk", 90.0, "CRITICAL"
        return {
            "label": lab, "family": fam, "classification": cls,
            "confidence": 0.99, "probabilities": {}, "anomaly_score": -0.05,
            "anomaly_threshold": -0.0928, "risk_score": risk, "risk_level": lvl,
            "top_features": [], "shap_base_value": None,
        }

    def explain(self, features: dict, top_k: int = 5) -> dict:
        code = int(features["f0"])
        return {
            "predicted_class": "attacker" if code != BENIGN else "benign",
            "base_value": 0.0,
            "top_features": (
                [{"feature": "F", "shap_value": 0.1, "direction": "pushes_towards"}]
                if code != BENIGN else []
            ),
            "n_features_explained": 77,
        }


def _feats(code: float) -> dict:
    return {"f0": code, **{f"f{i}": 0.0 for i in range(1, 77)}}


_service_holder = {}


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    init_db()
    scenarios = tmp_path_factory.mktemp("scen")
    for name, code, port in (("portscan", SCAN, 80), ("dos", ATTACK, 80),
                             ("normal", BENIGN, 443)):
        flows = [
            {"seq": i, "source": {"portscan": "10.0.0.50"}.get(name, "10.0.1.7"),
             "destination": "10.0.0.9", "service_port": port + i,
             "ground_truth_label": name, "features": _feats(code)}
            for i in range(4)
        ]
        (scenarios / f"{name}.json").write_text(json.dumps({
            "schema": "scenario/v1", "name": name, "description": name,
            "logical_interval_seconds": 0.0, "flows": flows,
        }), encoding="utf-8")

    def _override():
        from backend.app.services.replay import ReplayService

        if "svc" not in _service_holder:
            svc = ReplayService(
                predictor=StubPredictor(),
                scenarios_dir=scenarios,
                db_factory=SessionLocal,
                replay_config={"speeds": [1, 5, 20], "default_speed": 5},
                incidents_config={"grouping_window_seconds": 30.0},
                sleep_fn=lambda _t: None,
            )
            _service_holder["svc"] = svc
        return _service_holder["svc"]

    app.dependency_overrides[get_replay_service] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _wait_state(client, wanted, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        st = client.get("/api/replay/status").json()
        if st["state"] == wanted:
            return st
        time.sleep(0.01)
    raise AssertionError(f"never {wanted}: {client.get('/api/replay/status').json()}")


def test_replay_scenarios_endpoint(client):
    r = client.get("/api/replay/scenarios")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    # committed fixtures in data/scenarios (the /scenarios endpoint reads the
    # real scenarios dir, not the temp override dir)
    assert {"normal", "portscan", "dos_or_ddos", "unknown"} <= set(names)
    for s in r.json():
        assert s["flows"] > 0


def test_replay_start_status_complete(client):
    r = client.post("/api/replay/start", json={"scenario": "portscan", "speed": 20})
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "RUNNING"
    assert body["total"] == 4
    done = _wait_state(client, "COMPLETED")
    assert done["processed"] == 4
    assert done["suspicious"] == 4
    assert done["known_attacks"] == 4
    assert done["incidents"] == 1
    assert done["progress"] == 1.0


def test_replay_unknown_scenario_404(client):
    r = client.post("/api/replay/start", json={"scenario": "does-not-exist"})
    assert r.status_code == 404


def test_replay_bad_speed_422(client):
    r = client.post("/api/replay/start", json={"scenario": "normal", "speed": 99})
    assert r.status_code == 422


def test_replay_concurrent_start_409(client):
    gate = threading.Event()  # unset -> blocks the pacing sleep

    svc = _service_holder["svc"]
    old_sleep = svc._sleep
    svc._sleep = lambda _t: gate.wait(timeout=0.5)
    try:
        r1 = client.post("/api/replay/start", json={"scenario": "portscan", "speed": 1})
        assert r1.status_code == 200
        # worker processed >=1 flow then blocks in the pacing gate; still RUNNING
        end = time.monotonic() + 5
        while time.monotonic() < end:
            if client.get("/api/replay/status").json()["state"] == "RUNNING":
                break
            time.sleep(0.01)
        assert client.get("/api/replay/status").json()["state"] == "RUNNING"
        r = client.post("/api/replay/start", json={"scenario": "normal", "speed": 1})
        assert r.status_code == 409
    finally:
        gate.set()
        svc._sleep = old_sleep
        try:
            svc.stop()
        except Exception:
            pass
    _wait_state(client, "STOPPED")


def test_replay_status_before_start(client):
    r = client.get("/api/replay/status")
    assert r.status_code == 200
    # after earlier tests the shared service may be IDLE or a finished state;
    # it must never be RUNNING/PAUSED because nothing is live right now.
    assert r.json()["state"] in {"IDLE", "COMPLETED", "STOPPED"}


def test_replay_recent_flows_endpoint(client):
    """Traffic table contract: GET /api/replay/flows returns the persisted
    replay evidence newest-first, incl. benign rows and replay side-car."""
    client.post("/api/replay/start", json={"scenario": "portscan", "speed": 20})
    _wait_state(client, "COMPLETED")
    r = client.get("/api/replay/flows", params={"limit": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 4  # module-scoped DB may hold rows from prior tests
    ids = [f["id"] for f in body["flows"]]
    assert ids == sorted(ids, reverse=True)  # newest first
    first = body["flows"][0]
    assert first["scenario"] == "portscan"
    assert first["source"] == "10.0.0.50"
    assert first["destination"] == "10.0.0.9"
    assert first["service_port"] is not None
    assert first["classification"] == "KNOWN_ATTACK"
    assert first["confidence"] is not None
    assert first["risk_score"] is not None
    assert first["replay_time"] is not None


def test_replay_recent_flows_includes_benign(client):
    """The traffic table must show pure-BENIGN replay rows too (normal
    scenario), not just flows that joined an incident."""
    client.post("/api/replay/start", json={"scenario": "normal", "speed": 20})
    _wait_state(client, "COMPLETED")
    r = client.get("/api/replay/flows", params={"limit": 500})
    assert r.status_code == 200
    body = r.json()
    normal = [f for f in body["flows"] if f["scenario"] == "normal"]
    benign = [f for f in normal if f["classification"] == "BENIGN"]
    assert benign, "normal replay must surface BENIGN evidence rows"
    assert all(f["source"] == "10.0.1.7" for f in benign)


def test_run_scoped_flows_and_incidents_isolate_sequential_runs(client):
    """Phase-3.5 hardening: the /flows feed and /incidents list accept a
    run_id so two sequential replays never mix. PortScan then Normal must give:
    /flows?run_id=<normal> -> only normal rows; /incidents?run_id=<normal> -> 0,
    while an unscoped /incidents still returns the full history."""
    ps = client.post("/api/replay/start", json={"scenario": "portscan", "speed": 20}).json()
    assert ps["state"] == "RUNNING"
    ps_done = _wait_state(client, "COMPLETED")
    ps_run = ps_done["run_id"]
    assert ps_run and ps_run != ""

    nm = client.post("/api/replay/start", json={"scenario": "normal", "speed": 20}).json()
    assert nm["state"] == "RUNNING"
    nm_done = _wait_state(client, "COMPLETED")
    nm_run = nm_done["run_id"]
    assert nm_run and nm_run != ps_run

    r = client.get("/api/replay/flows", params={"limit": 500, "run_id": nm_run})
    assert r.status_code == 200
    nm_flows = r.json()["flows"]
    assert nm_flows, "normal run must have its own feed rows"
    assert {f["scenario"] for f in nm_flows} == {"normal"}, (
        "stale portscan rows leaked into the normal run's feed"
    )
    assert all(f["source"] == "10.0.1.7" for f in nm_flows)

    r = client.get("/api/replay/flows", params={"limit": 500, "run_id": ps_run})
    ps_flows = r.json()["flows"]
    assert ps_flows and {f["scenario"] for f in ps_flows} == {"portscan"}

    r = client.get("/api/incidents", params={"run_id": nm_run})
    assert r.status_code == 200
    assert r.json()["total"] == 0, "normal run must expose zero incidents"

    r = client.get("/api/incidents", params={"run_id": ps_run})
    assert r.status_code == 200
    assert r.json()["total"] >= 1, "portscan run must expose its own incident"

    full = client.get("/api/incidents").json()
    assert full["total"] >= 1, "unscoped incidents list must keep full history"


def test_incidents_list_and_detail(client):
    client.post("/api/replay/start", json={"scenario": "portscan", "speed": 20})
    _wait_state(client, "COMPLETED")
    r = client.get("/api/incidents")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    inc = body["incidents"][0]
    assert inc["classification"] == "KNOWN_ATTACK"
    assert inc["family"] == "Reconnaissance"
    assert inc["source"] == "10.0.0.50"
    assert inc["flow_count"] >= 1

    detail = client.get(f"/api/incidents/{inc['id']}").json()
    assert detail["id"] == inc["id"]
    assert len(detail["flows"]) == inc["flow_count"]
    flow = detail["flows"][0]
    assert flow["prediction_id"]
    assert flow["source"] == "10.0.0.50"
    assert flow["replay_time"] is not None
    assert flow["anomaly_score"] is not None
    assert isinstance(flow["baseline_features"], dict)
    assert isinstance(flow["top_features"], list)
    assert detail["confidence"] is not None


def test_incident_detail_enriched_from_prediction(client):
    """A5: the detail endpoint joins the linked Prediction row for anomaly,
    SHAP top_features and the baseline feature subset, and exposes the
    dominant-flow summary confidence/anomaly."""
    client.post("/api/replay/start", json={"scenario": "portscan", "speed": 20})
    _wait_state(client, "COMPLETED")
    body = client.get("/api/incidents").json()
    inc = body["incidents"][0]
    detail = client.get(f"/api/incidents/{inc['id']}").json()
    assert detail["anomaly_score"] is not None
    assert detail["confidence"] is not None
    for fl in detail["flows"]:
        assert fl["prediction_id"]
        assert fl["anomaly_score"] is not None


def test_threshold_snapshot_reaches_feed_and_incident_detail(client):
    client.post('/api/replay/start', json={'scenario': 'portscan', 'speed': 20})
    done = _wait_state(client, 'COMPLETED')
    feed = client.get('/api/replay/flows', params={'run_id': done['run_id']}).json()
    assert all(f['anomaly_threshold'] == -0.0928 for f in feed['flows'])
    incidents = client.get('/api/incidents', params={'run_id': done['run_id']}).json()
    detail = client.get(f"/api/incidents/{incidents['incidents'][0]['id']}").json()
    assert all(f['anomaly_threshold'] == -0.0928 for f in detail['flows'])


def test_benign_baselines_endpoint(client):
    """A5: static benign baseline artifact is exposed for the Incident Detail
    UI behaviour-vs-normal comparison (PRD §13)."""
    r = client.get("/api/baselines/benign")
    assert r.status_code == 200
    body = r.json()
    assert body["feature_count"] == 10
    assert "Flow Packets/s" in body["features"]
    assert "median" in body["baselines"]["Flow Packets/s"]


def test_incidents_detail_404(client):
    r = client.get("/api/incidents/999999")
    assert r.status_code == 404


def test_normal_replay_creates_no_incident(client):
    client.post("/api/replay/start", json={"scenario": "normal", "speed": 20})
    done = _wait_state(client, "COMPLETED")
    assert done["suspicious"] == 0
    assert done["incidents"] == 0
    scans = client.get("/api/incidents", params={"source": "10.0.1.7"}).json()
    for inc in scans["incidents"]:
        assert inc["family"] != "BENIGN" or inc["classification"] != "KNOWN_ATTACK"
