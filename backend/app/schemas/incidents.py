"""schemas/incidents.py — Incident API contract (Phase 3, PRD §14, §17).

The replay run produces a deterministic incident stream. This contract lets a
monitor UI list grouped incidents (with aggregate bulletin) and open one to
inspect the persisted per-flow evidence (IncidentFlow rows). All aggregates
(flow_count, first/last seen, max severity/risk) are computed at replay time
by the IncidentGrouper and persisted — the API does not recompute them.

Phase-3 UI closure contract (2026-08-10): IncidentFlowOut additionally exposes
the per-flow fields the Incident Detail screen requires (PRD §17):
anomaly_score, the persisted SHAP top_features (suspicious flows only) and a
small baseline_features subset (the config-listed benign-baseline features)
read from the linked Prediction row. The benign-baseline statistics themselves
are served once by ``GET /api/baselines/benign`` (static artifact), so the UI
can render "behaviour vs normal". IncidentDetail also carries the summary
confidence/anomaly of the dominant (max-risk) evidence flow.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IncidentSummary(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: int
    label: Optional[str] = None
    family: Optional[str] = None
    classification: Optional[str] = Field(
        default=None, description="KNOWN_ATTACK | UNKNOWN_SUSPICIOUS"
    )
    severity: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    service_port: Optional[int] = None
    flow_count: int
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class IncidentFlowOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: int
    flow_id: Optional[str] = None
    prediction_id: Optional[int] = None
    label: Optional[str] = None
    confidence: Optional[float] = None
    anomaly_threshold: Optional[float] = None
    classification: Optional[str] = None
    family: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    service_port: Optional[int] = None
    replay_time: Optional[datetime] = None
    anomaly_score: Optional[float] = Field(
        default=None, description="IsolationForest decision_function (PRD §9)"
    )
    top_features: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Persisted SHAP contributions for this evidence flow "
        "(suspicious flows only, PRD §12)",
    )
    baseline_features: Dict[str, float] = Field(
        default_factory=dict,
        description="Values of the config-listed benign-baseline features for "
        "this flow (PRD §13)",
    )


class IncidentDetail(IncidentSummary):
    flows: List[IncidentFlowOut] = Field(default_factory=list)
    confidence: Optional[float] = Field(
        default=None, description="confidence of the dominant (max-risk) flow"
    )
    anomaly_score: Optional[float] = Field(
        default=None, description="anomaly score of the dominant (max-risk) flow"
    )


class IncidentList(BaseModel):
    model_config = {"protected_namespaces": ()}

    total: int
    incidents: List[IncidentSummary]


class BenignBaselineStats(BaseModel):
    model_config = {"protected_namespaces": ()}

    median: float
    mean: float
    p25: float
    p75: float
    std: float
    n: int


class BenignBaselinesOut(BaseModel):
    """Static benign-baseline artifact (PRD §13), served for the UI comparison."""

    model_config = {"protected_namespaces": ()}

    version: str
    source: str
    n_benign_flows: int
    feature_count: int
    features: List[str]
    baselines: Dict[str, BenignBaselineStats]
    unit_note: str
