"""Profile preview/persistence for the scenario-based Playground."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.db.models import PlaygroundProfile, PlaygroundRun, PlaygroundResult
from backend.app.schemas.playground import ProfileOut, ProfileRequest, RunRequest, RunOut
from backend.app.services.playground import select_suite, run_profile, NOTICE
from backend.app.services.scenarios import ScenarioError
from backend.app.api.predict import get_predictor
from backend.app.services.predictor import PredictorError

router = APIRouter(prefix='/api/playground', tags=['playground'])


def get_db():
    with SessionLocal() as db:
        yield db


@router.post('/profile', response_model=ProfileOut)
def create_profile(req: ProfileRequest, db: Session = Depends(get_db)):
    try:
        plan = select_suite(req)
    except (ScenarioError, ValueError, OSError) as exc:
        raise HTTPException(503, 'Scenario library unavailable') from exc
    row = PlaygroundProfile(name=req.environment.replace('_',' '), config=req.model_dump())
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(503, 'Profile could not be saved') from exc
    return dict(id=row.id, profile=row.config, **plan)


def get_playground_predictor():
    try:
        return get_predictor()
    except PredictorError as exc:
        raise HTTPException(503, 'Inference unavailable; check model artifacts') from exc


@router.post('/run', response_model=RunOut)
def run(req: RunRequest, db: Session = Depends(get_db), predictor=Depends(get_playground_predictor)):
    profile = db.get(PlaygroundProfile, req.profile_id)
    if profile is None:
        raise HTTPException(404, 'Profile not found')
    try:
        return run_profile(db, profile, predictor)
    except (SQLAlchemyError, ScenarioError, ValueError, OSError) as exc:
        db.rollback()
        raise HTTPException(503, 'Evaluation could not be saved or prepared') from exc


@router.get('/results/{run_id}', response_model=RunOut)
def results(run_id: int, db: Session = Depends(get_db)):
    run = db.get(PlaygroundRun, run_id)
    if run is None:
        raise HTTPException(404, 'Run not found')
    result = db.query(PlaygroundResult).filter_by(run_id=run_id).order_by(PlaygroundResult.id.desc()).first()
    return result.data if result else dict(run_id=run_id, status=run.status, notice=NOTICE)
