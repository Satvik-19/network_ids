# Project Handoff

Updated: 2026-10-31. The user-approved reliability/evaluation/first Playground scope
is complete and verified. Do not begin Phase 5 without user authorization.
Read AGENTS.md, full PRD, PROJECT_CONTEXT, ARCHITECTURE_LOCK, IMPLEMENTATION_STATUS
and PHASES/PHASE_4.md in the prescribed order. SPRINT_LOG.md holds batch history.

## Current state

All Tasks 1-10 complete. Existing FastAPI/SQLite/React/predictor reused. No new
models, retraining, thresholds, infrastructure or dependencies. Prediction/incident
history retained; Playground writes only playground_* tables. Frozen threshold
values .75 and -.0928; .5/.5 readiness weights are separate config.

Runner: POST profile -> deterministic suite -> POST run(profile_id) -> saved result;
GET results/run_id never reinterprets evidence. <=64 flows, current max52. Startup
marks interrupted runs failed once. Failed/missing-evidence runs have no success
score. The browser page also allows retrieval by saved ID.

## Final evidence

Full `python -m pytest ml/tests backend/tests -q -p no:cacheprovider --tb=short`:
142 passed in 203.45s (network-enabled pinned dataset checks). Five frontend Node
tests, TypeScript and production build PASS. Original Uvicorn four-scenario gate
and sequential isolation PASS. Browser Home/Web/Lab (all seven), persisted reload,
404, actual misses/false alerts, unsupported services, readiness recovery and
post-Playground Monitor isolation PASS. Fresh session no errors before intentional
backend-offline check. A short browser locator wait expired during the 52-flow
request; the completed result was then observed (no application failure).

Initial final-suite failure was a stale all-fixture expected detection count;
explicit original-four and expanded-seven regressions now both pass. The original
four vectors, truth, sidecars and order remain identical to f84fb71. All original
config sections unchanged; only readiness weights added. SHA256:
- supervised: 9067a808b7159a87918571f74cde1ccb54cbd652818c3816c10f6e66be85bd41
- IF: 89efc5a382c97e55aa40d0bd714e3cbd4511f7fa08312dcf0a09f36e3724c176

## Interpretation and deferred work

Read EVALUATION_PROTOCOL.md and DEC-019..022. Shared-cohort hybrid adds2 detections
and5011 benign alerts; do not tune this away. Original PortScan5 and DoS1 exact
training matches are disclosed, not unbiased held-out evidence. New SSH/FTP/web
samples exclude matches; web misses4. Unknown fixture is benign anomaly control.
Scores summarize selected scenarios, never real-network security or zero-day skill.
Home has no malicious evidence -> not applicable; Web(public,web)70.83; full Lab78.33.

Retain future work: live ingestion, mitigation, drift, integrations, enterprise,
advanced intelligence, extra datasets/models, unknown/zero-day research, full Model
Lab, expanded investigation and optional PDF export. Graph poll relayout and
large JS bundle remain polish limits. Fresh supervised artifact supply/curated
clean-environment lock work was not part of this batch.

## Reproduction and Git

Validated Python: C:/Users/BIT/.pyenv/pyenv-win/versions/3.10.11/python.exe.
Run backend from root, frontend from frontend/ (Vite /api proxies to localhost8000).
Use NETWORK_IDS_DB for disposable checks; don't replace developer evidence.
Tests need existing local model artifacts and dataset access/cache. Do not overwrite
historical evaluation JSON when running the replay gate; use a temporary OUT path.
Governance writes require atomic UTF-8 replacement and re-read as AGENTS.md directs.

Existing human Git identity retained; no Codex attribution. Existing remote is
https://github.com/Satvik-19/network_ids.git, branch main. Final remote check fetched
main, found no divergence. Push outcome is reported by the final delivery message;
verify `git status -sb` when continuing. Pre-existing .freebuff/ and shot1_setup.png,
shot2_normal.png, shot3_portscan_monitor.png remain untracked and untouched.
