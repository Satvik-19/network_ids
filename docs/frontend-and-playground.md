# Frontend, Monitor, incidents and Playground

## Navigation and data flow

The current application has three top-level views: Security Monitor, Incidents and Security Playground. An incident opens a detail view inside Incidents. There is no Model Evaluation Lab page. `frontend/src/App.tsx` polls health every five seconds; the monitor page polls replay status/evidence using the typed API client and `usePolling`. Vite proxies relative `/api` calls to the local backend. See [navigation diagram](diagrams.md#frontend-routes-and-playground-workflow).

## Security Monitor

`frontend/src/pages/SecurityMonitor.tsx` offers prepared scenario selection and replay start/pause/resume/stop controls. It shows run-scoped status, flow evidence, timeline and risk distribution, incident summary, and host communication evidence. Charts preserve numeric meaning: risk uses a fixed 0–100 scale, distribution uses actual counts. Missing risk is unavailable, not zero.

`frontend/src/components/CommGraph.tsx` and `frontend/src/lib/graph.ts` build a deterministic directed graph from recorded source/destination endpoints. Each host IP is a node; each observed ordered host pair is an edge, with ports/count/risk shown as edge evidence. Nodes retain lane positions as the dataset updates; filtering and selection do not create a force layout. A suspicious-only filter changes visible edges. Ports are not standalone hosts. The graph represents records in the selected fixture and does not infer protocol or physical topology. Addresses are synthetic fixture metadata.

## Incident investigation

The Incidents view defaults to persisted history. A Monitor-to-detail link opens a grouped incident and its supporting flows. Detail includes aggregate risk/time/count and flow-level supervised label/confidence, anomaly score/threshold, SHAP contributions when produced, and selected baseline feature values. The app describes SHAP as influence on the supervised XGBoost prediction; it does not attribute the anomaly decision or establish causality. No response action or firewall mitigation is available.

## Personalized Security Playground

### Profile and deterministic suite rules

The user chooses an environment, device scale, exposure and service set. The backend sorts/deduplicates services, persists the profile and builds the suite using these rules:

| Rule | Selected fixture |
|---|---|
| Always | `normal`, `unknown` (the latter is a benign anomaly challenge used to count false alerts) |
| `ssh` selected | `ssh_bruteforce` |
| `ftp` selected | `ftp_bruteforce` |
| `web` selected and exposure is not internal | `web_attack` |
| Exposure is public/some-public or scale `50+` | `dos_or_ddos` |
| Environment `lab` or `small_organisation`, or scale is not `1-10` | `portscan` |

Database and file-sharing profile choices have no prepared scenario coverage. Every planned scenario reports availability, count, reason and purpose. Selection is deterministic; it is not personalized using an LLM and does not inspect targets.

### Run and assessment

`POST /api/playground/run` evaluates available selected fixtures synchronously, rejecting suites over 64 flows. It calls the existing predictor for every flow; suspicious outputs get a local explanation. Ground truth is read after prediction to classify fixture outcomes as detected, missed, false alert or correct benign. Saved output includes selected/executed/unavailable coverage, unsupported services, scenario counts, each flow's output, provenance, model metadata/hash context and thresholds.

Readiness is available only when the selected suite contains malicious support and benign support and all selected scenarios are available. Current formula:

```text
100 × (detection_weight × unweighted mean of attack-scenario recall
     + false_alert_weight × pooled benign specificity)
```

The current weights are 0.5/0.5. Score status is incomplete when selected fixtures are missing and not applicable when required attack/benign support is absent. The strongest/blind-spot lists compare supported per-scenario recall and/or specificity. The UI shows totals, scenario matrix, risk, coverage, misses and false alerts rather than presenting score alone.

Example results are fixed examples from current artifacts, not promised outcomes after model replacement: home/internal/no services selects two benign-control fixtures, produces four false alerts and no score; public web with web selects normal, unknown, web and DoS/DDoS (28 rows), produced 12 detections, 4 misses, 4 false alerts and 70.83; a large public lab profile with web/SSH/FTP selects all seven fixtures (52 rows), produced 36 detections, 4 misses, 4 false alerts and 78.33. The `unknown` fixture has four benign rows, so its alerts are false alerts, not unseen malicious detections.

Every assessment is explicitly a simulation over prepared scenario records. It does not measure real network readiness, service exposure, devices or controls. Full Model Evaluation Lab, expanded incident investigation and PDF export are deferred. See [evaluation limitations](machine-learning/evaluation.md).
