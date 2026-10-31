# Implementation Status

Updated: 2026-10-31. Current phase: Phase 4 approved first version COMPLETE and
VALIDATED within the reviewed scope. Phase 5 remains deferred, not authorized.
Historical detail lives in SPRINT_LOG.md; next-agent orientation in HANDOFF.md.

## Approved milestones

| Milestone | Status | Implemented and validated |
|---|---|---|
| 1 reliability (Tasks 1-3) | COMPLETE | Failed-worker rollback/cleanup, restart synchronization, readiness, run-scoped Monitor, boolean graph selectors, accurate unknown text and recorded threshold evidence |
| 2 evaluation (Tasks 4-6) | COMPLETE | Reporting corrections, identical-cohort frozen comparison, provenance, three small SSH/FTP/web scenario additions |
| 3 Playground backend (Tasks 7-8) | COMPLETE | Strict profiles, deterministic relevance rules, existing SQLite tables, <=64-flow runner, outcome scoring, snapshots, failure/interruption handling |
| 4 Playground UI/final gates (Tasks 9-10) | COMPLETE | Questionnaire, preview/run/retrieve, score/counts/coverage/matrix/risk chart/flow evidence, final regression and invariant checks |

## Validation (executed)

- Full Python: 142 passed in 203.45s; command `python -m pytest ml/tests backend/tests -q -p no:cacheprovider --tb=short`.
- Frontend: 5 Node tests PASS; TypeScript --noEmit --incremental false PASS; Vite production build PASS.
- Original four-scenario real Uvicorn gate with sequential isolation PASS; evidence written to temporary paths to preserve historical artifacts.
- Browser: Home, public Web and all-seven-scenario Lab suites; actual misses/false alerts; profile invalidation; uncovered database; saved ID reload; 404 state; readiness loss/recovery; process-restart persistence; Monitor isolation PASS.
- Fresh browser completed 52-flow suite with no console errors before deliberate backend-offline test.
- Models, original config sections, canonical features/preprocessing/labels, hybrid/risk/SHAP code and original four fixture vectors/sidecars unchanged (asserted against f84fb71 and recorded hashes).
- Initial final run: 138 passed / 1 failed because an all-fixture parity assertion still assumed the original four. Replaced with explicit original-four (16 detections) and seven-fixture (36) checks; no runtime change to satisfy it.

## Current interfaces and evidence

Monitor/prediction/incidents APIs preserve existing fields; nullable anomaly_threshold
is additive and legacy rows stay null. Replay adds FAILED. Health adds readiness/message.
Playground: POST /api/playground/profile, POST /api/playground/run, GET
/api/playground/results/{run_id}. Evidence lives only in playground_* tables.
Seven fixtures / 52 flows, 77 features each. Inference thresholds remain .75 / -.0928.
Readiness weights .5/.5 combine macro attack-scenario recall and benign specificity.
Missing selected scenarios suppress score; attack-free Home suite has no score.
Unsupported services and unknown-attack coverage stay explicit.

## Retained limitations

- Small fixtures are demonstrations. Legacy PortScan 5/8 and DoS/DDoS 1/8 vectors
  match training features; original source-row identity cannot be recovered.
- Unknown fixture contains benign anomaly false alerts, not unknown attacks.
- New web fixture retains 4/8 misses. Tiny class support limits interpretation.
- Locked reused random cohort (282788): hybrid FPR .023136, only 2 additional
  malicious rescues and 5011 additional benign alerts versus confidence gate.
- Historical test reuse and weak temporal generalization remain disclosed.
- Single-process local SQLite and bounded synchronous Playground execution; permanent
  database failure can prevent durable failure evidence. Replay failures preserve
  committed rows and may leave incident end markers unset on finalization failure.
- Graph poll relayout polish and >500kB production bundle warning remain deferred.
- Fresh clone needs the existing supervised artifact supplied/regenerated separately;
  no model was retrained, replaced or added during this work.

Live capture, mitigation, drift, external alerting, enterprise deployment, advanced
threat intelligence, extra datasets/models, zero-day research, full Model Lab,
expanded investigation and optional PDF export remain future work.
