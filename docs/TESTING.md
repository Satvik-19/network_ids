# TESTING.md — Validation Strategy

Defines the project's validation approach. Distinguish strictly:

```text
implemented != tested
tested     != validated
```

Never describe an unexecuted test as passing. Never mark functionality
VALIDATED in `IMPLEMENTATION_STATUS.md` unless its tests actually ran.

---

## Scope-by-scope Validation

### 1. Preprocessing / data tests

- Raw row counts match recorded `DATA_ML_CONTRACT.md` values.
- Non-finite / inf / NaN handling applied deterministically.
- Duplicate-column cleanup is reproducible.
- Label normalisation produces exactly the recorded label set.
- Feature ordering after preprocessing matches `feature_schema.json`.
- No held-out test data used to fit preprocessing (no leakage).
- Minority classes not silently dropped (PRD §29).

### 2. ML reproducibility checks

- Fixed random seed reproduces the same split and metrics.
- Random split and temporal split remain distinct experiments (PRD §26).
- Saved artifacts (`ml/artifacts/`) reproduce evaluation metrics on reload.
- Model input format matches `feature_schema.json` exactly.

### 3. Backend unit tests

- Hybrid decision layer returns correct outcome for boundary confidence and
  anomaly-score values (incl. config-driven thresholds).
- Risk engine maps (family, confidence, anomaly, volume) → correct
  LOW/MEDIUM/HIGH/CRITICAL.
- Preprocessor load + single-flow inference returns the documented contract
  fields.

### 4. API integration tests

- `POST /api/predict` returns the Phase-2 contract (classification, family,
  confidence, anomaly_score, risk, top_features) (PRD §38, §58 Phase-2 gate).
- Replay start/stop/status transitions are correct (PRD §42).
- Incident endpoints return incidents with retained underlying flow IDs
  (PRD §66.17).
- Playground profile → run → results flow (PRD §44).

### 5. Database tests

- SQLite schema matches the documented tables (PRD §41).
- Incident grouping writes incident + incident_flows consistently.

### 6. Incident grouping tests

- Prepared multi-flow attack scenarios collapse into the expected single
  incident using family + source + destination + service/port + time window.
- Grouping window boundary behaviour matches config.

### 7. Replay tests

- Deterministic: same input + seed + speed → same observed stream.
- Speed multipliers (1x/5x/20x) advance flows as expected.
- Pause/resume/stop controls behave correctly.

### 8. Frontend / component validation

- Security Monitor summary cards render correct metrics.
- Cytoscape graph renders nodes/edges from a known fixture.
- Incident Detail shows SHAP contributions and baseline comparison.
- Model Lab charts render model-comparison and random-vs-temporal data.

### 9. Playground tests

- Different environment profiles produce different logical suites (Phase-4
  gate, PRD §58).
- Readiness score and blind-spot detection derived from actual test outcomes.

### 10. Final end-to-end completion gates

- **Phase 1 gate:** load dataset → preprocess flow → train baseline → call
  prediction API.
- **Phase 2 gate:** one flow returns classification, family, confidence,
  anomaly_score, risk, top_features.
- **Phase 3 gate:** normal traffic → suspicious flows → grouped incident →
  explainable incident detail.
- **Phase 4 gate:** different profiles produce different logical test suites.
- **Phase 5 gate:** final system + reproducible evaluation + polished demo.

---

## Validation Commands

Canonical commands, confirmed working 2026-08-09:

