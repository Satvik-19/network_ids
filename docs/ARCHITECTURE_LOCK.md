# ARCHITECTURE_LOCK.md — Locked Architecture Decisions

These are decisions agents must NOT casually change. Each entry uses the
format required by the bootstrap charter. The PRD remains the ultimate
authority; this file is a curated index of locked decisions with PRD
references.

**If existing repository code conflicts with anything here or in the PRD:
STOP and document the conflict before changing the architecture.**

Architecture changes require either explicit user approval or strong
demonstrated technical evidence with documented approval.

---

## 1. System Pipeline (PRD §67, §10)

```text
CICIDS2017
     │
     ▼
PREPROCESSING
     │
     ├───────────────┐
     ▼               ▼
Random Forest /   Isolation Forest
XGBoost
Known threats      Anomalies
     │               │
     └───────┬───────┘
             ▼
       HYBRID DECISION
             │
             ├── Risk
             ├── SHAP explanation
             └── Normal baseline comparison
             │
             ▼
       INCIDENT GROUPING
             │
   ┌─────────┼──────────────┐
   ▼         ▼              ▼
SECURITY   SECURITY      MODEL EVALUATION
MONITOR    PLAYGROUND       LAB
   │         │           (academic ML module:
   ▼         ▼            model comparison,
Network     Personalised  random vs temporal,
Graph       Scenarios     confusion matrices,
Timeline    Readiness     feature importance,
Incidents   Blind Spots   optional global SHAP)
   │
   ▼
INCIDENT DETAIL
```

The four downstream boxes (Security Monitor, Incident Detail, Security
Playground, Model Evaluation Lab) are **distinct major application modules**
per PRD §6 — they are NOT chained into each other. Only the Security Monitor
drills down into Incident Detail (PRD §7, §17). The Playground and Model
Evaluation Lab do not depend on the Monitor/Incident flow.

- **Decision:** Locked pipeline order above; four distinct modules, not a
  chain.
- **Reason:** It is the project's primary differentiator — lightweight ML
  components combined into one understandable, interactive system (PRD §2,
  §6, §67).
- **Change allowed only when:** PRD is amended with explicit team approval.
- **PRD reference:** §6, §10, §17, §42, §44, §67.

---

## 2. Dataset Selection (PRD §27, §28, §66.1)

- **Decision:** CICIDS2017 (UNB) is the single primary dataset. Convenience
  layer: Hugging Face `lacg030175/CICIDS2017` (Parquet, random + temporal
  splits).
- **Reason:** Cleaned numeric features, reduced wrangling, exposes both
  random and temporal splits required by the academic evaluation.
- **Change allowed only when:** The HF derivative fails validation AND the
  official MachineLearningCSV fallback (PRD §63) is used, OR explicit
  instruction. Never add CICIDS2018/UNSW-NB15/NSL-KDD.
- **PRD reference:** §27, §28, §62, §63, §66.1.

---

## 3. Supervised Candidates (PRD §32, §33, §66.2/3)

- **Decision:** Logistic Regression (baseline only), Random Forest
  (`sklearn.ensemble.RandomForestClassifier`), XGBoost
  (`xgboost.XGBClassifier`). Final model chosen by macro/weighted F1,
  per-class recall, false-positive behaviour, temporal generalisation,
  inference cost — NOT accuracy alone. Expected final: RF or XGBoost.
- **Reason:** Strong on tabular data, CPU-friendly, SHAP TreeExplainer
  support. SVM excluded (unnecessary cost at CICIDS scale). No deep-learning
  classifier mandatory.
- **Change allowed only when:** Evaluation evidence shows both RF and XGBoost
  are clearly inadequate AND time remains (would then consult PRD fallback
  matrix §63). Never silently add LSTM/Transformer/SVM.
- **PRD reference:** §32, §33, §35, §62, §63, §66.2/3.

---

## 4. Anomaly Detector (PRD §34, §35, §66.8)

- **Decision:** `sklearn.ensemble.IsolationForest`, fit primarily on benign
  training traffic, evaluated on held-out benign + malicious/unseen flows,
  threshold calibrated on validation data.
- **Reason:** CPU-friendly, no deep-learning overhead, deterministic.
- **Change allowed only when:** Isolation Forest clearly underperforms AND
  project time remains — then a small Autoencoder is the documented fallback
  (PRD §35, §63). Never silently switch to an Autoencoder.
- **PRD reference:** §9, §34, §35, §63, §66.8.

---

## 5. SHAP Explainability Strategy (PRD §12, §36, §66.9)

- **Decision:** SHAP `TreeExplainer` with the final tree-based supervised
  model (RF/XGBoost). Local explanations drive the dashboard; global
  summaries are optional in the Model Lab.
- **Reason:** Project principle "Explainability First" (PRD §61). Tree models
  enable fast, accurate SHAP.
