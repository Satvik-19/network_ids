"""Risk engine (PRD §11).

Risk is calculated TRANSPARENTLY — no extra ML model — from:
  - attack family severity (config-driven base severity per family),
  - supervised confidence,
  - anomaly score,
  - (incident volume/intensity is a Phase-3 refinement, PRD §11 optional term).

Formula (deterministic, transparent, PRD §57):

    confidence_factor = 0.5 + 0.5 * confidence        # 0.5 .. 1.0
    anomaly_signal    = 0..1 from raw anomaly score    # PRD §11 anomaly term
    anomaly_bonus     = 15 * anomaly_signal            # 0 .. +15 points

    risk_score = clamp( severity[family] * confidence_factor
                        + (anomaly_bonus if KNOWN_ATTACK/UNKNOWN else 0),
                        0, 100 )

    risk_level = CRITICAL if score >= critical_threshold
               = HIGH      if score >= high_threshold
               = MEDIUM    if score >= medium_threshold
               = LOW       otherwise

Semantics (matches PRD §11 example: confident DDoS -> CRITICAL):
  - confidence 1.0 -> factor 1.0, so a confident attack on a high-severity
    family (e.g. Denial of Service = 90) reaches CRITICAL.
  - confidence 0.5 (unconfident) halves the family severity.
  - a strong anomaly signal adds up to +15 points on top.
  - BENIGN keeps its (tiny) base severity -> always LOW.
  - UNKNOWN_SUSPICIOUS uses a neutral severity of 60 boosted by the anomaly
    signal -> MEDIUM floor, can reach HIGH for strong anomalies.

The formula is a project-level prioritisation indicator (PRD §11), not an
industry-standard risk score.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ml.hybrid.decision import BENIGN, KNOWN_ATTACK, UNKNOWN_SUSPICIOUS

LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"
CRITICAL = "CRITICAL"

# severity = risk_score at confidence 1.0 (upper bound of the family).
_DEFAULT_SEVERITY: Dict[str, float] = {
    "BENIGN": 5.0,
    "Botnet": 60.0,
    "Denial of Service": 90.0,
    "Brute Force": 70.0,
    "Reconnaissance": 50.0,
    "Web Attack": 80.0,
    "Heartbleed": 95.0,
    "Infiltration": 85.0,
}

_UNKNOWN_SEVERITY = 60.0  # neutral severity for unknown/suspicious flows


@dataclass(frozen=True)
class RiskThresholds:
    """Config-driven risk thresholds (PRD §57)."""

    medium_threshold: float = 40.0
    high_threshold: float = 65.0
    critical_threshold: float = 85.0
    severity: Dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.severity is None:
            object.__setattr__(self, "severity", dict(_DEFAULT_SEVERITY))


def _anomaly_signal(anomaly_score: float, anomaly_threshold: float) -> float:
    """Map a raw anomaly score to a 0..1 signal.

    The raw decision_function is centred near 0 (positive = normal). We map
    ``score < anomaly_threshold`` (anomalous) to a positive signal that grows
    as the score drops further below the threshold. A score of exactly the
    threshold yields 0.5; BENIGN-level scores (>= 0) yield ~0.
    """
    if anomaly_score >= 0.0:
        return 0.0
    distance = anomaly_threshold - anomaly_score  # >= 0 when anomalous
    if distance <= 0.0:
        return 0.0
    span = max(0.1, -anomaly_threshold)  # avoid div-by-zero; span >= 0.1
    return min(1.0, distance / span)


def risk_score(
    *,
    classification: str,
    family: str,
    confidence: float,
    anomaly_score: float,
    anomaly_threshold: float = -0.0928,
    thresholds: RiskThresholds | None = None,
) -> dict:
    """Return ``{"score": float, "level": str}`` for one flow (PRD §11).

    Args:
        classification: hybrid outcome (BENIGN / KNOWN_ATTACK /
            UNKNOWN_SUSPICIOUS).
        family: canonical display family (from ml.preprocessing.labels).
        confidence: supervised top-1 probability in [0, 1].
        anomaly_score: IsolationForest raw decision_function.
        anomaly_threshold: calibrated config threshold.
        thresholds: config-driven risk thresholds.
    """
    if thresholds is None:
        thresholds = RiskThresholds()

    if classification == UNKNOWN_SUSPICIOUS:
        severity = _UNKNOWN_SEVERITY
    elif classification == BENIGN:
        # A BENIGN verdict must floor at LOW regardless of the supervised
        # label's family (e.g. a low-confidence fallback prediction).
        severity = float(thresholds.severity.get("BENIGN", 5.0))
    else:
        severity = float(thresholds.severity.get(family, 50.0))

    if classification == BENIGN:
        score = severity * 0.5  # benign base stays LOW
    elif classification in (KNOWN_ATTACK, UNKNOWN_SUSPICIOUS):
        confidence_factor = 0.5 + 0.5 * max(0.0, min(1.0, confidence))
        signal = _anomaly_signal(anomaly_score, anomaly_threshold)
        score = severity * confidence_factor + 15.0 * signal
    else:
        raise ValueError(f"Unknown classification {classification!r}")

    score = max(0.0, min(100.0, score))
    if score >= thresholds.critical_threshold:
        level = CRITICAL
    elif score >= thresholds.high_threshold:
        level = HIGH
    elif score >= thresholds.medium_threshold:
        level = MEDIUM
    else:
        level = LOW
    return {"score": round(score, 2), "level": level}
