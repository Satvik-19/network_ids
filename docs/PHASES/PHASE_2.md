# Phase 2 — Final Detection Intelligence

Source: PRD §58 (Phase 2). Active only after Phase 1 gate passes.

## Goal

Complete the core ML pipeline: final supervised model, anomaly detector,
hybrid decision, risk, explainability, and the academic random-vs-temporal
evaluation.

## PRD Scope

**Supervised (PRD §32, §33):**
- Light RF/XGBoost tuning (avoid large hyperparameter searches).
- Select final model.

**Anomaly (PRD §34, §46):**
- Isolation Forest fit primarily on benign training traffic.
- Threshold calibration on validation data.
- Unknown / unseen experiment (held-out family or temporal unseen classes).
  Use wording "unseen / unknown anomaly simulation" — never "zero-day
  detection" (PRD §46, §64.3).

**Hybrid (PRD §10):**
- Known classification + anomaly score → deterministic hybrid decision.
- Risk scoring (LOW/MEDIUM/HIGH/CRITICAL).

**Explainability (PRD §12, §36):**
- SHAP TreeExplainer (local explanations).
- Benign baselines for behaviour-vs-normal comparison (PRD §13).

**Academic (PRD §26, §47):**
- Random vs temporal evaluation as a generalisation gap.

## Explicitly Out of Scope During This Phase

- Replay engine, incident grouping, dashboards, Cytoscape graph (Phase 3).
- Playground (Phase 4).
- Model Evaluation Lab UI polish (Phase 5).
- Autoencoder (only if Isolation Forest clearly fails AND time remains —
  PRD §35, §63).
- Deep-learning / SVM models (PRD §33, §62).

## Required Deliverables (PRD §58 Phase 2)

- Final supervised artifact.
- Anomaly artifact.
- Hybrid engine.
- Risk engine.
- SHAP (local).
- Evaluation results.

## Implementation Tasks

- [x] Light RF/XGBoost tuning; compare on macro/weighted F1, per-class recall,
      FP behaviour, temporal generalisation, inference cost (not accuracy
      alone).
- [x] Select final supervised model; record rationale in DECISIONS.md.
- [x] Persist supervised model + label_mapping + feature_schema +
      model_metadata.
- [x] Train Isolation Forest on benign training traffic; calibrate threshold
      on validation.
- [x] Run the unknown/unseen anomaly experiment (Option B per PRD §46).
- [x] Implement the deterministic hybrid decision layer (config-driven
      thresholds — PRD §57).
- [x] Implement the transparent risk engine (config-driven thresholds).
- [x] Implement SHAP local explanations (native TreeSHAP).
- [x] Build benign baselines (`benign_baselines.json`) for selected features.
- [x] Run random vs temporal evaluation; report the generalisation gap
      (supervised + anomaly).
- [x] Lock the inference output contract (Phase-2 gate fields).

## Dependencies / Prerequisites

- Phase 1 complete (dataset loader, preprocessing, feature schema, baselines,
  skeletons).
- Locked feature schema and label mapping.

## Files / Components Expected (PRD §55, §56)

- `ml/training/` (final supervised + anomaly training).
- `ml/evaluation/` (metrics, random vs temporal).
- `ml/artifacts/` (`supervised_model`, `isolation_forest`, `scaler` if used,
  `label_mapping.json`, `feature_schema.json`, `benign_baselines.json`,
  `model_metadata.json`).
- `backend/app/services/inference/`, `anomaly/`, `explainability/`.

## Validation Plan

- Hybrid decision boundary tests (config-driven thresholds).
- Risk engine mapping tests.
- SHAP produces the documented top-feature contract for a flagged flow.
- Anomaly metrics: precision, recall, F1, FPR, score distributions (PRD §47).
- Random vs temporal results recorded reproducibly
  (`ml/evaluation/results/supervised_selection_random.json` vs `_temporal.json`).

## Completion Gate (PRD §58)

One flow returns:

```json
{
  "classification": "...",
  "family": "...",
  "confidence": 0.0,
  "anomaly_score": 0.0,
  "risk": "...",
  "top_features": []
}
```

## Completion Gate Evidence

Implemented and validated 2026-08-09.

The Phase-2 gate is `ml/hybrid/*` + `backend/app/services/predictor.py`
(`Phase2Predictor`) and the Phase-2 `/api/predict` contract
(`backend/app/schemas/predict.py`).