- **Change allowed only when:** SHAP becomes blocking — fallback is native
  feature importance (PRD §63). Do NOT use PCA in the final explainable
  runtime model (transforms reduce interpretability — PRD §31).
- **PRD reference:** §12, §31, §36, §63, §66.9.

---

## 6. Deterministic Hybrid Decision Layer (PRD §10, §66.16)

- **Decision:** Lightweight deterministic layer combining supervised
  confidence and anomaly score. Outcomes: `BENIGN`, `KNOWN ATTACK`,
  `UNKNOWN SUSPICIOUS`. Thresholds are config-driven, calibrated during
  evaluation.
- **Reason:** Determinism, reproducibility, explainability — no extra ML
  model needed for the decision itself.
- **Change allowed only when:** Explicit team approval with documented
  evidence. Prediction responses must always retain class, confidence,
  anomaly score, risk, and explanation where applicable (PRD §66.16).
- **PRD reference:** §10, §57, §66.16.

---

## 7. Risk Logic Principle (PRD §11, §66.11)

- **Decision:** Transparent risk score computed from attack-family severity,
  supervised confidence, anomaly score, and optional incident
  volume/intensity. Levels: LOW / MEDIUM / HIGH / CRITICAL. No separate ML
  model. Function documented and configurable.
- **Reason:** Transparency over a black-box risk model; project-level
  prioritisation indicator, not an industry-standard score.
- **Change allowed only when:** Calibration evidence + config update. Initial
  thresholds are placeholders until evaluation (PRD §57).
- **PRD reference:** §11, §57, §66.11.

---

## 8. Incident Grouping Principle (PRD §14, §66.17)

- **Decision:** Rule-based grouping by attack family + source + destination +
  destination/service where useful + time window. Incidents must retain
  underlying evidence/flow IDs. No clustering neural network.
- **Reason:** Deterministic, explainable, low complexity. One attack can
  generate hundreds of flows; grouping is essential for human understanding.
- **Change allowed only when:** Explicit team approval. Window/threshold is
  config-driven (PRD §57).
- **PRD reference:** §14, §57, §66.17.

---

## 9. Replay Architecture (PRD §7, §42, §66.7)

- **Decision:** Baseline monitoring input is **dataset traffic replay**, not
  live attack generation. Recorded labelled flows stream progressively
  through the full pipeline. Controls: start / pause / stop / speed.
- **Reason:** Deterministic, reproducible, safe, easy to demonstrate,
  independent of live network permissions.
- **Change allowed only when:** Core system complete — then NFStream
  passive live input is an optional evaluation only (PRD §43, §63). Never
  promise live traffic without a reliable feature mapping (CICFlowMeter vs
  NFStream schema mismatch — PRD §43).
- **PRD reference:** §7, §42, §43, §54, §63, §66.7.

---

## 10. Backend — FastAPI (PRD §38, §50, §66.5/6)

- **Decision:** FastAPI + Uvicorn + Pydantic + SQLAlchemy + SQLite. Suggested
  routes in PRD §38. No authentication in baseline scope.
- **Reason:** Lightweight, async-friendly, CPU-friendly, Pydantic schemas
  align with the shared-contract requirement.
- **Change allowed only when:** Explicit instruction. Never silently add
  authentication, PostgreSQL, Redis, Celery, Kafka, Elasticsearch,
  microservices, or cloud SOC infrastructure (PRD §62).
- **PRD reference:** §38, §50, §62, §66.5/6.

---

## 11. Database — SQLite (PRD §41, §50)

- **Decision:** SQLite stores predictions, incidents, incident_flows,
  playground_profiles, playground_runs, playground_results. Training data
  stays in Parquet/CSV — NOT loaded into SQLite.
- **Reason:** Zero-infra, file-based, student-scale appropriate.
- **Change allowed only when:** Explicit instruction.
- **PRD reference:** §41, §50, §62.

---

## 12. Frontend Stack (PRD §39, §50, §66.10)

- **Decision:** React + TypeScript + Vite + Tailwind CSS.
- **Reason:** Interactive network graph, multiple screens, incident
  drill-down, replay controls, playground workflow, custom visualisations —
  Streamlit cannot serve these well.
- **Change allowed only when:** Frontend schedule becomes a serious delivery
  risk — then Streamlit is the documented emergency fallback (PRD §39, §63).
  Never silently switch.
- **PRD reference:** §39, §50, §63, §66.10.

---

## 13. Visualisation — Recharts (PRD §16, §40)

- **Decision:** Recharts for timelines, attack/risk distributions, model
  metrics, SHAP contribution bars, readiness reports, random-vs-temporal
  comparisons.
- **Reason:** React-native, simple, sufficient for the required charts.
- **Change allowed only when:** Frontend charting blocks delivery — fallback
  is static evaluation charts (PRD §63).
- **PRD reference:** §16, §40, §63.

