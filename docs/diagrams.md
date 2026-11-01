# Workflow diagrams

These editable Mermaid diagrams reflect current runtime behavior. They can be rendered by GitHub Markdown or a Mermaid-compatible editor.

## Flow scoring and hybrid decision

```mermaid
flowchart TD
  A["77 numeric flow features"] --> B["Validate exact feature schema and order"]
  B --> C["Replace non-finite values; no inference labels"]
  C --> D["XGBoost multiclass prediction: label + confidence"]
  C --> E["Isolation Forest decision_function"]
  D --> F{"Predicted label is non-BENIGN<br/>and confidence >= configured threshold?"}
  F -- yes --> K["KNOWN_ATTACK"]
  F -- no --> G{"Anomaly score < configured threshold?"}
  G -- yes --> U["UNKNOWN_SUSPICIOUS"]
  G -- no --> N["BENIGN"]
  K --> R["Risk score and severity"]
  U --> R
  N --> R
  K --> X["Top-5 native TreeSHAP for XGBoost predicted class"]
  U --> X
  R --> O["API / persistence"]
  X --> O
  N -. "no SHAP in replay" .-> O
```

## Training and evaluation

```mermaid
flowchart LR
  D["Pinned HF CICIDS2017 derivative"] --> S["Random and temporal source splits"]
  S --> C["Canonical preprocessing: 77 features, 15 labels"]
  C --> B["LR / RF / XGBoost candidate experiments"]
  B --> SEL["Select xgb_200; selection used random/test"]
  C --> IF["Isolation Forest fit on benign training records"]
  IF --> CAL["Calibrate threshold under FPR constraint"]
  SEL --> INF["Export inference artifacts and metadata"]
  CAL --> INF
  INF --> RAND["Random benchmark evaluation"]
  INF --> TEMP["Temporal generalization diagnostic"]
  INF --> HYB["Shared-cohort supervised vs hybrid comparison"]
  INF --> FIX["Prepared scenario fixtures and provenance"]
```

## Prediction and API lifecycle

```mermaid
sequenceDiagram
  participant UI as React UI
  participant API as FastAPI
  participant P as Shared predictor
  participant DB as SQLite
  UI->>API: POST /api/predict (feature mapping)
  API->>P: Validate and score
  P-->>API: supervised, anomaly, hybrid, risk, explanation
  API->>DB: Persist prediction row
  API-->>UI: PredictResponse
```

## Replay and incident lifecycle

```mermaid
sequenceDiagram
  participant UI as Monitor
  participant API as Replay API
  participant W as In-process worker
  participant P as Predictor
  participant G as Incident grouper
  participant DB as SQLite
  UI->>API: POST /api/replay/start
  API->>W: Validate suite and spawn run_id worker
  loop each fixture row in seq order
    W->>P: Predict features; explain only if suspicious
    P-->>W: Verdict and evidence
    W->>DB: Persist prediction
    W->>G: Assign suspicious flow
    G-->>W: Create/update/close group
    W->>DB: Persist incident and evidence links
  end
  UI->>API: Poll status, /flows?run_id=, /incidents?run_id=
  API-->>UI: Run-scoped persisted evidence
```

## Database entity relationship

```mermaid
erDiagram
  INCIDENT ||--o{ INCIDENT_FLOW : contains
  PREDICTION ||--o{ INCIDENT_FLOW : supports
  PLAYGROUND_PROFILE ||--o{ PLAYGROUND_RUN : configures
  PLAYGROUND_RUN ||--o{ PLAYGROUND_RESULT : snapshots
  PREDICTION {
    int id PK
    string run_id
    string classification
    float confidence
    float anomaly_score
    json features
    json top_features
  }
  INCIDENT {
    int id PK
    string run_id
    string family
    string source
    string destination
    int flow_count
  }
  INCIDENT_FLOW {
    int id PK
    int incident_id FK
    int prediction_id FK
    string flow_id
  }
  PLAYGROUND_PROFILE {
    int id PK
    json config
  }
  PLAYGROUND_RUN {
    int id PK
    int profile_id FK
    string status
    json config
  }
  PLAYGROUND_RESULT {
    int id PK
    int run_id FK
    json data
  }
```

SQLite tables are created by SQLAlchemy metadata initialization. JSON columns hold structured features, SHAP values, profile inputs and saved result payloads. Current schema/index detail is in [backend reference](backend-reference.md).

## Frontend routes and Playground workflow

```mermaid
flowchart LR
  NAV["Application navigation"] --> MON["Security Monitor"]
  NAV --> INC["Incidents history"]
  INC --> DETAIL["Incident detail"]
  NAV --> PG["Security Playground"]
  MON -->|replay controls + polling| REPLAY["Selected fixture run"]
  REPLAY --> MON
  PG --> PROFILE["Choose environment, scale, exposure, services"]
  PROFILE --> PREVIEW["POST profile: deterministic suite preview"]
  PREVIEW --> RUN["Run selected available scenarios"]
  RUN --> RESULT["Readiness (if supported), coverage, misses, false alerts, evidence"]
  RESULT --> SAVED["Retrieve saved result by run ID"]
  DETAIL -->|flow evidence| EXPLAIN["XGBoost attribution + baseline comparison"]
```
