# Phase 1 — Dataset, Research Baseline and Project Foundation

Source: PRD §58 (Phase 1). This is the active phase.

## Goal

Establish the data pipeline, architecture, and reproducible baselines.

## PRD Scope

**Dataset (PRD §27–29):**
- Obtain cleaned CICIDS2017 derivative (HF `lacg030175/CICIDS2017`).
- Verify against official CICIDS2017 description.
- Inspect labels/classes.
- Build development subset (~200k–500k class-aware flows).
- Establish random and temporal splits.

**ML Baseline (PRD §32, §33):**
- Logistic Regression (baseline only).
- Basic Random Forest.
- Initial XGBoost.
- Binary + multiclass evaluation.

**Application (PRD §38, §39, §41, §55):**
- Repository structure.
- FastAPI skeleton.
- React/Vite frontend skeleton.
- SQLite.
- Shared schemas.

## Explicitly Out of Scope During This Phase

- Final model selection (Phase 2).
- Isolation Forest tuning / threshold calibration / unknown experiment
  (Phase 2).
- Hybrid decision, risk, SHAP, baselines (Phase 2).
- Replay engine, incident grouping, dashboards, Cytoscape graph (Phase 3).
- Playground (Phase 4).
- Model Evaluation Lab UI (Phase 5).

A tiny interface/schema decision required to prevent later integration
problems is the only exception.

## Required Deliverables (PRD §58 Phase 1)

- Dataset loader.
- Preprocessing pipeline.
- Baseline metrics.
- Feature schema.
- Working frontend/backend skeleton.

## Implementation Tasks

- [x] **Inspect first (do NOT blindly download/materialise the entire
      dataset):** read the HF `lacg030175/CICIDS2017` dataset card, config
      and split names, schema, available metadata, and stream a small sample.
      (Done 2026-08-09 — see `data/processed/dataset_inspection_cicids2017.json` and DEC-001.)
- [x] Verify the random config (80/20 stratified) and the temporal config —
      specifically HOW the Monday–Thursday train / Friday test split is
      provided. It is a **precomputed config+split partition with NO timestamp
      column** (verified; see DATA_ML_CONTRACT §18).
- [x] Verify the derivative against the official CICIDS2017 description
      (PRD §27) — confirmed via dataset card (CICFlowMeter features, 15 classes,
      CC BY 4.0, cite Sharafaldin et al. 2018).
- [x] Record in `docs/DATA_ML_CONTRACT.md`: exact HF revision/config/split
      names, observed row counts, raw feature columns + dtypes, actual label
      set, temporal metadata. (Done — sections 1,2,2a,3,4,8,9,18 marked `[SET]`.)
- [x] Build the label → family mapping from the real cleaned label set.
      (Done — 15 classes mapped; Heartbleed/Infiltration left as rare
      categories. See DATA_ML_CONTRACT §9, DEC-003.)
- [x] **Then** decide the class-aware ~200k–500k development subset strategy
      (size, per-class ratios, seed, minority-class handling) and record it.
      (DEC-004: target 300,000, per_class_cap 60,000, cap_floor 8,000, seed 42.)
- [x] Materialise only the development subset needed (not the full dataset).
      (`dev_random_train.parquet` + `dev_temporal_train.parquet`, 300k each,
      with `.meta.json` — see DATA_ML_CONTRACT §2a.)
- [x] Implement preprocessing (non-finite handling, duplicate-column cleanup,
      label normalisation, class mapping, train/test separation, class
      imbalance handling, scaling per model family per
      `docs/DATA_ML_CONTRACT.md` §13) — no test-data leakage; scaler fit on
      train only. (`ml/preprocessing/preprocess.py` + `labels.py`.)
- [x] Lock the feature schema (`feature_schema.json`) and canonical ordering.
      (77 features, version 1.0 — DEC-005.)
- [x] Train Logistic Regression baseline (with scaling); record binary +
      multiclass metrics. (random: acc 0.8673 bin / 0.9470 mc; temporal: 0.7519 / 0.5827)