```text
# ML / data (Phase 1 — PASS)
python -m pytest ml/tests -q
   -> 13 passed (labels, preprocessing invariants, dev-subset contract,
      sampling reproducibility)

# Baselines (Phase 1 — PASS)
python -m ml.training.train_baseline --experiments random temporal --models lr rf xgb
   -> writes ml/artifacts/baselines/*.joblib and
      ml/evaluation/results/baseline_metrics_{random,temporal}.json

# Inference model export (Phase 1 — PASS)
python -m ml.training.export_inference_model
   -> writes ml/artifacts/inference/{model.joblib,model_metadata.json,feature_order.json}

# Backend (Phase 1 — PASS)
python -m pytest backend/tests -q
   -> 4 passed (health, /api/predict E2E, missing/extra-feature 422s)

# Backend live smoke
python -m uvicorn backend.app.main:app --port 8000
   -> GET  /api/health -> {"status":"ok","model_loaded":true,"feature_count":77}
   -> POST /api/predict -> Phase-1 baseline response (see PHASE_1.md)

# Frontend (Phase 1 — PASS)
npm run build        (frontend/) -> vite build + tsc -b, dist generated

# Full suite (Phase 1 — PASS)
python -m pytest ml/tests backend/tests -q -> 17 passed
```

## Validation Commands — Phase 2 (validated 2026-08-09)

```text
# Hybrid decision unit tests (Phase 2 — PASS)
python -m pytest ml/tests/test_hybrid.py -q
   -> 14 passed (three-outcome boundaries, BENIGN floor, config thresholds,
      anomaly separation, risk monotonicity)

# SHAP local attribution tests (Phase 2 — PASS)
python -m pytest ml/tests/test_shap.py -q
   -> 3 passed (top-5 ordering, feature names, SHAP base/bias verified)

# Full predictor contract tests (Phase 2 — PASS)
python -m pytest ml/tests/test_predictor.py -q
   -> 6 passed (response contract, hybrid consistency, real-row anomaly sep,
      +3 BUG-005 runtime-purity regressions added 2026-08-09)

# Backend Phase-2 contract tests (Phase 2 — PASS)
python -m pytest backend/tests -q
   -> 4 passed (health phase-2, full predict contract incl. top_features,
      missing/extra-feature 422s)

# Full suite (Phase 2 — PASS)
python -m pytest ml/tests backend/tests -q
   -> 43 passed (2026-08-09; was 40, +3 BUG-005 predictor regressions)

# BUG-005 runtime-purity evidence (Phase-2 closure — PASS)
python -m ml.evaluation.record_e2e_evidence
   -> writes ml/evaluation/results/e2e_evidence_phase2.json (6 real held-out
      rows through the FULL Phase-2 pipeline; evaluation_truth_label recorded
      for scoring ONLY, never fed to predict(); PortScan confirmed KNOWN_ATTACK
      MEDIUM(50) at runtime; one real UNKNOWN_SUSPICIOUS benign candidate)

# Anomaly threshold calibration (Phase 2 — PASS)
python -m ml.training.train_isolation_forest
   -> writes ml/artifacts/isolation_forest.joblib + calibration/eval JSON

# Unknown / unseen anomaly experiment (Phase 2 — PASS)
python -m ml.training.run_unknown_experiment
   -> writes ml/evaluation/results/unknown_experiment_temporal.json (honest metrics;
      re-run 2026-08-09 with corrected hybrid rescue semantics)

# IF sensitivity + threshold trade-off audit (Phase-2 closure audit — PASS)
python -m ml.training.if_sensitivity
   -> writes ml/evaluation/results/if_sensitivity.json (4 configs, seed 42,
      same FPR<=5% calibration; deployed config kept — unseen recall within
      0.003 across configs, so the limitation is structural, not a tuning
      artifact)

# Phase-2 live gate (Phase 2 — PASS): uvicorn on 127.0.0.1:8765, real API
# sent real flows; every response carried classification, family, confidence,
# anomaly_score, risk_level, risk_score, top_features (see PHASE_2.md).
```

Phase-1 completion gate evidence (commands + outputs) is recorded in
`docs/PHASES/PHASE_1.md` → "Completion Gate Evidence".

Phase-2 gate evidence (commands + outputs) is recorded in
`docs/PHASES/PHASE_2.md` → "Completion Gate Evidence".

---

## Status Discipline

When reporting, state explicitly:

