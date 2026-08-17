# AI-Powered Network Intrusion Detection & Security Evaluation System
## Product Requirements Document (PRD)

**Project Type:** Final-year / semester minor project  
**Team Size:** 3  
**Primary Domain:** Machine Learning, Cybersecurity, Explainable AI, Data Visualization  
**Status:** Architecture and implementation plan locked  
**Primary Constraint:** Student-scale, free/open-source, CPU-friendly, minimal infrastructure, no production-grade overengineering.

---

# 1. Executive Summary

This project is an **Explainable Hybrid Network Intrusion Detection and Security Evaluation System** designed to convert large volumes of raw network-flow data into understandable security incidents.

The system behaves like an AI-assisted security monitor for a computer network. Instead of requiring a network administrator to inspect thousands of low-level network records manually, the system should answer:

- Is this network flow normal or suspicious?
- If suspicious, what known attack does it resemble?
- If it does not resemble a known attack, is its behaviour still abnormal?
- Why did the model flag it?
- Is this one isolated record or part of a larger security incident?
- How severe is the incident?
- How does the suspicious behaviour differ from normal traffic?
- How well would the detector perform for a selected type of user/network environment?

The product combines:

1. **Known attack classification**
2. **Unknown/anomalous behaviour detection**
3. **Explainable predictions**
4. **Incident grouping**
5. **Risk scoring**
6. **Visual network monitoring**
7. **A personalised Security Playground**
8. **An academic Model Evaluation Lab**

The system deliberately does **not** attempt to become a production Security Operations Center (SOC), firewall, SIEM, enterprise IDS appliance, or penetration-testing platform.

The objective is to build a **high-quality academic ML project with a clean practical demonstration** while keeping implementation complexity manageable for a three-person student team.

---

# 2. Origin and Refined Project Direction

The original project synopsis proposed an AI-powered Network Intrusion Detection System using publicly available network traffic data, preprocessing and feature selection, supervised models such as Random Forest, XGBoost and SVM, anomaly detection through Isolation Forest or an Autoencoder, a FastAPI backend, a monitoring dashboard, risk scores and alerts.

The refined project preserves that academic foundation but improves the design in a restrained way. Instead of implementing multiple disconnected ML experiments, the project connects the strongest components into one coherent system:

```text
KNOWN ATTACK CLASSIFICATION
            +
UNKNOWN ANOMALY DETECTION
            +
EXPLAINABILITY
            +
INCIDENT INTELLIGENCE
            +
PERSONALISED SECURITY EVALUATION
```

The system's main differentiator is therefore not a new neural-network architecture. It is the way lightweight ML components are combined into an understandable, interactive security-monitoring and evaluation system.

---

# 3. Problem Statement

Modern computer networks generate very large amounts of communication traffic. Each network flow may contain information such as source and destination, destination port, connection duration, packet count, packet rate, packet length, forward/backward traffic, inter-arrival times, TCP flags and byte volume.

A human administrator cannot realistically inspect each record manually.

Cyberattacks also produce recognisable or abnormal patterns.

### DDoS / Denial of Service
A target may receive unusually large amounts of traffic over a short period.

### Port Scanning
One source may attempt connections to many destination ports to discover available services.

### Brute Force
A source may repeatedly attempt access/authentication patterns.

### Botnet Activity
Traffic behaviour may resemble automated malicious control or communication.

### Web Attacks
Traffic patterns may correspond to malicious web activity represented in the selected dataset.

A supervised ML model can learn known attack patterns, but it is strongest when the attack resembles something that existed in its training data. Therefore the system uses a **hybrid approach**:

- supervised ML for known attacks,
- unsupervised anomaly detection for unusual behaviour.

The result is a security assistant that can say either:

> “This resembles a Port Scan with high confidence.”

or:

> “This does not confidently match a known class, but its behaviour is significantly different from normal traffic.”

---

# 4. Target Users

This is an academic prototype, but the interface is designed around realistic user profiles:

- college/lab network administrators,
- small organisations,
- developers managing a small server/network,
- cybersecurity students,
- security analysts learning IDS behaviour,
- technical teams evaluating basic network-monitoring readiness.

The project does not claim to replace professional enterprise products. Its practical value is converting complex network-flow records into a small number of understandable, explainable security incidents.

---

# 5. Product Vision

## 5.1 Core Vision

The product should allow a user with basic cybersecurity understanding to visually understand:

- what happened,
- when it happened,
- which systems were involved,
- what the ML model believes the attack is,
- how confident the prediction is,
- how unusual the behaviour is,
- why it was considered suspicious,
- whether many low-level flows belong to the same incident.

## 5.2 Interaction Philosophy

The project should be **visual first, raw-data second**.

The dashboard should avoid becoming a wall of tables. Network traffic naturally contains temporal information, source/destination relations, attack families, risk levels and behavioural differences. These should be visualised wherever visualisation improves understanding.

---

# 6. Locked Product Modules

The application contains four major screens/modules:

```text
1. SECURITY MONITOR
2. INCIDENT DETAIL
3. SECURITY PLAYGROUND
4. MODEL EVALUATION LAB
```

