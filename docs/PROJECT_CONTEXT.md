# PROJECT_CONTEXT.md — Compact Project Briefing for Agents

This is a navigation/orientation document, NOT a replacement for the PRD.
Always read the full PRD (`Network_IDS_Security_Evaluation_PRD.md`) for
authoritative detail. References below use `PRD §N` notation.

---

## Project Purpose

Build an **Explainable Hybrid Network Intrusion Detection and Security
Evaluation System** (PRD §1, §68). It converts large volumes of raw
network-flow data into a small number of understandable, explainable security
incidents, and lets users run personalised security-evaluation scenarios.

It answers: WHAT happened? What does the model think it is? How confident?
How abnormal? WHY flagged? Which machines/flows? Is this one incident? How
does it compare to normal? How well does the detector perform for my
environment? Where are its blind spots? (PRD §68)

This is a **student-scale final-year/semester minor project**, team of 3
(PRD header, §59). It is explicitly NOT a production SOC, firewall, SIEM,
enterprise IDS, or penetration-testing platform (PRD §1, §62, §64).

---

## Target Users (PRD §4)

College/lab network administrators, small organisations, developers managing
small servers/networks, cybersecurity students, security analysts learning
IDS behaviour, technical teams evaluating basic monitoring readiness.

---

## Major Product Modules (PRD §6)

Four core screens:

1. **Security Monitor** — main dashboard with replay-driven live monitoring
   (PRD §7, §15, §16).
2. **Incident Detail** — drill-down on grouped suspicious flows (PRD §17).
3. **Security Playground** — personalised scenario-based security evaluation
   (PRD §18–24, §44).
4. **Model Evaluation Lab** — academic ML comparison & random-vs-temporal
   generalisation (PRD §25, §26, §47, §48).

Optional stretch (only after all core gates pass): **App Security Quick
Check** (PRD §51–53).

---

## Core ML Concept (PRD §10, §67)

Hybrid, deterministic decision layer combining:

- **Supervised known-attack classifier** (Random Forest or XGBoost after
  evaluation; Logistic Regression is baseline only) — PRD §32, §33.
- **Isolation Forest anomaly detector** (primary; Autoencoder only as fallback
  if IF clearly fails) — PRD §34, §35.
- **SHAP TreeExplainer** for local/global explainability — PRD §36.
- **Benign baseline comparison** for human-readable behaviour contrast —
  PRD §13.
- **Rule-based incident grouping** (family + source + destination +
  service/port + time window) — PRD §14.
- **Transparent risk scoring** (LOW/MEDIUM/HIGH/CRITICAL from family
  severity, confidence, anomaly score, optional volume) — PRD §11.

Hybrid outcomes: `BENIGN`, `KNOWN ATTACK`, `UNKNOWN SUSPICIOUS`.

---

## Primary Dataset (PRD §27–29)

- **CICIDS2017** (Canadian Institute for Cybersecurity, UNB) — single
  primary dataset. Do not add CICIDS2018 / UNSW-NB15 / NSL-KDD.
- **Convenience layer:** Hugging Face `lacg030175/CICIDS2017` (cleaned,
  Parquet, exposes random + temporal splits).
- Always cite the original CICIDS2017 source/paper academically.
- Development subset ~200k–500k class-aware flows; final evaluation uses as
  much as feasible. Never silently remove rare classes.

---

## Mandatory Stack (PRD §50, §67)

**ML (Python, CPU):** pandas, numpy, scikit-learn, xgboost, shap, joblib,
pyarrow, matplotlib.

**Backend:** FastAPI, Uvicorn, Pydantic, SQLAlchemy, **SQLite**.

**Frontend:** React, TypeScript, Vite, Tailwind CSS, **Recharts**,
**Cytoscape.js**.

No GPU-required model is mandatory. The final demo must run on CPU
(i5/Ryzen 5, 8–16 GB RAM, SSD) — PRD §49.

---

## Student-Scale Constraints (PRD §49, §61, §62)

CPU-first, free/open-source, minimal infrastructure, no production-grade
overengineering, reproducible. Choose reproducible+well-evaluated over
flashy-but-fragile. Reuse established tools (CICIDS2017, scikit-learn,
XGBoost, SHAP, FastAPI, Cytoscape.js).

---

## Important Terminology (PRD §8, §10, §11, §14, §46)

- **Flow** — one network-flow record (CICFlowMeter-style features).
- **Replay** — deterministic streaming of recorded labelled flows through the
  pipeline (NOT live attack generation) — PRD §7, §42.
- **Family** — broader attack grouping (e.g. Denial of Service, Brute Force,
  Reconnaissance, Web Attack, Botnet). Hierarchy must be generated from the
  actual cleaned label set, not assumed — PRD §8.
- **Hybrid decision** — deterministic combination of supervised confidence +
  anomaly score → BENIGN / KNOWN ATTACK / UNKNOWN SUSPICIOUS — PRD §10.
- **Incident** — group of related suspicious flows — PRD §14.
- **UNKNOWN SUSPICIOUS** — does NOT mean real zero-day detection; it is an
  unseen/unknown anomaly simulation — PRD §46, §64.

---

## Explicit Non-Goals (PRD §62)

No: production live packet blocking, firewall control, SIEM integration,
Kafka, Elasticsearch, Kubernetes, user management/authentication, cloud SOC
deployment, malware reverse engineering, active exploitation, automated IP
scanning, paid threat intelligence / paid APIs, LSTM/Transformer IDS,
reinforcement learning, federated learning, agentic security automation.

---

## Current Active Phase

Phase 1 — Dataset, Research Baseline and Project Foundation.
See `docs/PHASES/PHASE_1.md` and `docs/IMPLEMENTATION_STATUS.md`.

---

## PRD Section Index (quick reference)

| PRD § | Topic |
|-------|-------|
| 1–5   | Vision, problem, users |
| 6–17  | Product modules: Monitor, detection, hybrid, risk, SHAP, baseline, incidents, graph, dashboard |
| 18–24 | Security Playground |
| 25–26 | Model Evaluation Lab, random vs temporal |
| 27–31 | Dataset, size strategy, feature prep/selection |
| 32–36 | Supervised models, selection, anomaly, no-autoencoder rationale, SHAP |
| 37    | Reference GitHub repos (references only) |
| 38–43 | Backend, frontend, viz stack, DB, replay, optional live input |
| 44–48 | Playground architecture, scenarios, unknown experiment, metrics, visuals |
| 49–50 | Hardware, software stack |
| 51–53 | Optional App Security Quick Check (stretch) |
| 54    | Ethical boundaries |
| 55–57 | Repo structure, artifact contract, configuration |
| 58    | Implementation roadmap (5 phases) |
| 59    | Team distribution |
| 60–64 | Demo scenarios, quality principles, non-goals, fallback matrix, academic limitations |
| 65–69 | Resources, coding-agent instructions, architecture lock, final definition, scope rule |