Evidence:

1. The deterministic hybrid (`ml/hybrid/decision.py`) returns exactly the three
   PRD-required outcomes (BENIGN / KNOWN_ATTACK / UNKNOWN_SUSPICIOUS) with
   config thresholds `known_confidence_threshold: 0.75`,
   `anomaly_threshold: -0.0928` (validated 2026-08-09).
2. Phase-2 closure audit (2026-08-09) fixed + locked the hybrid rescue
   semantics (BUG-007): KNOWN_ATTACK only for a malicious predicted label at
   confidence >= 0.75; the anomaly rescue then runs for every other flow, so
   a high-confidence BENIGN verdict can still surface as UNKNOWN_SUSPICIOUS.
   Regression test `test_high_confidence_benign_rescued_by_anomaly` added.
3. Live E2E gate passed on real uvicorn (127.0.0.1:8765), real API (re-run
   2026-08-09 closure audit):
   - benign flow  -> classification BENIGN,     conf 1.0, risk LOW (2.5)
   - DoS H2       -> KNOWN_ATTACK, conf 1.0, risk CRITICAL (100.0)
   - SSH-Patator  -> KNOWN_ATTACK / HIGH (70)
   - PortScan     -> KNOWN_ATTACK / MEDIUM (50)
   - DDoS         -> KNOWN_ATTACK / CRITICAL (90)
   Every response carried `{classification, label, family, confidence,
   anomaly_score, risk_level, risk_score, top_features}`.
4. TreeSHAP additivity verified for all 15 classes
   (`test_shap_additivity_across_all_classes`: sum(contributions) + bias ==
   raw margin) and the explainer is confirmed to rank the PREDICTED class's
   contributions (`test_shap_explainer_uses_predicted_class`).
5. Isolation Forest sensitivity audit (`ml/training/if_sensitivity.py`): 4
   configs varying n_estimators / max_samples / max_features, seed 42 fixed,
   same FPR<=5% calibration. DDoS-class recall 0.1685-0.1716 across
   configs; deployed config kept -- the low unseen recall is structural, not
   a tuning artifact. Threshold trade-off table in `if_sensitivity.json`.
6. Unit/contract test coverage:
   - `ml/tests/test_hybrid.py` -- 15 passed (three-outcome boundaries, BENIGN
     floor, config thresholds, high-confidence-BENIGN rescue).
   - `ml/tests/test_shap.py` -- 5 passed (top-5, feature names, additivity,
     predicted-class ranking, benign baselines).
   - `ml/tests/test_predictor.py` -- 6 passed (contract fields, hybrid
     consistency, real-row anomaly separation, +3 BUG-005 runtime-purity
     regressions: no ground-truth param, metadata ignored, extra keys rejected).
   - `backend/tests/test_api.py` -- 4 passed (health phase-2, full predict
     contract incl. top_features/anomaly_score/risk, missing/extra 422s).
   Full suite: `python -m pytest ml/tests backend/tests -q` -> 43 passed.


## Current Status

**COMPLETE / VALIDATED (2026-08-09).**

## Blockers

None.

## Decisions Made During This Phase

- Final supervised model: XGBoost multiclass random (xgb_200) — DEC-007.
- Isolation Forest anomaly threshold: -0.0928 (FPR-constrained max-F1, FPR<=5%)
  — DEC-008.
- SHAP via XGBoost native TreeSHAP (pred_contribs) — DEC-009.
- Hybrid + risk config-driven contract (0.75 / risk thresholds, severity map)
  — DEC-010.
- Unknown experiment: temporal Option B (Friday-only classes) — PRD §46.
- Benign baseline features: the 10 runtime baseline features in config.
See docs/DECISIONS.md DEC-004–DEC-010 for rationale and consequences.

## Evaluation clarification - 2026-10-31

Aggregate unseen IF recall across the sensitivity variants is 0.074955–0.076569;
0.1685–0.1716 is DDoS-class recall. Two variants are equivalent. Supervised
selection used random/test and reused it for reporting. Frozen results are kept
as development evidence; see DEC-019 and EVALUATION_PROTOCOL.md. Friday labeled
validation includes the attack classes later evaluated, and no row timestamps
establish chronological ordering within its two halves. No retraining/tuning.