- which command ran,
- the exact result (pass/fail + key metrics),
- the date,
- any caveats.

A model, endpoint, feature, transformation, metric, or UI component counts as
existing only when its code exists AND (for "validated") its test has passed.

## Validation Commands — Phase 3 (backend engine, validated 2026-08-09)

```text
# Scenario fixture build (one-time; fixtures are committed)
python -m ml.evaluation.build_scenarios
   -> writes data/scenarios/{normal,portscan,dos_or_ddos,unknown}.json

# Incident grouping unit tests (Phase 3 — PASS)
python -m pytest backend/tests/test_incidents.py -q
   -> 16 passed

# Replay engine unit tests (stub predictor, no real time — PASS)
python -m pytest backend/tests/test_replay.py -q
   -> 11 passed

# Replay + incidents API tests (sandbox DB — PASS)
python -m pytest backend/tests/test_replay_api.py -q
   -> 9 passed

# Full suite (Phase 3 — PASS)
python -m pytest ml/tests backend/tests -q
   -> 79 passed (was 43; +36 Phase-3)

# Live Uvicorn E2E gate (Phase 3 — PASS)
python -m backend.tests.e2e_replay_phase3
   -> PASS; writes ml/evaluation/results/e2e_replay_phase3.json
      (portscan replay -> 1 incident; normal replay -> 0 incidents)
```

## Validation Commands — Phase 3 frontend (validated 2026-08-10)

```text
# Frontend build (Phase 3 UI - PASS)
npm run build        (frontend/) -> tsc -b + vite build; dist generated (only a
   chunk-size warning from cytoscape+recharts)

# Full suite (Phase 3 - PASS, now 89)
python -m pytest ml/tests backend/tests -q
   -> 89 passed (50 backend; incl. +2 recent-flows API tests)

# Live gate (Phase 3 UI contract - PASS)
python -m backend.tests.e2e_replay_phase3
   -> PASS; now also asserts GET /api/replay/flows (newest-first, limit 1..500,
      422 on limit 9999)

# Real-browser UI E2E (Phase 3 - PASS, zero console errors)
# headless Edge via CDP against uvicorn:8000 + `npm run dev` (5173, /api proxied)
# 1) monitor renders with health + scenario list
# 2) Start -> real replay -> COMPLETED (dos_or_ddos 8/8 CRITICAL 92.67)
# 3) RUNNING -> PAUSE -> RESUME driven through live buttons
# 4) traffic table fills from /api/replay/flows
# 5) Recharts timeline + risk charts render (4 surfaces)
# 6) Cytoscape canvas paints (3 canvases) and node/edge selection works
# 7) incidents list -> Incident Detail renders SHAP + baseline sections
# Evidence: ui_e2e_report.json / ui_e2e_interactions.json (opencode temp)
```

```text
# Phase 3.5 hardening (2026-08-10 - PASS, now 91)
python -m pytest ml/tests backend/tests -q
   -> 92 passed (52 backend, 40 ml; +1 predictor explain, +1 replay run-scoping,
   +1 replay restart-isolation BUG-012)

# Sequential-run isolation evidence (MIXED -> ISOLATED)
python ml/evaluation/phase35_evidence_before.py  # VERDICT=MIXED (pre-fix, BUG-011)
python ml/evaluation/phase35_evidence_after.py   # VERDICT=ISOLATED (post-fix)
   -> evidence JSONs in ml/evaluation/results/phase35_evidence_{before,after}.json

# Live gate now also asserts sequential-run isolation
python -m backend.tests.e2e_replay_phase3
   -> PASS (incl. portscan -> normal on one server: feed/incidents show only
      the current run; unscoped list keeps history)

# Real-browser sequential replay E2E (Phase 3.5 - PASS, zero console errors)
# headless Edge via CDP: replay PortScan to COMPLETED, then Normal to COMPLETED
# 1) table repaints to Normal-only rows after the second run
# 2) Incidents hub shows 0 (current run has none); prior run incident history intact
# 3) no console errors
```


