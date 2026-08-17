"""
dataset.py — Minimal, reusable CICIDS2017 loader (Phase 1).

Loads a config/split of the cleaned HF derivative into a pandas DataFrame.
Does NOT do any preprocessing — that is a later Phase-1 step
(see docs/DATA_ML_CONTRACT.md). Keep this loader intentionally small.

NOTES on the loader path (verified 2026-08-09, see BUG_LOG / DECISIONS):
- The canonical load is the HF ``load_dataset`` API with the CONFIG passed
  positionally, e.g. ``load_dataset("lacg030175/CICIDS2017", "temporal",
  revision=<pinned>)``. This works with the pinned revision.
- The ``config_name=`` KEYWORD form fails with a TypeError because the
  packaged Parquet builder receives config_name twice. That is an API-argument
  quirk of this derivative's packaged builder, NOT an HF bug.
- For efficiency and determinism we load the parquet files directly via the
  hf:// URL with the pinned revision. Both paths yield identical rows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


REPO_ID = "lacg030175/CICIDS2017"
# Lock the exact revision discovered during inspection. Update only via an ADR
# in docs/DECISIONS.md if a different dataset version is deliberately chosen.
REVISION = "d071fd53782d9ca7cdc15173b8ceb858fea04628"

# Canonical configs exposed by the dataset (see docs/DATA_ML_CONTRACT.md §2).
CONFIG_FILES = {
    "random": ["random/train-00000-of-00001.parquet",
               "random/test-00000-of-00001.parquet"],
    "random_3way": ["random_3way/train-00000-of-00001.parquet",
                    "random_3way/validation-00000-of-00001.parquet",
                    "random_3way/test-00000-of-00001.parquet"],
    "temporal": ["temporal/train-00000-of-00001.parquet",
                 "temporal/test-00000-of-00001.parquet"],
    "temporal_3way": ["temporal_3way/train-00000-of-00001.parquet",
                      "temporal_3way/validation-00000-of-00001.parquet",
                      "temporal_3way/test-00000-of-00001.parquet"],
    "standard": [],  # alias; use "temporal"
}


def parquet_url(filename: str, revision: str = REVISION) -> str:
    return f"hf://datasets/{REPO_ID}@{revision}/{filename}"


@dataclass
class LoadConfig:
    """How to load a subset of the dataset.

    columns: None = all (default). Pass a list to project only what's needed
             (e.g. ['Label', 'label'] for a fast label scan). Order preserved.
    config / split: choose which HF config and split to load.
    """
    config: str = "temporal"
    split: str = "train"
    columns: Optional[list[str]] = None


def load_split(cfg: LoadConfig) -> pd.DataFrame:
    """Load one (config, split) as a DataFrame with optional column projection."""
    if cfg.config == "standard":
        cfg = LoadConfig(config="temporal", split=cfg.split, columns=cfg.columns)
    files = [f for f in CONFIG_FILES.get(cfg.config, [])
             if f"/{cfg.split}-" in f]
    if not files:
        raise ValueError(
            f"No parquet for config={cfg.config!r} split={cfg.split!r}. "
            f"Available configs: {list(CONFIG_FILES)}"
        )
    # Single-file per (config, split) for this dataset.
    url = parquet_url(files[0])
    return pd.read_parquet(url, columns=cfg.columns)


def load_label_scan(cfg: LoadConfig) -> tuple[pd.Series, pd.Series]:
    """Fast label-only scan (recommended for label-set discovery)."""
    df = load_split(LoadConfig(config=cfg.config, split=cfg.split,
                               columns=["Label", "label"]))
    return df["Label"], df["label"]
