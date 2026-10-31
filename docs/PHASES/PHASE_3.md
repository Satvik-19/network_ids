# Phase 3 — Monitor, Incidents and Visual Intelligence

Source: PRD §58 (Phase 3), §7, §14–17, §42. Active only after Phase 2 gate
passes.

## Goal

Turn the ML pipeline into an understandable, visual monitoring experience:
replay engine, incident grouping, Security Monitor, network graph, and
Incident Detail.

## PRD Scope

**Replay (PRD §7, §42):**
- Deterministic dataset-flow replay through the full pipeline.
- Controls: start / pause / stop / speed (1x/5x/20x). Polling first.

**Incidents (PRD §14):**
- Rule-based grouping: family + source + destination + service/port + time
  window. Incidents retain underlying flow IDs.

**Security Monitor (PRD §7, §15, §16):**
- Summary cards (traffic analysed, suspicious flows, active incidents,
  current overall risk; optional unknown/anomalous flows).
- Traffic / attack timeline.
- Cytoscape.js communication graph (nodes = hosts/servers/optional
  service-port nodes; edges = observed communication — NOT physical
  topology, PRD §15, §64.6).
- Supporting charts: attack distribution, risk distribution, incident count
  over time, normal vs suspicious trend.

**Incident Detail (PRD §17):**
- Incident summary; incident network graph; attack timeline; Why Flagged?
  (top SHAP); behaviour vs baseline (2–4 features vs benign); raw evidence
  (expandable flow table).

## Explicitly Out of Scope During This Phase

- Playground (Phase 4).
- Model Evaluation Lab UI (Phase 5).
- WebSockets (only if polling demonstrably fails — PRD §42).
- Live NFStream input (post-core optional — PRD §43).

## Required Deliverables (PRD §58 Phase 3)

- Security Monitor.
- Network graph.
- Incident pages.
- Replay.

## Implementation Tasks

- [x] Implement replay engine: read next flow → preprocess → supervised →
      anomaly → hybrid decision → SHAP if suspicious → incident grouping →
      persist/update UI. (backend done + VALIDATED)
- [x] Implement replay controls + speed multipliers (polling-based status).
- [x] Implement rule-based incident grouping with retained flow IDs.
- [x] Implement SQLite writes for predictions / incidents / incident_flows.
- [x] Build Security Monitor summary cards.
- [x] Build traffic / attack timeline (Recharts).
- [x] Build Cytoscape communication graph with suspicious-node drill-down.
- [x] Build supporting charts (attack/risk distribution, incident-over-time,
      normal-vs-suspicious trend).
- [x] Build Incident Detail page (summary, graph, timeline, SHAP, baseline
      comparison, raw evidence).

## Dependencies / Prerequisites

- Phase 2 complete (final supervised + anomaly artifacts, hybrid decision,
  risk, SHAP, baselines, inference contract).

## Files / Components Expected (PRD §55)

- `backend/app/services/replay/`, `incidents/`.
- `frontend/src/pages/` (SecurityMonitor, IncidentDetail).
- `frontend/src/network/` (Cytoscape wrapper).
- `frontend/src/charts/` (Recharts components).

## Validation Plan

- Replay determinism tests (same input + seed + speed → same stream).
- Incident grouping tests on prepared multi-flow scenarios.
- Cytoscape renders from a known fixture; suspicious-node click shows the
  documented fields.
- Phase-3 gate end-to-end.

## Completion Gate (PRD §58)

```text
normal traffic → suspicious flows → grouped incident → explainable incident detail
```

## Completion Gate Evidence

Backend engine gate (2026-08-09 PASS; hardened 2026-08-10):

```text
normal traffic -> suspicious flows -> grouped incident -> explainable incident detail
portscan replay : COMPLETED 8/8, 8 KNOWN_ATTACK -> 1 incident (flow_count 8)
                  incident detail: 8 persisted flows, each with prediction_id +
                  synthetic replay_time + source 10.0.0.50 (KNOWN_ATTACK/Recon)
dos_or_ddos     : COMPLETED 8/8, 8 KNOWN_ATTACK -> CRITICAL DoS incident
                  (family Denial of Service, risk 92.67, flow_count 8, detail
                  carries anomaly_score + persisted SHAP + baseline subset)
unknown replay  : 4/4 processed -> 4 UNKNOWN_SUSPICIOUS -> 1 incident (anomaly
                  branch, source 10.0.0.60)
normal replay   : COMPLETED 8/8, 0 suspicious, 0 incidents
baselines       : GET /api/baselines/benign -> 10 features (median/mean/...)
live uvicorn    : python -m backend.tests.e2e_replay_phase3 -> PASS
suite           : python -m pytest ml/tests backend/tests -q -> 87 passed
evidence        : ml/evaluation/results/e2e_replay_phase3.json
```

## Current Status

