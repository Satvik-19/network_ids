"""replay.py — In-process, thread-based replay engine (Phase 3, PRD §13–14).

The replay engine re-runs a deterministic scenario through the SHARED Phase-2
predictor, persists each prediction, and feeds the persistent rule-based
incident grouping (IncidentGrouper). It is in-process (no cells/queues/Redis —
ARCHITECTURE_LOCK) and polling-first: clients poll ``GET /api/replay/status``
while a background worker thread advances the replay.

State machine: IDLE -> RUNNING <-> PAUSED -> COMPLETED | STOPPED
  - start():        IDLE/COMPLETED/STOPPED -> RUNNING   (rejects concurrent)
  - pause():        RUNNING -> PAUSED
  - resume():       PAUSED -> RUNNING
  - stop():         RUNNING/PAUSED -> STOPPED

Determinism:
  * flows replay in exact scenario ``seq`` order,
  * a flow's synthetic replay timestamp = scenario base + seq × interval,
  * progress counters are monotonic; same scenario+speed => identical stream.
  * the pacing sleep is injectable so tests never wait on real time.

The shared Phase-2 predictor is used for EVERY flow (its hybrid dict is the
only input to grouping). SHAP is computed ONLY for suspicious flows (the
decision layer runs for all, which is where hybrid needs to decide);
benign flows are persisted without SHAP to keep replay fast.
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.app.db.database import SessionLocal
from backend.app.db.models import Incident, IncidentFlow, Prediction
from backend.app.services.incidents import IncidentGrouper
from backend.app.services.scenarios import (
    SCENARIOS_DIR,
    Scenario,
    ScenarioError,
    ScenarioPlayer,
    load_scenario,
)

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "config.yaml"

STATE_IDLE, STATE_RUNNING, STATE_PAUSED, STATE_COMPLETED, STATE_STOPPED = (
    "IDLE", "RUNNING", "PAUSED", "COMPLETED", "STOPPED",
)


class ReplayConflict(RuntimeError):
    """Invalid transition for the current replay state (API returns 409)."""


class ReplayNotFound(RuntimeError):
    """Unknown scenario name (API returns 404)."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReplayService:
    """Owns replay state, the worker thread, and per-run DB writes."""

    def __init__(
        self,
        *,
        predictor,
        scenarios_dir: Path = SCENARIOS_DIR,
        db_factory=SessionLocal,
        replay_config: dict | None = None,
        incidents_config: dict | None = None,
        sleep_fn=time.sleep,
    ) -> None:
        self._predictor = predictor          # shared Phase-2 predictor
        self._scenarios_dir = Path(scenarios_dir)
        self._db_factory = db_factory
        self._sleep = sleep_fn               # injectable pacing sleep (tests)

        cfg = replay_config or {}
        self._speeds = set(int(s) for s in cfg.get("speeds", [1, 5, 20]))
        self._default_speed = int(cfg.get("default_speed", 5))

        inc = incidents_config or {}
        self._window = float(inc.get("grouping_window_seconds", 30.0))

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pause_evt = threading.Event()  # set() = not paused
        self._pause_evt.set()

        self._state = STATE_IDLE
        self._scenario: Scenario | None = None
        self._player: ScenarioPlayer | None = None
        self._speed = self._default_speed
        # run counters (monotonic, guard with _lock)
        self._processed = 0
        self._total = 0
        self._suspicious = 0
        self._known = 0
        self._unknown = 0
        self._incidents = 0
        self._errors = 0
        self._last_error: str | None = None
        self._seq = -1
        self._base_ts = 0.0
        self._started_at: datetime | None = None
        self._run_id: str | None = None
        self._max_risk_score = 0.0
        self._max_risk_level = "LOW"
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------ #
    # controls
    # ------------------------------------------------------------------ #
    def start(self, scenario_name: str, speed: int | None = None) -> None:
        stale_thread: threading.Thread | None = None
        with self._lock:
            if self._state in (STATE_RUNNING, STATE_PAUSED):
                raise ReplayConflict(
                    f"cannot start while state={self._state}; pause/resume/stop first"
                )
            if speed is not None and int(speed) not in self._speeds:
                raise ValueError(
                    f"speed {speed} not allowed (allowed: {sorted(self._speeds)})"
                )
            scenario = self._load_scenario(scenario_name)
            stale_thread = self._thread
            if stale_thread is not None and stale_thread.is_alive():
                # stop() flips the STATE synchronously but the worker thread may
                # still be draining its current flow. Never spawn a fresh run on
                # top of it or the stale thread would race the new one on the
                # same counters/DB (docs/BUG_LOG.md BUG-012).
                self._stop_event.set()
                self._pause_evt.set()

        if stale_thread is not None:
            stale_thread.join(timeout=10.0)

        with self._lock:
            if self._state in (STATE_RUNNING, STATE_PAUSED):
                raise ReplayConflict(
                    "cannot start while a replay is active (concurrent start raced)"
                )
            if speed is not None and int(speed) not in self._speeds:
                raise ValueError(
                    f"speed {speed} not allowed (allowed: {sorted(self._speeds)})"
                )
            self._scenario = scenario
            self._player = ScenarioPlayer(scenario)
            self._speed = self._default_speed if speed is None else int(speed)

            # reset run state
            self._processed = 0
            self._total = scenario.total
            self._suspicious = 0
            self._known = 0
            self._unknown = 0
            self._incidents = 0
            self._errors = 0
            self._last_error = None
            self._max_risk_score = 0.0
            self._max_risk_level = "LOW"
            self._seq = -1
            self._base_ts = time.time()      # wall-clock base for synthetic time
            self._started_at = _utcnow()
            self._run_id = uuid.uuid4().hex   # run-scopes persisted evidence
            self._stop_event.clear()
            self._pause_evt.set()
            self._state = STATE_RUNNING

            self._thread = threading.Thread(
                target=self._run, daemon=True, name=f"replay-{scenario_name}"
            )
            self._thread.start()

    def pause(self) -> None:
        with self._lock:
            if self._state != STATE_RUNNING:
                raise ReplayConflict(
                    f"cannot pause; state={self._state} (must be RUNNING)"
                )
            self._state = STATE_PAUSED
            self._pause_evt.clear()

    def resume(self) -> None:
        with self._lock:
            if self._state != STATE_PAUSED:
                raise ReplayConflict(
                    f"cannot resume; state={self._state} (must be PAUSED)"
                )
            self._state = STATE_RUNNING
            self._pause_evt.set()

    def stop(self) -> None:
        with self._lock:
            if self._state not in (STATE_RUNNING, STATE_PAUSED):
                raise ReplayConflict(
                    f"cannot stop; state={self._state} (must be RUNNING or PAUSED)"
                )
            self._state = STATE_STOPPED
        self._stop_event.set()
        self._pause_evt.set()

    # ------------------------------------------------------------------ #
    # status
    # ------------------------------------------------------------------ #
    def status(self) -> dict:
        with self._lock:
            interval = (
                self._scenario.logical_interval_seconds
                if self._scenario else 1.0
            )
            pace = interval / self._speed if self._speed else 0.0
            return {
                "state": self._state,
                "scenario": self._scenario.name if self._scenario else None,
                "speed": self._speed,
                "speeds": sorted(self._speeds),
                "pace_seconds": round(pace, 4),
                "processed": self._processed,
                "total": self._total,
                "suspicious": self._suspicious,
                "known_attacks": self._known,
                "unknown_suspicious": self._unknown,
                "incidents": self._incidents,
                "errors": self._errors,
                "error": self._last_error,
                "progress": (self._processed / self._total) if self._total else 0.0,
                "current_sequence": self._seq,
                "current_replay_time": self._synthetic_time(
                    self._seq, self._base_ts
                ) if self._player else None,
                "max_risk_score": self._max_risk_score,
                "max_risk_level": self._max_risk_level,
                "started_at": (
                    self._started_at.isoformat() if self._started_at else None
                ),
                "run_id": self._run_id,
            }

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #
    def _load_scenario(self, name: str) -> Scenario:
        path = self._scenarios_dir / f"{name}.json"
        if not path.exists():
            known = ", ".join(sorted(p.stem for p in self._scenarios_dir.glob("*.json")))
            raise ScenarioError(
                f"unknown scenario {name!r} (available: {known or 'none'})"
            )
        return load_scenario(path)

    def _synthetic_time(self, seq: int, base: float) -> str | None:
        if seq < 0 or self._player is None:
            return None
        body = self._player.replay_time(seq, base)
        return datetime.fromtimestamp(body, tz=timezone.utc).isoformat()

    def _run(self) -> None:
        grouper = IncidentGrouper(window_seconds=self._window)
        db = self._db_factory()
        incident_rows: dict[int, Incident] = {}
        closed: set[int] = set()
        try:
            while True:
                with self._lock:
                    if self._state == STATE_STOPPED:
                        break
                self._pause_evt.wait()       # cleared on pause; resume/stop set it
                with self._lock:
                    if self._state == STATE_STOPPED:
                        break
                    next_seq = self._processed
                if next_seq >= self._total:
                    break

                try:
                    flow = self._player.flow(next_seq)
                    prediction = self._predict_one(flow)
                    self._persist(
                        db, flow, prediction, grouper, next_seq,
                        incident_rows, closed,
                    )
                    with self._lock:
                        self._processed += 1
                        self._seq = next_seq
                        cls = prediction["classification"]
                        if cls != "BENIGN":
                            self._suspicious += 1
                        if cls == "KNOWN_ATTACK":
                            self._known += 1
                        elif cls == "UNKNOWN_SUSPICIOUS":
                            self._unknown += 1
                        if prediction["risk_score"] > self._max_risk_score:
                            self._max_risk_score = prediction["risk_score"]
                            self._max_risk_level = prediction["risk_level"]
                except Exception as exc:  # per-flow isolation; keep replay going
                    with self._lock:
                        self._errors += 1
                        self._last_error = repr(exc)
                    self._sleep(0.0)

                # pacing (skip on the last flow to avoid a trailing wait)
                if self._processed < self._total:
                    self._sleep(
                        self._scenario.logical_interval_seconds / self._speed
                    )
        finally:
            for gid, row in incident_rows.items():
                if gid not in closed:
                    # close with the incident's own last activity (synthetic
                    # replay time), not wall clock, so ended_at never precedes
                    # the last recorded flow.
                    row.ended_at = row.last_activity_at or _utcnow()
            db.commit()
            db.close()
            with self._lock:
                if self._state != STATE_STOPPED:
                    self._state = STATE_COMPLETED

    def _predict_one(self, flow: dict) -> dict:
        """One scoring pass; SHAP attached only for suspicious flows.

        Suspicious flows get ``explain()`` (a single extra SHAP computation)
        instead of a second full ``predict`` call, so the supervised + anomaly
        + hybrid + risk pipeline runs exactly once per flow (Phase-3.5
        hardening, docs/BUG_LOG.md BUG-010).
        """
        out = self._predictor.predict(flow["features"], with_shap=False)
        if out["classification"] != "BENIGN":
            shap = self._predictor.explain(flow["features"])
            out["top_features"] = shap["top_features"]
            out["shap_base_value"] = shap.get("base_value")
        return out

    def _persist(
        self,
        db,
        flow: dict,
        prediction: dict,
        grouper: IncidentGrouper,
        seq: int,
        incident_rows: dict[int, Incident],
        closed: set[int],
    ) -> None:
        replay_dt = datetime.fromtimestamp(
            self._player.replay_time(seq, self._base_ts), tz=timezone.utc
        )

        row = Prediction(
            flow_id=f"{self._scenario.name}-f{seq}",
            source_config=f"replay:{self._scenario.name}",
            run_id=self._run_id,
            model_name=self._predictor.model_name,
            model_version=self._predictor.model_version,
            label=prediction["label"],
            family=prediction["family"],
            classification=prediction["classification"],
            confidence=prediction["confidence"],
            anomaly_score=prediction.get("anomaly_score"),
            risk_level=prediction["risk_level"],
            risk_score=prediction["risk_score"],
            top_features=prediction.get("top_features") or [],
            features=dict(sorted(flow["features"].items())),
            # replay side-car (live traffic table, PRD §7)
            source=flow.get("source"),
            destination=flow.get("destination"),
            service_port=flow.get("service_port"),
            replay_time=replay_dt,
            seq=seq,
        )
        db.add(row)
        db.flush()

        assign = grouper.assign(
            classification=prediction["classification"],
            family=prediction["family"],
            label=prediction["label"],
            source=flow.get("source"),
            destination=flow.get("destination"),
            service_port=flow.get("service_port"),
            replay_time=replay_dt,
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
        )
        if assign.incident is None:
            db.commit()
            return

        # close a superseded open incident (window elapsed / key changed)
        if assign.superseded is not None:
            old_row = incident_rows.get(assign.superseded.group_id)
            if old_row is not None and assign.superseded.group_id not in closed:
                old_row.ended_at = replay_dt
                closed.add(assign.superseded.group_id)

        if assign.is_new and assign.incident.group_id not in incident_rows:
            inc = Incident(
                started_at=replay_dt,
                last_activity_at=replay_dt,
                run_id=self._run_id,
                label=assign.incident.label,
                family=assign.incident.family,
                classification=assign.incident.classification,
                source=assign.incident.source,
                destination=assign.incident.destination,
                service_port=assign.incident.service_port,
                flow_count=assign.incident.flow_count,
                severity=assign.incident.max_risk_level,
                risk_level=assign.incident.max_risk_level,
                risk_score=assign.incident.max_risk_score,
            )
            db.add(inc)
            db.flush()
            incident_rows[assign.incident.group_id] = inc
            with self._lock:
                self._incidents += 1

        inc = incident_rows[assign.incident.group_id]
        # keep aggregates fresh on every joined flow
        inc.flow_count = assign.incident.flow_count
        inc.last_activity_at = replay_dt
        inc.severity = assign.incident.max_risk_level
        inc.risk_level = assign.incident.max_risk_level
        inc.risk_score = assign.incident.max_risk_score
        inc.label = assign.incident.label

        db.add(
            IncidentFlow(
                incident_id=inc.id,
                flow_id=f"{self._scenario.name}-f{seq}",
                prediction_id=row.id,
                label=prediction["label"],
                confidence=prediction["confidence"],
                source=flow.get("source"),
                destination=flow.get("destination"),
                service_port=flow.get("service_port"),
                replay_time=replay_dt,
                classification=prediction["classification"],
                family=prediction["family"],
                risk_level=prediction["risk_level"],
                risk_score=prediction["risk_score"],
            )
        )
        db.commit()