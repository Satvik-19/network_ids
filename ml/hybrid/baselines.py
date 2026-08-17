"""Benign behaviour baselines (PRD §13).

Builds ``ml/artifacts/benign_baselines.json`` from benign training traffic:
simple descriptive statistics (median / mean / p25 / p75 / std) for selected
features. The UI compares a suspicious flow's feature values against these
baselines to produce human-readable statements like:

    "Normal median packet rate: 22 flows/sec — current flow: 540 flows/sec"

Selected features are config-driven (config/config.yaml ->
``inference.baseline_features``). A simple descriptive baseline is sufficient
per PRD §13; no time-series anomaly model.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.labels import binary_target
from ml.preprocessing.preprocess import preprocess_frame
from ml.preprocessing.subset import load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"
SEED = 42

BASELINE_FEATURES = [
    "Flow Duration",
    "Flow Packets/s",
    "Flow Bytes/s",
    "Packet Length Mean",
    "Packet Length Std",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Average Packet Size",
    "Flow IAT Mean",
    "Active Mean",
]


def _stats(x: np.ndarray) -> dict:
    clean = x[np.isfinite(x)]
    return {
        "median": round(float(np.median(clean)), 6),
        "mean": round(float(np.mean(clean)), 6),
        "p25": round(float(np.percentile(clean, 25)), 6),
        "p75": round(float(np.percentile(clean, 75)), 6),
        "std": round(float(np.std(clean)), 6),
        "n": int(len(clean)),
    }


def build_benign_baselines(
    subset_path: str | Path,
    features: list[str] | None = None,
    out_path: str | Path | None = None,
    config: str = "random",
) -> dict:
    """Build benign baselines from the benign rows of a dev training subset.

    Only BENIGN rows are used (PRD §34). The subset is the SAME class-aware
    dev subset used for supervised training, so baselines describe the
    training-distribution norm.
    """
    features = features or BASELINE_FEATURES
    out_path = Path(out_path) if out_path else ARTIFACTS / "benign_baselines.json"

    df = load_dev_subset(str(subset_path))
    raw = preprocess_frame(df, scale=False)
    labels = [binary_target(str(l)) for l in raw.labels]
    benign_mask = np.array([l == 0 for l in labels])
    print(f"benign rows in {subset_path.name}: {int(benign_mask.sum())} "
          f"of {len(labels)}")

    cols = raw.columns
    baseline = {}
    for f in features:
        if f not in cols:
            raise KeyError(f"feature {f!r} not in canonical feature order")
        idx = int(cols.index(f))
        baseline[f] = _stats(raw.X[benign_mask, idx])

    payload = {
        "version": "1.0",
        "dataset": "lacg030175/CICIDS2017",
        "revision": "d071fd53782d9ca7cdc15173b8ceb858fea04628",
        "source": f"{subset_path.name} (benign rows, {config} dev subset, seed {SEED})",
        "n_benign_flows": int(benign_mask.sum()),
        "feature_count": len(features),
        "features": features,
        "baselines": baseline,
        "unit_note": "CICIDS2017 units; durations in microseconds, rates in per-second, lengths/bytes in bytes.",
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    return payload


if __name__ == "__main__":
    raise SystemExit(
        build_benign_baselines(ROOT / "data" / "processed" / "dev_random_train.parquet")
    )
