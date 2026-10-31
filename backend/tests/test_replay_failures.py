"""Failure boundaries for the real replay worker and SQLite transactions."""
import threading

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.database import Base
from backend.app.db.models import Incident, IncidentFlow, Prediction
from backend.app.services.replay import ReplayConflict, ReplayService
from backend.tests.test_replay import ATTACK, StubPredictor, _feats, write_scenario


@pytest.fixture
def replay_case(tmp_path):
    write_scenario(tmp_path, "attack", [
        dict(seq=i, source="s", destination="d", service_port=80,
             features=_feats(ATTACK)) for i in range(2)
    ], interval=0)
    engine = create_engine(f"sqlite:///{(tmp_path / 'failure.db').as_posix()}")
    Base.metadata.create_all(engine)
    yield tmp_path, engine
    engine.dispose()


def finish(svc):
    svc._thread.join(2)
    alive = svc._thread.is_alive()
    if alive:
        svc.stop()
        svc._thread.join(2)
    assert not alive, "worker kept retrying instead of terminating"


@pytest.mark.parametrize("stage", ["predict", "explain", "open", "flush", "commit", "finalize"])
def test_failure_terminates_rolls_back_and_closes(replay_case, stage):
    directory, engine = replay_case
    sessions = []

    class FailingSession(Session):
        commits = 0
        rollbacks = 0
        closed = False

        def flush(self, *args, **kwargs):
            super().flush(*args, **kwargs)
            if stage == "flush":
                raise RuntimeError("controlled flush failure")

        def commit(self):
            self.commits += 1
            if (stage == "commit" and self.commits == 2) or (
                stage == "finalize" and self.commits == 3
            ):
                raise RuntimeError("controlled commit failure")
            return super().commit()

        def rollback(self):
            self.rollbacks += 1
            return super().rollback()

        def close(self):
            self.closed = True
            return super().close()

    class FailingPredictor(StubPredictor):
        def predict(self, features, **kwargs):
            if stage == "predict":
                raise RuntimeError("controlled prediction failure")
            return super().predict(features, **kwargs)

        def explain(self, features, **kwargs):
            if stage == "explain":
                raise RuntimeError("controlled explanation failure")
            return super().explain(features, **kwargs)

    def factory():
        if stage == "open":
            raise RuntimeError("controlled session creation failure")
        db = FailingSession(bind=engine)
        sessions.append(db)
        return db

    svc = ReplayService(predictor=FailingPredictor(), scenarios_dir=directory,
                        db_factory=factory, sleep_fn=lambda _: None)
    svc.start("attack")
    finish(svc)
    status = svc.status()
    assert status["state"] == "FAILED"
    assert status["errors"] == 1 and "controlled" in status["error"]
    expected = {"commit": 1, "finalize": 2}.get(stage, 0)
    assert status["processed"] == expected
    assert status["incidents"] == (1 if expected else 0)
    for db in sessions:
        assert db.closed and db.rollbacks >= 1
    with Session(engine) as db:
        assert db.query(Prediction).count() == expected
        assert db.query(IncidentFlow).count() == expected
        inc = db.query(Incident).first()
        assert (inc.flow_count if inc else 0) == expected

    # A failed run cannot poison the next session/run.
    svc._predictor = StubPredictor()
    svc._db_factory = lambda: Session(engine)
    svc.start("attack")
    finish(svc)
    assert svc.status()["state"] == "COMPLETED"
    assert svc.status()["processed"] == 2


def test_restart_refuses_worker_that_survives_join(replay_case, monkeypatch):
    directory, engine = replay_case
    entered, release = threading.Event(), threading.Event()

    class BlockingPredictor(StubPredictor):
        def predict(self, features, **kwargs):
            entered.set()
            assert release.wait(5)
            return super().predict(features, **kwargs)

    svc = ReplayService(predictor=BlockingPredictor(), scenarios_dir=directory,
                        db_factory=lambda: Session(engine), sleep_fn=lambda _: None)
    svc.start("attack")
    assert entered.wait(2)
    old_thread = svc._thread
    old_run = svc.status()["run_id"]
    svc.stop()
    try:
        # Model a timed-out join without making the test wait ten seconds.
        with monkeypatch.context() as patch:
            patch.setattr(old_thread, "join", lambda timeout=None: None)
            with pytest.raises(ReplayConflict, match="worker"):
                svc.start("attack")
        assert svc._thread is old_thread
        assert svc.status()["run_id"] == old_run
    finally:
        release.set()
        old_thread.join(2)
        if svc._thread is not old_thread:
            svc._thread.join(2)


