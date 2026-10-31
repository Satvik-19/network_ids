"""Profile preview/persistence for the scenario-based Playground."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.db.models import PlaygroundProfile
from backend.app.schemas.playground import ProfileOut, ProfileRequest
from backend.app.services.playground import select_suite
from backend.app.services.scenarios import ScenarioError

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
