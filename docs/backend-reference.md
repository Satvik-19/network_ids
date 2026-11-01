# Backend API, persistence and replay

Implementation sources: `backend/app/main.py`, `backend/app/api/`, `backend/app/schemas/`, `backend/app/services/`, and `backend/app/db/`. FastAPI publishes an interactive OpenAPI UI at `/docs` and schema at `/openapi.json`. The tables below summarize the Pydantic route contracts; use the live schema as the exact machine-readable reference for a running build.

## API routes

| Method and path | Input | Success response | Errors/notes |
|---|---|---|---|
| `GET /api/health` | None | `status`, `model_loaded`, `feature_count`, `phase`, `version`, `readiness`, `message` | HTTP success can still report `readiness: unavailable`; inference routes then fail readiness. |
| `POST /api/predict` | `{features: {<77 canonical feature>: number}, flow_id?: string}` | prediction id, classification, label, family, confidence, anomaly score/threshold, risk level/score, top features, model name/version | Invalid feature vector → 422; persisted prediction uses shared DB. |
| `GET /api/replay/scenarios` | None | array `{name, description, flows}` | Invalid scenario library can fail. |
| `POST /api/replay/start` | `{scenario: string, speed?: 1\|5\|20}` | `ReplayStatus` | Invalid speed/request 422; unknown scenario 404; active/conflicting worker 409; unavailable inference 503. |
| `POST /api/replay/pause` | Empty JSON | `ReplayStatus` | Invalid state 409. |
| `POST /api/replay/resume` | Empty JSON | `ReplayStatus` | Invalid state 409. |
| `POST /api/replay/stop` | Empty JSON | `ReplayStatus` | Invalid state 409. |
| `GET /api/replay/status` | None | `ReplayStatus` | Includes state, counters, progress, run ID and latest error. |
| `GET /api/replay/flows?limit=50&run_id=...` | `limit` 1–500; optional run id | `{total, flows[]}` newest first | Feed includes persisted replay records, including benign rows. Without run ID it can show history. |
| `GET /api/incidents` | Optional `source`, `destination`, `family`, `classification`, `run_id`, `limit` 1–1000 | `{total, incidents[]}` | Without run ID shows history, not only active replay. |
| `GET /api/incidents/{incident_id}` | Integer path id | Incident summary plus evidence `flows[]`; dominant-flow confidence/anomaly | Missing id → 404. Flow entries include linked prediction SHAP and selected baseline feature values when present. |
| `GET /api/baselines/benign` | None | Version/source/support/features and per-feature median, mean, quartiles, std, support | Missing artifact → 404. |
| `POST /api/playground/profile` | Environment profile JSON | Profile id, normalized profile, scenario suite, unsupported services, unknown detection status, notice | Invalid profile → 422; scenario library/profile persistence failure → 503. |
| `POST /api/playground/run` | `{profile_id: positive integer}` | Saved run status, assessment, coverage, scenarios/flow decisions, profile/context, notice | Missing profile 404; missing model 503; preparation/persistence failure 503. Run executes synchronously and is bounded to 64 selected flows. |
| `GET /api/playground/results/{run_id}` | Integer path id | Saved run-result snapshot | Missing run → 404; a run interrupted by restart remains retrievable as failed. |

### Key request/response fields

`PredictRequest.features` must contain all and only 77 names from `ml/artifacts/feature_schema.json`. `TopFeature` has `feature`, `shap_value`, `direction`. `ReplayStatus` includes `state` (`IDLE`, `RUNNING`, `PAUSED`, `COMPLETED`, `STOPPED`, `FAILED`), scenario/speed, processed/total counts, suspicious/known/unknown counts, incidents/errors, progress, sequence, synthetic replay time, max risk and `run_id`.

Playground `ProfileRequest` accepts `environment` from `home`, `lab`, `small_organisation`, `web_server`; `scale` from `1-10`, `10-50`, `50+`; `exposure` from `internal`, `some_public`, `public`; and up to five service values from `web`, `ssh`, `ftp`, `database`, `file_sharing`. Unknown fields are forbidden; services are de-duplicated and sorted.

## SQLite schema and persistence

The default file is `data/network_ids.db`, overridable with `NETWORK_IDS_DB`. `backend/app/db/database.py` uses SQLAlchemy `create_all` and small additive SQLite `ALTER TABLE` migrations for columns added after an existing database was created. Training data stays in Parquet/CSV.

| Table | Important columns | Relationships and purpose |
|---|---|---|
| `predictions` | id, created_at, flow_id, source_config, run_id, model name/version, label/family/classification/confidence, anomaly score/threshold, risk, JSON top_features/features, source/destination/service_port/replay_time/seq | A `/predict` request or replay flow. Replay source config identifies the fixture; run ID scopes replay evidence. Full feature JSON is retained. |
| `incidents` | id, timestamps, label/family/classification, source/destination/service port, flow_count, severity/risk, run_id | Replay-time aggregate. Run groups remain separately queryable. |
| `incident_flows` | id, incident_id FK, prediction_id FK nullable, flow metadata, classification/family/risk | Per-flow incident evidence; incident delete cascades its membership rows. |
| `playground_profiles` | id, created_at, name/description, JSON config | Saved validated questionnaire values. |
| `playground_runs` | id, created_at, profile_id FK nullable, status, JSON config/context | Synchronous evaluation run and model/threshold/artifact context. |
| `playground_results` | id, created_at, run_id FK, JSON data | Persisted complete result snapshot, scenario provenance and flow evidence. Run delete cascades result rows. |

No additional indexes are declared in the ORM model. `Incident.flows` has ORM delete-orphan cascade; the schema uses explicit foreign keys. Playground persistence is logically separate from Monitor prediction/incident tables. Startup changes any Playground run left `running` to failed and saves an interruption result; it cannot resume a synchronous run after process restart.

## Replay and incident lifecycle

Scenario files use `scenario/v1`, contiguous sequence numbers and exactly 77 finite feature values per flow. Source IP, destination IP, service port, ground truth and synthetic time are fixture sidecar fields. Predictor receives only features. At replay start the service creates a run ID, initializes run counters and launches one worker thread. Each row is predicted; suspicious rows get local SHAP; the prediction is flushed and committed per flow. Suspicious rows are grouped by `(classification, family, source, destination, service_port)` except Reconnaissance omits service port so scans across ports do not fragment. Same-key flows join if within configured time of the group's start; otherwise the previous group closes and a new one opens. Benign flows never join incidents. End-of-run closes open incident timestamps.

Pause, resume and stop are state transitions. Starting a new replay waits for a previous worker to drain; overlapping runs are rejected. On a worker exception, state becomes `FAILED`, the active transaction is rolled back and the session is closed; prior per-flow commits remain. A failure while finalizing incident timestamps may therefore leave committed evidence without an end marker. The frontend scopes monitor traffic and incident views using the active run ID; the Incidents page can show full persisted history.

Replay times are generated from run start and scenario sequence interval, not original capture timestamps. See [editable sequence diagram](diagrams.md#replay-and-incident-lifecycle).
