"""rescue_summary.py — A1: IF unseen flag rate vs hybrid incremental rescue rate.

Reads the authoritative unknown/unseen anomaly-simulation result
(ml/evaluation/results/unknown_experiment_temporal.json) and derives a small
machine-readable summary that CLEARLY distinguishes two different rates that
must NOT be compared as equivalent populations:

  1. IF unseen flag rate
       Population: ALL temporally-unseen malicious flows (Friday test,
       unseen classes Bot + DDoS + PortScan).
       Numerator:   flows whose raw IsolationForest decision_function score
                    is below the calibrated threshold (the IF flags them on
                    its OWN, independent of the supervised model).
       This is a plain anomaly-detector recall on the unseen-malicious
       population (aggregate = anomaly.metrics.recall; exact count =
       anomaly.metrics.true_positive from the authoritative experiment).

  2. Hybrid incremental rescue rate
       Population: unseen malicious flows NOT already classified
                    KNOWN_ATTACK by the supervised branch of the hybrid
                    (rescue_denominator = total_unseen - supervised_known).
       Numerator:  flows surfaced to UNKNOWN_SUSPICIOUS by the IF anomaly
                    branch of the hybrid.
       This measures what the anomaly branch ADDS on top of supervised
       inference. Because the denominator excludes supervised-known flows,
       this rate is LOWER than the IF flag rate by construction and the two
       numbers are not comparable.

Exactness policy:
  * Aggregate IF flagged count (anomaly.metrics.true_positive) is EXACT.
  * Per-class IF flag counts are NOT stored exactly in the experiment JSON;
    only the rounded percentage ``pct_flagged_anomalous`` is available, so
    per-class counts are named ``estimated_if_flag_count`` and computed as
    round(n * pct). They are estimates, never presented as exact.

This script does NOT retrain or re-run the detectors.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "ml" / "evaluation" / "results"

SRC = EVAL_DIR / "unknown_experiment_temporal.json"
OUT = EVAL_DIR / "unknown_rescue_summary.json"

UNSEEN_CLASSES = ["Bot", "DDoS", "PortScan"]


def _estimated_flag_count(n: int, pct: float) -> int:
    """Estimate per-class IF-flagged flows from the ROUNDED source pct.

    Only the rounded percentage exists per class in the experiment JSON, so
    this is an ESTIMATE (see field name estimated_if_flag_count), not exact.
    """
    return round(n * pct)


def main() -> int:
    if not SRC.exists():
        raise FileNotFoundError(f"missing source experiment file: {SRC}")

    src = json.loads(SRC.read_text(encoding="utf-8"))
    per_class = src["per_class"]
    anomaly = src["anomaly"]

    classes = []
    for cls in UNSEEN_CLASSES:
        pc = per_class[cls]
        n = int(pc["n"])
        flag_pct = float(pc["pct_flagged_anomalous"])  # IF unseen flag rate (per class)
        estimated_flag_count = _estimated_flag_count(n, flag_pct)
        outcomes = pc["hybrid_outcomes"]
        known = int(outcomes.get("KNOWN_ATTACK", 0))    # supervised-known (hybrid)
        rescued = int(outcomes.get("UNKNOWN_SUSPICIOUS", 0))
        candidates = n - known                          # population B: not known_attack
        rescue_pct = (rescued / candidates) if candidates > 0 else 0.0
        classes.append(
            {
                "attack_family_or_class": cls,
                "n": n,
                "if_unseen_flag_rate": round(flag_pct, 6),
                "estimated_if_flag_count": estimated_flag_count,  # ESTIMATE from rounded pct
                "flag_count_source": (
                    "estimated: round(n * pct_flagged_anomalous); the experiment "
                    "JSON stores per-class flagged count only as a rounded "
                    "percentage (exact per-class counts not available)"
                ),
                "supervised_known_attack_count": known,   # population B exclusion
                "hybrid_rescued_to_unknown_count": rescued,
                "rescue_denominator_not_known_attack": candidates,  # population B
                "hybrid_incremental_rescue_rate": round(rescue_pct, 6),
            }
        )

    total_n = sum(int(per_class[c]["n"]) for c in UNSEEN_CLASSES)
    total_known = sum(
        int(per_class[c]["hybrid_outcomes"].get("KNOWN_ATTACK", 0))
        for c in UNSEEN_CLASSES
    )
    total_rescued = sum(
        int(per_class[c]["hybrid_outcomes"].get("UNKNOWN_SUSPICIOUS", 0))
        for c in UNSEEN_CLASSES
    )
    total_candidates = total_n - total_known

    # Aggregate IF flag data is EXACT from the authoritative metrics block.
    if_rate_exact = float(anomaly["metrics"]["recall"])
    if_count_exact = int(anomaly["metrics"]["true_positive"])
    summary_estimated = sum(c["estimated_if_flag_count"] for c in classes)

    result = {
        "title": "IF unseen flag rate vs hybrid incremental rescue rate (Phase-2 closure; A1 precision)",
        "wording": "unseen / unknown anomaly simulation (NOT zero-day detection)",
        "source": str(SRC.resolve()),
        "model": "IsolationForest (benign only) + hybrid decision layer",
        "population_notes": (
            "The IF unseen flag rate and the hybrid incremental rescue rate use "
            "DIFFERENT populations. Population A (IF flag rate) = all temporally-"
            "unseen malicious flows (Bot + DDoS + PortScan, Friday test). "
            "Population B (rescue rate) = unseen malicious flows NOT already "
            "classified KNOWN_ATTACK by supervised inference. The rescue rate "
            "therefore sits below the IF flag rate by construction; the two "
            "numbers MUST NOT be compared as equivalent."
        ),
        "if_unseen_flag_rate_definition": (
            "fraction of ALL temporally-unseen malicious flows (population A) "
            "flagged by the anomaly detector on raw anomaly score < calibrated "
            "threshold (anomaly recall)"
        ),
        "if_unseen_flag_rate_population": {
            "population": "ALL unseen malicious flows (Bot + DDoS + PortScan)",
            "denominator": total_n,
            "numerator": if_count_exact,
        },
        "if_unseen_flag_rate_aggregate": if_rate_exact,     # EXACT (metrics.recall)
        "if_unseen_flag_count_aggregate_exact": if_count_exact,   # EXACT (metrics.true_positive)
        "note": (
            "aggregate IF flag rate/count are EXACT from "
            "unknown_experiment_temporal.json anomaly.metrics"
        ),
        "hybrid_incremental_rescue_rate_definition": (
            "among unseen malicious flows NOT already classified KNOWN_ATTACK "
            "by the supervised branch (population B), fraction surfaced to "
            "UNKNOWN_SUSPICIOUS by the IF anomaly branch of the hybrid"
        ),
        "hybrid_incremental_rescue_aggregate": {
            "population": "unseen malicious flows NOT classified KNOWN_ATTACK",
            "total_unseen_flows": total_n,
            "supervised_known_attack_count": total_known,
            "rescue_denominator_not_known_attack": total_candidates,
            "rescued_to_unknown_suspicious": total_rescued,
            "hybrid_incremental_rescue_rate": (
                round(total_rescued / total_candidates, 6)
                if total_candidates > 0 else 0.0
            ),
        },
        "estimate_consistency": {
            "per_class_estimate_sum": summary_estimated,
            "aggregate_exact_count": if_count_exact,
            "note": (
                "The per-class estimated IF counts (sum above) are derived from "
                "rounded per-class percentages and may differ by a few rows from "
                "the EXACT aggregate count (metrics.true_positive). Use the "
                "aggregate exact count as authoritative; per-class counts are "
                "named estimated_if_flag_count."
            ),
        },
        "per_class_breakdown": classes,
        "traceability_note": (
            "both rates are evaluated at the SAME anomaly+confidence "
            "thresholds (-0.115716 temporal / 0.75 known-confidence); "
            "derived from unknown_experiment_temporal.json (2026-08-09)."
        ),
    }

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for row in classes:
        print(
            f"  {row['attack_family_or_class']:9s} "
            f"if_rate={row['if_unseen_flag_rate']:.4f} "
            f"est_flag={row['estimated_if_flag_count']:>6d} "
            f"known={row['supervised_known_attack_count']:>6d} "
            f"rescue_rate={row['hybrid_incremental_rescue_rate']:.6f}"
        )
    agg = result["hybrid_incremental_rescue_aggregate"]
    print(
        f"EXACT aggregate IF flag rate={if_rate_exact:.4f} "
        f"count={if_count_exact} (population A, n={total_n})"
    )
    print(
        f"rescue={agg['rescued_to_unknown_suspicious']}/"
        f"{agg['rescue_denominator_not_known_attack']} "
        f"rescue rate={agg['hybrid_incremental_rescue_rate']:.6f} "
        f"(population B, total_unseen={total_n})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())