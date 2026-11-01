# Implementation Status

Updated: 2026-11-01. Phase 4 implementation and UI redesign are complete within
approved scope. This documentation audit is the documentation portion of Phase 5;
the broader Phase-5 completion gate remains incomplete/deferred. The Model
Evaluation Lab, expanded incident investigation and advanced evaluation research
are not implemented. Historical detail: `SPRINT_LOG.md`; current handoff:
`HANDOFF.md`.

## Approved and validated implementation

| Milestone | Status | Evidence |
|---|---|---|
| Reliability hardening | COMPLETE | Replay failure rollback/session cleanup, restart synchronization, readiness, run-scoped Monitor, graph selectors and unknown-suspicious explanations; see BUG_LOG and TESTING. |
| Evaluation credibility | COMPLETE within approved scope | Report distinctions, frozen same-cohort comparison, fixture provenance and small fixture additions; no retraining or threshold sweep. |
| Playground backend | COMPLETE | Strict profiles, deterministic fixture selection, existing SQLite tables, <=64-flow run, outcome assessment/snapshots, failure/interruption handling. |
| Playground UI and gate | COMPLETE | Profile, preview, run/retrieve, coverage, counts, matrix, risk and evidence. |
| Network IDS UI redesign | COMPLETE | Responsive dark/light console; host-only deterministic directed SVG; meaningful metric scale; see DESIGN_SYSTEM.md and DEC-023. |
| Documentation system | COMPLETE for current implementation reference | Root README, architecture, ML/evaluation, API/persistence, frontend/Playground, diagrams, run/test and academic/demo references added; docs audit and links checked for this commit. |
| Phase-5 full completion gate | DEFERRED / NOT COMPLETE | Model Lab, expanded research and any unapproved future scope remain open. |

## Current interfaces and evidence

The application has Security Monitor, Incidents/detail and Security Playground.
The Model Evaluation Lab is not a current screen. Seven fixtures contain 52 rows
with 77 features each. Inference thresholds are 0.75 and -0.0928; readiness
weights are 0.5/0.5. Missing selected fixtures suppress the Playground score;
attack-free profiles have no score. Unsupported services and unknown-attack
coverage remain explicit. See `docs/backend-reference.md` and
`docs/frontend-and-playground.md`.

## Recorded application validation

The last recorded implementation validation (2026-10-31) reports 142 Python
checks, 10 frontend Node checks, TypeScript, Vite build, original real-HTTP replay
gate and browser workflows passing. Those results predate this documentation-only
change; this commit records documentation validation separately in
`docs/testing.md` and the sprint log. Existing Vite >500 kB warning remains.

## Retained limitations

- Small fixtures are demonstrations. Legacy PortScan 5/8 and DoS/DDoS 1/8
  vectors match deployed-training feature vectors; source-row identity cannot
  be recovered. Unknown fixture is benign and its anomaly alerts are false alerts.
- New web fixture has 4/8 misses. Rare-class supports in the dataset are tiny.
- On a reused 282,788-row random cohort, hybrid FPR is 0.023136; it adds 2
  malicious rescues and 5,011 benign alerts over the confidence gate.
- Historical test reuse and poor temporal generalization remain disclosed.
- SQLite and replay are single-process local-demo components. Permanent database
  failure can prevent durable failure evidence; replay finalization failure may
  leave incident end markers unset while prior commits remain.
- Fresh clone requires compatible serialized model artifacts; model binaries
  are not committed. The frontend build retains a >500 kB bundle warning.
- No live capture, mitigation, drift, external alerting, enterprise deployment,
  advanced threat intelligence, extra datasets/models, real zero-day claim,
  full Model Lab, expanded investigation or PDF export is implemented.

## Scope boundary

The Playground uses prepared scenario records and deterministic profile rules; it
does not test a user's real network. SHAP describes supervised XGBoost output
only. The graph describes observed fixture relationships rather than physical
topology. See `docs/machine-learning/evaluation.md` for full methodology and
limitations.
