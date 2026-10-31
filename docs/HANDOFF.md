## Latest: Milestone 1 complete (2026-10-31)

Tasks 1-3 tested in focused batches; models/config unchanged. Current next task:
Milestone 2 evaluation reporting, shared-cohort comparison, scenario provenance.
Playground still NOT STARTED. Batch 3: 69 Python checks, 4 Node tests, TS/build
and real replay gate PASS; browser red edges and UNKNOWN/detail semantics PASS.
See latest sprint entry; no push until full scope passes.

# Latest batch: Task 2 complete (2026-10-31)

Readiness + run-scoped UI: 32 focused tests PASS, TS/build PASS, browser missing
models, sequential runs, delayed old response, restart/history and FAILED/recovery
PASS. Next: Task 3 graph/semantics. Do not redo Tasks 1-2; models unchanged.

# HANDOFF.md — Current Operational Handoff

Current operational handoff, refreshed continuously. Permanent history lives
in `SPRINT_LOG.md`. Tell the next agent what it needs without making it
rebuild the whole session.

---

## Current implementation authorization - 2026-10-31

User approved actual implementation in tested, focused batches and local commits.
Existing branch main; origin https://github.com/Satvik-19/network_ids.git;
configured human identity Satvik-19. Do not add agent attribution. Push only when
all approved scope and final checks pass; never force push or rewrite history.
Pre-existing untracked .freebuff/ and shot1_setup.png/shot2_normal.png/
shot3_portscan_monitor.png must remain untouched/uncommitted.

Task 1 changes: terminal FAILED, rollback/cleanup, committed counters, restart
worker guard, API error distinctions, shutdown hook. Targeted 62 passed and real
four-scenario live gate PASS; network-enabled full suite passed (106 tests in 250.99s). See new backend/tests/test_replay_failures.py.
Next batches: readiness/current-run UI, graph/semantics, reporting/evaluation,
scenario provenance + at most SSH/FTP/web fixtures, Playground rules/backend,
Playground UI and final gates. No retraining or threshold/model/risk changes.
Previous historical freeze instructions below are superseded by user authorization.

## Most Recent Task

**Phase-3 frontend UX pass — recovery reconciliation + completion (2026-08-13):
recovery audit found the Phase-3 UX largely already in place and KEPT it;
surgically fixed residual defects (header dev-copy, duplicated anomaly
threshold, invisible benign timeline bars, missing risk empty state, baseline
p25-p75 semantics, BUG-013 blank graph on load). `npm run build` PASS; full
suite 92 passed (frozen baseline); browser-tested Normal / PortScan / DoS /
Unknown / Incident Detail / Incidents hub with zero console errors. Phase 3
remains FROZEN; Phase 4 NOT authorized.**

- Recovery method: no git history in this workspace -> audited current files +
  rendered UI only (brief §2 classification). Prior-agent attribution skipped
  by design.
- KEPT as-is: shell/nav, SecurityStatus verdict, UNKNOWN explanation blocks,
  incident cards/detail, SHAP wording, tables, scenario labels.
- Fixed: `App.tsx` header ("System ready"), `ui.tsx` shared
  `ANOMALY_THRESHOLD`/`isAnomalyFlagged()`, `AttackTimeline.tsx` benign bar +
  floored Y-axis, `RiskDistribution.tsx` empty state, `IncidentDetail.tsx`
  baseline band semantics, `CommGraph.tsx` `cy.resize()` (BUG-013).
- Backend/ML untouched (no integration bug found). BUG-013 logged FIXED.

**Phase-3.5 hardening & freeze (2026-08-10): sequential-replay isolation audit;
fixed BUG-010 (single-pass replay SHAP) + BUG-011 (run-scoped Monitor feed/incidents);
before/after evidence recorded; full gates re-run. Backend 52 tests PASS; full suite 92
passed (stable x2); live uvicorn E2E gate PASS (incl. sequential-run isolation); `npm run build`
PASS; real-browser (headless Edge CDP) sequential replay E2E PASS with zero console
errors. Phase 3 FROZEN.**

- Demonstrated defect before fix: after PortScan -> COMPLETED -> Normal ->
  COMPLETED on one server, `GET /api/replay/flows` still returned 8 stale
  PortScan rows and `GET /api/incidents` still listed the PortScan incident
  though the current run had none (evidence
  `ml/evaluation/results/phase35_evidence_before.json`, VERDICT=MIXED).
- BUG-010: `_predict_one` ran the full Phase-2 pipeline twice per suspicious
  flow (`predict` without SHAP then `predict` with SHAP). Fixed via new
  `Phase2Predictor.explain(features)` — SHAP-only single pass, identical SHAP
  block to the `with_shap=True` path. Regressions: `test_explain_matches_predict_shap`
  + truth-isolation counts updated (12 predict + 12 explain; canonical keys only).
