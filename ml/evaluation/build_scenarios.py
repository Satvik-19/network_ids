"""build_scenarios.py — build Phase-3 replay scenario fixtures (data/scenarios).

Each fixture is a SMALL, deterministic JSON with a handful of REAL flows pulled
from the DISJOINT random_3way/test split (held-out evaluation data). It stores:

  * the full 77 canonical model features for each flow (Phase-2 predict input),
  * synthetic side-car replay metadata ONLY (source, destination, service_port,
    seq) used by the replay/grouping engine and future UI. This metadata is
    NEVER part of the model feature vector (see note in each JSON; BUG-005
    runtime purity applies — predictor.predict() never sees these),
  * ground_truth_label as an evaluation-note ONLY (like e2e_evidence_phase2);
    it is never consumed by predictor.predict().

Scenarios:
  normal        — several BENIGN flows (no incident expected)
  portscan      — several PortScan flows from one synthetic source (1 incident)
  dos_or_ddos   — mix of DoS Hulk + DDoS flows (same Denial-of-Service family;
                  deterministic grouping by family/source/dest)
  unknown       — real benign flows that the anomaly branch flags
                  UNKNOWN_SUSPICIOUS. OPTIONAL: only written when such a real
                  candidate exists in a bounded scan (deterministic first hit).

Run:  python -m ml.evaluation.build_scenarios
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.predictor import Phase2Predictor
from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.preprocess import preprocess_frame

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT / "data" / "scenarios"

# Synthetic replay-metadata side-cars. Deterministic; NOT model features.
SIDE = {
    "normal":     {"source": "10.0.0.8",  "destination": "10.0.0.9",
                   "service_ports": [80, 443, 443, 80, 443, 80, 443, 53]},
    "portscan":   {"source": "10.0.0.50", "destination": "10.0.0.9",
                   "service_ports": list(range(20, 28))},
    "dos_or_ddos": {"source": "10.0.1.7", "destination": "10.0.0.20",
                    "service_ports": [80] * 8},   # single DoS campaign on :80
    "unknown":    {"source": "10.0.0.60", "destination": "10.0.0.12",
                   "service_ports": [53] * 8},    # rare single-service anomaly
}
LOGICAL_INTERVAL = 1.0  # seconds between consecutive flows (replay pacing)


def _indexes_of(labels: list[str], wanted: dict[str, int]) -> list[tuple[str, int]]:
    """First N row indexes per truth label (deterministic, stable parquet order)."""
    out: list[tuple[str, int]] = []
    for truth, count in wanted.items():
        taken = 0
        for i, lab in enumerate(labels):
            if lab == truth:
                out.append((truth, i))
                taken += 1
                if taken >= count:
                    break
    return out


def _feature_dict(res, idx: int) -> dict:
    return {c: float(v) for c, v in zip(res.columns, res.X[idx].tolist())}


def _write_scenario(name: str, flows: list[dict], description: str) -> None:
    doc = {
        "schema": "scenario/v1",
        "name": name,
        "description": description,
        "logical_interval_seconds": LOGICAL_INTERVAL,
        "note": (
            "features = 77 canonical CICIDS2017 flow features (Phase-2 predict "
            "input). source/destination/service_port/seq are SYNTHETIC side-car "
            "replay metadata for replay + incident grouping + UI ONLY — they are "
            "never part of the model feature vector and predictor.predict() "
            "never receives them (BUG-005 runtime purity). ground_truth_label is "
            "an evaluation note ONLY; it is never consumed at inference time."
        ),
        "flows": flows,
    }
    (SCENARIOS_DIR / f"{name}.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"wrote data/scenarios/{name}.json  ({len(flows)} flows)")


def _flow_record(truth: str, idx: int, res, side: dict, seq: int) -> dict:
    ports = side["service_ports"]
    return {
        "seq": seq,
        "source": side["source"],
        "destination": side["destination"],
        "service_port": ports[seq % len(ports)],
        "ground_truth_label": truth,  # evaluation note only (never inferred)
        "features": _feature_dict(res, idx),
    }


def _find_unknown_flows(predictor, res, labels, want: int = 4) -> list[dict]:
    """Deterministic scan for real BENIGN flows the anomaly rescue flags.

    Cheap IF decision_function scan over a bounded window, then the FULL
    predict (with SHAP) only on flagged candidates to confirm the runtime
    classification is UNKNOWN_SUSPICIOUS. Returns [] if none exist (the
    `unknown` scenario is then skipped).
    """
    import numpy as np

    benign = res.y_binary == 0
    idxs = [i for i in range(len(labels)) if benign[i]]
    window_end = min(len(idxs), 60_000)  # bounded deterministic scan
    if window_end == 0:
        return []
    # Vectorised IF scan in chunks (fast, deterministic order preserved).
    Xb = res.X[idxs[:window_end]]
    below = np.zeros(window_end, dtype=bool)
    chunk = 10_000
    for start in range(0, window_end, chunk):
        stop = min(start + chunk, window_end)
        scores = predictor.isolation_forest.decision_function(Xb[start:stop])
        below[start:stop] = scores < predictor.anomaly_threshold
    found: list[int] = []
    for pos in np.flatnonzero(below):
        i = idxs[int(pos)]
        out = predictor.predict(_feature_dict(res, i))
        if out["classification"] == "UNKNOWN_SUSPICIOUS":
            found.append(i)
            if len(found) >= want:
                break
    return found


def main() -> int:
    predictor = Phase2Predictor()
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_split(LoadConfig(config="random_3way", split="test"))
    res = preprocess_frame(df, scale=False)
    labels = res.labels

    # ---- normal (strictly-BENIGN real flows) ----
    # The normal profile must replay without creating any incident, so we
    # choose real held-out BENIGN rows that the pipeline classifies as pure
    # BENIGN (no anomaly rescue). Deterministic first-hit scan, classification
    # only (with_shap=False keeps the scan fast).
    benign_idxs = [i for i in range(len(labels)) if labels[i] == "BENIGN"]
    normal_flows: list[dict] = []
    for i in benign_idxs:
        out = predictor.predict(_feature_dict(res, i), with_shap=False)
        if out["classification"] == "BENIGN":
            normal_flows.append(
                _flow_record("BENIGN", i, res, SIDE["normal"], len(normal_flows))
            )
            if len(normal_flows) >= 8:
                break
    _write_scenario(
        "normal", normal_flows,
        "8 real BENIGN flows from held-out test that replay as strictly BENIGN "
        "(no incident expected)"
    )

    # ---- portscan ----
    picks = _indexes_of(labels, {"PortScan": 8})
    flows = [
        _flow_record(truth, i, res, SIDE["portscan"], seq)
        for seq, (truth, i) in enumerate(picks)
    ]
    _write_scenario("portscan", flows,
                    "8 real PortScan flows, one synthetic scanning host -> one "
                    "target host (1 grouped incident)")

    # ---- dos_or_ddos (same family, two labels) ----
    picks = _indexes_of(labels, {"DoS Hulk": 4, "DDoS": 4})
    flows = [
        _flow_record(truth, i, res, SIDE["dos_or_ddos"], seq)
        for seq, (truth, i) in enumerate(sorted(picks, key=lambda x: x[1]))
    ]
    _write_scenario("dos_or_ddos", flows,
                    "4 DoS Hulk + 4 DDoS flows from held-out test; same Denial-of-"
                    "Service family and synthetic source/dest -> deterministic "
                    "grouping")

    # ---- unknown (optional: real anomaly-branch candidates) ----
    if _find_unknown_flows(predictor, res, labels):
        idxs = _find_unknown_flows(predictor, res, labels)
        flows = [
            _flow_record(labels[i], i, res, SIDE["unknown"], seq)
            for seq, i in enumerate(idxs)
        ]
        _write_scenario(
            "unknown", flows,
            "real benign flows flagged UNKNOWN_SUSPICIOUS by the anomaly rescue"
        )
    else:
        print("skipped data/scenarios/unknown.json (no real anomaly candidate)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())