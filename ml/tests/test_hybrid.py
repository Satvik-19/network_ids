"""Unit tests for the Phase-2 hybrid decision + risk engines (PRD §10, §11).

Pure-logic tests that do NOT require trained artifacts or a model. Run:
python -m pytest ml/tests/test_hybrid.py -q
"""
from __future__ import annotations

import pytest

from ml.hybrid.decision import (
    BENIGN,
    KNOWN_ATTACK,
    UNKNOWN_SUSPICIOUS,
    HybridThresholds,
    hybrid_decision,
)
from ml.hybrid.risk import (
    CRITICAL,
    HIGH,
    LOW,
    MEDIUM,
    RiskThresholds,
    risk_score,
)


# ---------------------------------------------------------------------- #
# Hybrid decision (PRD §10)
# ---------------------------------------------------------------------- #
TH = HybridThresholds(known_confidence_threshold=0.75, anomaly_threshold=-0.0928)


def test_high_confidence_known_attack():
    assert hybrid_decision(
        confidence=0.9, label="DoS Hulk", anomaly_score=-0.2, thresholds=TH
    ) == KNOWN_ATTACK


def test_high_confidence_benign_no_anomaly():
    assert hybrid_decision(
        confidence=0.9, label="BENIGN", anomaly_score=0.1, thresholds=TH
    ) == BENIGN


def test_high_confidence_benign_rescued_by_anomaly():
    # Phase-2 closure regression: a high-confidence BENIGN prediction must
    # NOT mask a suspicious anomaly signal -> UNKNOWN_SUSPICIOUS.
    assert hybrid_decision(
        confidence=0.99, label="BENIGN", anomaly_score=-0.5, thresholds=TH
    ) == UNKNOWN_SUSPICIOUS


def test_low_confidence_high_anomaly_unknown():
    assert hybrid_decision(
        confidence=0.5, label="BENIGN", anomaly_score=-0.5, thresholds=TH
    ) == UNKNOWN_SUSPICIOUS


def test_low_confidence_low_anomaly_benign():
    assert hybrid_decision(
        confidence=0.5, label="BENIGN", anomaly_score=0.1, thresholds=TH
    ) == BENIGN


def test_confidence_boundary_inclusive():
    # confidence exactly at threshold -> supervised path
    assert hybrid_decision(
        confidence=0.75, label="FTP-Patator", anomaly_score=-0.5, thresholds=TH
    ) == KNOWN_ATTACK


def test_anomaly_boundary_exclusive():
    # score exactly at threshold -> NOT anomalous (strict <)
    assert hybrid_decision(
        confidence=0.5, label="BENIGN", anomaly_score=-0.0928, thresholds=TH
    ) == BENIGN


def test_default_thresholds_are_config_driven():
    # defaults must match the calibrated values recorded in config.yaml
    assert HybridThresholds() == TH


# ---------------------------------------------------------------------- #
# Risk engine (PRD §11)
# ---------------------------------------------------------------------- #
RT = RiskThresholds(
    medium_threshold=40, high_threshold=65, critical_threshold=85,
    severity={
        "BENIGN": 5.0,
        "Denial of Service": 90.0,
        "Reconnaissance": 50.0,
    },
)


def test_risk_benign_low():
    r = risk_score(
        classification=BENIGN, family="BENIGN", confidence=0.99,
        anomaly_score=0.1, thresholds=RT,
    )
    assert r["level"] == LOW
    assert r["score"] < 40


def test_risk_benign_low_even_when_family_is_severe():
    # A BENIGN verdict must NOT inherit the supervised label's family severity.
    r = risk_score(
        classification=BENIGN, family="Web Attack", confidence=0.5,
        anomaly_score=0.1, thresholds=RT,
    )
    assert r["level"] == LOW
    assert r["score"] < 40


def test_risk_dos_critical():
    r = risk_score(
        classification=KNOWN_ATTACK, family="Denial of Service", confidence=0.99,
        anomaly_score=-0.2, anomaly_threshold=-0.09, thresholds=RT,
    )
    assert r["level"] == CRITICAL
    assert r["score"] >= 85


def test_risk_unknown_suspicious_medium_or_higher():
    r = risk_score(
        classification=UNKNOWN_SUSPICIOUS, family="BENIGN", confidence=0.4,
        anomaly_score=-0.5, anomaly_threshold=-0.09, thresholds=RT,
    )
    assert r["score"] >= RT.medium_threshold
    assert r["level"] in {MEDIUM, HIGH, CRITICAL}


def test_risk_score_monotonic_in_confidence():
    low = risk_score(
        classification=KNOWN_ATTACK, family="Reconnaissance", confidence=0.5,
        anomaly_score=0.0, thresholds=RT,
    )
    high = risk_score(
        classification=KNOWN_ATTACK, family="Reconnaissance", confidence=0.99,
        anomaly_score=0.0, thresholds=RT,
    )
    assert high["score"] > low["score"]


def test_risk_score_bounded():
    r = risk_score(
        classification=KNOWN_ATTACK, family="Denial of Service", confidence=1.0,
        anomaly_score=-0.9, anomaly_threshold=-0.09, thresholds=RT,
    )
    assert 0.0 <= r["score"] <= 100.0


def test_risk_rejects_unknown_classification():
    with pytest.raises(ValueError):
        risk_score(
            classification="NOT_A_CLASS", family="BENIGN", confidence=0.9,
            anomaly_score=0.0, thresholds=RT,
        )