---

## 14. Network Graph — observed host communication

- **Original PRD decision:** Cytoscape.js was the proposed graph tool; graph
  nodes/edges must represent communication, not physical topology.
- **Current approved implementation (DEC-023, 2026-10-31):** deterministic
  SVG renderer with source/destination IP hosts as nodes and directed observed
  host-pair edges. Service ports and recorded risk/count remain edge metadata;
  no port nodes, protocol inference or physical topology is introduced.
- **Reason for superseding the proposed tool:** stable positions across polling,
  filtering and selection, and direct host-to-host evidence semantics.
- **Boundary:** preserve actual observed flow relationships. Any future renderer
  change must retain these semantics and documented evidence.
- **PRD reference:** §15, §40, §63, §64.6, §66.10; approved override DEC-023.

---

## 15. Polling-First Rule (PRD §42, LOCKED BOUNDARIES)

- **Decision:** Polling is acceptable initially for replay/dashboard updates.
- **Reason:** Simplicity and reliability for a student project.
- **Change allowed only when:** Polling demonstrably becomes insufficient —
  then add WebSockets. Never introduce WebSockets by default.
- **PRD reference:** §42.

---

## 16. CPU-First Rule (PRD §49, §61, §66.15)

- **Decision:** Every mandatory feature must run without a dedicated GPU.
  Target i5/Ryzen 5, 8–16 GB RAM, SSD. No GPU-required model is mandatory.
- **Reason:** Student-scale, free/open-source, reproducible. The final demo
  must work without a GPU.
- **Change allowed only when:** Never for mandatory scope. Optional free
  compute (Colab/Kaggle) may be used for training (PRD §49).
- **PRD reference:** §49, §61, §66.15.

---

## 17. Artifact Contract (PRD §56)

- **Decision:** Persist: supervised model, anomaly model, preprocessor,
  label mapping, feature schema, benign baselines, model metadata. Example
  layout under `ml/artifacts/` (joblib / native XGBoost).
- **Reason:** Reproducible inference and shared contract between training and
  backend.
- **Change allowed only when:** Documented in `docs/DATA_ML_CONTRACT.md` and
  `docs/DECISIONS.md`. Artifact version metadata must accompany changes.
- **PRD reference:** §56. See `docs/DATA_ML_CONTRACT.md`.

---

## 18. Configuration-Driven Thresholds (PRD §57, §66.11)

- **Decision:** All tunable project-level parameters live in a configuration
  layer: known-confidence threshold, anomaly threshold, incident grouping
  window, risk thresholds, replay speed defaults, etc. Initial values are
  placeholders until evaluation calibrates them.
- **Reason:** Avoid scattered magic numbers; keep experiments reproducible.
- **Change allowed only when:** Calibration evidence recorded in
  `docs/DECISIONS.md`. Never pretend placeholder thresholds are empirically
  validated.
- **PRD reference:** §57, §66.11.

---

## 19. Repository Structure (PRD §55)

- **Decision:** Top-level layout `backend/`, `frontend/`, `ml/`, `data/`,
  `docs/`, `config/`, `README.md` with substructure per PRD §55.
- **Reason:** Clear separation of ML, application, data, docs, config.
- **Change allowed only when:** Documented in `docs/DECISIONS.md` with PRD
  compatibility justification.
- **PRD reference:** §55.

---

## 20. Ethical Boundaries (PRD §54, §62)

- **Decision:** No launching attacks against external networks, no scanning
  arbitrary public IPs, no harmful traffic generation, no automatic
  exploitation, no blocking/modifying real traffic. Playground uses
  prepared/simulated samples. Optional live input is passive only.
- **Reason:** Ethical and legal safety; academic scope.
- **Change allowed only when:** Never within this project's scope.
- **PRD reference:** §54, §62.

---

## Explicit Architecture Non-Goals (PRD §62, §66)

The following must NOT be introduced as core/baseline dependencies:

- Authentication / user management
- PostgreSQL, Redis, Celery, Kafka, Elasticsearch
- Kubernetes, microservices, cloud SOC infrastructure
- Paid APIs, paid threat intelligence
- LLM-based personalisation (Playground is rule-based — PRD §20)
- Deep-learning IDS models, LSTM/Transformer IDS, reinforcement learning,
  federated learning, agentic security automation
- SVM in the main training pipeline
- Autoencoder (unless IF fallback condition is met — PRD §35)
- Active penetration testing, attack generation, arbitrary IP/network
  scanning
- Live traffic as a baseline dependency
- WebSockets (unless polling demonstrably fails)
- Additional cybersecurity datasets
- Additional ML models beyond the locked candidates
- App Security Quick Check before all core completion gates (PRD §53)
- PCA in the final explainable runtime model (PRD §31)

Optional/stretch scope must never become a dependency of core functionality
(PRD §69).