- [x] Train initial Random Forest (no scaling); record binary + multiclass
      metrics. (random: acc 0.9985 bin / 0.9983 mc; temporal: 0.7044 / 0.5887)
- [x] Train initial XGBoost (no scaling); record binary + multiclass metrics.
      (random: acc 0.9979 bin / 0.9987 mc; temporal: 0.7040 / 0.5889)
- [x] Scaffold FastAPI skeleton (PRD §38 routes as stubs, no auth).
      (`backend/app/main.py` — `/api/predict` wired, `/api/health`.)
- [x] Scaffold React/Vite/TypeScript/Tailwind frontend shell.
      (`frontend/` — builds with `npm run build`.)
- [x] Set up SQLite schema (PRD §41 tables). (All 6 tables; predictions persisted.)
- [x] Define shared Pydantic schemas. (`backend/app/schemas/predict.py`.)
- [x] Wire a minimal `POST /api/predict` that runs the baseline end-to-end.
      (Validated via API tests + live HTTP calls.)

## Dependencies / Prerequisites

- Python deps installed here (recorded in `requirements.txt` + SPRINT_LOG).
- Dataset revision/configs locked via DEC-001.

## Files / Components Expected (PRD §55)

- `ml/preprocessing/`, `ml/training/`, `ml/notebooks/`.
- `backend/app/` (api, schemas, db, services), `backend/app/main.py`.
- `frontend/src/` (pages, components, charts, network, services).
- `data/processed/`, `config/`, `ml/artifacts/` (schema files).

## Validation Plan

- Data tests: row counts, label set, feature ordering, no leakage, no silent
  minority-class removal (see `docs/TESTING.md` §1).
- ML reproducibility: fixed seed reproduces split + metrics; random and
  temporal splits kept distinct.
- API: `POST /api/predict` returns a baseline prediction for one flow.
- Run the Phase-1 completion gate end-to-end.

## Completion Gate (PRD §58)

```text
load dataset → preprocess flow → train baseline → call prediction API
```

## Completion Gate Evidence

**Status: COMPLETE — run end-to-end on 2026-08-09.**

**Audit decision (2026-08-09): PHASE 1 VALIDATED.** A final correctness
audit re-verified every gate component from source + executed artifacts
instead of relying on prior summaries. Results:
- Temporal leakage check: `dev_temporal_train.parquet` contains exactly the
  12 Monday–Thursday classes (verified from the materialised file); NO
  Bot/DDoS/PortScan present. Source `temporal/train` distribution matches.
- Feature contract: 77 canonical features; order verified identical across
  `preprocess.py`, `feature_schema.json`, `inference/feature_order.json`,
  `model_metadata.json`, and the API predictor; equals raw parquet order
  minus the verified duplicate `Fwd Header Length.1`.
- Labels: raw parquet codepoints re-checked (U+FFFD in the three Web Attack
  classes); canonical hyphen forms deterministic; mappings match the
  persisted artifacts.
- Inference artifact: `model_metadata.json` clearly marks
  `"phase": "phase-1-baseline"` / "Provisional ... final model selection in
  Phase 2."
- Metrics: `baseline_metrics_{random,temporal}.json` include
  precision/recall/F1/macro/weighted F1/per-class/confusion matrix/ROC-AUC.
- Tests re-run: `python -m pytest ml/tests -q` → 13 passed;
  `python -m pytest backend/tests -q` → 4 passed (17 total);
  `npm run build` → PASS.
- Live E2E: uvicorn + `POST /api/predict` → 200, correct label, missing
  feature → 422, invalid value → 422, prediction persisted to SQLite.

Commands executed (Python: `C:\Users\BIT\.pyenv\pyenv-win\versions\3.10.11\python.exe`):

