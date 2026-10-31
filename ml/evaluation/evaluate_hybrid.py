"""Compare frozen detectors on identical records; never fit or tune anything.

Run: python -m ml.evaluation.evaluate_hybrid
Historical test reuse still applies; see docs/EVALUATION_PROTOCOL.md.
"""
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np

from ml.evaluation.metrics import evaluate_binary, evaluate_multiclass
from ml.hybrid.decision import HybridThresholds, hybrid_decision
from ml.preprocessing.dataset import LoadConfig, REVISION, REPO_ID, load_split
from ml.preprocessing.labels import CANONICAL_LABELS, INT_TO_LABEL, encode_label
from ml.preprocessing.preprocess import preprocess_frame

ROOT = Path(__file__).resolve().parents[2]


def score_rows(predictor, matrix):
    probabilities = predictor.supervised.predict_proba(matrix)
    indices = np.argmax(probabilities, axis=1)
    labels = np.array([INT_TO_LABEL[int(predictor.supervised.classes_[i])] for i in indices])
    confidence = probabilities[np.arange(len(indices)), indices]
    scores = predictor.isolation_forest.decision_function(matrix)
    return labels, confidence, scores


def _binary(truth, alerts):
    tn = int(np.sum(~truth & ~alerts))
    fp = int(np.sum(~truth & alerts))
    fn = int(np.sum(truth & ~alerts))
    tp = int(np.sum(truth & alerts))
    return {
        **evaluate_binary(truth.astype(int), alerts.astype(int)),
        "true_positive": tp, "false_positive": fp,
        "true_negative": tn, "false_negative": fn,
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "fpr": fp / (tn + fp) if tn + fp else None,
    }


def evaluate_outputs(truth_labels, predicted_labels, confidence, anomaly_scores,
                     confidence_threshold, anomaly_threshold):
    n = len(truth_labels)
    if not n or any(len(a) != n for a in (predicted_labels, confidence, anomaly_scores)):
        raise ValueError("evaluation arrays must have equal nonzero length")
    truth_labels, predicted_labels = np.asarray(truth_labels), np.asarray(predicted_labels)
    confidence, anomaly_scores = np.asarray(confidence), np.asarray(anomaly_scores)
    if any(a.ndim != 1 for a in (truth_labels, predicted_labels, confidence, anomaly_scores)):
        raise ValueError("evaluation arrays must be one-dimensional")
    if not np.isfinite(confidence).all() or not np.isfinite(anomaly_scores).all():
        raise ValueError("evaluation scores must be finite")
    thresholds = HybridThresholds(confidence_threshold, anomaly_threshold)
    outcomes = np.array([
        hybrid_decision(label=str(label), confidence=float(conf), anomaly_score=float(score), thresholds=thresholds)
        for label, conf, score in zip(predicted_labels, confidence, anomaly_scores)
    ])
    truth = truth_labels != "BENIGN"
    known = (predicted_labels != "BENIGN") & (confidence >= confidence_threshold)
    alerts = {
        "xgboost": predicted_labels != "BENIGN",
        "supervised_gate": known,
        "isolation_forest": anomaly_scores < anomaly_threshold,
        "hybrid": outcomes != "BENIGN",
    }
    rescued = ~known & alerts["hybrid"]
    candidates = int(np.sum(truth & ~known))
    malicious_rescued = int(np.sum(truth & rescued))
    return {
        "n": n,
        "methods": {name: _binary(truth, a) for name, a in alerts.items()},
        "multiclass_xgboost": evaluate_multiclass(
            np.array([encode_label(str(l)) for l in truth_labels]),
            np.array([encode_label(str(l)) for l in predicted_labels]), CANONICAL_LABELS,
        ),
        "incremental": {
            "malicious_not_already_known": candidates,
            "malicious_rescued": malicious_rescued,
            "rescue_rate": malicious_rescued / candidates if candidates else None,
            "additional_benign_alerts": int(np.sum(~truth & rescued)),
        },
        "per_class": {
            str(label): {
                "support": int(np.sum(truth_labels == label)),
                **{f"{name}_detected": int(np.sum((truth_labels == label) & a)) for name, a in alerts.items()},
                "supervised_correct_label": int(np.sum((truth_labels == label) & (predicted_labels == label))),
                "confident_correct_label": int(np.sum((truth_labels == label) & (predicted_labels == label) & known)),
            } for label in sorted(set(truth_labels))
        },
    }


def main():
    from backend.app.services.predictor import Phase2Predictor

    paths = [ROOT/'ml/artifacts/supervised_model.joblib', ROOT/'ml/artifacts/isolation_forest.joblib', ROOT/'config/config.yaml']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    predictor = Phase2Predictor()
    raw = preprocess_frame(load_split(LoadConfig(config="random_3way", split="test")), scale=False)
    labels, confidence, scores = score_rows(predictor, raw.X)
    report = evaluate_outputs(raw.labels, labels, confidence, scores,
                              predictor.known_confidence_threshold, predictor.anomaly_threshold)
    cohort = hashlib.sha256(raw.X.astype('<f8').tobytes())
    cohort.update(json.dumps(raw.labels).encode('utf-8'))
    report["provenance"] = {
        "dataset": REPO_ID, "revision": REVISION, "config": "random_3way", "split": "test",
        "sampling": "entire published partition; no resampling", "rows": len(raw.X),
        "ordered_cohort_sha256": cohort.hexdigest(), "feature_order": raw.columns,
        "artifact_config_sha256": hashes,
        "supervised_parameters": predictor.meta["params"],
        "isolation_forest_parameters": predictor.isolation_forest.get_params(),
        "random_seed": predictor.meta["params"]["random_state"],
        "known_confidence_threshold": predictor.known_confidence_threshold,
        "anomaly_threshold": predictor.anomaly_threshold,
        "versions": {p: version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'xgboost']},
        "qualification": "Previously used evaluation cohort; not an untouched post-selection benchmark. No fitting or tuning.",
        "definitions": "BENIGN truth alerts are false positives; non-BENIGN truth alerts are detections, not necessarily correct attack names. roc_auc null for hard verdicts.",
    }
    assert hashes == {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    out = ROOT/'ml/evaluation/results/locked_hybrid_random.json'
    data = json.dumps(report, indent=2).encode('utf-8')
    tmp = out.with_suffix('.json.tmp')
    tmp.write_bytes(data)
    tmp.replace(out)
    assert json.loads(out.read_text(encoding='utf-8')) == report
    for name, metrics in report['methods'].items():
        print(name, {k: metrics[k] for k in ['precision', 'recall', 'f1', 'fpr']})
    print('incremental', report['incremental'])
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