def test_shutdown_wakes_paused_worker_and_joins(replay_case):
    directory, engine = replay_case
    entered, release = threading.Event(), threading.Event()

    class BlockingPredictor(StubPredictor):
        def predict(self, features, **kwargs):
            entered.set()
            assert release.wait(5)
            return super().predict(features, **kwargs)

    svc = ReplayService(predictor=BlockingPredictor(), scenarios_dir=directory,
                        db_factory=lambda: Session(engine))
    svc.start("attack")
    assert entered.wait(2)
    svc.pause()
    release.set()
    try:
        svc.shutdown()
        assert not svc._thread.is_alive()
        assert svc.status()["state"] in {"STOPPED", "COMPLETED"}
    finally:
        if svc._thread.is_alive():
            svc.stop()
            svc._thread.join(2)


@pytest.mark.parametrize("action", ["start", "pause", "resume", "stop"])
def test_unexpected_control_errors_are_not_conflicts(action):
    from fastapi.testclient import TestClient
    from backend.app.api.replay import get_replay_service
    from backend.app.main import app

    class BrokenControl:
        def __getattr__(self, name):
            def fail(*args):
                raise RuntimeError("unexpected control failure")
            return fail

    app.dependency_overrides[get_replay_service] = lambda: BrokenControl()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(f"/api/replay/{action}", json={"scenario": "normal"})
            assert response.status_code == 500
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


def test_unavailable_predictor_returns_service_unavailable(monkeypatch):
    from fastapi.testclient import TestClient
    import backend.app.api.predict as predict_api
    import backend.app.api.replay as replay_api
    from backend.app.main import app
    from backend.app.services.predictor import PredictorError

    def unavailable():
        raise PredictorError("missing artifacts")

    monkeypatch.setattr(replay_api, "_replay_service", None)
    monkeypatch.setattr(predict_api, "get_predictor", unavailable)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/replay/start", json={"scenario": "normal"})
        assert response.status_code == 503


def test_lifespan_shuts_down_existing_replay_service(replay_case, monkeypatch):
    from fastapi.testclient import TestClient
    import backend.app.api.replay as replay_api
    from backend.app.main import app
    directory, engine = replay_case
    entered, release = threading.Event(), threading.Event()

    class BlockingPredictor(StubPredictor):
        def predict(self, features, **kwargs):
            entered.set()
            assert release.wait(5)
            return super().predict(features, **kwargs)

    svc = ReplayService(predictor=BlockingPredictor(), scenarios_dir=directory,
                        db_factory=lambda: Session(engine))
    monkeypatch.setattr(replay_api, "_replay_service", svc)
    try:
        with TestClient(app):
            svc.start("attack")
            assert entered.wait(2)
            svc.pause()
            release.set()
        assert not svc._thread.is_alive()
        assert svc.status()["state"] == "STOPPED"
    finally:
        release.set()
        if svc._thread.is_alive():
            svc.stop()
            svc._thread.join(2)


@pytest.mark.parametrize("stage", ["rollback", "close"])
def test_cleanup_failure_is_reported_without_losing_primary_error(replay_case, stage):
    directory, engine = replay_case
    sessions = []

    class BrokenCleanup(Session):
        closed = False

        def commit(self):
            raise RuntimeError("primary commit failure")

        def rollback(self):
            super().rollback()
            if stage == "rollback":
                raise RuntimeError("secondary rollback failure")

        def close(self):
            self.closed = True
            super().close()
            if stage == "close":
                raise RuntimeError("secondary close failure")

    def factory():
        db = BrokenCleanup(bind=engine)
        sessions.append(db)
        return db

    svc = ReplayService(predictor=StubPredictor(), scenarios_dir=directory,
                        db_factory=factory, sleep_fn=lambda _: None)
    svc.start("attack")
    finish(svc)
    status = svc.status()
    assert status["state"] == "FAILED" and status["processed"] == 0
    assert "primary commit failure" in status["error"]
    assert f"secondary {stage} failure" in status["error"]
    assert sessions[0].closed
    with Session(engine) as db:
        assert db.query(Prediction).count() == 0
        assert db.query(Incident).count() == 0
