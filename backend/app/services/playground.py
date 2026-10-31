"""Deterministic scenario selection for the approved academic Playground."""
from pathlib import Path
import hashlib
import json
import logging
import math

from backend.app.schemas.playground import ProfileRequest
from backend.app.services.scenarios import SCENARIOS_DIR, load_scenario
from backend.app.db.models import PlaygroundRun, PlaygroundResult
from ml.preprocessing.labels import CANONICAL_LABELS

NOTICE = 'Prepared scenario evaluation only. This does not inspect or certify your real network.'
logger = logging.getLogger(__name__)


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


def assess_results(results, unavailable, weights):
    detection = float(weights['detection_weight'])
    false_alert = float(weights['false_alert_weight'])
    if (not all(math.isfinite(w) and w >= 0 for w in (detection, false_alert))
            or not math.isclose(detection + false_alert, 1.0)):
        raise ValueError('Readiness weights must be nonnegative and sum to one')
    keys = ['malicious','detected','missed','benign','false_alerts','correct_benign']
    totals = {k:sum(s['counts'][k] for s in results) for k in keys}
    recalls, quality = [], {}
    for scenario in results:
        counts = scenario['counts']
        values = []
        if counts['malicious']:
            recalls.append(counts['detected'] / counts['malicious'])
            values.append(recalls[-1])
        if counts['benign']:
            values.append(counts['correct_benign'] / counts['benign'])
        if values:
            quality[scenario['name']] = sum(values) / len(values)
    mean_recall = sum(recalls) / len(recalls) if recalls else None
    specificity = totals['correct_benign'] / totals['benign'] if totals['benign'] else None
    status = 'incomplete' if unavailable else 'complete' if recalls and specificity is not None else 'not_applicable'
    score = round(100*(detection*mean_recall + false_alert*specificity),2) if status == 'complete' else None
    return {
        **totals, 'status':status, 'score':score,
        'mean_scenario_recall':mean_recall, 'benign_specificity':specificity,
        'blind_spots':[name for name,q in quality.items() if q == min(quality.values()) and q < 1],
        'strongest':[name for name,q in quality.items() if q == max(quality.values()) and q > 0],
        'weights':dict(weights),
    }


def run_profile(db, profile_row, predictor):
    profile = ProfileRequest(**profile_row.config)
    plan = select_suite(profile, SCENARIOS_DIR)
    scenarios = [load_scenario(SCENARIOS_DIR/f"{s['name']}.json") for s in plan['suite'] if s['available']]
    if sum(s.total for s in scenarios) > 64:
        raise ValueError('Suite exceeds the small 64-flow Playground execution bound')
    weights = dict(predictor.config['playground'])
    context = {
        'profile':profile.model_dump(), 'suite':plan['suite'],
        'thresholds':{'known_confidence':predictor.known_confidence_threshold, 'anomaly':predictor.anomaly_threshold},
        'risk':predictor.config['risk'], 'readiness_weights':weights,
        'model_name':predictor.model_name, 'model_version':predictor.model_version,
        'artifact_sha256':{name:hashlib.sha256((predictor.artifacts/name).read_bytes()).hexdigest()
                           for name in ['supervised_model.joblib','isolation_forest.joblib']},
        'model_metadata':{name:json.loads((predictor.artifacts/name).read_text(encoding='utf-8'))
                          for name in ['supervised_model_metadata.json','isolation_forest_metadata.json']},
    }
    run = PlaygroundRun(profile_id=profile_row.id, status='running', config=context)
    db.add(run); db.commit(); db.refresh(run)
    run_id = run.id
    results = []
    missing = [s['name'] for s in plan['suite'] if not s['available']]
    payload = {
        'run_id':run_id, 'status':'running', 'assessment':None, 'scenarios':results,
        'coverage':{'selected':len(plan['suite']), 'executed':0, 'unavailable':missing,
                    'unsupported_services':plan['unsupported_services'], 'unknown_attack_detection':'not established'},
        'profile':profile.model_dump(), 'context':context, 'notice':NOTICE, 'error':None,
    }
    try:
        for scenario in scenarios:
            flows = []
            counts = dict(malicious=0,detected=0,missed=0,benign=0,false_alerts=0,correct_benign=0)
            for flow in scenario.flows:
                truth = flow.get('ground_truth_label')
                if truth not in CANONICAL_LABELS:
                    raise ValueError('Scenario lacks a canonical evaluation truth label')
                out = predictor.predict(flow['features'], with_shap=False)
                if out['classification'] != 'BENIGN':
                    out['top_features'] = predictor.explain(flow['features'])['top_features']
                alert = out['classification'] != 'BENIGN'
                if truth == 'BENIGN':
                    counts['benign'] += 1
                    counts['false_alerts' if alert else 'correct_benign'] += 1
                else:
                    counts['malicious'] += 1
                    counts['detected' if alert else 'missed'] += 1
                flows.append({'seq':flow['seq'], 'truth_label':truth, 'features':flow['features'],
                              'provenance':flow.get('provenance', {}),
                              'output':{k:out[k] for k in ['classification','label','family','confidence','anomaly_score',
                                                         'anomaly_threshold','risk_score','risk_level','top_features']}})
            results.append({'name':scenario.name, 'purpose':scenario.purpose, 'counts':counts, 'flows':flows,
                            'provenance':scenario.provenance,
                            'training_feature_matches':sum(f.get('provenance',{}).get('matches_deployed_training_features',False) for f in scenario.flows)})
        payload['coverage']['executed'] = len(results)
        payload['assessment'] = assess_results(results, missing, weights)
        payload['status'] = run.status = 'completed'
        db.add(PlaygroundResult(run_id=run_id, data=payload))
        db.commit()
    except Exception:
        logger.exception('Playground run %s failed', run_id)
        db.rollback()
        payload['status'] = run.status = 'failed'
        payload['assessment'] = None
        payload['coverage']['executed'] = len(results)
        payload['error'] = 'Scenario evaluation failed. Check the backend log and start a new run.'
        db.add(PlaygroundResult(run_id=run_id, data=payload))
        db.commit()
    return payload


def interrupt_runs(db):
    """A process restart cannot resume a bounded request that was interrupted."""
    for run in db.query(PlaygroundRun).filter_by(status='running').all():
        run.status = 'failed'
        db.add(PlaygroundResult(run_id=run.id, data={
            'run_id':run.id, 'status':'failed', 'assessment':None,
            'error':'Evaluation interrupted by backend restart. Start a new run.',
            'profile':(run.config or {}).get('profile',{}), 'context':run.config or {},
            'coverage':{}, 'scenarios':[], 'notice':NOTICE,
        }))
    db.commit()
