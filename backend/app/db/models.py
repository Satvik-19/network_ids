"""models.py — SQLAlchemy ORM models for PRD §41 tables.

Phase 1 creates the schema and persists predictions. The incident /
incident_flows / playground tables are created now to lock the schema
(ARCHITECTURE_LOCK §11) but are written by later phases.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Prediction(Base):
    """One Phase-2 prediction for one flow (hybrid + risk + anomaly)."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # Source / flow identity.
    flow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_config: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Phase-3.5 run-scoping: one replay run id (uuid hex) shared by every row
    # the run persists, so the Monitor feed can isolate the current run.
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Model + result.
    model_name: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(64))
    family: Mapped[str] = mapped_column(String(64))
    classification: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)

    # Phase-2 fields.
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_features: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Full feature values (JSON) so the prediction is reproducible.
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Phase-3 replay side-car metadata (PRD §7 traffic stream). Additive,
    # populated only by the replay engine; /api/predict leaves these NULL so
    # the traffic table can distinguish replay evidence.
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(64), nullable=True)
    service_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replay_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Incident(Base):
    """Grouped incident (created by the Phase-3 replay/grouping engine)."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    flow_count: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Phase-3 fields (added by the replay/grouping engine, PRD §14).
    classification: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(64), nullable=True)
    service_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Phase-3.5 run-scoping: the replay run that produced this incident.
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    flows: Mapped[list["IncidentFlow"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentFlow(Base):
    """Per-flow membership inside an incident (Phase 3)."""

    __tablename__ = "incident_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE")
    )
    flow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("predictions.id"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Phase-3 evidence fields (replay metadata + risk, PRD §14).
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(64), nullable=True)
    service_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replay_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    classification: Mapped[str | None] = mapped_column(String(32), nullable=True)
    family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="flows")


class PlaygroundProfile(Base):
    """A saved traffic-profile scenario for the Playground (Phase 4)."""

    __tablename__ = "playground_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON)  # profile parameters


class PlaygroundRun(Base):
    """A Playground simulation run (Phase 4)."""

    __tablename__ = "playground_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("playground_profiles.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PlaygroundResult(Base):
    """One row of Playground run output (Phase 4)."""

    __tablename__ = "playground_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("playground_runs.id", ondelete="CASCADE")
    )
    data: Mapped[dict] = mapped_column(JSON)  # run result payload
