"""Deterministic scenario selection for the approved academic Playground."""
from pathlib import Path

from backend.app.schemas.playground import ProfileRequest
from backend.app.services.scenarios import SCENARIOS_DIR, load_scenario

NOTICE = 'Prepared scenario evaluation only. This does not inspect or certify your real network.'


def select_suite(profile: ProfileRequest, directory: Path = SCENARIOS_DIR) -> dict:
    requested = [
        ('normal', 'Benign control; measure false alerts'),
        ('unknown', 'Benign anomaly challenge; false-alert accounting, not unknown-attack detection'),
    ]
    if 'ssh' in profile.services:
        requested.append(('ssh_bruteforce', 'SSH service enabled'))
    if 'ftp' in profile.services:
        requested.append(('ftp_bruteforce', 'FTP service enabled'))
    if 'web' in profile.services and profile.exposure != 'internal':
        requested.append(('web_attack', 'Public web service enabled'))
    if profile.exposure != 'internal' or profile.scale == '50+':
        requested.append(('dos_or_ddos', 'Public services or larger network'))
    if profile.environment in {'lab','small_organisation'} or profile.scale != '1-10':
        requested.append(('portscan', 'Multi-device environment'))
    suite = []
    for name, reason in requested:
        path = directory / f'{name}.json'
        scenario = load_scenario(path) if path.is_file() else None
        suite.append(dict(name=name, reason=reason, available=scenario is not None,
                          flow_count=scenario.total if scenario else 0,
                          purpose=scenario.purpose if scenario else 'unavailable'))
    return {
        'suite':suite,
        'unsupported_services':[s for s in profile.services if s in {'database','file_sharing'}],
        'unknown_attack_detection':'not established',
        'notice':NOTICE,
    }