- BUG-011: `ReplayService` now stamps every persisted `Prediction`/`Incident`
  row with a per-run `run_id` (uuid hex; additive columns + migration).
  `GET /api/replay/flows?run_id=` and `GET /api/incidents?run_id=` scope to a
  run; SecurityMonitor passes `status.run_id`; Incidents page omits it (full
  history). Post-fix evidence `ml/evaluation/results/phase35_evidence_after.json`
  = VERDICT=ISOLATED; pytest `test_run_scoped_flows_and_incidents_isolate_sequential_runs`;
  live gate block; headless-browser sequential replay (table repaints to
  Normal-only rows; Incidents (0); zero console errors).
- Decisions DEC-015 (run-scoping) / DEC-016 (single-pass explain). Bugs logged
  BUG-010 / BUG-011 / BUG-012 (FIXED). BUG-012: stop() while a flow was
  mid-predict could let an immediate start() race the still-draining worker
  (restart now joins the stale thread). Test counts 89 -> 92 (+3 new); no failures.

**Phase-3 frontend closure (2026-08-10): Security Monitor, Cytoscape communication graph, Incident Detail, Incidents hub + Predict tab; full Phase-3 gate CLOSED. Backend 50 tests PASS; full suite 89 passed; live uvicorn E2E gate PASS (incl. recent-flows feed); `npm run build` PASS; real-browser (headless Edge CDP) UI E2E PASS with zero console errors.**

- Frontend built on the real replay/incident APIs: `SecurityMonitor` (replay controls -> status pump, summary cards, attack timeline + risk distribution (Recharts), live traffic table from new `GET /api/replay/flows`, Cytoscape communication graph, incident list), `IncidentDetail` (summary, evidence table, SHAP top features, behaviour-vs-baseline vs `/api/baselines/benign`, incident graph), `IncidentsPage` hub, Predict demo tab.
- New backend contract (small, justified gap): `GET /api/replay/flows` serves newest-first persisted replay EvidenceFeed rows for the live traffic table; `ReplayFlowOut/ReplayFlowsOut` schemas; `Prediction` side-car columns (source, destination, service_port, seq, replay_time) populated by `_persist`.
- Real-browser validation via headless Edge CDP: monitor renders, Start -> real replay completes, RUNNING/PAUSE/RESUME driven through live buttons, traffic table fills from the feed, timeline/risk charts render, Cytoscape canvas paints, incidents list -> detail renders SHAP + baseline. Zero console errors.
- Bug found and fixed during live E2E: BUG-009 — Cytoscape never initialised because the mount-only effect ran while the empty-state placeholder rendered (no ref container existed); fix = always-mounted container + overlay message.

**Phase-3 backend hardening (2026-08-10): incident boundary determinism, enriched incident-detail contract, live E2E gate extended to dos_or_ddos + unknown + benign baselines. 44 backend tests PASS; full suite 87 passed; live uvicorn gate PASS.** [prior entry — replaced by the Phase-3 frontend closure above]

- A4: `test_window_boundary_delta_equals_window_still_joins` pins the INCLUSIVE grouping window rule.
- A5: incident detail now exposes anomaly_score + top_features + baseline_features per flow and summary confidence; new `GET /api/baselines/benign` endpoint feeds the behaviour-vs-normal comparison (`test_incident_detail_enriched_from_prediction`, `test_benign_baselines_endpoint`).
- A6: replay determinism tests corrected (SHAP second-pass accounting; restart test pacing).
- A3: `e2e_replay_phase3.py` now also proves dos_or_ddos grouping into a CRITICAL DoS incident and the unknown anomaly branch; evidence in `ml/evaluation/results/e2e_replay_phase3.json`.

**Phase 3 backend engine (2026-08-09): replay engine + deterministic incident
grouping + REST API + 36 tests + live Uvicorn E2E gate — all VALIDATED.**

- Scenario fixtures: `data/scenarios/{normal,portscan,dos_or_ddos,unknown}.json`
  (schema `scenario/v1`), built ONCE from real held-out random_3way/test rows
  via the SHARED Phase-2 predictor (`ml/evaluation/build_scenarios.py`).
  `features` = the 77 canonical model inputs; source/destination/service_port
  are SYNTHETIC side-car replay metadata (never model features — BUG-005
  purity holds); ground_truth_label is an evaluation note only.
- Replay service: `backend/app/services/replay.py` — in-process daemon worker
  thread, IDLE/RUNNING/PAUSED/COMPLETED/STOPPED, start rejects concurrent runs,
  speeds {1,5,20} (pacing only, injectable sleep for tests), exact scenario
  seq order, synthetic replay time = base + seq*interval.
