import importlib.util

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app


def modules():
    assert importlib.util.find_spec('backend.app.schemas.playground') is not None, 'Playground profile schemas missing'
    from backend.app.schemas.playground import ProfileRequest
    from backend.app.services.playground import select_suite
    return ProfileRequest, select_suite


def test_profiles_select_different_deterministic_suites():
    Profile, select = modules()
    lab = Profile(environment='lab', scale='10-50', exposure='some_public', services=['ssh'])
    web = Profile(environment='web_server', scale='1-10', exposure='public', services=['web','ssh'])
    lab_names = [s['name'] for s in select(lab)['suite']]
    web_names = [s['name'] for s in select(web)['suite']]
    assert lab_names == ['normal','unknown','ssh_bruteforce','dos_or_ddos','portscan']
    assert web_names == ['normal','unknown','ssh_bruteforce','web_attack','dos_or_ddos']
    assert select(lab) == select(lab)


def test_missing_scenarios_and_unsupported_services_remain_visible(tmp_path):
    Profile, select = modules()
    profile = Profile(environment='home', services=['database','file_sharing'])
    plan = select(profile, tmp_path)
    assert len(plan['suite']) == 2 and all(not s['available'] for s in plan['suite'])
    assert plan['unsupported_services'] == ['database','file_sharing']
    assert plan['unknown_attack_detection'] == 'not established'


def test_profile_validation_rejects_targets_and_normalizes_services():
    Profile, _ = modules()
    assert Profile(environment='lab', services=['ssh','ftp','ssh']).services == ['ftp','ssh']
    with pytest.raises(ValidationError): Profile(environment='lab', target_ip='1.2.3.4')
    with pytest.raises(ValidationError): Profile(environment='invalid')


def test_profile_endpoint_persists_canonical_profile_and_preview():
    with TestClient(app) as client:
        response = client.post('/api/playground/profile', json={'environment':'web_server','exposure':'public','services':['web']})
    assert response.status_code == 200
    body = response.json()
    from backend.app.db.database import SessionLocal
    from backend.app.db.models import PlaygroundProfile
    with SessionLocal() as db:
        row = db.get(PlaygroundProfile, body['id'])
        assert row.config == body['profile']
    assert {'web_attack','dos_or_ddos'} <= {s['name'] for s in body['suite']}
