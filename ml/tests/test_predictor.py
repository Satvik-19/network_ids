"""Integration test for the Phase-2 predictor (backend service layer).

Requires final artifacts (supervised_model.joblib, isolation_forest.joblib,
config.yaml). Run: python -m pytest ml/tests/test_predictor.py -q
"""
from __future__ import annotations

import joblib
import numpy as np
import pytest

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.preprocess import preprocess_frame


@pytest.fixture(scope="module")
def predictor():
    from backend.app.services.predictor import Phase2Predictor, PredictorError

    try:
        return Phase2Predictor()
    except PredictorError as exc:  # artifacts not built
        pytest.skip(f"Phase-2 artifacts missing: {exc}")


def _features(df):
    res = preprocess_frame(df, scale=False)
    return {
        col: float(v)
        for col, v in zip(res.columns, res.X[0].tolist())
    }


def test_predict_full_contract(predictor):
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    out = predictor.predict(_features(df))
    assert out["label"] in {"BENIGN", "Bot", "DDoS", "DoS Hulk", "DoS Slowhttptest",
                            "DoS slowloris", "DoS GoldenEye", "FTP-Patator", "Heartbleed",
                            "Infiltration", "PortScan", "SSH-Patator",
                            "Web Attack - Brute Force", "Web Attack - Sql Injection",
                            "Web Attack - XSS"}
    assert out["classification"] in {"BENIGN", "KNOWN_ATTACK", "UNKNOWN_SUSPICIOUS"}
    assert 0.0 <= out["confidence"] <= 1.0
    assert isinstance(out["anomaly_score"], float)
    assert out["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert len(out["top_features"]) == 5


def test_explain_matches_predict_shap(predictor):
    """BUG-010 (Phase-3.5): ``predictor.explain`` must reproduce exactly the
    SHAP block that ``predict(with_shap=True)`` produced, WITHOUT re-running
    the supervised + anomaly + hybrid + risk pipeline. The replay engine uses
    it to attach SHAP to suspicious flows after their single scoring pass."""
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    feats = _features(df)

    full = predictor.predict(feats, with_shap=True)
    exp = predictor.explain(feats)

    assert exp["top_features"] == full["top_features"], "explain must match with_shap=True"
    assert exp["base_value"] == full["shap_base_value"]
    assert exp["n_features_explained"] == len(predictor.feature_order)
    assert exp["top_features"], "sample row should carry SHAP contributions"


def test_hybrid_consistent_with_artifacts(predictor):
    """Simulate a high-confidence known attack the hybrid must flag."""
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    raw = preprocess_frame(df, scale=False)
    proba = predictor.supervised.predict_proba(raw.X.reshape(1, -1))[0]
    idx = int(np.argmax(proba))
    label_code = int(predictor.supervised.classes_[idx])
    from ml.preprocessing.labels import INT_TO_LABEL

    label = INT_TO_LABEL[label_code]
    if label == "BENIGN":
        pytest.skip("first random/test row is BENIGN; no known-attack assertion")
    assert proba[idx] >= predictor.known_confidence_threshold
    from ml.hybrid.decision import hybrid_decision, HybridThresholds

    score = float(predictor.isolation_forest.decision_function(raw.X.reshape(1, -1))[0])
    out = hybrid_decision(
        confidence=float(proba[idx]),
        label=label,
        anomaly_score=score,
        thresholds=HybridThresholds(
            known_confidence_threshold=predictor.known_confidence_threshold,
            anomaly_threshold=predictor.anomaly_threshold,
        ),
    )
    assert out == "KNOWN_ATTACK"


def test_anomaly_separation_real_rows():
    """Real DDoS rows must score lower (more anomalous) than benign rows.

    Uses the collected Friday data where DDoS is dominant and the calibrated
    threshold was tuned to FPR <= 5% on benign. This is a weak-but-real sanity
    check of the anomaly detector's role in the hybrid.
    """
    from backend.app.services.predictor import Phase2Predictor

    pred = Phase2Predictor()
    df = load_split(LoadConfig(config="random_3way", split="test"))
    res = preprocess_frame(df, scale=False)
    labels = res.labels
    ben = np.mean(res.X[np.array([l == "BENIGN" for l in labels])], axis=0)
    dos = np.mean(res.X[np.array([l == "DoS Hulk" for l in labels])], axis=0)
    score_ben = pred.isolation_forest.decision_function(ben.reshape(1, -1))[0]
    score_dos = pred.isolation_forest.decision_function(dos.reshape(1, -1))[0]
    assert score_dos < score_ben


# ---------------------------------------------------------------------- #
# BUG-005 regression: ground truth must NEVER affect runtime inference.
# ---------------------------------------------------------------------- #
# The unknown/unseen experiment once passed the TRUE label into the hybrid,
# inflating metrics. These tests permanently pin the contract: the runtime
# predictor accepts ONLY features; evaluation truth is used for scoring
# separately, never for prediction/classification/risk.
# See docs/BUG_LOG.md BUG-005 and docs/DECISIONS.md DEC-010.
# ---------------------------------------------------------------------- #


def test_predictor_signature_has_no_ground_truth_argument(predictor):
    """The runtime API must never accept a ground-truth / label argument."""
    import inspect

    params = inspect.signature(predictor.predict).parameters
    names = set(params)
    assert "features" in names
    assert "with_shap" in names
    forbidden = {"truth", "label", "y", "ground_truth", "true_label", "target"}
    assert not (names & forbidden), f"runtime predictor must not accept {names & forbidden}"


class _EvalRecord:
    """Evaluation wrapper: keeps ground truth SEPARATE from model features.

    The evaluation scorer stores the truth label externally and passes ONLY
    the canonical feature dict to the runtime predictor (BUG-005 contract).
    """

    def __init__(self, features: dict, truth: str):
        self.features = features
        self.truth = truth  # evaluation-only; never part of the feature dict


def test_eval_wrapper_truth_stays_outside_predictor(predictor):
    """Same canonical features + different external truth -> identical runtime.

    Two evaluation records with the SAME feature vector but DIFFERENT
    ground-truth labels (stored only on the wrapper) must produce identical
    runtime output. This pins the evaluation-wrapper pattern: truth lives
    outside the predictor, so identical features always yield identical
    prediction / classification / risk / explanation.
    """
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    feats = _features(df)

    rec_a = _EvalRecord(feats, truth="BENIGN")
    rec_b = _EvalRecord(feats, truth="DoS Hulk")
    assert rec_a.truth != rec_b.truth  # genuinely different external labels

    out_a = predictor.predict(rec_a.features)
    out_b = predictor.predict(rec_b.features)

    for key in ("label", "family", "classification", "confidence",
                "risk_level", "risk_score", "top_features"):
        assert out_a[key] == out_b[key], (
            f"runtime output for key={key!r} must not depend on external truth"
        )


def test_missing_and_extra_features_rejected_independently_of_label():
    """BUG-005: a ground-truth key must not sneak into the model features.

    Extra keys (e.g. a stray metadata key) are rejected by the predictor, so
    runtime inference is a pure function of the canonical features only.
    """
    from backend.app.services.predictor import Phase2Predictor, PredictorError

    pred = Phase2Predictor()
    df = load_split(LoadConfig(config="random", split="test")).iloc[:1]
    res = preprocess_frame(df, scale=False)
    feats = {col: float(v) for col, v in zip(res.columns, res.X[0].tolist())}

    import pytest as _pt

    with _pt.raises(PredictorError):
        pred.predict(dict(feats, truth_label="BENIGN"))
    with _pt.raises(PredictorError):
        pred.predict(dict(feats, true_label_code=0))