"""schemas/replay.py — Replay engine API contract (Phase 3, PRD §13).

Endpoints:
  GET  /api/replay/scenarios     -> available scenario names + descriptions
  POST /api/replay/start         {scenario, speed} -> ReplayStatus
  POST /api/replay/pause         -> ReplayStatus
  POST /api/replay/resume        -> ReplayStatus
  POST /api/replay/stop          -> ReplayStatus
  GET  /api/replay/status        -> ReplayStatus

ReplayStatus carries the full deterministic ledger for the current run:
traffic analysed (processed/total), suspicious flows (known vs unknown),
incident count, progress, current sequence, synthetic replay time and the
current run's max risk. Thresholds/values come from real artifacts/config.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ScenarioInfo(BaseModel):
    model_config = {"protected_namespaces": ()}

    name: str
    description: str
    flows: int


class ReplayFlowOut(BaseModel):
    """One replayed flow for the live traffic table (PRD §7 traffic stream).

    Served from the persisted Prediction rows (replay side-car metadata), so
    the Monitor traffic table reflects real replay evidence — including pure
    BENIGN rows that never join an incident. Aggregations live in ReplayStatus;
    this is the per-flow view.
    """

    model_config = {"protected_namespaces": ()}

    id: int
    flow_id: Optional[str] = None
    scenario: Optional[str] = None
    seq: Optional[int] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    service_port: Optional[int] = None
    label: Optional[str] = None
    family: Optional[str] = None
    classification: Optional[str] = None
    confidence: Optional[float] = None
    anomaly_score: Optional[float] = None
    anomaly_threshold: Optional[float] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    replay_time: Optional[str] = None


class ReplayFlowsOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    total: int
    flows: List[ReplayFlowOut]


class ReplayStartRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    scenario: str = Field(..., description="Scenario fixture name (see /scenarios)")
    speed: Optional[int] = Field(default=None, description="1, 5 or 20 (default from config)")


class ReplayStatus(BaseModel):
    model_config = {"protected_namespaces": ()}

    state: str = Field(..., description="IDLE | RUNNING | PAUSED | COMPLETED | STOPPED | FAILED")
    scenario: Optional[str] = None
    speed: int
    speeds: List[int]
    pace_seconds: float
    processed: int = Field(..., description="flows analysed so far")
    total: int
    suspicious: int
    known_attacks: int
    unknown_suspicious: int
    incidents: int
    errors: int
    error: Optional[str] = None
    progress: float = Field(..., ge=0.0, le=1.0)
    current_sequence: Optional[int] = None
    current_replay_time: Optional[str] = Field(
        default=None,
        description="synthetic replay timestamp (scenario base + seq*interval)",
    )
    max_risk_score: float
    max_risk_level: str
    started_at: Optional[str] = None
    run_id: Optional[str] = Field(
        default=None,
        description="run-scoping id of the current/last replay run; the Monitor "
        "passes it to /flows and /incidents to isolate current-run evidence",
    )
