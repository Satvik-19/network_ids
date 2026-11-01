# Phase 5 — Evaluation, Quality Hardening and Final Presentation

Source: PRD §58 (Phase 5), §47, §48, §51–53, §64. Active only after Phase 4
gate passes.

## Goal

Convert the prototype into a strong, reproducible academic submission with a
polished demo.

## PRD Scope

**Evaluation (PRD §47):**
- Final dataset runs.
- Binary metrics (accuracy, precision, recall, F1, ROC-AUC, confusion
  matrix).
- Multiclass metrics (macro F1, weighted F1, per-class precision/recall,
  confusion matrix).
- Temporal evaluation (generalisation gap).
- Anomaly evaluation (precision, recall, F1, FPR, score distributions).
- Unknown experiment results.
- Latency (inference time, SHAP latency, replay throughput, incident
  grouping correctness).

**Model Evaluation Lab (PRD §25, §48):**
- Model comparison (LR / RF / XGBoost).
- Confusion matrix.
- Random vs temporal split chart.
- Top feature importance.
- Optional SHAP global summary.
- Optional anomaly-score distribution.

**Quality:**
- Error handling; model metadata; replay reliability; loading states; tests;
  UI polish.

**Documentation (PRD §64):**
- Setup, architecture, methodology, dataset citations, limitations,
  demo guide. State academic limitations (CICIDS2017 ≠ every modern
  network; replay ≠ live deployment; UNKNOWN SUSPICIOUS ≠ real zero-day;
  anomaly false positives possible; SHAP ≠ causation; graphs ≠ topology;
  playground ≠ certification).

**Optional (stretch, PRD §51–53):**
- App Security Quick Check (Bandit + Gitleaks; optional Semgrep) — ONLY if
  all four core screens are stable, ML evaluation complete, replay/dashboard
  complete, and time remains. Must not be presented as part of the trained
  IDS. Do not build a custom SAST engine.

## Explicitly Out of Scope / Boundaries

- No live attack generation, no scanning arbitrary IPs (PRD §54).
- No new datasets / models beyond locked candidates (PRD §62).
- App Quick Check must not become a core dependency (PRD §53, §69).

## Required Deliverables (PRD §58 Phase 5)

- Final system.
- Reproducible evaluation.
- Polished dashboard.
- Report.
- Presentation / demo.

## Implementation Tasks

- [ ] Run final binary + multiclass + temporal + anomaly + unknown +
      latency evaluations; record metrics reproducibly.
- [ ] Build Model Evaluation Lab UI (comparison, confusion matrix, random vs
      temporal, feature importance, optional global SHAP, optional anomaly
      distribution).
- [ ] Harden error handling, loading states, replay reliability.
- [ ] Add/expand tests across ML, backend, frontend.
- [ ] UI polish across all four core screens.
- [x] Write setup / architecture / methodology / limitations / demo docs (documentation reference set completed 2026-11-01; full Phase-5 gate remains incomplete).
- [x] Cite CICIDS2017 source + dataset paper; a peer-reviewed dataset-quality study is included as a literature-review starting reference.
- [ ] (Optional, stretch) Evaluate App Security Quick Check only after core
      completion; gate it behind PRD §53 conditions.

## Dependencies / Prerequisites

- Phases 1–4 complete (full core system).

## Files / Components Expected

- `ml/evaluation/` (final reproducible evaluation scripts + outputs).
- `frontend/src/pages/` (ModelLab).
- `docs/` (final user/academic documentation), `README.md`.

## Validation Plan

- Reproducible evaluation: fixed seed + recorded config reproduces all
  reported metrics.
- Model Lab charts render from real evaluation outputs.
- Full end-to-end demo of all key demo scenarios (PRD §60 A–E).
- Final completion gate: final system + reproducible evaluation + polished
  demo.

## Completion Gate (PRD §58 Phase 5)

Final system + reproducible evaluation + polished dashboard + report +
presentation/demo.

## Completion Gate Evidence

`TBD — fill when gate passes`.

## Current Status

Documentation reference deliverables completed 2026-11-01 under the user
authorized documentation audit. The broader Phase-5 gate remains NOT COMPLETE:
final research runs, Model Evaluation Lab, latency evaluation and other remaining
quality/presentation tasks are not claimed complete.

## Blockers

No blocker for the completed documentation task. Remaining Phase-5 deliverables
are deferred and require their own scope/authorization.

## Decisions Made During This Phase

(Record: final reported metrics, evaluation config/version, Model Lab chart
choices, App Quick Check go/no-go per PRD §53.)
