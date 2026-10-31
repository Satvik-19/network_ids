"""predict.py — POST /api/predict (Phase-2 end-to-end gate).

Runs: flow features -> preprocessing -> supervised + anomaly -> hybrid ->
risk -> SHAP, and persists the prediction to SQLite.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.db.models import Prediction
from backend.app.schemas.predict import PredictRequest, PredictResponse, TopFeature
from backend.app.services.predictor import Phase2Predictor, PredictorError

router = APIRouter(prefix="/api", tags=["predict"])

_predictor: Phase2Predictor | None = None


def get_predictor() -> Phase2Predictor:
    global _predictor
    if _predictor is None:
        _predictor = Phase2Predictor()
    return _predictor


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/predict", response_model=PredictResponse)
def predict(
    req: PredictRequest,
    db: Session = Depends(get_db),
    predictor: Phase2Predictor = Depends(get_predictor),
) -> PredictResponse:
    try:
        result = predictor.predict(req.features)
    except PredictorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    row = Prediction(
        flow_id=req.flow_id,
        source_config=None,
        model_name=predictor.model_name,
        model_version=predictor.model_version,
        label=result["label"],
        family=result["family"],
        classification=result["classification"],
        confidence=result["confidence"],
        anomaly_score=result["anomaly_score"],
        anomaly_threshold=result["anomaly_threshold"],
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        top_features=result["top_features"],
        features=dict(sorted(req.features.items())),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return PredictResponse(
        prediction_id=row.id,
        classification=result["classification"],
        label=result["label"],
        family=result["family"],
        confidence=result["confidence"],
        anomaly_score=result["anomaly_score"],
        anomaly_threshold=result["anomaly_threshold"],
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        top_features=[
            TopFeature(**tf) for tf in result["top_features"]
        ],
        model_name=predictor.model_name,
        model_version=predictor.model_version,
    )
