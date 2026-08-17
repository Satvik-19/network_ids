"""subset.py — Reproducible class-aware development subset builder.

Design (per PRD §29 and DATA_ML_CONTRACT §2a):
- Start from a source (config, split) — canonical: ``random/train`` for the
  random experiment and ``temporal/train`` for the temporal experiment.
- RETAIN every attack class (never silently drop minority classes).
- Downsample only dominant BENIGN (and, if needed, over-represented attack
  classes) to reach a target total in the ~200k–500k range.
- Fixed random seed for reproducibility.
- Record exact per-class counts before/after sampling.

Sampling algorithm (deterministic):
  1. Count each class.
  2. Classes below a per-class floor (``cap_floor``) are kept in full.
  3. Classes above a per-class cap (``per_class_cap``) are sampled down to
     the cap.
  4. BENIGN is downsampled to the remainder needed to hit ``target``.
The concrete caps are configurable; the defaults produce a ~300k subset.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.labels import normalize_label


class DevSubsetError(RuntimeError):
    pass


def _counts(df: pd.DataFrame) -> Dict[str, int]:
    """Per-class row counts (canonical labels) in source order of appearance."""
    counts: Dict[str, int] = {}
    for raw in df["Label"]:
        lbl = normalize_label(raw)
        counts[lbl] = counts.get(lbl, 0) + 1
    return counts


def _sample_group(
    df: pd.DataFrame,
    label: str,
    n: int,
    seed: int,
) -> pd.DataFrame:
    """Deterministically sample n rows from df (single class)."""
    if n >= len(df):
        return df
    return df.sample(n=n, random_state=seed)


def build_dev_subset(
    *,
    config: str = "random",
    split: str = "train",
    target: int = 300_000,
    per_class_cap: int = 60_000,
    cap_floor: int = 8_000,
    seed: int = 42,
    out_path: Optional[str] = None,
) -> tuple[pd.DataFrame, dict]:
    """Build and return a class-aware dev subset plus a metadata record.

    Returns (subset_df, metadata). If ``out_path`` is given, writes the
    subset to parquet and the metadata next to it as ``{out_path}.meta.json``.
    """
    if target < 200_000 or target > 500_000:
        raise DevSubsetError(
            f"target {target} outside PRD §29 range 200k–500k"
        )

    src = load_split(LoadConfig(config=config, split=split))
    before = _counts(src)
    classes = sorted(before)

    # Which classes need capping?
    keep_full = {c for c in classes if before[c] <= per_class_cap}
    cap_down = {c for c in classes if before[c] > per_class_cap}

    frames: list[pd.DataFrame] = []
    # First retain full minority classes (everything <= cap).
    for c in sorted(keep_full):
        group = src[src["Label"].map(normalize_label) == c]
        frames.append(group)

    # Cap over-represented classes.
    for c in sorted(cap_down):
        if c == "BENIGN":
            continue  # BENIGN handled last to fill target remainder
        n_cap = min(before[c], per_class_cap)
        group = src[src["Label"].map(normalize_label) == c]
        frames.append(_sample_group(group, c, n_cap, seed=seed))

    filled = sum(len(f) for f in frames)
    benign_total = before.get("BENIGN", 0)
    benign_needed = target - filled
    if benign_needed < 0:
        raise DevSubsetError(
            f"target {target} too small for retained classes (min {filled})"
        )
    if benign_needed > benign_total:
        raise DevSubsetError(
            f"cannot reach target {target}: BENIGN total {benign_total} "
            f"insufficient (need {benign_needed})"
        )

    if benign_total > 0:
        benign_group = src[src["Label"].map(normalize_label) == "BENIGN"]
        frames.append(
            _sample_group(benign_group, "BENIGN", benign_needed, seed=seed)
        )

    subset = pd.concat(frames, ignore_index=True)
    after = _counts(subset)

    metadata = {
        "source": {"config": config, "split": split},
        "seed": seed,
        "target": target,
        "per_class_cap": per_class_cap,
        "cap_floor": cap_floor,
        "total_before": int(len(src)),
        "total_after": int(len(subset)),
        "counts_before": dict(sorted(before.items())),
        "counts_after": dict(sorted(after.items())),
        "retained_fully": sorted(keep_full),
        "capped_down": sorted(cap_down),
    }

    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        subset.to_parquet(p, index=False)
        meta_path = p.with_suffix(p.suffix + ".meta.json")
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return subset, metadata


def load_dev_subset(parquet_path: str) -> pd.DataFrame:
    """Load a previously materialised dev subset."""
    return pd.read_parquet(parquet_path)
