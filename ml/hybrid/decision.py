"""Hybrid decision layer (PRD §10).

Combines the supervised classifier and the anomaly detector through a
lightweight deterministic decision layer:

```text
IF supervised predicts a known MALICIOUS class
   AND confidence >= known_confidence_threshold:
       KNOWN_ATTACK
ELSE IF anomaly_score < anomaly_threshold:
       UNKNOWN_SUSPICIOUS
ELSE:
       BENIGN (low-confidence normal)
```

The anomaly rescue is intentionally NOT gated on the supervised confidence:
a high-confidence BENIGN prediction must never mask a suspicious anomaly
signal, so such a flow is surfaced as UNKNOWN_SUSPICIOUS. KNOWN_ATTACK is
only emitted when the supervised label is itself a malicious class
(Phase-2 closure audit, PRD §10).

All thresholds are configuration-driven (config/config.yaml, PRD §57) and
calibrated during Phase-2 evaluation. The layer is deterministic — no ML
model involved — and is unit-testable without any artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass

# Possible hybrid outcomes (PRD §10).
BENIGN = "BENIGN"
KNOWN_ATTACK = "KNOWN_ATTACK"
UNKNOWN_SUSPICIOUS = "UNKNOWN_SUSPICIOUS"


@dataclass(frozen=True)
class HybridThresholds:
    """Configuration-driven thresholds for the hybrid layer."""

    known_confidence_threshold: float = 0.75
    anomaly_threshold: float = -0.0928  # calibrated random_3way/validation


def hybrid_decision(
    *,
    confidence: float,
    label: str,
    anomaly_score: float,
    thresholds: HybridThresholds | None = None,
) -> str:
    """Return the deterministic hybrid outcome for one flow.

    Args:
        confidence: top-1 supervised classifier probability in [0, 1].
        label: the supervised predicted canonical label.
        anomaly_score: IsolationForest raw decision_function (lower = more
            abnormal, NOT a probability).
        thresholds: config-driven thresholds (default = Phase-2 calibrated).

    Returns:
        One of BENIGN / KNOWN_ATTACK / UNKNOWN_SUSPICIOUS.
    """
    if thresholds is None:
        thresholds = HybridThresholds()

    if confidence >= thresholds.known_confidence_threshold and label != "BENIGN":
        return KNOWN_ATTACK

    if anomaly_score < thresholds.anomaly_threshold:
        return UNKNOWN_SUSPICIOUS

    return BENIGN