An optional fifth module may be added only after the core system is complete:

```text
5. APP SECURITY QUICK CHECK (stretch)
```

---

# 7. Module 1 — Security Monitor

The Security Monitor is the application's main dashboard. Its purpose is to simulate how the trained IDS would behave while network traffic is arriving.

The baseline project uses **traffic replay**, not live attack generation.

Recorded labelled network flows from the dataset are streamed/replayed progressively through the prediction pipeline.

Example:

```text
14:32:01   BENIGN
14:32:02   BENIGN
14:32:03   BENIGN
14:32:04   PORT SCAN
14:32:05   PORT SCAN
14:32:06   DDoS
```

This creates a live-style security-monitoring experience while remaining deterministic, reproducible, safe, easy to demonstrate and independent of live network permissions.

## 7.1 Summary Cards

The top dashboard should show only high-value metrics:

- Traffic analysed
- Suspicious flows
- Active incidents
- Current overall risk

Optional:

- Unknown/anomalous flows

Do not overload the header with many cards.

---

# 8. Known Attack Detection

The supervised classifier analyses a network-flow feature vector.

Example output:

```json
{
  "label": "DDoS",
  "family": "Denial of Service",
  "confidence": 0.97
}
```

The system supports binary classification:

```text
BENIGN
MALICIOUS
```

and multiclass/attack-family classification based on CICIDS2017.

For display and analysis, exact attack classes may be mapped into broader families:

```text
BENIGN

Denial of Service
├── DDoS
├── DoS Hulk
├── DoS GoldenEye
├── DoS Slowloris
└── DoS Slowhttptest

Brute Force
├── FTP-Patator
└── SSH-Patator

Reconnaissance
└── PortScan

Web Attack
├── Web Brute Force
├── XSS
└── SQL Injection

Botnet
└── Bot
```

The exact hierarchy must be generated from the final cleaned label set rather than assumed blindly.

---

# 9. Unknown / Anomalous Behaviour Detection

A second detector evaluates whether traffic strongly differs from normal behaviour.

### Primary model
**Isolation Forest**

Purpose:

```text
Does this traffic look significantly unlike normal network traffic?
```

Example:

```json
{
  "known_attack_confidence": 0.42,
  "anomaly_score": 0.83,
  "classification": "UNKNOWN_SUSPICIOUS"
}
```

The anomaly detector does not claim to identify the exact name of a new attack. Its role is to flag unusual behaviour that the known-attack classifier does not confidently recognise.

---

# 10. Hybrid Decision Layer

The supervised classifier and anomaly detector are combined through a lightweight deterministic decision layer.

Example:

```text
IF supervised confidence is high:
    use supervised known attack classification

ELSE IF anomaly score is high:
    label as UNKNOWN / SUSPICIOUS

ELSE:
    classify as BENIGN / LOW-CONFIDENCE NORMAL
```

Exact thresholds are configuration-driven and tuned during evaluation.

Possible outcomes:

```text
BENIGN
KNOWN ATTACK
UNKNOWN SUSPICIOUS
```

This hybrid architecture is one of the project's primary differentiators.

---

# 11. Risk Scoring

The project should not build another ML model merely to generate a risk score.

Risk is calculated transparently from:

- attack family severity,
- supervised confidence,
- anomaly score,
- optional incident volume/intensity.

Possible levels:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Example:

```text
Threat: DDoS
Confidence: 0.97
Anomaly score: 0.91
Risk: CRITICAL
```

The risk function must be documented and configurable. It is a project-level prioritisation indicator, not an industry-standard risk score.

---

# 12. Explainable Alerts

The system must not only say what it detected; it should explain which traffic features most influenced the prediction.

### Primary tool
**SHAP TreeExplainer**

Use SHAP with the final tree-based supervised model.

Example:

```text
Prediction:
DDoS — 96%

Why flagged:
1. Flow Packets/s
2. Packet Length Std
3. Flow IAT Mean
4. Bwd Packet Length Std
```

The UI should convert numerical feature contributions into readable statements where possible.

Example:

> Packet rate strongly increased the probability of a DDoS classification.

Raw SHAP values may remain available in an expandable technical section.

---

# 13. Behaviour vs Normal Baseline

An anomaly score alone is difficult for a human to understand.

For selected important features, compare current suspicious behaviour with a learned normal baseline.

Example:

```text
Normal median packet rate: 22 flows/sec
Current incident: 540 flows/sec

≈24.5× normal baseline
```

This provides the human-readable interpretation:

> “This traffic is far outside the behaviour normally observed.”

Simple descriptive baselines derived from benign training traffic are sufficient. A complex time-series anomaly model is not required.

---

# 14. Incident Grouping

One attack can generate hundreds of suspicious flows.

Related suspicious flows should be grouped into an **incident** using:

- attack family,
- source,
- destination,
- destination/service where useful,
- time window.

Example:

```text
Incident SEC-014

Type: Port Scan
Started: 14:05:18
Last Activity: 14:05:37
Suspicious Flows: 148
Source: Device A
Targets/Ports: 91 unique ports
Risk: HIGH
```

This remains rule-based. No clustering neural network is required.

---

# 15. Network Communication Graph

The Security Monitor includes an interactive communication graph.

### Tool
**Cytoscape.js**

Nodes represent hosts/devices, servers and optionally service/port nodes.

Edges represent observed communication.

Normal:

```text
PC-01 ───── Web Server
PC-02 ───── Web Server
Admin ───── Database
```

Port scan:

```text
             Service :21
            /
           Service :22
Source ──── Service :80
           \
            Service :443
```

DDoS:

```text
PC-1 ──┐
PC-2 ──┤
PC-3 ──┤
PC-4 ──┼──── Web Server
PC-5 ──┘
```

The graph is a **communication graph**, not a claim that the application reconstructed the physical network topology.

Clicking suspicious nodes should show risk, incident count, suspicious connections, attack prediction and anomaly score.

---

# 16. Dashboard Visualisations

## Mandatory

1. Network communication graph
2. Traffic / attack timeline
3. Incident behaviour vs normal baseline
4. Feature-contribution / explainability chart
5. Playground security-readiness result

## Supporting

- attack distribution
- risk distribution
- incident count over time
- normal vs suspicious traffic trend

Charts should be used because they clarify information, not for decoration.

---

# 17. Incident Detail Screen

Required sections:

### Incident Summary
- type
- risk
- start/end
- confidence
- anomaly score
- flow count

### Incident Network Graph
Only devices/relations associated with the selected incident.

### Attack Timeline
A small progression view.

### Why Flagged?
Top SHAP feature contributions.

### Behaviour vs Baseline
Compare 2–4 relevant features against benign traffic.

### Raw Evidence
Expandable selected flow table.

Raw data is secondary to the visual explanation.

---

# 18. Security Playground

The Playground gives users a personalised testing mode.

The user describes a basic environment and the system generates a relevant **security test profile**.

This is not penetration testing.

The playground uses existing/synthetic/replayed flow scenarios and must never automatically scan or attack a user-supplied IP/network.

---

# 19. Playground Questionnaire

Keep it deliberately short.

### Environment Type
- Personal / Home
- College / Computer Lab
- Small Organisation
- Web Application / Server Environment

### Approximate Scale
- 1–10 devices
- 10–50
- 50+

### Internet Exposure
- Internal only
- Some public services
- Public-facing server/application

### Services
- Web / HTTP(S)
- SSH
- FTP
- Database
- File sharing

No long infrastructure questionnaire.

---

# 20. Personalised Scenario Generation

Scenario generation is rule-based.

```text
IF SSH enabled:
    include SSH brute-force scenario

IF FTP enabled:
    include FTP brute-force scenario

IF public web environment:
    include web-attack scenario

IF public-facing / larger network:
    include DDoS scenario

IF multi-device environment:
    include Port Scan / reconnaissance

ALWAYS:
    include unknown anomaly scenario
```

No LLM is required.

---

# 21. Playground Test Execution

Prepared held-out scenario flows are passed through the exact same final detection pipeline.

Example:

```text
College Lab

Port Scan         DETECTED    95%
SSH Brute Force   DETECTED    91%
DDoS Burst        DETECTED    98%
Unknown Pattern   FLAGGED     anomaly 0.79
```

---

# 22. Security Readiness Report

The playground produces a concise report.

Example:

```text
Security Readiness
76 / 100
```

The score is based primarily on actual test outcomes.

Possible breakdown:

```text
Known attack detection      28/30
Unknown anomaly detection   17/20
Scenario coverage           16/20
False alert control         15/20
Explainability              10/10
```

Exact weights remain configurable.

---

# 23. Blind Spot Detection

The playground identifies the weakest tested area.

Example:

> **Blind Spot: Web Attack Detection**

> Web-attack samples produced lower detection confidence than the other relevant scenarios.

This is derived from test results. No extra model is required.

---

# 24. Playground Visualisations

Include:

- readiness score,
- scenario result matrix,
- risk distribution,
- known vs unknown detection coverage,
- strongest area,
- blind spot.

PDF export is optional and must not block completion.

---

# 25. Model Evaluation Lab

This page demonstrates the academic ML work.

### Models
- Logistic Regression baseline
- Random Forest
- XGBoost

### Metrics
- precision
- recall
- F1
- accuracy where useful
- ROC-AUC for binary evaluation where meaningful
- per-class metrics
- confusion matrix

### Additional
- feature importance
- optional SHAP global summary

---

# 26. Random vs Temporal Evaluation

The project must not rely only on a random train/test split.

Use:

## A. Random Stratified Split
Typical benchmark condition.

## B. Temporal Split
Train on earlier-day traffic and test on later-day traffic.

The selected cleaned CICIDS2017 Hugging Face dataset exposes:

```text
Random: 80/20 stratified split
Temporal: Train Monday–Thursday, Test Friday
```

The evaluation page visualises the performance difference as a **generalisation gap**.

