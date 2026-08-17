"""test_replay.py — ReplayService state machine, determinism, persistence (Phase 3).

Uses a StubPredictor (deterministic classification driven by a signal feature)
so tests never touch real time, the real model, or the committed fixtures.
Scalability + spec: every flow is classified per its scenario intention.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

from backend.app.db.models import Incident, IncidentFlow, Prediction
from backend.app.services.replay import (
    ReplayConflict,
    ReplayService,
    STATE_COMPLETED,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RUNNING,
    STATE_STOPPED,
)

BENIGN = 0.0
ATTACK = 1.0
SCAN = 2.0
UNKNOWN = 3.0


class StubPredictor:
    """Deterministic Phase-2-shaped predictor keyed on the f0 signal feature."""

    model_name = "stub-model"
    model_version = "test"

    def predict(self, features: dict, *, with_shap: bool = True) -> dict:
        code = int(features["f0"])
        if code == BENIGN:
            classification, family, label = "BENIGN", "BENIGN", "BENIGN"
            risk, level = 5.0, "LOW"
        elif code == SCAN:
            classification, family, label = "KNOWN_ATTACK", "Reconnaissance", "PortScan"
            risk, level = 50.0, "MEDIUM"
        elif code == UNKNOWN:
            classification, family, label = "UNKNOWN_SUSPICIOUS", "BENIGN", "BENIGN"
            risk, level = 72.9, "HIGH"
        else:  # generic DoS
            classification, family, label = "KNOWN_ATTACK", "Denial of Service", "DoS Hulk"
            risk, level = 90.0, "CRITICAL"

        anomaly = -0.05 if code else 0.1
        out = {
            "label": label,
            "family": family,
            "classification": classification,
            "confidence": 0.99 if code else 0.9,
            "probabilities": {},
            "anomaly_score": anomaly,
            "anomaly_threshold": -0.0928,
            "risk_score": risk,
            "risk_level": level,
            "top_features": [],
            "shap_base_value": None,
        }
        if with_shap and classification != "BENIGN":
            out["top_features"] = [{"feature": "F", "shap_value": 0.1, "direction": "pushes_towards"}]
        return out

    def explain(self, features: dict, top_k: int = 5) -> dict:
        """Single-pass SHAP surrogate (mirrors Phase2Predictor.explain)."""
        code = int(features["f0"])
        suspicious = code != BENIGN
        return {
            "predicted_class": "attacker" if suspicious else "benign",
            "base_value": 0.0,
            "top_features": (
                [{"feature": "F", "shap_value": 0.1, "direction": "pushes_towards"}]
                if suspicious else []
            ),
            "n_features_explained": 77,
        }


def _feats(code: float) -> dict:
    return {"f0": code, **{f"f{i}": 0.0 for i in range(1, 77)}}


def write_scenario(
    path: Path,
    name: str,
    flows: list[dict],
    *,
    interval: float = 1.0,
) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema": "scenario/v1",
        "name": name,
        "description": "test fixture",
        "logical_interval_seconds": interval,
        "flows": flows,
    }
    out = path / f"{name}.json"
    out.write_text(json.dumps(doc), encoding="utf-8")
    return out


def build_service(tmp_path: Path, interval: float = 1.0, window: float = 30.0,
                  sleep_fn=None) -> ReplayService:
    if sleep_fn is None:
        sleep_fn = lambda _t: None
    return ReplayService(
        predictor=StubPredictor(),
        scenarios_dir=tmp_path,
        replay_config={"speeds": [1, 5, 20], "default_speed": 5},
        incidents_config={"grouping_window_seconds": window},
        sleep_fn=sleep_fn,
    )


def _wait(svc, wanted, timeout: float = 5.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if svc.status()["state"] == wanted:
            return
        time.sleep(0.005)
    raise AssertionError(f"state never became {wanted}; got {svc.status()['state']}")


def test_initial_state_idle(tmp_path):
    svc = build_service(tmp_path)
    st = svc.status()
    assert st["state"] == STATE_IDLE
    assert st["processed"] == 0 and st["total"] == 0


def test_full_run_reaches_completed_with_counts(tmp_path, monkeypatch):
    write_scenario(tmp_path, "portscan", [
        {"seq": i, "source": "10.0.0.50", "destination": "10.0.0.9",
         "service_port": 20 + i, "ground_truth_label": "PortScan",
         "features": _feats(SCAN)} for i in range(8)
    ], interval=0.0)
    svc = build_service(tmp_path, interval=0.0)
    svc.start("portscan", speed=20)
    _wait(svc, STATE_COMPLETED)
    st = svc.status()
    assert st["processed"] == 8 == st["total"]
    assert st["known_attacks"] == 8
    assert st["unknown_suspicious"] == 0
    assert st["incidents"] == 1


def test_reject_concurrent_start(tmp_path):
    gate = threading.Event()

    def blocked(_t):
        gate.wait(timeout=5.0)

    write_scenario(tmp_path, "portscan", [
        {"seq": 0, "source": "s", "destination": "d", "service_port": 80,
         "ground_truth_label": "PortScan", "features": _feats(SCAN)},
        {"seq": 1, "source": "s", "destination": "d", "service_port": 81,
         "ground_truth_label": "PortScan", "features": _feats(SCAN)},
    ], interval=1.0)
    svc = build_service(tmp_path, interval=1.0, sleep_fn=blocked)
    svc.start("portscan", speed=1)
    deadline = time.monotonic() + 5
    while svc.status()["processed"] < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert svc.status()["state"] == STATE_RUNNING
    with pytest.raises(ReplayConflict):
        svc.start("portscan", speed=1)
    svc.stop()
    gate.set()
    _wait(svc, STATE_STOPPED)


def test_pause_resume_cycle(tmp_path):
    flows = [
        {"seq": i, "source": "10.0.1.7", "destination": "10.0.0.20",
         "service_port": 80, "ground_truth_label": "DoS Hulk",
         "features": _feats(ATTACK)} for i in range(20)
    ]
    write_scenario(tmp_path, "dos", flows, interval=0.5)

    gate = threading.Event()
    gate.set()  # open by default

    def paced(seconds):
        # real pacing would make PAUSE racy; block on a test gate instead so
        # the pause is observable deterministically.
        gate.wait(timeout=5.0)

    svc = build_service(tmp_path, interval=0.5, sleep_fn=paced)
    svc.start("dos", speed=1)
    deadline = time.monotonic() + 5
    while svc.status()["processed"] < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    # flow 1 was processed; the worker now blocks in our gate -> pause it
    svc.pause()
    assert svc.status()["state"] == STATE_PAUSED
    gate.set()  # release the pacing sleep; worker must stay paused
    time.sleep(0.02)
    assert svc.status()["state"] == STATE_PAUSED
    gate.clear()
    svc.resume()
    assert svc.status()["state"] == STATE_RUNNING
    svc.stop()
    assert svc.status()["state"] == STATE_STOPPED


def test_stop_leaves_partial_progress(tmp_path):
    gate = threading.Event()

    def blocked(_t):
        gate.wait(timeout=5.0)

    write_scenario(tmp_path, "portscan", [
        {"seq": i, "source": "s", "destination": "d", "service_port": 20 + i,
         "ground_truth_label": "PortScan", "features": _feats(SCAN)} for i in range(40)
    ], interval=1.0)
    svc = build_service(tmp_path, interval=1.0, sleep_fn=blocked)
    svc.start("portscan", speed=1)
    deadline = time.monotonic() + 5
    while svc.status()["processed"] < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    svc.stop()
    gate.set()
    _wait(svc, STATE_STOPPED)
    st = svc.status()
    assert st["processed"] < 40
    assert st["state"] == STATE_STOPPED


def test_determinism_two_runs_same_stream(tmp_path):
    flows = [
        {"seq": i, "source": "10.0.0.50", "destination": "10.0.0.9",
         "service_port": 20 + i, "ground_truth_label": "PortScan",
         "features": _feats(SCAN)} for i in range(6)
    ]
    write_scenario(tmp_path, "portscan", flows, interval=0.0)

    def run() -> list:
        svc = build_service(tmp_path, interval=0.0)
        svc.start("portscan", speed=20)
        _wait(svc, STATE_COMPLETED)
        st = svc.status()
        return [st["processed"], st["suspicious"], st["known_attacks"],
                st["unknown_suspicious"], st["incidents"]]

    assert run() == run()


def test_unknown_suspicious_counts(tmp_path):
    write_scenario(tmp_path, "unknown", [
        {"seq": i, "source": "10.0.0.60", "destination": "10.0.0.12",
         "service_port": 53, "ground_truth_label": "BENIGN",
         "features": _feats(UNKNOWN)} for i in range(4)
    ], interval=0.0)
    svc = build_service(tmp_path, interval=0.0)
    svc.start("unknown", speed=20)
    _wait(svc, STATE_COMPLETED)
    st = svc.status()
    assert st["suspicious"] == 4 and st["unknown_suspicious"] == 4
    assert st["known_attacks"] == 0
    assert st["incidents"] >= 1


def test_unknown_scenario_rejected(tmp_path):
    svc = build_service(tmp_path)
    with pytest.raises(Exception):
        svc.start("nope")


def test_disallowed_speed_rejected(tmp_path):
    write_scenario(tmp_path, "a", [
        {"seq": 0, "source": "s", "destination": "d", "service_port": 80,
         "ground_truth_label": "BENIGN", "features": _feats(BENIGN)},
    ], interval=0)
    svc = build_service(tmp_path, interval=0)
    with pytest.raises(ValueError):
        svc.start("a", speed=7)


def test_pace_seconds_reflects_speed(tmp_path):
    write_scenario(tmp_path, "a", [
        {"seq": 0, "source": "s", "destination": "d", "service_port": 80,
         "ground_truth_label": "BENIGN", "features": _feats(BENIGN)},
    ], interval=1.0)
    svc = build_service(tmp_path, interval=1.0)
    svc.start("a", speed=20)
    _wait(svc, STATE_COMPLETED)
    assert svc.status()["pace_seconds"] == pytest.approx(0.05)
    assert svc.status()["speed"] == 20


def test_persists_predictions_and_incident_evidence(tmp_path):
    """End-to-end service persistence: Prediction rows + Incident + IncidentFlow."""
    write_scenario(tmp_path, "portscan", [
        {"seq": i, "source": "10.0.0.50", "destination": "10.0.0.9",
         "service_port": 20 + i, "ground_truth_label": "PortScan",
         "features": _feats(SCAN)} for i in range(5)
    ], interval=0.0)
    svc = build_service(tmp_path, interval=0.0)

    import tempfile
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.db.database import Base, init_db

    tmp_db = Path(tempfile.mkdtemp(prefix="replay_db_")) / "t.db"
    eng = create_engine(f"sqlite:///{tmp_db.as_posix()}")
    Base.metadata.create_all(bind=eng)
    Session = sessionmaker(bind=eng)
    db = Session()

    svc._db_factory = Session
    svc.start("portscan", speed=20)
    _wait(svc, STATE_COMPLETED)

    preds = db.query(Prediction).all()
    assert len(preds) == 5
    for p in preds:
        assert len(p.features) == 77
        assert p.source_config == "replay:portscan"
    inc = db.query(Incident).first()
    assert inc is not None
    assert inc.flow_count == 5
    assert inc.family == "Reconnaissance"
    assert inc.classification == "KNOWN_ATTACK"
    ifflows = db.query(IncidentFlow).all()
    assert len(ifflows) == 5
    assert all(f.replay_time is not None for f in ifflows)
    assert all(f.prediction_id for f in ifflows)
    db.close()


# ---------------------------------------------------------------------- #
# A1 — replay-level truth isolation (PRD §47 / DEC-010 / BUG-005).
# ---------------------------------------------------------------------- #
# Scenario fixtures carry ground_truth_label as an evaluation note only; it
# must NEVER influence runtime inference. This is the replay-level pin of the
# invariant already locked at predictor level (ml/tests/test_predictor.py):
# identical 77 features + different external truth -> identical stream.
# ---------------------------------------------------------------------- #


class RecordingPredictor(StubPredictor):
    """Stub that records every feature dict sent to inference (predict) and to
    the single-pass SHAP explainer (explain)."""

    def __init__(self):
        self.seen: list[dict] = []
        self.shap_seen: list[dict] = []

    def predict(self, features: dict, *, with_shap: bool = True) -> dict:
        self.seen.append(dict(features))
        return super().predict(features, with_shap=with_shap)

    def explain(self, features: dict, top_k: int = 5) -> dict:
        self.shap_seen.append(dict(features))
        return super().explain(features, top_k=top_k)


def test_replay_truth_label_never_enters_inference(tmp_path):
    """Same 77 features, two different ground_truth_labels -> identical stream.

    A malicious different ground_truth_label must produce identical
    predictions/incidents, and the predictor must never see any key other than
    the canonical feature vector (no source/destination/service_port/seq/
    ground_truth_label metadata leaks into inference).
    """
    feats = _feats(ATTACK)
    base = {
        "source": "10.0.1.7", "destination": "10.0.0.20", "service_port": 80,
    }
    write_scenario(tmp_path, "truth_a", [
        dict(seq=i, ground_truth_label="DoS Hulk", features=feats, **base)
        for i in range(6)
    ], interval=0.0)
    write_scenario(tmp_path, "truth_b", [
        dict(seq=i, ground_truth_label="BENIGN", features=feats, **base)
        for i in range(6)
    ], interval=0.0)

    pred = RecordingPredictor()

    def run(name):
        svc = ReplayService(
            predictor=pred, scenarios_dir=tmp_path,
            replay_config={"speeds": [1, 5, 20], "default_speed": 5},
            incidents_config={"grouping_window_seconds": 30.0},
            sleep_fn=lambda _t: None,
        )
        svc.start(name, speed=20)
        _wait(svc, STATE_COMPLETED)
        return svc.status()

    st_a = run("truth_a")
    st_b = run("truth_b")

    for key in ("processed", "suspicious", "known_attacks",
                "unknown_suspicious", "incidents", "max_risk_score",
                "max_risk_level"):
        assert st_a[key] == st_b[key], f"{key}: {st_a[key]} != {st_b[key]}"

    # The predictor only ever received the canonical 77 feature keys.
    # BUG-010 (Phase-3.5): each flow is SCORED exactly once (1 predict call per
    # flow), and only SUSPICIOUS flows get a separate single-pass SHAP
    # explanation. 2 runs x 6 attack flows -> 12 predict + 12 explain calls,
    # and never any metadata key.
    assert len(pred.seen) == 12, f"expected one scoring pass per flow, got {len(pred.seen)}"
    assert len(pred.shap_seen) == 12, "expected one explain per suspicious flow"
    for seen in pred.seen + pred.shap_seen:
        assert set(seen) == set(_feats(0.0).keys()), "metadata leaked into inference"
        assert len(seen) == 77
        assert all(k.startswith("f") for k in seen)


# ---------------------------------------------------------------------- #
# A6 — replay lifecycle transitions not covered earlier.
# ---------------------------------------------------------------------- #


def test_stop_while_paused(tmp_path):
    gate = threading.Event()

    def paced(_t):
        gate.wait(timeout=5.0)

    write_scenario(tmp_path, "dos", [
        {"seq": i, "source": "10.0.1.7", "destination": "10.0.0.20",
         "service_port": 80, "ground_truth_label": "DoS Hulk",
         "features": _feats(ATTACK)} for i in range(20)
    ], interval=1.0)
    svc = build_service(tmp_path, interval=1.0, sleep_fn=paced)
    svc.start("dos", speed=1)
    deadline = time.monotonic() + 5
    while svc.status()["processed"] < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    svc.pause()
    assert svc.status()["state"] == STATE_PAUSED
    svc.stop()                      # allowed from PAUSED
    gate.set()
    _wait(svc, STATE_STOPPED)
    assert svc.status()["processed"] < 20


def test_restart_after_stopped(tmp_path):
    gate = threading.Event()

    def paced(_t):
        gate.wait(timeout=5.0)

    write_scenario(tmp_path, "portscan", [
        {"seq": i, "source": "10.0.0.50", "destination": "10.0.0.9",
         "service_port": 20 + i, "ground_truth_label": "PortScan",
         "features": _feats(SCAN)} for i in range(40)
    ], interval=1.0)
    svc = build_service(tmp_path, interval=1.0, sleep_fn=paced)
    svc.start("portscan", speed=1)
    deadline = time.monotonic() + 5
    while svc.status()["processed"] < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    svc.stop()
    gate.set()
    _wait(svc, STATE_STOPPED)
    first = svc.status()
    assert first["processed"] < 40

    # fresh run on the same service after STOPPED must reset the counters
    svc.start("portscan", speed=20)  # gate is open -> pacing passes instantly
    _wait(svc, STATE_COMPLETED)
    second = svc.status()
    assert second["state"] == STATE_COMPLETED
    assert second["processed"] == 40 == second["total"]
    assert second["incidents"] >= 1
    assert second["processed"] > first["processed"]


def test_restart_waits_for_stale_worker_before_resetting(tmp_path):
    """BUG-012: a stop() while a flow is mid-predict must not let a subsequent
    start() spawn a second thread that races the still-draining old worker.

    stop() flips the STATE synchronously; the worker thread can still be inside
    predict()/persist() for a beat. start() must JOIN the stale thread before
    resetting counters and spawning a fresh one.
    """
    entered = threading.Event()
    release = threading.Event()

    class BlockingPredictor(StubPredictor):
        def predict(self, features: dict, *, with_shap: bool = True) -> dict:
            entered.set()
            assert release.wait(timeout=5.0)
            return super().predict(features, with_shap=with_shap)

    write_scenario(tmp_path, "portscan", [
        {"seq": i, "source": "10.0.0.50", "destination": "10.0.0.9",
         "service_port": 20 + i, "ground_truth_label": "PortScan",
         "features": _feats(SCAN)} for i in range(40)
    ], interval=1.0)
    svc = ReplayService(
        predictor=BlockingPredictor(),
        scenarios_dir=tmp_path,
        replay_config={"speeds": [1, 5, 20], "default_speed": 5},
        incidents_config={"grouping_window_seconds": 30.0},
        sleep_fn=lambda _t: None,
    )
    svc.start("portscan", speed=1)
    assert entered.wait(timeout=5.0)   # worker is mid-predict on flow 0
    svc.stop()                          # STATE -> STOPPED while worker still predicting
    threading.Timer(0.2, release.set).start()
    svc.start("portscan", speed=20)     # must join the stale worker before resetting
    _wait(svc, STATE_COMPLETED)
    st = svc.status()
    assert st["state"] == STATE_COMPLETED
    assert st["processed"] == 40 == st["total"], st
    assert st["incidents"] >= 1


def test_restart_after_completed_and_no_inactive_residue(tmp_path):
    write_scenario(tmp_path, "portscan", [
        {"seq": i, "source": "10.0.0.50", "destination": "10.0.0.9",
         "service_port": 20 + i, "ground_truth_label": "PortScan",
         "features": _feats(SCAN)} for i in range(8)
    ], interval=0.0)
    svc = build_service(tmp_path, interval=0.0)
    svc.start("portscan", speed=20)
    _wait(svc, STATE_COMPLETED)
    assert svc.status()["state"] == STATE_COMPLETED

    svc.start("portscan", speed=20)  # restart directly after COMPLETED
    _wait(svc, STATE_COMPLETED)
    st = svc.status()
    assert st["processed"] == 8 == st["total"]
    assert st["known_attacks"] == 8
    assert st["incidents"] == 1


def test_completed_run_replays_each_flow_once(tmp_path):
    """No duplicated flows within a run: processed == total and no seq skipped."""
    write_scenario(tmp_path, "mixed", [
        {"seq": i, "source": "s", "destination": "d", "service_port": 80,
         "ground_truth_label": "mix", "features": _feats(ATTACK if i % 2 else BENIGN)}
        for i in range(10)
    ], interval=0.0)
    svc = build_service(tmp_path, interval=0.0)
    svc.start("mixed", speed=20)
    _wait(svc, STATE_COMPLETED)
    st = svc.status()
    assert st["processed"] == 10 == st["total"]
    assert st["current_sequence"] == 9
    assert st["suspicious"] == 5