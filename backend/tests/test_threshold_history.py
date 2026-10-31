import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateTable

import backend.app.db.database as database
from backend.app.db.models import Prediction
from backend.app.main import app


def test_additive_threshold_migration_preserves_legacy_evidence(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    ddl = str(CreateTable(Prediction.__table__).compile(engine))
    ddl = '\n'.join(line for line in ddl.splitlines() if 'anomaly_threshold' not in line)
    with engine.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(text("""INSERT INTO predictions
            (id, created_at, model_name, model_version, label, family, classification, confidence)
            VALUES (1, '2026-08-13', 'legacy', 'phase-2', 'BENIGN', 'BENIGN', 'BENIGN', .99)"""))
    monkeypatch.setattr(database, 'engine', engine)
    try:
        database.init_db()
        database.init_db()
        with engine.connect() as conn:
            row = conn.execute(text('SELECT model_name, anomaly_threshold FROM predictions WHERE id=1')).one()
        assert row == ('legacy', None)
    finally:
        engine.dispose()


def test_real_prediction_returns_and_persists_effective_threshold():
    fixture = Path(__file__).resolve().parents[2] / 'data/scenarios/normal.json'
    flow = json.loads(fixture.read_text(encoding='utf-8'))['flows'][0]
    with TestClient(app) as client:
        response = client.post('/api/predict', json={'features': flow['features']})
    assert response.status_code == 200
    body = response.json()
    assert body['anomaly_threshold'] == -0.0928
    with database.SessionLocal() as db:
        prediction = db.get(Prediction, body['prediction_id'])
        assert prediction.anomaly_threshold == body['anomaly_threshold']