This is one of the project's strongest academic differentiators because it adds quality without much implementation overhead.

---

# 27. Primary Dataset — CICIDS2017

Official source:

**Canadian Institute for Cybersecurity, University of New Brunswick**

https://www.unb.ca/cic/datasets/ids-2017.html

CICIDS2017 contains benign traffic and common attacks, with labelled flow CSVs and PCAPs. The official dataset provides flow information including timestamps, source/destination data, ports, protocols and attack labels.

This is the **single primary dataset**.

Do not add CICIDS2018, UNSW-NB15, NSL-KDD or another benchmark unless future evaluation proves a real need.

---

# 28. Dataset Convenience Layer

Preferred convenient source:

**Hugging Face — lacg030175/CICIDS2017**

https://huggingface.co/datasets/lacg030175/CICIDS2017

Reasons:

- derived from CICIDS2017,
- cleaned numeric flow features,
- Parquet format,
- random split,
- temporal split,
- easier loading,
- reduced manual wrangling.

Current dataset card exposes roughly:

```text
Temporal:
Train ~2.125M
Test  ~0.703M

Random:
Train ~2.262M
Test  ~0.566M
```

Exact counts must be read from the version used during implementation.

Always cite the original CICIDS2017 source/paper academically.

---

# 29. Dataset Size / Hardware Strategy

Millions of rows can create unnecessary RAM/training pressure.

### Development
Use a class-aware representative subset, approximately:

```text
200k–500k flows
```

for quick iteration.

### Final Evaluation
Use as much of the cleaned dataset as feasible.

If full multiclass training is too slow:

- retain minority attack samples where feasible,
- downsample dominant benign traffic,
- document the sampling ratio.

Never silently remove rare classes.

---

# 30. Feature Preparation

CICIDS2017 already contains engineered flow-level features.

Baseline preprocessing may include:

- invalid/non-finite handling,
- duplicate column cleanup,
- label normalisation,
- class mapping,
- train/test separation,
- scaling only where needed,
- class imbalance handling.

Do not standardise tree models without a reason.

---

# 31. Feature Selection

Keep feature selection lightweight.

1. remove invalid/redundant features,
2. inspect model feature importance,
3. optionally evaluate a top-N feature subset.

If a reduced feature set preserves performance, prefer it for faster inference and clearer explanations.

Do **not** use PCA in the final explainable runtime model because transformed components reduce interpretability.

---

# 32. Supervised Models

## Logistic Regression
Purpose: baseline only.

## Random Forest
Primary candidate.

Use:

`sklearn.ensemble.RandomForestClassifier`

Why:
- strong on tabular data,
- CPU-friendly,
- robust,
- class weights,
- easy feature importance,
- SHAP TreeExplainer support.

## XGBoost
Primary competitor.

Use:

`xgboost.XGBClassifier`

Why:
- strong tabular performance,
- efficient histogram training,
- CPU support,
- sklearn-style API,
- SHAP support.

---

# 33. Final Known-Attack Model Selection

Compare Logistic Regression, Random Forest and XGBoost on:

- macro F1,
- weighted F1,
- per-class recall,
- false-positive behaviour,
- temporal generalisation,
- inference cost.

Do not choose solely by accuracy.

Expected final candidate:
- Random Forest or XGBoost.

SVM is excluded from the locked baseline because it adds unnecessary training cost at CICIDS scale.

No deep-learning classifier is mandatory.

---

# 34. Anomaly Detection

## Primary
**Isolation Forest**

Use:

`sklearn.ensemble.IsolationForest`

Preferred protocol:

```text
fit primarily on benign training traffic
evaluate on held-out benign + malicious/unseen flows
```

Calibrate threshold using validation data.

---

# 35. Why No Autoencoder in Baseline?

The original synopsis mentioned an Autoencoder as an anomaly option.

It is deliberately excluded from the baseline because it introduces:

- deep-learning framework overhead,
- architecture tuning,
- reconstruction threshold tuning,
- more hardware dependence.

Fallback only:

Use a small Autoencoder only if Isolation Forest clearly underperforms and project time remains.

---

# 36. Explainability Stack

## SHAP TreeExplainer

https://shap.readthedocs.io/

Use with the selected Random Forest/XGBoost model.

### Local explanations
Why one flow was flagged.

### Global explanations
Which features matter overall.

Core dashboard uses local explanations; Model Lab may include global summaries.

---

# 37. Reference GitHub Repositories

These are references, not codebases to copy wholesale.

## CICIDS2017 ML Pipeline
https://github.com/noushinpervez/Intrusion-Detection-CICIDS2017

Useful for:
- preprocessing,
- imbalance handling,
- binary/multiclass evaluation,
- confusion matrices,
- baseline comparisons.

## Strong Tree-Based IDS Research Reference
https://github.com/Western-OC2-Lab/Intrusion-Detection-System-Using-Machine-Learning

Useful for:
- Random Forest/XGBoost patterns,
- sampled CICIDS workflows,
- ML experimentation.

Do not adopt its larger ensemble/AutoML stack.

