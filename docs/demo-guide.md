# Demonstration guide

## Prerequisites

Use [installation instructions](running-the-project.md). Confirm both Phase-2 model binaries are available, start FastAPI and Vite, and verify `/api/health` reports `model_loaded: true`. If using a clean database for a repeatable demo, set `NETWORK_IDS_DB` before starting the backend. The prepared scenario files are committed; full benchmark data is not needed for replay when the model artifacts are present.

## Suggested 8–12 minute sequence

1. **Orient the audience.** Point out the app's academic-prototype scope and prepared-flow/no-live-capture notice.
2. **Show system readiness.** Explain model availability and XGBoost + Isolation Forest. Do not interpret health status as proof of network security.
3. **Show the benign control.** In Security Monitor choose `normal`, run at default/1× speed, and show recorded flow rows, timeline/risk scale and empty incident state.
4. **Replay PortScan.** Select `portscan`, start, and wait for completion. Explain the fixture sequence and that addresses/time are synthetic metadata.
5. **Inspect communications.** Identify host nodes and directed edges. Show service ports in the connection evidence table; emphasize that ports are not separate hosts and graph edges do not reconstruct topology.
6. **Investigate the incident.** Open the incident; review dominant risk, flow count, evidence rows and the time window. Explain that only suspicious flows join groups.
7. **Inspect an explanation.** Select a suspicious flow and show signed TreeSHAP values. State that they describe contributions to the supervised XGBoost predicted-class margin only. A benign anomaly challenge can demonstrate the distinction between supervised prediction and hybrid outcome.
8. **Run Playground.** Select a public web/server profile with the web service and public exposure; preview the deterministic suite; run it; inspect scenario coverage, detected/missed/false-alert counts, score and saved run ID. If repeating exact sample counts, use artifacts matching the recorded metadata.
9. **Explain the evaluation.** Contrast supervised random, temporal, standalone anomaly, locked hybrid and Playground tables from [evaluation results](machine-learning/evaluation.md). Do not combine them or call fixture score a network readiness certification.
10. **Close with limits/future work.** Mention poor temporal scores, rare-class support, test reuse, IF misses/false alerts and deferred Model Evaluation Lab/live ingestion.

## Reliability notes

- Replay is asynchronous in one local backend process and the UI polls it. Wait for the terminal replay state before starting another scenario.
- A saved Playground assessment is retrievable by its run ID. Backend restart marks an unfinished synchronous Playground run failed; it does not resume.
- The database persists prior replay runs. Monitor views scope to the selected run; the Incidents history view may include older runs.
- Home profiles without attack scenarios have no readiness score by design.
- Database and file-sharing services have no prepared scenario coverage.
- The unknown scenario contains benign rows, so suspicious outcomes there count as false alerts.
- Do not describe replay timestamps or sidecar IP/port values as recovered original capture metadata.

For a presentation flow and suggested screenshots, see [academic preparation](academic/README.md).