## Phase-3 Frontend UX Pass — Browser Validation (2026-08-13)

Live browser pass (Vite dev server against live uvicorn backend on :8000):

```text
Normal      : green "No suspicious activity detected"; benign bars visible and
              tiny (Y-axis floored at 1); 0 incidents state. PASS
PortScan    : "Reconnaissance detected" MEDIUM; graph labels readable, no
              collisions; one grouped incident card. PASS
DoS/DDoS    : "Denial of Service detected" CRITICAL; tall red timeline bars. PASS
Unknown     : "Unrecognized suspicious behavior" HIGH; classifier-benign vs
              anomaly-flagged explained in verdict + detail; non-contradictory. PASS
IncidentDetail: hero story block, SHAP "What Influenced the Model Prediction?"
              with model-contribution disclaimer, baseline rows with x-of-normal
              ratios, "Why Was It Flagged as Suspicious?" for UNKNOWN. PASS
Console     : zero app errors across the whole session. PASS
```

Commands: `npm run build` (frontend/); `python -m pytest ml/tests backend/tests -q`
-> 92 passed.

## Approved implementation Batch 8 - 2026-10-31

46 tests PASS: playground_api, playground, replay_api, replay_failures, readiness.
Includes real frozen pipeline, saved-result equality, no Monitor writes, commit
rollback, inference failure, restart interruption, missing coverage and model 503.
Original four-scenario live HTTP gate PASS with temporary evidence output.
No frontend claim until Task 9 browser gate.

## Approved implementation Batch 9 - 2026-10-31

5 frontend Node tests PASS, TypeScript --noEmit --incremental false PASS, Vite build
PASS. Browser: Home and public web different suites; scores/counts match backend;
profile edits clear state; database unsupported; 404 clears old assessment; saved
result reload; missed web prediction and benign anomaly SHAP explanation PASS.
Final clean-session browser/error and full Python regression checks remain Task 10.

## Final approved-scope gate - 2026-10-31 (supersedes prior current counts)

Commands executed using Python3.10.11 and existing installed dependencies:

```text
python -m pytest ml/tests backend/tests -q -p no:cacheprovider --tb=short
142 passed in203.45s (network-enabled pinned dataset checks)
frontend: node --test tests/*.test.mjs ->5 passed
frontend: node node_modules/typescript/bin/tsc --noEmit --incremental false ->PASS
frontend: node node_modules/vite/bin/vite.js build ->PASS (>500kB warning retained)
backend.tests.e2e_replay_phase3.main with temporary OUT ->PASS
```

Initial full run138 passed/1 failed: stale all-fixture detection expectation. Final
parity has explicit original-four16 and all-seven36 checks, keeping both standards.
Added bounded65-flow rejection and saved assessment unchanged under changed weights.
No test was skipped or weakened and no runtime logic changed for this failure.

Fresh live browser: Normal Monitor8 benign/0 incidents; Home2 scenarios no score;
public Web4 scenarios70.83 with12 detected/4 missed/4FP; Lab all7/52 flows78.33 with
36 detected/4 missed/4FP. Actual missed web and benign-anomaly SHAP viewed. Unsupported
database, profile edit invalidation, historical reload,404 no stale assessment,
backend readiness loss (run disabled), recovery and persisted result after process
restart PASS. Monitor afterward retained its normal-only8-flow evidence. Fresh
session console had no errors before intentionally stopping backend; offline network
errors then expected. Default short locator wait expired on full-suite request;
completed assessment was observed on next inspection, no application failure.

Invariant assertions against f84fb71 and original hashes PASS: original4 vectors,
truth/sequence/sidecars, existing config sections, all preprocessing/label/schema,
hybrid/risk/TreeSHAP code, artifact metadata and model bytes unchanged. Only additive
playground weights and threshold-history schema introduced. Git diff --check PASS.
Clean-environment dependency installation and production deployment NOT executed.