## Simple Dashboard Architecture Reference
https://github.com/Akashcp111/ML-IDS-Machine-Learning-Enhanced-Intrusion-Detection-System

Useful for:
- simple project structure,
- model artifact flow,
- dashboard-style IDS demonstration.

Do not add Snort unless a later optional live-input experiment requires it.

## Explainable IDS Reference
https://github.com/ogarreche/XAI_NIDS

Useful for:
- SHAP patterns,
- local/global explanations,
- CICIDS2017 XAI examples.

---

# 38. Backend Architecture

## FastAPI

Suggested routes:

```text
POST   /api/predict
POST   /api/replay/start
POST   /api/replay/stop
GET    /api/replay/status

GET    /api/incidents
GET    /api/incidents/{id}

POST   /api/playground/profile
POST   /api/playground/run
GET    /api/playground/results/{id}

GET    /api/evaluation/models
GET    /api/evaluation/metrics
```

No authentication is required in baseline scope.

---

# 39. Frontend Architecture

Locked stack:

- React
- TypeScript
- Vite
- Tailwind CSS

React is preferred over Streamlit because the design includes:

- interactive network graph,
- multiple screens,
- incident drill-down,
- replay controls,
- playground workflow,
- custom visualisations.

Emergency fallback:
Streamlit only if frontend schedule becomes a serious delivery risk.

---

# 40. Visualisation Stack

## General charts
**Recharts**

Use for:
- timelines,
- attack distribution,
- risk distribution,
- model metrics,
- SHAP contribution bars,
- readiness reports,
- random vs temporal comparison.

## Network graph
**Cytoscape.js**

Do not write a custom network renderer.

---

# 41. Database

Use **SQLite**.

Store:

```text
predictions
incidents
incident_flows
playground_profiles
playground_runs
playground_results
```

Do not store the entire training dataset in SQLite. Training remains in Parquet/CSV.

---

# 42. Traffic Replay Engine

Processing:

```text
read next flow
    ↓
preprocess
    ↓
supervised classifier
    ↓
anomaly detector
    ↓
hybrid decision
    ↓
SHAP if suspicious
    ↓
incident grouping
    ↓
persist/update UI
```

Controls:
- Start
- Pause
- Stop
- Speed

Example speeds:
- 1x
- 5x
- 20x

Polling is acceptable initially. Add WebSockets only if needed after baseline reliability.

---

# 43. Optional Live Traffic Input

Not core.

**NFStream** may be evaluated after core completion because it supports PCAP/live interfaces and network-flow aggregation.

Important limitation:

CICIDS2017 uses CICFlowMeter-style features. NFStream's feature schema will not automatically match the trained model.

Therefore do not promise live traffic unless a reliable feature mapping exists.

---

# 44. Playground Architecture

```text
USER PROFILE
    ↓
RULE-BASED SCENARIO SELECTOR
    ↓
PREPARED SCENARIO SAMPLES
    ↓
FINAL HYBRID IDS PIPELINE
    ↓
TEST OUTCOMES
    ↓
READINESS SCORE
    ↓
BLIND SPOT
    ↓
VISUAL REPORT
```

No additional ML model is required for personalisation.

---

# 45. Prepared Scenario Library

Example structure:

```text
scenarios/
├── ddos/
├── port_scan/
├── ssh_bruteforce/
├── ftp_bruteforce/
├── web_attack/
├── botnet/
├── benign/
└── unknown_anomaly/
```

Each scenario contains representative held-out flows and expected metadata.

The unknown scenario must be built through a controlled experiment rather than fake “zero-day” claims.

---

# 46. Unknown-Attack Experiment

Preferred approaches:

## Option A — Held-Out Attack Family
Remove one family from supervised training, then test those flows later. Isolation Forest attempts to flag them as anomalous.

Use only one or two families.

## Option B — Temporal Unseen Classes
Use the temporal split where later-day attacks are unseen in earlier training, if the label distribution supports the experiment cleanly.

Use wording:

> **unseen / unknown anomaly simulation**

Do not claim real zero-day exploit detection.

---

# 47. Evaluation Metrics

## Binary
- accuracy
- precision
- recall
- F1
- ROC-AUC
- confusion matrix

## Multiclass
- macro F1
- weighted F1
- per-class precision
- per-class recall
- confusion matrix

## Anomaly
- precision
- recall
- F1
- false-positive rate
- anomaly-score distributions

## Operational
- inference time
- SHAP latency
- replay throughput
- incident grouping correctness on prepared scenarios.

---

# 48. Model Evaluation Visuals

Include only meaningful visuals:

1. model comparison chart
2. confusion matrix
3. random vs temporal split chart
4. top feature importance
5. optional SHAP global summary
6. anomaly score distribution if useful

---

# 49. Hardware Requirements

Target:

- Intel Core i5 / AMD Ryzen 5 equivalent
- 8 GB RAM minimum
- 16 GB recommended
- SSD
- CPU-only runtime

GPU is not required.

Optional free compute:
- Google Colab
- Kaggle notebooks

The final demo must work without a dedicated GPU.

