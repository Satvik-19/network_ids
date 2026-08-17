"""scenarios.py — Load deterministic replay scenario fixtures (Phase 3).

Scenario fixtures live in data/scenarios/*.json and were built ONCE by
ml/evaluation/build_scenarios.py from real held-out (random_3way/test) flows.
Each fixture is small and committed, so replay does NOT depend on the HF
dataset or any network access at runtime.

Schema (scenario/v1):
  name, description, logical_interval_seconds, note,
  flows: [{
      seq,                       # 0-based deterministic replay order
      source, destination, service_port,   # SYNTHETIC side-car metadata only
      ground_truth_label,                  # EVALUATION note only (never fed
                                           # to predictor.predict())
      features: {77 canonical feature values},
  }]
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.predictor import PredictorError

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_DIR = ROOT / "data" / "scenarios"
FEATURE_COUNT = 77


class ScenarioError(RuntimeError):
    pass


class Scenario:
    """One loaded scenario fixture (immutable snapshot)."""

    def __init__(self, doc: dict) -> None:
        if doc.get("schema") != "scenario/v1":
            raise ScenarioError(f"unsupported scenario schema: {doc.get('schema')!r}")
        validate_scenario_doc(doc)
        self.name = doc["name"]
        self.description = doc.get("description", "")
        self.logical_interval_seconds = float(doc.get("logical_interval_seconds", 1.0))
        self.flows = doc["flows"]
        if not self.flows:
            raise ScenarioError(f"scenario {self.name!r} has no flows")

    @property
    def total(self) -> int:
        return len(self.flows)


def load_scenarios_dir(directory: Path = SCENARIOS_DIR) -> list[Scenario]:
    """Load every *.json fixture in the scenarios directory (deterministic
    order by name)."""
    if not directory.exists():
        return []
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            out.append(load_scenario(path))
        except (ScenarioError, json.JSONDecodeError) as exc:
            raise ScenarioError(f"invalid scenario {path.name}: {exc}") from exc
    return out


def load_scenario(path: Path) -> Scenario:
    return Scenario(json.loads(path.read_text(encoding="utf-8")))


def scenario_names() -> list[str]:
    return [s.name for s in load_scenarios_dir()]


class ScenarioPlayer:
    """Deterministic iterator over a scenario.

    ``flow(seq)`` returns (features, metadata) for the seq-th flow in replay
    order. It never mutates the scenario; rendering is pure.
    """

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self._by_seq = {f["seq"]: f for f in scenario.flows}

    def __len__(self) -> int:
        return len(self.scenario.flows)

    def flow(self, seq: int) -> dict:
        if seq < 0 or seq >= len(self.scenario.flows):
            raise ScenarioError(
                f"flow seq {seq} out of range for scenario {self.scenario.name!r}"
            )
        return self._by_seq[seq]

    def replay_time(self, seq: int, base: float) -> float:
        """Synthetic replay timestamp (epoch seconds) for the seq-th flow.

        scenario_start + seq × logical_interval (deterministic synthetic time;
        never presented as the original CICIDS capture timestamp).
        """
        return base + seq * self.scenario.logical_interval_seconds


def validate_scenario_doc(doc: dict) -> None:
    """Runtime-schema guard: reject fixtures that can't be replayed safely."""
    flows = doc.get("flows")
    if not flows:
        raise ScenarioError("empty flows list")
    seqs = [f.get("seq") for f in flows]
    if seqs != list(range(len(flows))):
        raise ScenarioError("flows must have contiguous 0-based seq order")
    for f in flows:
        feats = f.get("features")
        if not isinstance(feats, dict) or len(feats) != FEATURE_COUNT:
            raise ScenarioError(
                f"flow seq {f.get('seq')} must carry exactly {FEATURE_COUNT} features"
            )