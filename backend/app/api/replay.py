"""api/replay.py — Replay engine endpoints (Phase 3, PRD §13).

Exposes the shared ReplayService singleton in-process. Controls are REST
verbs; state is polled (ARCHITECTURE_LOCK: polling first, no WebSockets).
Replay runs on a background worker thread, so start() returns immediately.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas.replay import (
    ReplayFlowsOut,
    ReplayFlowOut,
    ReplayStartRequest,
    ReplayStatus,
    ScenarioInfo,
)
from backend.app.services.scenarios import (
    ScenarioError,
    load_scenarios_dir,
)
from backend.app.services.predictor import PredictorError
from backend.app.services.replay import ReplayConflict

router = APIRouter(prefix="/api/replay", tags=["replay"])

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "config.yaml"

_replay_service = None


def get_replay_service():
    """Lazily-built shared ReplayService (wraps the shared Phase-2 predictor)."""
    global _replay_service
    if _replay_service is None:
        import yaml

        from backend.app.api.predict import get_predictor
        from backend.app.services.replay import ReplayService

        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        try:
            _replay_service = ReplayService(
                predictor=get_predictor(),
                replay_config=cfg.get("replay", {}),
                incidents_config=cfg.get("incidents", {}),
            )
        except PredictorError as exc:
            raise HTTPException(status_code=503, detail="Inference unavailable; check model artifacts") from exc
    return _replay_service


def shutdown_replay_service() -> None:
    if _replay_service is not None:
        _replay_service.shutdown()


@router.get("/scenarios", response_model=list[ScenarioInfo])
def list_scenarios() -> list[ScenarioInfo]:
    return [
        ScenarioInfo(name=s.name, description=s.description, flows=s.total)
        for s in load_scenarios_dir()
    ]


@router.get("/flows", response_model=ReplayFlowsOut)
def recent_flows(
    limit: int = Query(default=50, ge=1, le=500),
    run_id: str | None = Query(
        default=None,
        description="scope to one replay run (the Monitor passes the current "
        "run so the live table never mixes sequential runs' evidence)",
    ),
) -> ReplayFlowsOut:
    """Most recent replayed flow predictions (live traffic table).

    Reads the persisted replay Prediction rows newest-first, so the Monitor
    traffic table shows real replay evidence (incl. benign rows) polling the
    same DB the incidents API reads. ``run_id`` scopes the feed to one replay
    run: the Security Monitor passes it so sequential replays never present a
    previous run's flows as current traffic (PRD §7 / Phase-3.5 hardening).
    """
    from backend.app.db.database import SessionLocal
    from backend.app.db.models import Prediction

    db = SessionLocal()
    try:
        q = db.query(Prediction).filter(Prediction.source_config.like("replay:%"))
        if run_id:
            q = q.filter(Prediction.run_id == run_id)
        rows = (
            q.order_by(Prediction.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
    return ReplayFlowsOut(
        total=len(rows),
        flows=[
            ReplayFlowOut(
                id=r.id,
                flow_id=r.flow_id,
                scenario=r.source_config.split(":", 1)[1] if r.source_config else None,
                seq=r.seq,
                source=r.source,
                destination=r.destination,
                service_port=r.service_port,
                label=r.label,
                family=r.family,
                classification=r.classification,
                confidence=r.confidence,
                anomaly_score=r.anomaly_score,
                anomaly_threshold=r.anomaly_threshold,
                risk_level=r.risk_level,
                risk_score=r.risk_score,
                replay_time=(r.replay_time.isoformat() if r.replay_time else None),
            )
            for r in rows
        ],
    )


@router.post("/start", response_model=ReplayStatus)
def start(
    req: ReplayStartRequest,
    svc=Depends(get_replay_service),
) -> ReplayStatus:
    try:
        svc.start(req.scenario, req.speed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ScenarioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReplayConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ReplayStatus(**svc.status())


@router.post("/pause", response_model=ReplayStatus)
def pause(svc=Depends(get_replay_service)) -> ReplayStatus:
    try:
        svc.pause()
    except ReplayConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ReplayStatus(**svc.status())


@router.post("/resume", response_model=ReplayStatus)
def resume(svc=Depends(get_replay_service)) -> ReplayStatus:
    try:
        svc.resume()
    except ReplayConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ReplayStatus(**svc.status())


@router.post("/stop", response_model=ReplayStatus)
def stop(svc=Depends(get_replay_service)) -> ReplayStatus:
    try:
        svc.stop()
    except ReplayConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ReplayStatus(**svc.status())


@router.get("/status", response_model=ReplayStatus)
def status(svc=Depends(get_replay_service)) -> ReplayStatus:
    return ReplayStatus(**svc.status())
