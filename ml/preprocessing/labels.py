"""labels.py — Canonical label normalisation, family mapping, and encodings.

Source of truth for the Phase-1 label contract. Derived from the ACTUAL
observed label strings in the cleaned HF derivative (verified 2026-08-09),
NOT from the illustrative PRD §8 hierarchy.

Observed raw labels contain a U+FFFD replacement character where the
publisher's web-attack labels should carry a dash, e.g.
``Web Attack \ufffd Brute Force``. We normalise those to an ASCII
hyphen + space form so the canonical strings are deterministic, ASCII-safe,
and stable across the JSON contract files.

Canonical labels are used:
- as the multiclass target (encoded to int via LABEL_TO_INT),
- for family mapping (display / aggregation),
- in the persisted ``label_mapping.json`` contract.
"""
from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# Observed raw label -> canonical label (deterministic normalisation).
# U+FFFD is the actual byte in the parquet data (verified), not an em/en-dash.
# ---------------------------------------------------------------------------
_RAW_TO_CANONICAL: Dict[str, str] = {
    "BENIGN": "BENIGN",
    "Bot": "Bot",
    "DDoS": "DDoS",
    "DoS GoldenEye": "DoS GoldenEye",
    "DoS Hulk": "DoS Hulk",
    "DoS Slowhttptest": "DoS Slowhttptest",
    "DoS slowloris": "DoS slowloris",
    "FTP-Patator": "FTP-Patator",
    "Heartbleed": "Heartbleed",
    "Infiltration": "Infiltration",
    "PortScan": "PortScan",
    "SSH-Patator": "SSH-Patator",
    "Web Attack \ufffd Brute Force": "Web Attack - Brute Force",
    "Web Attack \ufffd Sql Injection": "Web Attack - Sql Injection",
    "Web Attack \ufffd XSS": "Web Attack - XSS",
}

# Canonical label -> display family (used by API, dashboards, aggregation).
# Heartbleed / Infiltration are their own rare categories (no merged family).
FAMILY_MAP: Dict[str, str] = {
    "BENIGN": "BENIGN",
    "Bot": "Botnet",
    "DDoS": "Denial of Service",
    "DoS GoldenEye": "Denial of Service",
    "DoS Hulk": "Denial of Service",
    "DoS Slowhttptest": "Denial of Service",
    "DoS slowloris": "Denial of Service",
    "FTP-Patator": "Brute Force",
    "Heartbleed": "Heartbleed",
    "Infiltration": "Infiltration",
    "PortScan": "Reconnaissance",
    "SSH-Patator": "Brute Force",
    "Web Attack - Brute Force": "Web Attack",
    "Web Attack - Sql Injection": "Web Attack",
    "Web Attack - XSS": "Web Attack",
}

# Canonical label -> integer encoding (deterministic, alphabetical).
# The exact mapping is persisted in ml/artifacts/label_mapping.json.
LABEL_TO_INT: Dict[str, int] = {
    name: i for i, name in enumerate(sorted(FAMILY_MAP))
}
INT_TO_LABEL: Dict[int, str] = {
    v: k for k, v in LABEL_TO_INT.items()
}

# Canonical labels (ordered by integer encoding, matches label_mapping.json).
CANONICAL_LABELS: List[str] = [INT_TO_LABEL[i] for i in sorted(INT_TO_LABEL)]

BINARY_POSITIVE_LABEL = "MALICIOUS"
BINARY_NEGATIVE_LABEL = "BENIGN"


def normalize_label(raw: str) -> str:
    """Map an observed raw label string to its canonical form.

    Raises ValueError for labels not seen in the cleaned dataset.
    """
    key = raw.strip()
    if key not in _RAW_TO_CANONICAL:
        raise ValueError(
            f"Unknown label {raw!r}. Observed set is the 15-class CICIDS2017 "
            f"set; see ml/preprocessing/labels.py / DATA_ML_CONTRACT §8."
        )
    return _RAW_TO_CANONICAL[key]


def family_for(label: str) -> str:
    """Return the display family for a canonical label."""
    return FAMILY_MAP[label]


def encode_label(label: str) -> int:
    """Return the integer encoding for a canonical label."""
    return LABEL_TO_INT[label]


def decode_label(code: int) -> str:
    """Return the canonical label for an integer encoding."""
    return INT_TO_LABEL[code]


def binary_target(label: str) -> int:
    """Return the binary target (0 = BENIGN, 1 = attack)."""
    return 0 if label == "BENIGN" else 1