---

# 50. Software Stack

## Python / ML
```text
Python 3.x
pandas
numpy
scikit-learn
xgboost
shap
joblib
pyarrow
matplotlib
```

## Backend
```text
FastAPI
Uvicorn
Pydantic
SQLAlchemy
```

## Frontend
```text
React
TypeScript
Vite
Tailwind CSS
Recharts
Cytoscape.js
```

## Database
```text
SQLite
```

## Development
```text
Git
GitHub
Jupyter Notebook
VS Code
Postman / Bruno
```

---

# 51. Optional Vibe-Coded App Security Quick Check

**Stretch scope only.**

Purpose:

A developer uploads a small project/repository snapshot and receives a basic security hygiene report.

This is static application security, separate from the NIDS model.

Possible tools:

### Python security
**Bandit**

### Secret detection
**Gitleaks**

### Optional additional scanner
Semgrep may be evaluated only if its local/open usage remains straightforward for project needs.

Do not build a custom SAST engine.

---

# 52. App Quick Check Findings

Possible categories:

- hardcoded secrets,
- common unsafe Python patterns,
- insecure configuration,
- wildcard CORS,
- debug mode,
- basic dependency warnings if easy.

Example:

```text
CRITICAL
Hardcoded API credential

HIGH
Potential unsafe database query

MEDIUM
Wildcard CORS
```

This module aggregates existing tool findings and must not be presented as part of the trained IDS.

---

# 53. App Quick Check Decision Rule

Implement only if:

1. all four core screens are stable,
2. ML evaluation is complete,
3. replay/dashboard is complete,
4. sufficient time remains.

Otherwise leave it as future scope.

---

# 54. Security and Ethical Boundaries

The project must not:

- launch attacks against external networks,
- scan arbitrary public IP ranges,
- generate harmful traffic,
- automatically exploit systems,
- block/modify real traffic.

The Playground uses prepared/simulated samples.

Optional live input is passive only.

---

# 55. Repository Structure

```text
project/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── db/
│   │   ├── services/
│   │   │   ├── inference/
│   │   │   ├── anomaly/
│   │   │   ├── explainability/
│   │   │   ├── incidents/
│   │   │   ├── replay/
│   │   │   └── playground/
│   │   └── main.py
│   ├── models/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── charts/
│   │   ├── network/
│   │   └── services/
│
├── ml/
│   ├── notebooks/
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   └── artifacts/
│
├── data/
│   ├── processed/
│   └── scenarios/
│
├── docs/
├── config/
└── README.md
```

Do not commit the full CICIDS2017 dataset.

---

# 56. Model Artifact Contract

Persist:

```text
supervised model
anomaly model
preprocessor
label mapping
feature schema
benign baselines
model metadata
```

Example:

```text
ml/artifacts/
├── supervised_model.joblib
├── isolation_forest.joblib
├── scaler.joblib
├── label_mapping.json
├── feature_schema.json
├── benign_baselines.json
└── model_metadata.json
```

XGBoost may use its native model format.

---

# 57. Configuration

Important thresholds must be config-driven.

Example:

```yaml
inference:
  known_confidence_threshold: 0.75
  anomaly_threshold: -0.10

incidents:
  grouping_window_seconds: 30

risk:
  critical_threshold: 85
  high_threshold: 65
  medium_threshold: 40

replay:
  default_speed: 5
```

These are initial placeholders; final values come from evaluation.

---

# 58. Implementation Roadmap

The project is divided into **five substantial phases**.

---

## Phase 1 — Dataset, Research Baseline and Project Foundation

### Goal
Establish data pipeline, architecture and reproducible baselines.

### Work

**Dataset**
- obtain cleaned CICIDS2017 derivative,
- verify against official dataset description,
- inspect labels/classes,
- build development subset,
- establish random and temporal splits.

**ML Baseline**
- Logistic Regression,
- basic Random Forest,
- initial XGBoost,
- binary + multiclass evaluation.

**Application**
- repository structure,
- FastAPI skeleton,
- React/Vite frontend,
- SQLite,
- shared schemas.

### Deliverables
- dataset loader,
- preprocessing pipeline,
- baseline metrics,
- feature schema,
- working frontend/backend skeleton.

### Completion Gate
```text
load dataset
→ preprocess flow
→ train baseline
→ call prediction API
```

---

## Phase 2 — Final Detection Intelligence

### Goal
Complete the core ML pipeline.

### Work

**Supervised**
- light RF/XGBoost tuning,
- select final model.

Avoid large hyperparameter searches.

**Anomaly**
- Isolation Forest,
- threshold calibration,
- unknown/unseen experiment.

**Hybrid**
- known classification,
- anomaly score,
- hybrid decision,
- risk.

**Explainability**
- SHAP,
- local explanations,
- benign baselines.

**Academic**
- random vs temporal evaluation.

### Deliverables
- final supervised artifact,
- anomaly artifact,
- hybrid engine,
- risk engine,
- SHAP,
- evaluation results.

### Completion Gate
One flow returns:

