# Project context for maintainers

This is a navigation brief; the [PRD](../Network_IDS_Security_Evaluation_PRD.md), approved decisions and source code define scope and current behavior. Current public-facing documentation is indexed at [docs/README.md](README.md).

## Purpose and current status

Student-scale academic flow-based intrusion detection and scenario evaluation using CICIDS2017. Phase 4's first Playground workflow and the UI redesign are implemented and validated in the recorded 2026-10-31 checks. The application currently has Security Monitor, Incidents/detail and Security Playground views. The PRD's Model Evaluation Lab is not implemented. Phase 5 research, full Model Lab, expanded investigation, live input and operational integrations remain deferred.

## Runtime facts

- Input: exactly 77 ordered CICIDS2017 flow features; inference does not consume ground truth.
- Models: XGBoost multiclass `xgb_200` and benign-trained Isolation Forest; model binaries are local/ignored and not present in a clean clone.
- Hybrid order: confident non-benign class (`>=0.75`) -> `KNOWN_ATTACK`; else IF score `<-0.0928` -> `UNKNOWN_SUSPICIOUS`; else `BENIGN`. IF score is a raw decision function, not probability.
- SHAP: XGBoost native TreeSHAP for supervised predicted-class margin only.
- Data: pinned cleaned `lacg030175/CICIDS2017` revision `d071fd53782d9ca7cdc15173b8ceb858fea04628`; random/temporal experiments remain separate.
- Runtime: FastAPI, SQLAlchemy, single-process SQLite, in-process replay worker, React/TypeScript UI with polling. Host graph is stable directed SVG; ports are connection metadata.
- Playground: deterministic profile rules select prepared fixtures; synchronous execution <=64 flows; saved results are separate from Monitor predictions/incidents; score describes fixture outcomes only.

## Scope boundaries

No live capture, arbitrary scanning, attack generation, automated mitigation, zero-day claim, real-network certification, authentication, enterprise deployment, external alerting, drift monitoring, extra datasets/models, or LLM personalization. See [project overview](project-overview.md), [architecture](architecture.md), [ML/evaluation](ml-pipeline.md), [evaluation limitations](machine-learning/evaluation.md) and [implementation status](IMPLEMENTATION_STATUS.md).

## Repository map

`backend/app/` APIs/services/schemas/SQLite; `frontend/src/` views/components/client; `ml/preprocessing/`, `training/`, `evaluation/`, `hybrid/`; `data/scenarios/` prepared fixtures; `config/config.yaml`; `ml/artifacts/` contracts/metadata and local binary models; `docs/` guides and historical phase/decision records.

## Required reading for implementation changes

Follow `AGENTS.md`: read the entire PRD, architecture lock, data/ML contract, current status/phase/handoff and relevant decisions/bugs/tests; inspect source before edits; test behavior; use atomic UTF-8 updates for governance/history files. Do not expand scope without explicit authorization.
