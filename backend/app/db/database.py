"""database.py — SQLite engine, session factory, and init helpers.

Phase-1 scope (PRD §41): store predictions / incidents / incident_flows /
playground_profiles / playground_runs / playground_results. Training data
stays in Parquet/CSV — never loaded into SQLite.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "network_ids.db"
# Allow tests to point the engine at an isolated temp DB (NETWORK_IDS_DB).
DB_PATH = Path(os.environ.get("NETWORK_IDS_DB", str(_DEFAULT_DB)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db() -> None:
    """Create tables if they do not exist (idempotent)."""
    from . import models  # noqa: F401  (registers tables on Base.metadata)

    Base.metadata.create_all(bind=engine)
    _migrate_schema()


def _migrate_schema() -> None:
    """Idempotent additive migrations for the SQLite dev DB.

    SQLite `create_all` does not add columns to existing tables, so any column
    added to an ORM model after a DB already exists must be patched in here as
    an ADVISORY `ALTER TABLE ADD COLUMN`. Plain bool has no canonical SQLite
    representation; use `integer`. Missing base tables are created by
    `create_all` first, so these ALTERs only touch existing tables.

    Architecture discipline: additive columns only, never renames/drops — old
    rows stay readable (PRD §41). Update the table each time a new ORM column
    is added.
    """
    columns_by_table = {
        "incidents": [
            "classification VARCHAR(32)",
            "source VARCHAR(64)",
            "destination VARCHAR(64)",
            "service_port INTEGER",
            "last_activity_at DATETIME",
            "risk_level VARCHAR(16)",
            "risk_score FLOAT",
            "run_id VARCHAR(64)",
        ],
        "incident_flows": [
            "source VARCHAR(64)",
            "destination VARCHAR(64)",
            "service_port INTEGER",
            "replay_time DATETIME",
            "classification VARCHAR(32)",
            "family VARCHAR(64)",
            "risk_level VARCHAR(16)",
            "risk_score FLOAT",
        ],
        "predictions": [
            "source VARCHAR(64)",
            "destination VARCHAR(64)",
            "service_port INTEGER",
            "replay_time DATETIME",
            "seq INTEGER",
            "run_id VARCHAR(64)",
        ],
    }
    with engine.begin() as conn:
        for table, cols in columns_by_table.items():
            existing = {c["name"] for c in inspect(conn).get_columns(table)}
            for col in cols:
                name = col.split()[0]
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col}"))
