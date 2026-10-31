import importlib.util
import json
from pathlib import Path

import numpy as np

import pytest

from backend.app.services.scenarios import Scenario, ScenarioError
from ml.preprocessing.preprocess import CANONICAL_FEATURE_COLUMNS
from ml.preprocessing.dataset import REVISION


def document():
    return {'schema':'scenario/v1', 'name':'test', 'logical_interval_seconds':1,
            'flows':[{'seq':0, 'features':dict.fromkeys(CANONICAL_FEATURE_COLUMNS, 0.), 'service_port':80}]}


@pytest.mark.parametrize('bad', ['wrong_keys', 'nonfinite', 'text', 'negative_interval', 'bad_port'])
def test_invalid_runtime_fixture_is_rejected(bad):
    doc = document()
    features = doc['flows'][0]['features']
    if bad == 'wrong_keys': features['wrong'] = features.pop(CANONICAL_FEATURE_COLUMNS[0])
    elif bad == 'nonfinite': features[CANONICAL_FEATURE_COLUMNS[0]] = float('nan')
    elif bad == 'text': features[CANONICAL_FEATURE_COLUMNS[0]] = 'not numeric'
    elif bad == 'negative_interval': doc['logical_interval_seconds'] = -1
    else: doc['flows'][0]['service_port'] = 70000
    with pytest.raises(ScenarioError): Scenario(doc)


def test_provenance_available_without_becoming_model_features():
    doc = document(); doc['provenance'] = {'dataset':'pinned'}
    scenario = Scenario(doc)
    assert scenario.provenance == doc['provenance']
    assert set(scenario.flows[0]['features']) == set(CANONICAL_FEATURE_COLUMNS)


def test_new_scenario_sampling_does_not_depend_on_prediction():
    assert importlib.util.find_spec('ml.evaluation.prepare_scenarios') is not None, 'Provenance preparation missing'
    from ml.evaluation.prepare_scenarios import select_rows
    labels = ['SSH-Patator', 'FTP-Patator', 'SSH-Patator', 'FTP-Patator', 'SSH-Patator']
    fingerprints = ['train', 'a', 'b', 'a', 'c']
    selected = select_rows(labels, fingerprints, {'train'}, ['SSH-Patator','FTP-Patator'], limit=3)
    assert selected == [1,2,4]
    assert select_rows(labels, fingerprints, {'train'}, ['Bot']) == []


def test_registered_names_cannot_escape_scenarios_directory(tmp_path):
    from backend.app.services.replay import ReplayService
    outside = tmp_path / 'outside.json'
    outside.write_text(json.dumps(document()))
    directory = tmp_path / 'registered'; directory.mkdir()
    svc = ReplayService(predictor=None, scenarios_dir=directory)
    with pytest.raises(ScenarioError): svc.start('../outside')
    assert outside.exists()


def test_prepared_fixture_provenance_and_training_overlap_disclosure():
    from ml.evaluation.prepare_scenarios import fingerprints
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root/'data/processed/scenario_provenance.json').read_text())
    assert manifest['revision'] == REVISION
    for name, summary in manifest['scenarios'].items():
        doc = json.loads((root/f'data/scenarios/{name}.json').read_text())
        Scenario(doc)
        assert doc['provenance']['revision'] == REVISION
        assert doc['provenance']['split'] == 'test'
        assert len(doc['flows']) == summary['flows']
        for f in doc['flows']:
            values = np.array([[f['features'][c] for c in CANONICAL_FEATURE_COLUMNS]])
            assert fingerprints(values)[0] == f['provenance']['feature_sha256']
            assert f['provenance']['source_row_index'] >= 0
            if name in {'ssh_bruteforce','ftp_bruteforce','web_attack'}:
                assert not f['provenance']['matches_deployed_training_features']
    unknown = json.loads((root/'data/scenarios/unknown.json').read_text())
    assert unknown['purpose'] == 'benign_anomaly_challenge'
    assert {f['ground_truth_label'] for f in unknown['flows']} == {'BENIGN'}