- Incident grouping: `backend/app/services/incidents.py` — rule-based, window
  from config; service_port discriminant excluded for scanning families so a
  multi-port PortScan is ONE incident.
- API: `api/{replay,incidents}.py` + schemas; main.py now 0.3.0.
- DB: additive `ALTER TABLE ADD COLUMN` migration
  (`database.py::_migrate_schema`); `NETWORK_IDS_DB` env override lets tests
  sandbox the engine.

## Current Phase

**Phase 3 — FROZEN / COMPLETE / VALIDATED (2026-08-10).** Backend engine
COMPLETE + VALIDATED 2026-08-09; Phase-3 UI COMPLETE + VALIDATED 2026-08-10;
Phase-3.5 hardening + freeze 2026-08-10 (BUG-010 single-pass replay SHAP,
BUG-011 run-scoped Monitor isolation, BUG-012 restart-thread race; full gates
re-run, 92 passed, stable x2). Phase 3 is
FROZEN; Phase 4 (Playground) NOT authorized — do not start it.

## Current Repository State

- **ML (unchanged, Phase 2 frozen):** hybrid decision, risk, native TreeSHAP,
  final supervised + IF artifacts. Do NOT retrain or re-pick models.
- **Backend (Phase 3 backend):**
  - `backend/app/services/{incidents,replay,scenarios}.py` — engine + grouping.
  - `backend/app/api/{replay,incidents}.py`, `backend/app/schemas/{replay,incidents}.py`.
  - `backend/app/db/models.py` (Phase-3 columns), `database.py` (additive
    migration, env DB override), `main.py` 0.3.0.
  - `data/scenarios/*.json` — committed deterministic fixtures.
  - `backend/app/api/replay.py` — `GET /api/replay/flows` (recent-flows live feed).
  - Run-scoping: `Prediction`/`Incident` rows carry `run_id`; `?run_id=` filters on flows + incidents (DEC-015). `Phase2Predictor.explain(features)` = single-pass SHAP (DEC-016 / BUG-010).
- **Frontend (Phase 3, complete 2026-08-10):**
  - `frontend/src/api/{types,client,usePolling}.ts` — typed contract + polling hook.
  - `frontend/src/pages/{SecurityMonitor,IncidentDetail,IncidentsPage}.tsx` + `App.tsx` (useState nav, no router).
  - `frontend/src/components/{ReplayControls,SummaryCards,TrafficTable,AttackTimeline,RiskDistribution,CommGraph,IncidentList,ui}.tsx`.
  - `frontend/src/lib/graph.ts` — replay/incident flows -> cytoscape elements.
  - Deps added: `recharts@3.10.1`, `cytoscape@3.34.0`, `@types/cytoscape@3.21.9`.
- **Tests:** `backend/tests/test_incidents.py` (17), `test_replay.py` (17),
  `test_replay_api.py` (14 incl. run-scoping isolation), `e2e_replay_phase3.py`
  (live gate, incl. recent-flows + sequential isolation), `conftest.py` (sandbox
  DB), plus existing. Full suite 92 passed.
- **Evidence:** `ml/evaluation/results/e2e_replay_phase3.json`,
  `phase35_evidence_before.json`, `phase35_evidence_after.json`.
- **Config:** `replay.speeds {1,5,20}`, `replay.default_speed 5`,
  `incidents.grouping_window_seconds 30` (placeholder).

## What Is Complete (and how verified)

- Replay engine + states + speeds — `backend/tests/test_replay.py` (16 PASS),
  live uvicorn gate PASS.
- Incident grouping rules — `backend/tests/test_incidents.py` (16 PASS).
- API contract (scenarios/start/pause/resume/stop/status, incident list/
  detail, recent flows feed, run-scoped `?run_id=` filters) —
  `backend/tests/test_replay_api.py` (14 PASS).
- Live Uvicorn E2E: portscan replay COMPLETED 8/8 -> 1 incident
  (flow_count 8, KNOWN_ATTACK/Recon/MEDIUM 50); incident detail returned 8
  persisted flows with prediction_id + synthetic replay_time + source
  10.0.0.50; normal replay 0 incidents; 404/422 on live server.
