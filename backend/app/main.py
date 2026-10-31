"""main.py — FastAPI application entry point (Phase-1 skeleton).

PRD §38 routes exist as stubs except POST /api/predict which is fully wired
for the Phase-1 completion gate. No authentication (out of baseline scope).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.incidents import router as incidents_router
from backend.app.api.incidents import baselines_router
from backend.app.api.predict import router as predict_router
from backend.app.api.replay import router as replay_router
from backend.app.api.replay import shutdown_replay_service
from backend.app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        yield
    finally:
        shutdown_replay_service()


app = FastAPI(
    title="Network IDS — Security Evaluation",
    description="Phase-3: replay engine + deterministic incident grouping "
    "(wraps the Phase-2 predictor).",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(predict_router)
app.include_router(replay_router)
app.include_router(incidents_router)
app.include_router(baselines_router)


@app.get("/api/health")
def health() -> dict:
    from backend.app.api.predict import get_predictor  # lazy

    try:
        p = get_predictor()
        return {
            "status": "ok",
            "model_loaded": True,
            "feature_count": len(p.feature_order),
            "phase": "phase-2",
            "version": "0.2.0",
            "readiness": "ready",
            "message": None,
        }
    except Exception:  # artifacts not exported yet
        return {
            "status": "ok",
            "model_loaded": False,
            "feature_count": 0,
            "phase": "phase-2",
            "version": "0.2.0",
            "readiness": "unavailable",
            "message": "Model artifacts could not be loaded. Check the runtime artifacts and configuration.",
        }