```json
{
  "classification": "...",
  "family": "...",
  "confidence": 0.0,
  "anomaly_score": 0.0,
  "risk": "...",
  "top_features": []
}
```

---

## Phase 3 — Monitor, Incidents and Visual Intelligence

### Goal
Turn models into an understandable monitoring experience.

### Work
- replay engine,
- speed controls,
- incident grouping,
- summary metrics,
- traffic stream,
- attack timeline,
- Cytoscape communication graph,
- attack/risk charts,
- Incident Detail page,
- behaviour vs baseline,
- SHAP chart.

### Deliverables
- Security Monitor,
- network graph,
- incident pages,
- replay.

### Completion Gate
```text
normal traffic
→ suspicious flows
→ grouped incident
→ explainable incident detail
```

---

## Phase 4 — Personalised Security Playground

### Goal
Build the differentiating interactive layer without increasing ML complexity.

### Work
- minimal environment questionnaire,
- scenario rules,
- held-out scenario sets,
- test runner,
- readiness score,
- blind spot logic,
- visual report.

### Deliverables
- Playground page,
- scenario generator,
- personalised test results.

### Completion Gate

Different profiles produce different logical suites.

```text
College Lab
→ SSH + Port Scan + DDoS + anomaly

Web Server
→ Web Attack + DDoS + brute force + anomaly
```

---

## Phase 5 — Evaluation, Quality Hardening and Final Presentation

### Goal
Convert the prototype into a strong academic submission.

### Work

**Evaluation**
- final dataset runs,
- binary metrics,
- multiclass metrics,
- temporal evaluation,
- anomaly evaluation,
- unknown experiment,
- latency.

**Model Lab**
- model comparison,
- confusion matrix,
- random vs temporal,
- feature importance,
- anomaly results.

**Quality**
- error handling,
- model metadata,
- replay reliability,
- loading states,
- tests,
- UI polish.

**Documentation**
- setup,
- architecture,
- methodology,
- dataset citations,
- limitations,
- demo guide.

**Optional**
- evaluate App Security Quick Check only after core completion.

### Deliverables
- final system,
- reproducible evaluation,
- polished dashboard,
- report,
- presentation/demo.

---

# 59. Team Distribution

## Member 1 — Data & Known-Attack ML
- CICIDS2017
- preprocessing
- data quality
- labels
- Logistic Regression
- Random Forest
- XGBoost
- model comparison
- random/temporal experiments

## Member 2 — Anomaly, Explainability & Incident Intelligence
- Isolation Forest
- unknown experiment
- SHAP
- benign baselines
- hybrid decision
- risk
- incident grouping
- playground scoring/rules

## Member 3 — Application & Visualisation
- FastAPI
- SQLite
- replay
- React
- Cytoscape.js
- Recharts
- Security Monitor
- Incident Detail
- Playground UI
- Model Lab UI

All participate in integration, testing, documentation and final evaluation.

---

# 60. Key Demo Scenarios

## Scenario A — Port Scan
Show:
- normal traffic,
- one source contacting many ports,
- graph fan-out,
- Port Scan prediction,
- grouped incident,
- explanation.

## Scenario B — DDoS
Show:
- traffic spike,
- many flows targeting a server,
- critical risk,
- baseline comparison.

## Scenario C — Unknown Suspicious Activity
Show:
- supervised low confidence,
- high anomaly,
- UNKNOWN SUSPICIOUS.

## Scenario D — Playground
Profile:
```text
College Lab
20–50 devices
SSH enabled
public web service
```
Generate test suite and readiness report.

## Scenario E — Generalisation Lab
Show random vs temporal performance.

---

# 61. Project Quality Principles

## Reuse First
Use established:
- CICIDS2017,
- scikit-learn,
- XGBoost,
- SHAP,
- FastAPI,
- Cytoscape.js.

## Explainability First
Avoid black-box results where a readable explanation is possible.

## CPU First
Every mandatory feature must run without a dedicated GPU.

## Evaluation First
A feature should improve detection, understanding, evaluation or interaction.

## Minor-Project Discipline
Choose reproducible and well-evaluated over technically flashy but fragile.

---

# 62. Explicit Non-Goals

The core project will not include:

- production live packet blocking,
- firewall control,
- SIEM integration,
- Kafka,
- Elasticsearch,
- Kubernetes,
- user management,
- cloud SOC deployment,
- malware reverse engineering,
- active exploitation,
- automated IP scanning,
- paid threat intelligence,
- paid APIs,
- LSTM/Transformer IDS,
- reinforcement learning,
- federated learning,
- agentic security automation.

---

# 63. Fallback Decision Matrix

