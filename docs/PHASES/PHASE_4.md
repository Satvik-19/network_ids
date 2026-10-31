# Phase 4 - Personalized Security Playground

Status: approved first version COMPLETE and VALIDATED, 2026-10-31.
PRD: sections18-24,44-46,58. Scope is the reviewed implementation authorization;
research limitations and Phase 5 expansions deliberately remain.

## Delivered

- [x] Short questionnaire: environment, scale, exposure and five service options.
- [x] Validated deterministic relevance rules and saved profile preview.
- [x] Existing scenario infrastructure reused; original vectors preserved, provenance
      added; prediction-independent SSH/FTP/web sets added (8 each).
- [x] Existing hybrid predictor, thresholds, risk formula and SHAP semantics reused.
- [x] Bounded synchronous runner (<=64 flows) and separate saved Playground evidence.
- [x] Configurable outcome score, missed/false-alert counts, weakest/strongest areas.
- [x] UI scenario matrix, risk chart, coverage, flow decisions and explanations.
- [x] Saved ID retrieval, inference/database failure handling, restart interruption.
- [x] Explicit simulation boundary and unsupported/unknown coverage.
- [ ] Optional PDF export - deferred, not a completion dependency.
- [ ] Stronger unknown-attack experiment and fully independent larger scenario suite -
      retained research, not claimed complete by this first version.

## Rules and scoring

Always normal + unknown benign anomaly control. SSH/FTP enabled select corresponding
brute-force fixtures. Web + non-internal exposure selects web attacks. Non-internal
or50+ scale selects DoS/DDoS. Lab/small organisation or >10 scale selects PortScan.
Database/file sharing have no prepared coverage. Unknown-attack detection remains
not established; its benign challenge contributes false alerts only.

Score100*(detection_weight*mean attack-scenario recall +
false_alert_weight*pooled benign specificity); defaults .5/.5 sum1. No score if
selected fixtures are missing or attack/benign support absent. Coverage counts
execution, not real-network completeness. Weakest/strongest per-scenario quality
uses mean recall and specificity where supported; counts/matrix remain visible.

Examples verified: Home/internal/no services ->2 scenarios,4 false alerts,no attack
score. Web/public/web ->4 scenarios,12 detections,4 misses,4 false alerts,70.83.
Lab/50+/public/web+ssh+ftp ->7 scenarios,36 detections,4 misses,4 false alerts,78.33.

## Files

backend/app/{api,schemas,services}/playground.py, main.py startup hook;
existing db/models.py PlaygroundProfile/Run/Result; config/config.yaml playground;
frontend/src/pages/Playground.tsx, App.tsx, api client/types and shared risk chart;
data/scenarios/*.json, data/processed/scenario_provenance.json;
ml/evaluation/{prepare_scenarios,evaluate_hybrid}.py and locked report.

## Gate evidence

Different profiles produce different logical suites and complete the same frozen
pipeline. Full142 Python tests PASS (203.45s);5 Node tests,TypeScript/build PASS;
original replay real HTTP gate PASS. Live browser verifies Home/Web/Lab, outcomes,
profile invalidation, persisted reload/restart, readiness controls, missing-ID error,
flow explanations and Monitor isolation. See TESTING.md final batch and sprint log.

## Qualifications and retained scope

Prepared examples are tiny demonstrations, not an unbiased held-out performance
estimate. Original PortScan5/8 and DoS/DDoS1/8 vectors match deployed-training
features, retained per explicit user invariant; legacy identity uncertain. New
fixtures exclude exact matches. Unknown is benign, not a novel attack experiment.
Thus stronger PRD research aspirations are not claimed validated by this scope.
Historical temporal experiment remains separate. DEC-020..022 document choices.

No live capture, scanning, mitigation, drift, enterprise/alerting/intelligence
integrations, extra models/datasets, LLM personalization, full Model Lab or expanded
investigation. Phase 5 remains deferred. No active implementation blocker.