Backend engine portion COMPLETE + VALIDATED 2026-08-09 (hardened 2026-08-10):
scenario fixtures (data/scenarios/*.json), replay engine
(backend/app/services/replay.py), deterministic incident grouping
(backend/app/services/incidents.py), REST API (api/{replay,incidents}.py),
SQLite persistence with additive migration. Futurescribed: Security Monitor UI,
network graph (Cytoscape), Incident Detail page.

## Blockers

None.

## Decisions Made During This Phase

Recorded 2026-08-09:

- Incident grouping window: `incidents.grouping_window_seconds` (30s default,
  placeholder calibrated in Phase 3).
- Replay speed semantics: speeds {1,5,20} control pacing only
  (sleep = interval/speed); deterministic seq order; injectable pacing for tests.
- Polling interval: polling-first, no WebSockets (ARCHITECTURE_LOCK §69).
- Replay timestamp: synthetic = scenario base + seq × interval, never
  represented as original CICIDS capture time.
- service_port grouping: excluded for scanning families (Reconnaissance) so a
  multi-port PortScan is ONE incident; kept for non-scanning families.
- Cytoscape node/edge schema (built 2026-08-10): nodes = observed hosts plus
  `host:port` service nodes; edges = observed communications, NOT reconstructed
  topology (PRD §15/§64.6); style colours risk (normal slate, suspicious orange,
  high-risk red); tap node/edge -> selection panel with populated fields. Empty
  state renders a message in the always-mounted container (prevents the
  init-before-container bug, BUG-009).
- Recent-flows UI feed: `GET /api/replay/flows` (newest-first, limit 1..500,
  default 50) serves the live traffic table from persisted Prediction rows
  (DEC-014).

## Phase-3.5 Hardening & Freeze (2026-08-10)

Additive hardening on the frozen Phase-3 backend, then the phase was FROZEN.

### Done

- **BUG-010 (single-pass replay SHAP):** `Phase2Predictor.explain(features)`
  runs only the SHAP block; `_predict_one` scores once and explains suspicious
  flows. No output-semantics change; replay compute for attack flows halved.
  Regression: `test_explain_matches_predict_shap`.
- **BUG-011 (run-scoped monitor views):** per-run `run_id` stamped on every
  replayed `Prediction`/`Incident` row; `?run_id=` filters on `/api/replay/flows`
  and `/api/incidents`; Security Monitor passes `status.run_id`; Incidents page
  keeps full history. Sequential-replay evidence: VERDICT=MIXED -> ISOLATED.
- **Decisions:** DEC-015, DEC-016. **Bugs:** BUG-010, BUG-011 (FIXED).

### Verified

- BUG-012 fixed (restart joins the stale worker thread before resetting counters).
- Full suite: 92 passed (52 backend, 40 ml), stable x2.
- Live uvicorn E2E gate: PASS incl. sequential-run isolation.
- `npm run build`: PASS. Real-browser sequential replay E2E: PASS, zero console
  errors.
- Evidence JSONs: `ml/evaluation/results/phase35_evidence_{before,after}.json`.

### Verdict

Phase 3 (Monitor, Incidents, Visual Intelligence) is **COMPLETE, VALIDATED and
FROZEN (2026-08-10)**. Phase 4 is NOT authorized; do not start it.

## Frontend UX Pass — Recovery Reconciliation & Completion (2026-08-13)

A recovery brief requested an audit of partial prior UX work and completion of
the Phase-3 frontend UX pass (no git history available; audit based on current
files + rendered UI).

### Audit outcome

Already in place and KEPT: two-tab navigation (Monitor + Incidents only),
product-purpose header copy, runtime-generated security verdict block,
UNKNOWN_SUSPICIOUS explanation surfaces, human scenario labels, semantic risk
colours, event-style incident cards, story-first Incident Detail, correct SHAP
framing, baseline comparison, readable evidence tables. No Predict/Playground/
Model Lab surfaces exposed (backend `/api/predict` untouched).

### Defects fixed

- Header still showed "System ready · 77 features" (developer copy) -> "System
  ready".
- Anomaly threshold `-0.0928` duplicated as a magic number in three files ->
  single shared `ANOMALY_THRESHOLD`/`isAnomalyFlagged()` in `ui.tsx` (mirrors
  config/config.yaml).
- Replay Activity: benign flows rendered 0-height bars (Normal scenario showed
  an empty chart) -> minimal visible benign bar + Y-axis floored at 1.
- Risk Distribution lacked an empty state -> added.
- Baseline comparison ignored the p25-p75 band and below-normal values ->
  within/outside now uses the benign band; ratio always shown.
- BUG-013: Communication Map painted blank on initial load with a restored
  completed run -> `cy.resize()` before layout on data updates.

### Validation (2026-08-13)

`npm run build` PASS; `python -m pytest ml/tests backend/tests -q` -> 92
passed (frozen baseline); browser-tested Normal / PortScan / DoS / Unknown /
Incident Detail / Incidents hub with zero console errors; graph labels
readable; healthy state obvious; UNKNOWN semantics non-contradictory.


## Approved reliability reopening - 2026-10-31

User explicitly approved controlled implementation of the reviewed four-milestone
plan. The historical freeze is superseded only for those scoped corrections.
Task 1 replay lifecycle implemented; 62 related tests and live four-scenario gate
passed. Full dataset-backed suite: 106 passed in 250.99s with network access.
Task 2 readiness/frontend state and Task 3 graph/semantics are still pending.
See DEC-017, BUG-014 and latest sprint entry. Phase 3 is not re-declared complete.

## Reliability Task 2 complete - 2026-10-31

Readiness and run-scoped UI tested: 32 focused tests, TypeScript/build, browser
missing-model/failure/restart/sequential and delayed-response cases passed.
Task 3 remains pending; Milestone 1 is not yet complete. See latest sprint entry.

## Approved reliability milestone completed - 2026-10-31

Tasks 1-3 complete within approved scope. See Batch 1-3 sprint entries for exact
validation. Next is evaluation credibility/provenance, then Playground; expanded
investigation and Model Lab remain Phase 5. Original successful scenarios retained.