- Full suite `python -m pytest ml/tests backend/tests -q` -> 92 passed (52 backend, 40 ml), stable x2.
- live uvicorn gate (2026-08-10) -> PASS incl. dos_or_ddos (CRITICAL, risk 92.67), unknown (4 UNKNOWN_SUSPICIOUS -> 1 incident), and recent-flows feed contract.
- Frontend `npm run build` -> PASS (tsc -b + vite build; only a bundle-size warning from cytoscape+recharts).
- Real-browser UI E2E (headless Edge CDP, 2026-08-10) -> PASS, zero console errors: monitor renders; Start drives a real replay to COMPLETED; RUNNING/PAUSE/RESUME verified via live buttons; traffic table fills from /api/replay/flows; timeline + risk charts (Recharts) render; cytoscape canvas paints (3 canvases); incidents list -> detail renders SHAP + baseline sections.
- Phase-3.5 hardening: single-pass replay SHAP (BUG-010, `explain()` matches `predict(with_shap=True)`); run-scoped Monitor isolation (BUG-011); sequential before/after evidence (VERDICT MIXED -> ISOLATED); BUG-012 restart joins the stale worker thread; live gate + headless-browser sequential E2E re-run PASS, zero console errors.

## What Remains

**Nothing in Phase 3** — all Phase-3 scope is complete, validated and
FROZEN (2026-08-10). Phase 4 (Security Playground) and Phase 5 (Model Lab UI)
are NOT authorized; stop unless explicitly asked to investigate a Phase-3
defect.

## Important Files

- `docs/DECISIONS.md` DEC-011/012/013 (scenario fixtures, grouping key, replay
  engine), DEC-015 (run-scoping), DEC-016 (single-pass explain).
  `docs/PHASES/PHASE_3.md` — backend evidence + Phase-3.5 hardening recorded.
- `docs/BUG_LOG.md` BUG-008 (normal fixture anomaly leak, fixed), BUG-010
  (single-pass replay SHAP, fixed), BUG-011 (run-scoped Monitor isolation, fixed).
- `config/config.yaml`, `data/scenarios/*.json`,
  `ml/evaluation/results/e2e_replay_phase3.json`,
  `phase35_evidence_before.json`, `phase35_evidence_after.json`.

## Latest Test Result

`python -m pytest ml/tests backend/tests -q` -> **92 passed** (2026-08-10;
52 backend, 40 ml), stable x2. Live uvicorn Phase-3 gate -> **PASS** (incl. recent-flows
feed + sequential-run isolation). Frontend `npm run build` -> **PASS**.
Real-browser UI E2E (headless Edge CDP) -> **PASS, zero console errors**, incl.
sequential replay isolation (table repaints to current-run rows).

## Known Limitations / Blocker

- Phase-2 structured limitation carried forward: benign-only IF flags a small
  share of benign flows as UNKNOWN_SUSPICIOUS (normal scenario selects
  strictly-BENIGN rows so the profile plays clean).
- Frontend: Vite build warns the bundle is >500 kB (cytoscape + recharts) — not
  a defect at this scale; code-splitting is optional Phase-4+ polish.
- BUG-009 fixed during live-browser E2E (Cytoscape init lifetime); regression
  covered by the always-mounted container + re-run E2E.

## Implementation Assumptions (locked, do not re-derive)

- Dataset revision `d071fd53782d9ca7cdc15173b8ceb858fea04628`; 15 classes;
  77 canonical features; order = `feature_schema.json`.
- Random/temporal distinct experiments; RF/XGBoost/IF no scaling.
- Use pyenv Python `C:\Users\BIT\.pyenv\pyenv-win\versions\3.10.11\python.exe`;
  PATH `python` lacks xgboost/datasets/pyarrow.
- Scenario metadata (source/destination/port) is SYNTHETIC side-car; never a
  model feature.
- Replay timestamp is synthetic (base + seq*interval) — never original time.

## Next Agent instructions

1. Read AGENTS.md, the PRD, `docs/IMPLEMENTATION_STATUS.md`, `PHASE_3.md`,
   `DECISIONS.md` (DEC-011-016), `BUG_LOG.md` (BUG-008, BUG-010, BUG-011, BUG-012),
   this handoff.
2. Phase 3 is COMPLETE, VALIDATED and FROZEN (2026-08-10). Phase 4/5 NOT
   authorized. If a Phase-3 defect appears, re-run:
   `python -m pytest ml/tests backend/tests -q`,
   `python -m backend.tests.e2e_replay_phase3`, `npm run build` (frontend/),
   and a headless-browser pass (incl. a sequential two-scenario replay to
   confirm run isolation). Then capture evidence. Do not start Phase 4.
3. Run the UI: uvicorn on 127.0.0.1:8000 via pyenv Python, `npm run dev` in
   frontend/ (Vite proxies /api -> backend). The CommGraph container is
   always mounted so Cytoscape initialises even with zero flows (BUG-009).
4. Any governance write MUST use the UTF-8 atomic rule (AGENTS.md §2). Verify
   by re-read that no mangled signs exist.
5. Phase 2 is FROZEN — do not retrain or re-pick models.
