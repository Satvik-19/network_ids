"""api/incidents.py — Incident query endpoints (Phase 3, PRD §14).

Read-only: list grouped incidents (aggregate bulletin) and open one for the
persisted per-flow evidence. The aggregates were computed by the
IncidentGrouper during the replay run — the API serves persisted rows, never
re-derives them.

Phase-3 UI closure (PRD §17): GET /api/incidents/{id} joins the linked
Prediction row so each evidence flow exposes anomaly_score, the persisted SHAP
top_features (suspicious flows only) and the baseline_features subset (the
config-listed benign-baseline features). The static benign baselines are also
served by ``GET /api/baselines/benign``.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from backend.app.db.database import SessionLocal
from backend.app.db.models import Incident, Prediction
from backend.app.schemas.incidents import (
    BenignBaselinesOut,
    IncidentDetail,
    IncidentFlowOut,
    IncidentList,
    IncidentSummary,
)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])
baselines_router = APIRouter(prefix="/api/baselines", tags=["incidents"])

ROOT = Path(__file__).resolve().parents[3]
BASELINES_ARTIFACT = ROOT / "ml" / "artifacts" / "benign_baselines.json"
CONFIG_PATH = ROOT / "config" / "config.yaml"

_benign_baselines: BenignBaselinesOut | None = None
_baseline_feature_names: list[str] = []


def _load_baselines() -> BenignBaselinesOut | None:
    """Load + cache the benign baseline artifact (single source of truth)."""
    global _benign_baselines
    if _benign_baselines is None and BASELINES_ARTIFACT.exists():
        doc = json.loads(BASELINES_ARTIFACT.read_text(encoding="utf-8"))
        _benign_baselines = BenignBaselinesOut(**doc)
    return _benign_baselines


def _load_baseline_feature_names() -> list[str]:
    global _baseline_feature_names
    if not _baseline_feature_names:
        import yaml

        doc = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        _baseline_feature_names = list(
            (doc.get("inference") or {}).get("baseline_features", [])
        )
    return _baseline_feature_names


@baselines_router.get("/benign", response_model=BenignBaselinesOut)
def get_benign_baselines() -> BenignBaselinesOut:
    baselines = _load_baselines()
    if baselines is None:
        raise HTTPException(
            status_code=404,
            detail="benign_baselines.json artifact not present (run "
            "ml/hybrid/baselines.py first)",
        )
    return baselines


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _flow_out(flow, prediction: Prediction | None, baseline_names: list[str]) -> IncidentFlowOut:
    """Build an IncidentFlowOut, enriching from the linked Prediction row."""
    baseline_features = {}
    if prediction is not None and prediction.features:
        for name in baseline_names:
            value = prediction.features.get(name)
            if value is not None:
                baseline_features[name] = float(value)
    return IncidentFlowOut(
        id=flow.id,
        flow_id=flow.flow_id,
        prediction_id=flow.prediction_id,
        label=flow.label,
        confidence=flow.confidence,
        classification=flow.classification,
        family=flow.family,
        risk_level=flow.risk_level,
        risk_score=flow.risk_score,
        source=flow.source,
        destination=flow.destination,
        service_port=flow.service_port,
        replay_time=flow.replay_time,
        anomaly_score=prediction.anomaly_score if prediction else None,
        anomaly_threshold=prediction.anomaly_threshold if prediction else None,
        top_features=list(prediction.top_features or []) if prediction else [],
        baseline_features=baseline_features,
    )


def _summary(inc: Incident) -> IncidentSummary:
    return IncidentSummary(
        id=inc.id,
        label=inc.label,
        family=inc.family,
        classification=inc.classification,
        severity=inc.severity,
        risk_level=inc.risk_level,
        risk_score=inc.risk_score,
        source=inc.source,
        destination=inc.destination,
        service_port=inc.service_port,
        flow_count=inc.flow_count,
        started_at=inc.started_at,
        last_activity_at=inc.last_activity_at,
        ended_at=inc.ended_at,
    )


@router.get("", response_model=IncidentList)
def list_incidents(
    db: Session = Depends(get_db),
    source: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    family: str | None = Query(default=None),
    classification: str | None = Query(default=None),
    run_id: str | None = Query(
        default=None,
        description="scope to one replay run (Monitor incident side panel "
        "passes the current run; the Incidents page omits it for full history)",
    ),
    limit: int = Query(default=100, ge=1, le=1000),
) -> IncidentList:
    q = db.query(Incident).order_by(Incident.started_at.desc())
    if run_id:
        q = q.filter(Incident.run_id == run_id)
    if source:
        q = q.filter(Incident.source == source)
    if destination:
        q = q.filter(Incident.destination == destination)
    if family:
        q = q.filter(Incident.family == family)
    if classification:
        q = q.filter(Incident.classification == classification)
    rows = q.limit(limit).all()
    return IncidentList(total=len(rows), incidents=[_summary(r) for r in rows])


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
) -> IncidentDetail:
    inc = (
        db.query(Incident)
        .options(selectinload(Incident.flows))
        .filter(Incident.id == incident_id)
        .first()
    )
    if inc is None:
        raise HTTPException(status_code=404, detail="incident not found")

    baseline_names = _load_baseline_feature_names()

    # Join each evidence row to its Prediction for anomaly + SHAP + baseline.
    prediction_ids = [f.prediction_id for f in inc.flows if f.prediction_id]
    predictions = {}
    if prediction_ids:
        for p in db.query(Prediction).filter(Prediction.id.in_(prediction_ids)):
            predictions[p.id] = p

    flows = [
        _flow_out(f, predictions.get(f.prediction_id), baseline_names)
        for f in sorted(inc.flows, key=lambda x: x.replay_time or x.id)
    ]

    detail = _summary(inc).model_dump()
    detail["flows"] = flows

    # Dominant-flow summary for PRD §17 (confidence / anomaly of the max-risk
    # evidence flow, i.e. the flow that set the incident's label/risk).
    if flows:
        dominant = max(flows, key=lambda f: (f.risk_score or 0.0, -f.id))
        detail["confidence"] = dominant.confidence
        detail["anomaly_score"] = dominant.anomaly_score

    return IncidentDetail(**detail)
