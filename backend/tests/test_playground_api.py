import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.db.models import Prediction, Incident, PlaygroundRun, PlaygroundResult


def assessment():
    import backend.app.services.playground as service
    assert hasattr(service, 'assess_results'), 'Scenario assessment missing'
    return service.assess_results


def test_readiness_uses_misses_and_false_alerts_not_confidence():
    results = [
        dict(name='attack', counts=dict(malicious=2,detected=1,missed=1,benign=0,false_alerts=0,correct_benign=0)),
        dict(name='control', counts=dict(malicious=0,detected=0,missed=0,benign=2,false_alerts=1,correct_benign=1)),
    ]
    result = assessment()(results, [], {'detection_weight':.5,'false_alert_weight':.5})
    assert result['score'] == 50
    assert result['missed'] == 1 and result['false_alerts'] == 1
    assert result['status'] == 'complete'
    assert assessment()(results, ['missing'], {'detection_weight':.5,'false_alert_weight':.5})['score'] is None


def test_benign_anomaly_challenge_cannot_earn_attack_credit():
    results = [dict(name='unknown', counts=dict(malicious=0,detected=0,missed=0,benign=4,false_alerts=4,correct_benign=0))]
    result = assessment()(results, [], {'detection_weight':.5,'false_alert_weight':.5})
    assert result['score'] is None and result['status'] == 'not_applicable'
    assert result['detected'] == 0 and result['false_alerts'] == 4
    with pytest.raises(ValueError): assessment()(results, [], {'detection_weight':1,'false_alert_weight':1})


def create_web(client):
    response = client.post('/api/playground/profile', json={'environment':'web_server','exposure':'public','services':['web']})
    assert response.status_code == 200
    return response.json()['id']


def test_complete_workflow_preserves_monitor_and_saves_reproducible_results():
    with SessionLocal() as db:
        before = (db.query(Prediction).count(), db.query(Incident).count())
    with TestClient(app) as client:
        profile_id = create_web(client)
        monitor_before = client.get('/api/replay/status').json()
        response = client.post('/api/playground/run', json={'profile_id':profile_id})
        assert response.status_code == 200
        body = response.json()
        assert body['status'] == 'completed'
        assert body['assessment']['detected'] == 12 and body['assessment']['missed'] == 4
        assert body['assessment']['false_alerts'] == 4
        assert body['assessment']['score'] == pytest.approx(70.83)
        assert body['coverage']['executed'] == body['coverage']['selected'] == 4
        assert body['coverage']['unknown_attack_detection'] == 'not established'
        assert client.get(f"/api/playground/results/{body['run_id']}").json() == body
        assert client.get('/api/replay/status').json() == monitor_before
    with SessionLocal() as db:
        assert (db.query(Prediction).count(), db.query(Incident).count()) == before
        run = db.get(PlaygroundRun, body['run_id'])
        assert run.config['thresholds'] == {'known_confidence':.75,'anomaly':-.0928}
        assert run.config['artifact_sha256']['supervised_model.joblib']
    assert any(f['output']['top_features'] for s in body['scenarios'] for f in s['flows'])
    assert all('features' in f for s in body['scenarios'] for f in s['flows'])


def test_inference_failure_has_no_success_score(monkeypatch):
    from backend.app.api.predict import get_predictor
    predictor = get_predictor()
    def fail(*args, **kwargs): raise RuntimeError('controlled failure')
    monkeypatch.setattr(predictor, 'predict', fail)
    with TestClient(app) as client:
        response = client.post('/api/playground/run', json={'profile_id':create_web(client)})
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'failed' and result['assessment'] is None
        assert client.get(f"/api/playground/results/{result['run_id']}").json()['status'] == 'failed'


def test_result_commit_failure_rolls_back_completed_status_and_partial_result(monkeypatch):
    import backend.app.api.playground as api
    with TestClient(app) as client:
        profile_id = create_web(client)
        def session():
            with SessionLocal() as db:
                original = db.commit
                calls = 0
                def commit():
                    nonlocal calls
                    calls += 1
                    if calls == 2: raise SQLAlchemyError('controlled result commit failure')
                    return original()
                monkeypatch.setattr(db, 'commit', commit)
                yield db
        app.dependency_overrides[api.get_db] = session
        try:
            response = client.post('/api/playground/run', json={'profile_id':profile_id})
            assert response.status_code == 200
            result = response.json()
            assert result['status'] == 'failed' and result['assessment'] is None
        finally:
            app.dependency_overrides.pop(api.get_db, None)
    with SessionLocal() as db:
        assert db.get(PlaygroundRun, result['run_id']).status == 'failed'
        rows = db.query(PlaygroundResult).filter_by(run_id=result['run_id']).all()
        assert len(rows) == 1 and rows[0].data['status'] == 'failed'


def test_restart_marks_interrupted_runs_failed_once():
    with SessionLocal() as db:
        run = PlaygroundRun(status='running', config={})
        db.add(run); db.commit(); run_id = run.id
    for _ in range(2):
        with TestClient(app) as client:
            response = client.get(f'/api/playground/results/{run_id}')
            assert response.status_code == 200
            assert response.json()['status'] == 'failed'
            assert 'interrupted' in response.json()['error'].lower()
    with SessionLocal() as db:
        assert db.query(PlaygroundResult).filter_by(run_id=run_id).count() == 1


def test_missing_profile_and_result_are_404():
    with TestClient(app) as client:
        assert client.post('/api/playground/run', json={'profile_id':999999}).status_code == 404
        assert client.get('/api/playground/results/999999').status_code == 404


def test_missing_scenario_is_incomplete_not_a_success(monkeypatch, tmp_path):
    import shutil
    import backend.app.services.playground as service
    for name in ['normal', 'unknown', 'dos_or_ddos']:
        shutil.copy(service.SCENARIOS_DIR / f'{name}.json', tmp_path)
    monkeypatch.setattr(service, 'SCENARIOS_DIR', tmp_path)
    with TestClient(app) as client:
        result = client.post('/api/playground/run', json={'profile_id':create_web(client)}).json()
        assert result['status'] == 'completed'
        assert result['coverage']['unavailable'] == ['web_attack']
        assert result['assessment']['status'] == 'incomplete'
        assert result['assessment']['score'] is None


def test_unavailable_predictor_returns_503_without_creating_run(monkeypatch):
    import backend.app.api.playground as api
    from backend.app.services.predictor import PredictorError
    def fail(): raise PredictorError('controlled unavailable model')
    monkeypatch.setattr(api, 'get_predictor', fail)
    with SessionLocal() as db:
        before = db.query(PlaygroundRun).count()
    with TestClient(app) as client:
        response = client.post('/api/playground/run', json={'profile_id':create_web(client)})
        assert response.status_code == 503
    with SessionLocal() as db:
        assert db.query(PlaygroundRun).count() == before