```text
# 1. Load dataset (revision-locked HF derivative, random/train + random/test)
python -c "from ml.preprocessing.dataset import LoadConfig, load_split; ..."
   -> random/train 2,262,300 rows; random/test 565,576 rows

# 2. Preprocess a flow (drop duplicate col, normalise labels, canonical order)
python -m pytest ml/tests -q           -> 13 passed (preprocessing invariants)

# 3. Train baselines (LR / RF / XGB, binary + multiclass, random + temporal)
python -m ml.training.train_baseline --experiments random temporal --models lr rf xgb
   -> ml/evaluation/results/baseline_metrics_{random,temporal}.json
   -> ml/artifacts/baselines/*.joblib

# 4. Promote Phase-1 inference model (XGB multiclass, random)
python -m ml.training.export_inference_model
   -> ml/artifacts/inference/{model.joblib,model_metadata.json,feature_order.json}

# 5. Call prediction API (FastAPI + SQLite, live HTTP)
python -m uvicorn backend.app.main:app --port 8000
POST /api/predict {"flow_id":"gate-0","features":{...77 canonical features...}}
   -> {"prediction_id":1,"classification":"MALICIOUS","label":"DoS Hulk",
       "family":"Denial of Service","confidence":0.9999,
       "model_name":"xgb-multiclass (random experiment)",
       "model_version":"phase-1-baseline"}
   -> truth label matched prediction for 3/3 sampled flows
```

Baseline metrics summary (full detail in
`ml/evaluation/results/baseline_metrics_*.json`):

```text
=== random (train 300k dev subset, test = full random/test 565,576) ===
        binary (acc/F1/AUC)              multiclass (acc/macroF1/wF1)
LR   :  0.8673 / 0.7468 / 0.9759         0.9470 / 0.5344 / 0.9514
RF   :  0.9985 / 0.9963 / 0.9997         0.9983 / 0.8156 / 0.9983
XGBoost: 0.9979 / 0.9947 / 0.9999        0.9987 / 0.8877 / 0.9987

=== temporal (train 300k dev subset of Mon–Thu, test = Friday 702,718) ===
NOTE: Friday test classes (BENIGN, PortScan, DDoS, Bot) are partially unseen
at training time; multiclass reflects the intended generalisation gap.
        binary (acc/F1/AUC)              multiclass (acc/macroF1/wF1)
LR   :  0.7519 / 0.5997 / 0.7139         0.5827 / 0.0529 / 0.4675
RF   :  0.7044 / 0.4391 / 0.7576         0.5887 / 0.0532 / 0.4701
XGBoost: 0.7040 / 0.4391 / 0.7332        0.5889 / 0.0533 / 0.4711
```

Full automated test suite: `python -m pytest ml/tests backend/tests -q`
→ **17 passed**.
Frontend: `npm run build` (frontend/) → **PASS**.

## Current Status

COMPLETE (2026-08-09). All Phase-1 deliverables exist and are validated:
dataset loading, preprocessing, feature schema, dev subsets, LR/RF/XGBoost
baselines, FastAPI + SQLite + shared schemas, React/Vite/Tailwind shell, and
the end-to-end prediction gate. See `docs/IMPLEMENTATION_STATUS.md`.

Audit decision issued 2026-08-09: **PHASE 1 VALIDATED** — all 8 audit checks
passed (see Completion Gate Evidence above). The only defect found was
documentation-only: SPRINT_LOG.md was not valid UTF-8 (BUG-003, FIXED).

## Blockers

None. BUG-001 (duplicate `Fwd Header Length` column) resolved in
preprocessing (feature set is 77 unique columns). BUG-002 (HF loader
misdiagnosis) corrected. BUG-003 (SPRINT_LOG.md invalid UTF-8) fixed during
the Phase-1 audit (2026-08-09).

## Decisions Made During This Phase

- DEC-001 — dataset revision/configs locked.
- DEC-002 — HF loader: positional config canonical; `config_name=` is an
  API quirk, not a HF bug.
- DEC-003 — canonical labels use ASCII hyphens (U+FFFD normalised), not
  en-dashes.
- DEC-004 — dev subset: 300k, per_class_cap 60k, cap_floor 8k, seed 42.
- DEC-005 — feature schema locked at 77 features; `Fwd Header Length.1` dropped.
- DEC-006 — Phase-1 inference model = XGBoost multiclass (random).
