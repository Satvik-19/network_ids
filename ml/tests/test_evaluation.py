import importlib.util
import json
import warnings
from pathlib import Path

import numpy as np
import pytest


def evaluator():
    assert importlib.util.find_spec('ml.evaluation.evaluate_hybrid') is not None, 'Locked-system evaluator missing'
    from ml.evaluation import evaluate_hybrid
    return evaluate_hybrid


def test_same_population_counts_and_incremental_rescue():
    ev = evaluator()
    report = ev.evaluate_outputs(
        ['BENIGN','BENIGN','DDoS','Bot','PortScan','DDoS'],
        ['BENIGN','DDoS','BENIGN','Bot','PortScan','BENIGN'],
        np.array([.99,.9,.99,.5,.9,.9]), np.array([-.2,.2,-.2,-.2,.1,.1]),
        .75, -.0928,
    )
    assert report['methods']['hybrid']['confusion_matrix'] == [[0,2],[1,3]]
    assert report['methods']['xgboost']['confusion_matrix'] == [[1,1],[2,2]]
    assert report['methods']['supervised_gate']['confusion_matrix'] == [[1,1],[3,1]]
    assert report['methods']['isolation_forest']['confusion_matrix'] == [[1,1],[2,2]]
    assert report['incremental']['malicious_rescued'] == 2
    assert report['incremental']['additional_benign_alerts'] == 1
    assert report['per_class']['Bot']['hybrid_detected'] == 1
    assert report['per_class']['Bot']['supervised_correct_label'] == 1


def test_zero_denominators_are_explicit():
    with warnings.catch_warnings(record=True) as caught:
        report = evaluator().evaluate_outputs(['BENIGN'], ['BENIGN'], np.array([1.]), np.array([.1]), .75, -.0928)
    assert not caught, 'Single-class cohorts must retain the binary 2x2 matrix without warnings'
    assert report['methods']['hybrid']['confusion_matrix'] == [[1,0],[0,0]]
    assert report['methods']['hybrid']['fpr'] == 0
    assert report['incremental']['rescue_rate'] is None


def test_mismatched_populations_rejected():
    with pytest.raises(ValueError, match='length'):
        evaluator().evaluate_outputs(['BENIGN'], [], np.array([1.]), np.array([.1]), .75, -.0928)


def test_batch_scoring_matches_real_predictor_on_fixtures():
    from backend.app.services.predictor import Phase2Predictor
    ev = evaluator()
    predictor = Phase2Predictor()
    flows = [f for p in (Path(__file__).resolve().parents[2]/'data/scenarios').glob('*.json')
             for f in json.loads(p.read_text())['flows']]
    matrix = np.array([[f['features'][c] for c in predictor.feature_order] for f in flows])
    labels, confidence, scores = ev.score_rows(predictor, matrix)
    report = ev.evaluate_outputs([f['ground_truth_label'] for f in flows], labels, confidence, scores,
                                predictor.known_confidence_threshold, predictor.anomaly_threshold)
    for i,f in enumerate(flows):
        out = predictor.predict(f['features'], with_shap=False)
        assert labels[i] == out['label']
        assert confidence[i] == pytest.approx(out['confidence'])
        assert scores[i] == pytest.approx(out['anomaly_score'], abs=1e-6)
    assert report['methods']['hybrid']['true_positive'] == 16
    assert report['methods']['hybrid']['false_positive'] == 4
