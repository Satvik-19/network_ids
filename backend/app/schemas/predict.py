"""schemas — Shared Pydantic schemas for the Phase-2 API contract.

Phase-2 prediction response (PRD §58 Phase-2 gate):
  classification:  BENIGN | KNOWN_ATTACK | UNKNOWN_SUSPICIOUS (hybrid, PRD §10)
  label / family:  supervised canonical label + display family
  confidence:      supervised top-1 probability
  anomaly_score:   IsolationForest raw decision_function (lower = more abnormal)
  risk_level / risk_score: transparent risk engine (PRD §11)
  top_features:    SHAP local explanations (PRD §12)

Every field is computed from real artifacts — nothing is fabricated.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """One CICIDS2017-compatible flow (raw feature values, canonical names)."""

    model_config = ConfigDict(protected_namespaces=())

    flow_id: Optional[str] = Field(default=None, description="Optional flow id")
    features: Dict[str, float] = Field(
        ...,
        description="77 canonical feature values keyed by feature name",
    )


class TopFeature(BaseModel):
    """One SHAP feature attribution for the predicted class."""

    model_config = ConfigDict(protected_namespaces=())

    feature: str
    shap_value: float
    direction: str


class PredictResponse(BaseModel):
    """Phase-2 prediction response (PRD §58 Phase-2 gate)."""

    model_config = ConfigDict(protected_namespaces=())

    prediction_id: int
    classification: str = Field(
        ...,
        description="BENIGN | KNOWN_ATTACK | UNKNOWN_SUSPICIOUS (PRD §10)",
    )
    label: str = Field(..., description="Predicted canonical class label")
    family: str = Field(..., description="Attack family / BENIGN")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Classifier confidence (top-1 probability)"
    )
    anomaly_score: float = Field(
        ..., description="IsolationForest decision_function (lower = more abnormal)"
    )
    risk_level: str = Field(
        ..., description="LOW | MEDIUM | HIGH | CRITICAL (PRD §11)"
    )
    risk_score: float = Field(
        ..., ge=0.0, le=100.0, description="Transparent risk score"
    )
    top_features: List[TopFeature] = Field(
        default_factory=list, description="SHAP local explanations (PRD §12)"
    )
    model_name: str
    model_version: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    feature_count: int
    phase: str = "phase-2"
    version: str = "0.2.0"
    readiness: str = "unavailable"
    message: Optional[str] = None