| Capability | Primary | Backup | Backup Trigger |
|---|---|---|---|
| Known classifier | RF/XGBoost after evaluation | whichever performs better | F1 + temporal performance + latency |
| Baseline | Logistic Regression | none | comparison only |
| Anomaly | Isolation Forest | lightweight Autoencoder | only if IF clearly fails and time remains |
| Explainability | SHAP TreeExplainer | native feature importance | if SHAP becomes blocking |
| Dashboard | React + FastAPI | Streamlit | only if frontend schedule becomes critical |
| Network graph | Cytoscape.js | simplified connection view | only if graph integration is unstable |
| Charts | Recharts | static evaluation charts | only if frontend charting blocks delivery |
| Dataset | cleaned CICIDS2017 HF derivative | official MachineLearningCSV | if derivative validation fails |
| Replay | dataset flow replay | prepared scenario CSV replay | if full replay is too heavy |
| Live network | not baseline | NFStream | after core completion only |
| App scanner | not baseline | Bandit + Gitleaks | optional stretch only |

---

# 64. Academic Limitations

The final report must state:

1. CICIDS2017 is a benchmark dataset and does not represent every modern network.
2. Dataset replay is not equivalent to live enterprise deployment.
3. UNKNOWN SUSPICIOUS does not mean discovery of a real zero-day exploit.
4. Anomaly detection can produce false positives.
5. SHAP explains model contribution, not causal attack mechanisms.
6. Communication graphs represent observed relationships, not physical topology.
7. Playground readiness is not a cybersecurity certification.

---

# 65. Reference Resource Register

## Primary Dataset
CICIDS2017 — Canadian Institute for Cybersecurity  
https://www.unb.ca/cic/datasets/ids-2017.html

## Convenient Cleaned Dataset
https://huggingface.co/datasets/lacg030175/CICIDS2017

## Random Forest / Isolation Forest
https://scikit-learn.org/

## XGBoost
https://xgboost.readthedocs.io/

## Explainability
https://shap.readthedocs.io/

## Backend
https://fastapi.tiangolo.com/

## Network Visualisation
https://js.cytoscape.org/

## Optional Flow Capture
https://www.nfstream.org/

## Optional Python Security
https://bandit.readthedocs.io/

## Optional Secret Detection
https://github.com/gitleaks/gitleaks

---

# 66. Coding-Agent Instructions

This PRD is the architecture source of truth for Codex/OpenCode/other coding models.

1. Do not replace CICIDS2017 without explicit instruction.
2. Do not add deep-learning IDS models by default.
3. Do not add SVM to the main training pipeline unless requested.
4. Do not implement live attack generation.
5. Do not introduce user authentication.
6. Do not add production SOC infrastructure.
7. Keep replay as the baseline monitoring input.
8. Keep Isolation Forest as the baseline anomaly detector.
9. Keep SHAP associated with the selected tree classifier.
10. Keep network graph semantics as communication relationships.
11. Keep thresholds config-driven.
12. Do not claim zero-day attack identification.
13. Optional modules must not become core dependencies.
14. Prefer open-source tools over custom infrastructure.
15. Preserve low-end CPU execution.
16. Prediction responses must retain class, confidence, anomaly score, risk and explanation where applicable.
17. Incidents must retain underlying evidence/flow IDs.
18. Reject or simplify features that conflict with minor-project scope.
19. Architecture changes require evaluation evidence or explicit team decision.

---

# 67. Architecture Lock

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
      ┌──────┴─────────┐
      ▼                ▼
SECURITY MONITOR   SECURITY PLAYGROUND
      │                │
      ▼                ▼
Network Graph      Personalised Scenarios
Timeline           Readiness Report
Incidents          Blind Spots
      │
      ▼
INCIDENT DETAIL
      │
      ▼
MODEL EVALUATION LAB
```

Mandatory stack:

```text
Python
Pandas / NumPy
Scikit-learn
XGBoost
SHAP

FastAPI
SQLite

React
TypeScript
Vite
Tailwind CSS
Recharts
Cytoscape.js
```

Mandatory ML:

```text
Logistic Regression — baseline
Random Forest — supervised candidate
XGBoost — supervised candidate
Isolation Forest — anomaly detector
```

No GPU-required model is mandatory.

---

# 68. Final Product Definition

The finished project is:

> **An explainable AI-assisted network security monitoring and evaluation system that classifies known malicious traffic, flags unfamiliar anomalous behaviour, groups related suspicious flows into incidents, explains why activity was detected, visualises communication patterns, and allows users to run personalised security-evaluation scenarios for their type of network environment.**

It should answer:

```text
WHAT happened?
WHAT does the model think it is?
HOW confident is it?
HOW abnormal is it?
WHY was it flagged?
WHICH machines/flows were involved?
IS this one larger incident?
HOW does it compare to normal behaviour?
HOW well does the detector perform for my environment?
WHERE are its current blind spots?
```

---

# 69. Final Scope Rule

If time becomes constrained, priority is:

```text
1. Correct dataset + evaluation
2. Known classifier
3. Isolation Forest
4. Explainability
5. Incident grouping
6. Monitor + visualisations
7. Playground
8. Model Lab polish
9. Optional live input
10. Optional app security scanner
```

Items 1–8 form the intended complete project.

Items 9–10 are strictly optional.

The guiding principle is:

> **Build the smallest system that convincingly demonstrates high-quality ML, explainable security reasoning, useful interaction, and rigorous evaluation.**

---

**End of PRD**
