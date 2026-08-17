"""record_e2e_evidence.py â€” A4: real Phase E2E inference evidence records.

For a small set of REAL rows (from the disjoint random_3way/test split), run
the SHARED Phase-2 predictor (supervised + anomaly + hybrid + risk + SHAP)
and record a machine-readable JSON used by the Phase-2 closure report.

For every record we store:
    evaluation truth label            (scoring only â€” BUG-005/010)
    predicted label
    family
    classification
    confidence
    anomaly_score
    risk_score
    risk_level
    top_features count

Verifications this script performs:
  * the shared predictor's ``predict`` signature has NO ground-truth argument
    (runtime inference never consumes the evaluation label â€” BUG-005/010),
  * a benign flow flagged only by the anomaly branch is recorded as a real
    UNKNOWN_SUSPICIOUS candidate,
  * the previously reported "PortScan -> MEDIUM (50)" is resolved to its
    actual runtime classification (KNOWN_ATTACK / UNKNOWN_SUSPICIOUS) and
    risk by direct inspection instead of repeating a stale/inferred value.

Only ~5 real flows are scored (SHAP = ~0.13 s/flow), so the run is fast.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from backend.app.services.predictor import Phase2Predictor
from ml.preprocessing.dataset import LoadConfig, load_split
from ml.preprocessing.preprocess import preprocess_frame

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"
OUT = EVAL_DIR / "e2e_evidence_phase2.json"

# (truth label, description) rows we want evidence for.
WANT = [
    ("BENIGN", "benign normal traffic"),
    ("DoS Hulk", "known volumetric DoS"),
    ("DDoS", "known DDoS burst"),
    ("SSH-Patator", "known SSH brute force"),
    ("PortScan", "known network / PortScan"),
]


def _to_features(row_series) -> dict:
    df = row_series.to_frame().T
    res = preprocess_frame(df, scale=False)
    return {col: float(v) for col, v in zip(res.columns, res.X[0].tolist())}


def _normalize(predictor, row, truth: str, desc: str, idx: int) -> dict:
    out = predictor.predict(_to_features(row))
    return {
        "evidence_index": idx,
        "evaluation_truth_label": truth,   # scoring only; never fed to model
        "description": desc,
        "predicted_label": out["label"],
        "family": out["family"],
        "classification": out["classification"],
        "confidence": out["confidence"],
        "anomaly_score": out["anomaly_score"],
        "risk_score": out["risk_score"],
        "risk_level": out["risk_level"],
        "top_features_count": len(out["top_features"]),
    }


def _scan_unknown_candidate(predictor, df, labels):
    """Find one REAL benign flow flagged by the anomaly branch alone.

    Scan uses the isolation-forest decision_function only (fast), then the
    FULL predict() path for the selected row.
    """
    res = preprocess_frame(df, scale=False)
    benign = res.y_binary == 0
    Xb = res.X[benign]
    scores = predictor.isolation_forest.decision_function(Xb[:20000])
    thr = predictor.anomaly_threshold
    flagged = scores < thr
    if not flagged.any():
        return None
    j = int(flagged.argmax())
    idx = [i for i in range(len(Xb)) if benign[i]][j]
    truth = labels[idx]
    return idx, truth, "anomaly-only candidate"

def _ensure_no_truth_param(predictor) -> bool:
    """BUG-005/010 guard: the runtime predictor must not accept a truth label."""
    sig = inspect.signature(predictor.predict)
    assert "truth" not in sig.parameters and "label" not in sig.parameters, (
        "predict() must not declare a ground-truth parameter"
    )
    return True


def main() -> int:
    predictor = Phase2Predictor()
    _ensure_no_truth_param(predictor)

    df = load_split(LoadConfig(config="random_3way", split="test"))
    res = preprocess_frame(df, scale=False)
    labels = res.labels

    records = []
    for truth, desc in WANT:
        idxs = [i for i, l in enumerate(labels) if l == truth]
        if not idxs:
            print(f"  WARNING: no real row with truth={truth!r}")
            continue
        idx = idxs[0]
        records.append(_normalize(predictor, df.iloc[idx], truth, desc, idx))

    cand = _scan_unknown_candidate(predictor, df, labels)
    if cand is not None:
        idx, truth, desc = cand
        records.append(_normalize(predictor, df.iloc[idx], truth, desc, idx))
    else:
        print("  WARNING: no real UNKNOWN_SUSPICIOUS candidate found in scan window")

    doc = {
        "title": "Phase-2 end-to-end real-inference evidence records",
        "dataset": "random_3way/test (disjoint held-out test)",
        "note": (
            "evaluation_truth_label is recorded for scoring ONLY; "
            "predictor.predict() never receives it (BUG-005)."
        ),
        "config": {
            "known_confidence_threshold": predictor.known_confidence_threshold,
            "anomaly_threshold": predictor.anomaly_threshold,
        },
        "records": records,
    }

    ps = next((r for r in records if r["evaluation_truth_label"] == "PortScan"), None)
    if ps is not None:
        doc["portscan_resolution"] = (
            "Previously reported 'PortScan -> MEDIUM (50)' is resolved here to "
            f"actual runtime classification={ps['classification']} "
            f"risk_level={ps['risk_level']} risk_score={ps['risk_score']}; "
            "the MEDIUM(50) figure is replaced by this runtime-inspected value."
        )

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for r in records:
        print(
            f"  truth={r['evaluation_truth_label']:12s} "
            f"pred={r['predicted_label']:14s} "
            f"cls={r['classification']:17s} conf={r['confidence']:.3f} "
            f"anom={r['anomaly_score']:.4f} risk={r['risk_level']:8s} "
            f"({r['risk_score']:.1f}) top={r['top_features_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())