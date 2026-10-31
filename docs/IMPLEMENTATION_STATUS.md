## Latest: Milestone 1 complete (2026-10-31)

Tasks 1-3 tested in focused batches; models/config unchanged. Current next task:
Milestone 2 evaluation reporting, shared-cohort comparison, scenario provenance.
Playground still NOT STARTED. Batch 3: 69 Python checks, 4 Node tests, TS/build
and real replay gate PASS; browser red edges and UNKNOWN/detail semantics PASS.
See latest sprint entry; no push until full scope passes.

# IMPLEMENTATION_STATUS.md — What Actually Exists Right Now

This file answers, in under a few minutes: **what actually exists right now?**

It is continuously refreshed. Do not mark functionality VALIDATED unless its
tests/validation were actually run.

Legend: `NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `IMPLEMENTED` | `VALIDATED`

---

## Component Status

| Component | Status | Phase | Key Files | Tests | Notes |
|---|---|---|---|---|---|
| PRD | VALIDATED (read) | — | `Network_IDS_Security_Evaluation_PRD.md` | — | Read fully during bootstrap |
| Agent governance docs | VALIDATED | — | `AGENTS.md`, `docs/*` | — | Created during bootstrap; corrected 2026-08-09; SPRINT_LOG encoding normalised to UTF-8 (BUG-003 FIXED); 4 entries recovered after append-write truncation (BUG-004 FIXED) |
| Repo structure (PRD §55) | IMPLEMENTED | 1 | `backend/`, `ml/`, `data/`, `config/` | — | Dirs scaffolded |
| Python env + deps | VALIDATED | 1 | `requirements-lock.txt` | imports verified | pyenv 3.10.11 env fully working; lock file generated 2026-08-09 |
| Project config | IMPLEMENTED | 1 | `config/config.yaml` | — | Threshold placeholders; dataset revision pinned |
| Dataset inspection (HF) | VALIDATED | 1 | `ml/preprocessing/inspect_dataset.py` | ran; JSON written | Revision/configs/splits/counts/schema/labels/temporal mechanism all verified |
| Dataset loader (CICIDS2017 / HF) | VALIDATED | 1 | `ml/preprocessing/dataset.py` | loader smoke tests PASS | Reads parquet via `hf://`, revision-locked, optional column projection; docstring corrected (HF quirk, not bug) |
| Label mapping (15 classes) | VALIDATED | 1 | `ml/preprocessing/labels.py` | pytest PASS | Canonical labels, U+FFFD→hyphen, family map, int encoding |
| Preprocessing pipeline | VALIDATED | 1 | `ml/preprocessing/preprocess.py` | pytest PASS | Duplicate col dropped, non-finite safety net, canonical ordering, LR scaler train-only |
| Feature schema | VALIDATED | 1 | `ml/artifacts/feature_schema.json` | pytest PASS | 77 features, version 1.0, dropped_features recorded |
| Development subset | VALIDATED | 1 | `ml/preprocessing/subset.py`, `data/processed/dev_{random,temporal}_train.parquet` | pytest PASS + meta.json | 300k each, seed 42, all classes retained, counts recorded |
| Logistic Regression baseline | IMPLEMENTED | 1 | `ml/training/train_baseline.py` | metrics written | binary+multiclass, random+temporal, scaled train-only |
| Random Forest (initial) | IMPLEMENTED | 1 | `ml/training/train_baseline.py` | metrics written | binary+multiclass, random+temporal, no scaling |
| XGBoost (initial) | IMPLEMENTED | 1 | `ml/training/train_baseline.py` | metrics written | binary+multiclass, random+temporal, no scaling |
| Binary + multiclass evaluation | IMPLEMENTED | 1 | `ml/evaluation/metrics.py`, `ml/evaluation/results/*.json` | pytest PASS | acc/F1/AUC/per-class/confusion; random vs temporal distinct |
| Inference model (Phase-1 API) | VALIDATED | 1 | `ml/artifacts/inference/*` | pytest PASS | XGB multiclass random promoted; 99.8% top-1 agreement |
| FastAPI skeleton | VALIDATED | 1 | `backend/app/main.py` | pytest PASS | `/api/predict` + `/api/health`; no auth |
| SQLite schema | VALIDATED | 1 | `backend/app/db/models.py` | pytest PASS | All 6 PRD §41 tables created; predictions persisted |
| Shared schemas | VALIDATED | 1 | `backend/app/schemas/predict.py` | pytest PASS | Phase-1 baseline response only |
| React/Vite frontend skeleton | VALIDATED | 1 | `frontend/` | `npm run build` PASS | React+TS+Vite+Tailwind; nav shell + predict demo |
| Phase-1 completion gate | VALIDATED | 1 | — | E2E run PASS | load→preprocess→train→/api/predict (see PHASE_1.md) |
| Final supervised model | VALIDATED | 2 | `ml/training/train_final_supervised.py`, `ml/artifacts/supervised_model.joblib` | pytest + metrics JSON | xgb_200 chosen; random/test macro-F1 0.8898, weighted-F1 0.9988, acc 0.9987 |
| Isolation Forest | VALIDATED | 2 | `ml/training/train_isolation_forest.py`, `ml/artifacts/isolation_forest.joblib` | pytest + calibration JSON | Fit on 88,314 benign rows; threshold -0.0928 (FPR<=5%); random/test F1 0.4261 / FPR 0.0221 |
| IF sensitivity audit | VALIDATED | 2 | `ml/training/if_sensitivity.py`, `ml/evaluation/results/if_sensitivity.json` | ran; JSON written | 4 configs, seed 42, same FPR<=5% calibration; deployed config kept (unseen recall 0.1685-0.1716; limitation structural, not a tuning artifact) |
| Unknown/unseen anomaly experiment | VALIDATED | 2 | `ml/training/run_unknown_experiment.py`, `ml/evaluation/results/unknown_experiment_temporal.json` | ran; JSON written | temporal Option B (Friday-only unseen classes); honest metrics at FPR<=5%; re-run 2026-08-09 with corrected hybrid rescue semantics (BUG-007); rescue-summary derived in `ml/evaluation/results/unknown_rescue_summary.json` (A3) |
| Hybrid decision layer | VALIDATED | 2 | `ml/hybrid/decision.py` | pytest (15 total hybrid) | Deterministic, config-driven thresholds (0.75 / -0.0928); anomaly rescue not gated on confidence (BUG-007 FIXED) |
| Risk engine | VALIDATED | 2 | `ml/hybrid/risk.py` | pytest | Transparent formula; LOW/MEDIUM/HIGH/CRITICAL; BENIGN floor to LOW |
| SHAP local explanations | VALIDATED | 2 | `ml/hybrid/shap_explainer.py` | pytest (5) | Native TreeSHAP (pred_contribs), top-5 per flow; additivity + predicted-class ranking tests added (2026-08-09) |
| Benign baselines | VALIDATED | 2 | `ml/hybrid/baselines.py`, `ml/artifacts/benign_baselines.json` | pytest — | median/mean/p25/p75/std for 10 config-listed features |
| Replay engine (backend, in-process) | VALIDATED | 3 | `backend/app/services/replay.py`, `data/scenarios/*.json` | `backend/tests/test_replay.py` (17) | In-process worker thread; IDLE/RUNNING/PAUSED/COMPLETED/STOPPED; speeds 1/5/20; synthetic replay timestamp incl. per-flow side-car (source/dest/port/seq/time); shared Phase-2 predictor with single-pass SHAP on suspicious flows via explain() (BUG-010/DEC-016); per-run run_id evidence scoping (BUG-011/DEC-015); restart joins stale worker thread (BUG-012); E2E gate PASS |
| Incident grouping (backend, rule-based) | VALIDATED | 3 | `backend/app/services/incidents.py` | `backend/tests/test_incidents.py` (17) | Deterministic rules; window from config; port excluded for scanning families; aggregates persisted |
| Replay + incidents REST API | VALIDATED | 3 | `backend/app/api/{replay,incidents}.py`, `backend/app/schemas/{replay,incidents}.py` | `backend/tests/test_replay_api.py` (14 incl. benign baselines + recent flows + run-scoping) | scenarios/start/pause/resume/stop/status + incident list/detail + `?run_id=` scoped flows/incidents (DEC-015) |
| Security Monitor UI | VALIDATED | 3 | `frontend/src/pages/SecurityMonitor.tsx` | `npm run build` PASS + headless-CD UI E2E PASS | Summary cards, replay controls, live traffic table, risk/attack charts, incident list; 2026-08-13 UX pass: product-purpose shell, runtime verdict, benign-bar timeline, floored Y-axis, risk empty state |
| Communication graph (Cytoscape.js) | VALIDATED | 3 | `frontend/src/components/CommGraph.tsx` | CDP E2E PASS (canvas renders; node/edge selection) | Real replay evidence only; nodes = hosts + service-port nodes; edges = observed communications (NOT topology) |
| Incident Detail UI | VALIDATED | 3 | `frontend/src/pages/IncidentDetail.tsx` | CDP E2E PASS (SHAP + baseline blocks render) | Summary, evidence table, SHAP top features, behaviour-vs-baseline, incident graph; 2026-08-13 UX pass: baseline p25–p75 band semantics |
| Recent-flows live feed contract | VALIDATED | 3 | `backend/app/api/replay.py` (`GET /api/replay/flows`) | `test_replay_api.py` (14) + extended live E2E gate | Newest-first persisted replay rows; limit 1..500 default 50; `run_id` scoping isolates sequential runs (BUG-011, DEC-015); drives the live traffic table |
| Monitor run-scoping (Phase-3.5 hardening) | VALIDATED | 3 | `backend/app/services/replay.py`, `api/{replay,incidents}.py`, `SecurityMonitor.tsx` | `test_replay_api.py` (+1) + live E2E gate + CDP sequential browser E2E | Sequential replays show ONLY current-run evidence on the Monitor; Incidents page keeps full history; single-pass replay SHAP `explain()` (BUG-010, DEC-016) |
| Security Playground | NOT STARTED | 4 | — | — | — |
| Model Evaluation Lab UI | NOT STARTED | 5 | — | — | — |
| App Security Quick Check (stretch) | NOT STARTED | 5+ | — | — | Optional; blocked behind core completion gates |

---

## Phase Snapshot

```text
Current Phase:              3 — Monitor, Incidents and Visual Intelligence
Current Phase Status:       PHASE 3 FROZEN — engine + UI COMPLETE + VALIDATED (2026-08-10);
                            Phase-3.5 hardening 2026-08-10: single-pass replay SHAP
                            (BUG-010) + run-scoped Monitor isolation (BUG-011) fixed.
                            2026-08-13: frontend UX pass recovery reconciliation —
                            audit kept existing UX, fixed residual defects (header
                            dev-copy, shared anomaly threshold, benign timeline bars,
                            risk empty state, baseline band semantics, BUG-013 blank
                            graph on load). Re-validated: build PASS, 92 tests PASS,
                            browser pass over all 4 scenarios + detail, zero console
                            errors.
Gate Status:                Phase 2 CLOSED (2026-08-09). Phase 3 gate CLOSED + FROZEN
                            (2026-08-10): normal -> suspicious -> grouped incident ->
                            explainable incident detail, verified through the real API +
                            UI; Phase-3.5 audit found + fixed BUG-010/BUG-011;
                            2026-08-13 UX pass gate PASS (see PHASE_3.md).
Current Blockers:           None.
Next Recommended Task:      Phase 4 (Playground) — NOT authorized until requested.
                            Phase 3 is frozen; continue only if a Phase-3 defect appears.
Last Updated:               2026-08-13 (Phase-3 frontend UX pass completed + validated)
```

## Notes

- Phase-3 frontend UX pass (2026-08-13): recovery audit (no git history;
  current files + rendered UI as source of truth) kept the existing shell,
  verdict, incident and SHAP surfaces; fixed header dev-copy, duplicated
  anomaly threshold, invisible benign timeline bars, missing risk empty state,
  baseline p25–p75 semantics and BUG-013 (blank graph on load). Re-validation:
  `npm run build` PASS; 92 Python tests PASS; browser-tested Normal/PortScan/
  DoS/Unknown/Incident Detail with zero console errors.
- Phase 1 is complete and validated: dataset loading, preprocessing, feature
  schema, class-aware dev subsets, LR/RF/XGBoost baselines (binary +
  multiclass, random + temporal), FastAPI + SQLite + React/Vite skeletons,
  and the end-to-end prediction gate all have running tests / evidence.
- Phase-2 audit (2026-08-09): full suite `python -m pytest ml/tests backend/tests -q` = 37 passed; live E2E gate on real uvicorn (:8765) returned the full Phase-2 contract (classification, family, confidence, anomaly_score, risk, top_features) for benign, DoS H2, SSH-Patator, PortScan and DDoS flows.
- Phase-3.5 hardening + freeze (2026-08-10): BUG-010 (single-pass replay SHAP) and BUG-011 (run-scoped Monitor isolation) fixed; full suite re-run -> 92 passed (stable x2); BUG-012 restart-thread race fixed; live E2E gate incl. sequential-run isolation PASS; headless-browser sequential replay E2E PASS, zero console errors. See DECISIONS.md DEC-015/016, BUG_LOG.md BUG-010/011.
- Phase-2 closure audit (2026-08-09): full suite now 40 passed (+1 hybrid rescue regression, +2 SHAP additivity/ranking); hybrid rescue semantics fixed (BUG-007) and unknown experiment re-run; TreeSHAP additivity verified for all 15 classes; IF sensitivity experiment (if_sensitivity.json) shows the low unseen recall is structural; live E2E re-run on :8765 PASS.
- BUG-005 closure (2026-08-09): permanent runtime-purity regression tests added to `ml/tests/test_predictor.py` (now 6 tests; suite 43 passed total); rescue-summary scorecard `ml/evaluation/results/unknown_rescue_summary.json` (A3) and end-to-end real-inference evidence `ml/evaluation/results/e2e_evidence_phase2.json` (A4, 6 records) written. Full suite `python -m pytest ml/tests backend/tests -q` = 43 passed.
- Phase-2 truthful limitation recorded in HANDOFF/BUG_LOG: the benign-only Isolation Forest has low anomaly recall for feature-structurally-benign flows (PortScan 0.002 flagged, FTP/SSH-Patator 0.000); temporal-unseen recall 0.075 at FPR<=5%.
- Phase-3 frontend (2026-08-10): Security Monitor, Communication Graph (Cytoscape), Incident Detail, Incidents hub + Predict tabs built with typed API client (`frontend/src/api/client.ts`), polling hook, Recharts timeline/risk charts, reusable `CommGraph` + `lib/graph.ts` data builders. One bug found during live-browser E2E (BUG-009, Cytoscape never initialised while the list was empty: mount-only effect ran before the ref container existed) — fixed and re-verified.
- See `docs/PHASES/PHASE_2.md`, `docs/DECISIONS.md` DEC-007…DEC-010, and `docs/HANDOFF.md` for commands/metrics. Phase-1 audit (2026-08-09): re-ran all ML/backend tests (17 passed),
  frontend build (PASS), live E2E predict (200, correct label, persisted),
  temporal-leakage check (dev_temporal_train has only the 12 Mon–Thu
  classes; NO Bot/DDoS/PortScan), feature-order cross-check (77 features,
  identical across schema/artifacts/API), metrics completeness, and
  artifact provisional-marking. All 8 audit checks pass.
- See `docs/PHASES/PHASE_1.md` (Completion Gate Evidence) and
  `docs/HANDOFF.md` for the exact commands and results.
- Phase-3 UI (Security Monitor, Communication Graph, Incident Detail) is now
  complete and validated (2026-08-10). Playground (Phase 4) and Model Lab UI
  (Phase 5) remain pending by design — Phase 4/5 not authorized.


## Current authorized work - 2026-10-31 (supersedes prior freeze instructions)

The reviewed implementation plan is approved. Active work: Milestone 1, Task 1
replay lifecycle; implemented and targeted/live-gate tested (62 related passes).
Full regression: 106 passed in 250.99s with network access. Next: Task 2 readiness
and frontend run state, only after Task 1 checks. Playground remains NOT STARTED,
but is authorized after prerequisite gates. Phase 5 expansions remain deferred.

## Latest batch - 2026-10-31

Task 1 complete (commit 9a01453; full suite 106 passed plus final targeted 16).
Task 2 readiness/run-scoped UI complete: 32 focused passes, TS/build and browser
regressions passed. Current task next: Milestone 1 Task 3. Playground NOT STARTED.

## Latest: Milestone 2 Task 4 complete - 2026-10-31

Current evaluation reporting reconciled against scripts/JSON; numeric checks passed.
Historical evidence retained. Next: Task 5 same-cohort locked-model evaluation.

## Latest: Milestone 2 Task 5 complete - 2026-10-31

Shared-cohort locked-artifact report generated and tested (21 related passes).
Current next Task 6 provenance and small scenario additions. Playground not started.

## Latest: Milestones 1-2 complete - 2026-10-31

Task 6 passed 57 focused tests, preparation/repeatability checks and the original
live gate. Seven fixture types, 52 records; 4 web misses kept. Next: approved
Phase-4 Playground profile/rule implementation. Playground not implemented yet.

## Latest: Phase 4 profile backend implemented - 2026-10-31

Task 7 passed 30 related tests. Profiles persist and preview deterministic suites.
Playground execution, readiness assessment and UI still pending (Task 8 next).

## Latest batch - 2026-10-31 Task 8

Milestone 3 complete: profile preview/save, bounded runner, persisted assessments,
failure/restart recovery and historical retrieval. 46 related tests + original
replay HTTP gate PASS. Phase 4 active; frontend/final gates remain. No push yet.
