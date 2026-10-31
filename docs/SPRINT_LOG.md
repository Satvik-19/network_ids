# SPRINT_LOG.md — Permanent Append-Only Engineering Work Journal

Every meaningful coding session / agent task appends ONE structured entry
below. **Never rewrite old entries** to make history cleaner — corrections
are added as later entries.

---

## [2026-08-08 23:30] — Bootstrap Agent (GLM-5.2) — Project bootstrap & governance scaffolding

### Objective

Perform the project-bootstrap/governance task: read the entire PRD, inspect
the repository, and create the documentation/control system that every future
AI coding agent must use. Explicitly NOT implement Phase 1 application or ML
functionality.

### Phase

Pre-Phase-1 (governance). Relevant gate context: Phase 1 gate = load dataset
→ preprocess flow → train baseline → call prediction API (PRD §58).

### Context Reviewed

- `Network_IDS_Security_Evaluation_PRD.md` — read in full (all 69 sections,
  2066 lines).
- Repository root inspected — contained only the PRD; no existing code, docs,
  `.gitignore`, or configuration.
- Bootstrap charter (pasted-text instructions) — followed item-by-item.

### Work Performed

- Created the agent-operating documentation system required by the charter.
- Populated every document from the actual PRD (no generic boilerplate, no
  invented facts).
- Scaffolded `docs/DATA_ML_CONTRACT.md` with `TBD — requires validation`
  placeholders for all dataset-derived facts.
- Created the five phase documents directly from the PRD roadmap (§58) and
  gates.
- Created `.gitignore` reflecting PRD §55 git discipline.

### Files Created

- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/ARCHITECTURE_LOCK.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/HANDOFF.md`
- `docs/SPRINT_LOG.md`
- `docs/DECISIONS.md`
- `docs/BUG_LOG.md`
- `docs/TESTING.md`
- `docs/DATA_ML_CONTRACT.md`
- `docs/PHASES/PHASE_1.md`
- `docs/PHASES/PHASE_2.md`
- `docs/PHASES/PHASE_3.md`
- `docs/PHASES/PHASE_4.md`
- `docs/PHASES/PHASE_5.md`
- `.gitignore`

### Files Modified

None (repository previously contained only the PRD).

### Files Deleted

None.

### Key Implementation Decisions

- **Decision:** Treat the HF `lacg030175/CICIDS2017` derivative as the
  intended convenience dataset per PRD §28, but record NO concrete dataset
  facts (row counts, columns, labels) until Phase 1 inspection proves them.
  **Reasoning:** PRD §28 itself states "Exact counts must be read from the
  version used during implementation"; bootstrap must not invent values.
- **Decision:** Set every component to `NOT STARTED` and Phase 1 gate to
  `NOT STARTED`. **Reasoning:** no application/ML code exists; bootstrap was
  governance-only.
- **Decision:** Not scaffold FastAPI/React or install dependencies.
  **Reasoning:** charter items 13–17 explicitly forbid this during bootstrap.

### Commands Executed

```text
ls -la   (repository inspection — Windows/Git Bash)
```

### Testing / Validation

- No code was produced, so no tests ran.
- A self-review against the PRD was performed (see "Architecture / Contract
  Impact").

### Problems Encountered

None.

### Resolutions

N/A.

### Unresolved Issues

None introduced. (Open Phase-1 questions are recorded as
`TBD — requires validation` in `docs/DATA_ML_CONTRACT.md`.)

### Architecture / Contract Impact

None. No architecture was changed. The locked architecture was faithfully
recorded, not altered.

### Dependencies Added or Changed

None. Dependency files (`requirements.txt`, `package.json`, etc.) were NOT
created during bootstrap, by instruction.

### Data / Model Impact

None. No dataset downloaded, no models trained, no artifacts created.

### Next Recommended Action

First concrete Phase 1 implementation task: obtain the cleaned CICIDS2017
derivative (HF `lacg030175/CICIDS2017`), verify it against the official
CICIDS2017 description (PRD §27), inspect labels/classes, and record observed
row counts, raw columns, and the actual cleaned label set in
`docs/DATA_ML_CONTRACT.md`. Do not begin until instructed.

### Handoff Notes

- Read the PRD in full before any code (AGENTS.md Start Protocol).
- `docs/DATA_ML_CONTRACT.md` contains many `TBD — requires validation`
  placeholders that Phase 1 MUST fill from real inspection — never guess.
- The attack-family hierarchy in PRD §8 is illustrative; the final mapping
  must be generated from the actual cleaned label set (PRD §8).
- No `.gitignore` entries for dependency lockfiles yet because no dependency
  files exist; revisit when `backend/` and `frontend/` are scaffolded.

---

## [2026-08-09 00:10] — Bootstrap Agent (GLM-5.2) — Post-bootstrap governance corrections

### Objective

Apply five targeted corrections to the governance docs found during PRD
review. No Phase 1 implementation; no dependencies, dataset, or code.

### Phase

Pre-Phase-1 (governance).

### Work Performed

1. `docs/ARCHITECTURE_LOCK.md` — corrected the pipeline diagram so the four
   application modules (Security Monitor, Incident Detail, Security
   Playground, Model Evaluation Lab) appear as DISTINCT major modules per
   PRD §6/§67, not a chain. Only Monitor → Incident Detail drill-down is
   preserved; Playground leads to scenarios/readiness/blind spots; Lab is a
   separate academic module.
2. `docs/DATA_ML_CONTRACT.md` §13 scaling — made model-specific: RF/XGBoost no
   scaling by default; Logistic Regression requires scaling (fit on train
   only, persisted); Isolation Forest no scaling by default, revisit only
   with experimental evidence.
3. `docs/DATA_ML_CONTRACT.md` §2 and §18 temporal split — removed the
   assumption that we reconstruct the Mon–Thu/Fri split from a timestamp
   column; Phase 1 must first verify how the HF config provides it and use
   the native mechanism.
4. `docs/DECISIONS.md` — removed DEC-001 (session history, not an
   architectural decision; no implementation has started, so removal is
   safe — the bootstrap session remains in this sprint log). Added an
   "Expected ADR topics" list (dataset revision/config, sampling, label
   mapping, preprocessing contract, API contract, final model selection,
   etc.).
5. Refined the immediate Phase 1 next step across `docs/HANDOFF.md`,
   `docs/PHASES/PHASE_1.md`, `docs/IMPLEMENTATION_STATUS.md`: inspect/verify
   HF config + revision FIRST (streaming/sample, no full materialisation),
   verify random + temporal configs/schema/labels/metadata, THEN decide the
   ~200k–500k class-aware subset strategy.

### Files Created

None.

### Files Modified

- `docs/ARCHITECTURE_LOCK.md`
- `docs/DATA_ML_CONTRACT.md`
- `docs/DECISIONS.md`
- `docs/HANDOFF.md`
- `docs/PHASES/PHASE_1.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/SPRINT_LOG.md` (this entry)

### Files Deleted

None.

### Key Implementation Decisions

- **Decision:** Treat DEC-001 as session history, not an ADR; remove it.
  **Reasoning:** ADRs are for substantive architectural/implementation
  decisions; bootstrap scope is procedural and already in the sprint log.
- **Decision:** Make scaling model-specific rather than leaving it as a
  single TBD. **Reasoning:** the per-model defaults are PRD-determined
  (§30/§32); only the LR scaler type/feature set and any IF experiment
  remain TBD.

### Commands Executed

None (documentation edits only).

### Testing / Validation

No code; no tests. Re-read edited sections against PRD §6, §17, §26, §30,
§32, §67 for consistency.

### Problems Encountered

None.

### Resolutions

N/A.

### Unresolved Issues

None. All five requested corrections applied. The remaining open items are
Phase-1 empirical questions already marked `TBD — requires validation`.

### Architecture / Contract Impact

None — corrections bring the docs INTO stricter alignment with the PRD; no
locked decision was changed.

### Dependencies Added or Changed

None.

### Data / Model Impact

None.

### Next Recommended Action

Unchanged in spirit, refined in wording: inspect/verify the HF dataset
config + revision first (no full materialisation), then decide the
development subset strategy. Do not begin until instructed.

### Handoff Notes

- Diagram in `docs/ARCHITECTURE_LOCK.md` now matches PRD §6/§67 module
  independence.
- Temporal-split handling now defers to whatever mechanism the HF dataset
  exposes — do not pre-assume a timestamp-column reconstruction.
- ADR log is empty pending the first substantive Phase-1 decision.

---

## [2026-08-09] — Lead Agent — Phase 1: project foundation + dataset inspection

### Objective

Phase 1 foundation only: create the PRD §55 repository structure, set up
Python dependencies, and inspect/verify HF `lacg030175/CICIDS2017` before any
preprocessing/subset/training. Explicitly NOT building the dev subset,
preprocessing, models, React, or FastAPI (still Phase 1 scope gates).

### Phase

Phase 1 — Dataset, Research Baseline and Project Foundation.
Completion gate (not yet attempted end-to-end): load dataset → preprocess
flow → train baseline → call prediction API.

### Context Reviewed

- `Network_IDS_Security_Evaluation_PRD.md` (§55 structure, §27–29 dataset).
- `AGENTS.md` (Start/End protocols), `docs/PHASES/PHASE_1.md`,
  `docs/HANDOFF.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DATA_ML_CONTRACT.md`.

### Work Performed

- Created PRD §55 repo structure with `.gitkeep`:
  `backend/{app/{api,schemas,db,services},models,tests}`,
  `ml/{notebooks,preprocessing,training,evaluation,artifacts,tests}`,
  `data/{processed,scenarios}`, `config/`. Preserved existing `docs/`.
- Created `requirements.txt` (pandas, numpy, scikit-learn, xgboost, shap,
  joblib, pyarrow, matplotlib, datasets, fastapi, uvicorn, pydantic,
  sqlalchemy, pytest) and installed them (pyenv Python 3.10.11). All imports
  verified.
- Created `config/config.yaml` with placeholder thresholds (PRD §57) + pinned
  dataset revision.
- Wrote `ml/preprocessing/inspect_dataset.py` (metadata + label-column scan,
  no full download) and a minimal reusable loader `ml/preprocessing/dataset.py`
  (revision-locked parquet read via hf://, optional column projection) plus
  `ml/__init__.py`, `ml/preprocessing/__init__.py`.
- Inspected the live dataset and the HF dataset card.

### Files Created

- `requirements.txt`, `config/config.yaml`
- `ml/__init__.py`, `ml/preprocessing/__init__.py`
- `ml/preprocessing/inspect_dataset.py`
- `ml/preprocessing/dataset.py`
- `data/processed/dataset_inspection_cicids2017.json` (verified facts)
- directory skeletons (with `.gitkeep`) per PRD §55

### Files Modified

- `docs/DATA_ML_CONTRACT.md` (verified sections 1,2,2a,4,8,9,18,23)
- `docs/IMPLEMENTATION_STATUS.md`, `docs/HANDOFF.md`, `docs/DECISIONS.md`
  (added DEC-001), `docs/BUG_LOG.md` (added BUG-001), `docs/PHASES/PHASE_1.md`

### Key Implementation Decisions (see DECISIONS.md)

- **DEC-001:** Locked HF revision `d071fd53...` + configs (`random`,
  `temporal`, 3-way variants) after empirical verification. Loader loads
  parquet directly via `hf://` URL for reliability (the HF
  `load_dataset_builder`/`streaming` `config_name` path errored for this
  dataset).

### Commands Executed

```text
pip install -r requirements.txt
python -c "import pandas, numpy, sklearn, xgboost, shap, joblib, pyarrow, matplotlib, datasets, fastapi, uvicorn, pydantic, sqlalchemy"   # OK
python ml/preprocessing/inspect_dataset.py          # wrote inspection JSON
python -c loader smoke tests (load_split / load_label_scan)  # PASS
```

### Testing / Validation

- **Import validation:** all Phase-1 deps import cleanly. PASS.
- **Dataset inspection:** revision, configs, per-split counts, full schema
  (80 cols), full 15-class label set, and temporal mechanism verified and
  written to `data/processed/dataset_inspection_cicids2017.json`. PASS.
- **Loader smoke tests:** loaded `temporal_3way/validation` (351,359 × 80),
  label-only scan of `temporal/test` (702,718 rows → classes BENIGN/Bot/DDoS/
  PortScan only — confirms Friday holdout), and column projection on
  `random/train`. PASS.

### Problems Encountered

- HF `load_dataset_builder(config_name=...)` and `load_dataset(...,
  streaming=True, config_name=...)` raised a `config_name` keyword conflict
  for this dataset. Worked around by reading parquet directly via
  `hf://...{revision}/...` URLs. Documented in the loader docstring.
- Duplicate column `Fwd Header Length` / `Fwd Header Length.1` are identical
  (data-quality item — BUG-001 OPEN; to be fixed in preprocessing).

### Resolutions

- Used `huggingface_hub` metadata + `fsspec`+`pyarrow` parquet reads.
- Recorded the duplicate column as BUG-001 for the preprocessing step.

### Unresolved Issues

- BUG-001 OPEN (duplicate column — fix in preprocessing).
- Dev-subset, preprocessing contract, `feature_schema.json`, and multiclass
  integer encoding remain TBD (deliberately — not yet built).

### Architecture / Contract Impact

None. DATA_ML_CONTRACT filled with verified facts; no locked decision changed.

### Dependencies Added or Changed

Added `requirements.txt` (14 packages, all in PRD §50 + `datasets` for HF
loading + `pytest` for tests). Each recorded here per the dependency rule.

### Data / Model Impact

Verified dataset facts recorded; no cleaning/subset/training performed. No
model artifacts created.

### Next Recommended Action

Build the Phase-1 preprocessing pipeline: drop duplicate `Fwd Header
Length.1`, handle non-finite values, derive label/family mapping, define the
canonical feature order into `feature_schema.json`, then build the class-aware
dev subset from `random/train` (seed 42). Then train LR/RF/XGBoost baselines.

### Handoff Notes

- Verified facts live in `data/processed/dataset_inspection_cicids2017.json`
  and `docs/DATA_ML_CONTRACT.md`. Use loader `ml/preprocessing/dataset.py`
  (do NOT re-inspect the full dataset).
- 15 classes locked; families derived; `label` is binary. Temporal has NO
  timestamp column — use precomputed `temporal` config. Dev-subset must keep
  all minority attack rows; downsample only BENIGN/big-DoS with seed 42.


---

## [2026-08-09 22:00] - Phase 1 Completion Agent - Finish Phase 1 (recovery of interrupted session)

### Objective

Audit the interrupted Phase-1 state (do NOT restart), then complete every
remaining Phase-1 deliverable and run the completion gate end-to-end:
preprocessing, dev subsets, feature schema, LR/RF/XGBoost baselines,
FastAPI + SQLite + shared schemas, React/Vite/Tailwind shell, and a working
POST /api/predict.

### Phase

Phase 1 - Dataset, Research Baseline and Project Foundation. Gate:
load dataset -> preprocess flow -> train baseline -> call prediction API (PRD §58).

### Context Reviewed

- All governance docs (AGENTS.md, PRD, PROJECT_CONTEXT, ARCHITECTURE_LOCK,
  IMPLEMENTATION_STATUS, HANDOFF, PHASE_1, DATA_ML_CONTRACT, DECISIONS,
  BUG_LOG, TESTING, SPRINT_LOG).
- Existing `ml/preprocessing/dataset.py` + `inspect_dataset.py`.
- Config, .gitignore, existing dir skeletons.

### Work Performed

- Recovery audit (Items A-G): re-verified dataset access, official UNB page,
  duplicate column (bit-for-bit equal on all 4 canonical partitions), schema
  (80 cols = 78 features + Label + label), env/generic-python mismatch
  (pyenv 3.10.11 env is the working one; PATH python is a different install).
- `ml/preprocessing/labels.py`: canonical labels (U+FFFD -> ASCII hyphen),
  FAMILY_MAP, LABEL_TO_INT/INT_TO_LABEL, binary_target, CANONICAL_LABELS.
- `ml/preprocessing/preprocess.py`: RAW_FEATURE_COLUMNS (77), DUPLICATE_COLUMNS
  (Fwd Header Length.1), clean_numeric, fit_scaler, preprocess_frame.
- `ml/preprocessing/subset.py`: build_dev_subset (target 300k, cap 60k,
  floor 8k, seed 42), load_dev_subset.
- Materialised `data/processed/dev_random_train.parquet` + `dev_temporal_train.parquet`
  (300k each) with `.meta.json`.
- Artifacts: `ml/artifacts/{feature_schema.json,label_mapping.json,family_mapping.json}`.
- `ml/evaluation/metrics.py`; `ml/training/train_baseline.py`;
  `ml/training/export_inference_model.py`.
- `ml/tests/test_preprocessing.py` (13 tests).
- Backend: `backend/app/{main.py, api/predict.py, services/predictor.py,
  schemas/predict.py, db/{database,models}.py}`; `backend/tests/test_api.py`.
- Frontend: `frontend/` React+TS+Vite+Tailwind shell; `npm run build` PASS.
- Docs: DATA_ML_CONTRACT corrected to [SET]; DEC-002..006; BUG-001 FIXED +
  BUG-002 WONTFIX; PHASE_1 gate evidence; IMPLEMENTATION_STATUS, HANDOFF,
  TESTING updated.

### Files Created

- `ml/preprocessing/labels.py`, `ml/preprocessing/preprocess.py`,
  `ml/preprocessing/subset.py`, `ml/evaluation/metrics.py`,
  `ml/training/train_baseline.py`, `ml/training/export_inference_model.py`,
  `ml/tests/test_preprocessing.py`
- `ml/artifacts/{feature_schema,label_mapping,family_mapping}.json`
- `ml/artifacts/baselines/*.joblib`, `ml/artifacts/inference/*`
- `ml/evaluation/results/baseline_metrics_{random,temporal}.json`
- `data/processed/dev_{random,temporal}_train.parquet(.meta.json)`
- `backend/app/**` (main, api, services, schemas, db), `backend/tests/test_api.py`
- `frontend/**` (Vite React TS Tailwind shell)
- `requirements-lock.txt`

### Files Modified

- `ml/preprocessing/dataset.py` (docstring correction re: HF quirk)
- `docs/DATA_ML_CONTRACT.md`, `docs/DECISIONS.md`, `docs/BUG_LOG.md`,
  `docs/TESTING.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/HANDOFF.md`,
  `docs/PHASES/PHASE_1.md`

### Key Implementation Decisions (see DECISIONS.md)

- **DEC-002:** HF loader: positional config is canonical; config_name= keyword
  is an API-argument quirk of this derivative's packaged builder, NOT an HF
  bug. Kept direct hf:// parquet loading as the efficient default.
- **DEC-003:** canonical Web Attack labels use ASCII hyphens (U+FFFD normalised).
- **DEC-004:** dev subset 300k, per_class_cap 60k, cap_floor 8k, seed 42.
- **DEC-005:** feature schema locked at 77 features; Fwd Header Length.1 dropped.
- **DEC-006:** Phase-1 inference model = XGBoost multiclass (random experiment).

### Commands Executed

```text
python -m pytest ml/tests -q                              # 13 passed
python -m ml.training.train_baseline --experiments random temporal --models lr rf xgb
python -m ml.training.export_inference_model
python -m pytest backend/tests -q                         # 4 passed
python -m pytest ml/tests backend/tests -q                # 17 passed
python -m uvicorn backend.app.main:app --port 8000        # health + live predict
npm install && npm run build                              # frontend PASS
```

### Testing / Validation

- Preprocessing invariant tests PASS (duplicate dropped, 77 unique features,
  schema artifact matches, non-finite safety net, no leakage, sampling
  reproducible, dev-subset contract).
- Baselines: random - LR bin 0.8673 / mc 0.9470; RF bin 0.9985 / mc 0.9983;
  XGB bin 0.9979 / mc 0.9987. Temporal (generalisation gap expected) - see
  baseline_metrics_temporal.json.
- Inference model: top-1 agreement 0.998 on random/test sample; mean
  confidence 0.9981.
- Backend API tests PASS (health, predict E2E + DB persist, 422 on
  missing/extra features). Live HTTP: 3/3 sampled flows matched truth.
- SQLite: all 6 PRD §41 tables created; prediction rows persisted.
- Frontend: npm run build PASS (tsc + vite).
- Phase-1 gate: load -> preprocess -> train -> /api/predict PASS.

### Problems Encountered

- Temporal multiclass XGBoost raised "Invalid classes inferred from unique
  values of y" (class ids must be contiguous). Fixed by remapping the classes
  present in temporal/train to a contiguous range, then un-mapping predictions.
- Initial backend tests failed on DB path (backend/data did not exist) and
  on get_predictor import location; both fixed.
- Prior docs claimed en-dash Web Attack labels and dtype counts int64 x52 /
  float64 x26 - corrected to U+FFFD-normalised hyphen forms and int64 x55 /
  float64 x24 / large_string x1 (verified).

### Resolutions

- Remapped contiguous class ids in train_baseline.py multiclass path.
- Moved SQLite DB to project-root data/ and created the dir; fixed the health
  endpoint import.
- Corrected DATA_ML_CONTRACT and recorded DEC-003.

### Unresolved Issues

- None blocking Phase 1.
- Temporal multiclass generalisation gap is expected behaviour (unseen Friday
  classes), documented in DATA_ML_CONTRACT §18.
- Thresholds in config/config.yaml remain placeholders until Phase-2
  calibration (PRD §57).

### Next Recommended Action

Begin Phase 2: Isolation Forest anomaly detector (no scaling) on the random
dev subset, anomaly-threshold calibration on random/test (record calibrated
values in config + DECISIONS), then final supervised model selection
(RF vs XGBoost) with full metrics. Update PHASE_2.md before coding.
---

## [2026-08-09 23:45] - Phase 1 Audit Agent - Final Phase-1 correctness audit

### Objective

Perform a correctness and reproducibility audit of the completed Phase-1
deliverables against the PRD, DATA_ML_CONTRACT, and ARCHITECTURE_LOCK, then
decide the Phase-1 gate. The audit was requested after the previous session
(after the Phase-1 completion agent ended). Do NOT restart or re-implement any
completed work; verify existing artifacts and evidence instead.

### Phase

Phase 1 - Dataset, Research Baseline and Project Foundation. Gate:
load dataset -> preprocess flow -> train baseline -> call prediction API (PRD §58).

### Context Reviewed

- All governance docs (AGENTS.md, PRD, PROJECT_CONTEXT, ARCHITECTURE_LOCK,
  IMPLEMENTATION_STATUS, HANDOFF, PHASE_1, DATA_ML_CONTRACT, DECISIONS,
  BUG_LOG, TESTING, SPRINT_LOG).
- Phase-1 source: ml/preprocessing/{labels,preprocess,subset,dataset}.py,
  ml/evaluation/metrics.py, ml/training/{train_baseline,export_inference_model}.py,
  ml/tests/test_preprocessing.py, backend/app/** (main, api, services, schemas,
  db), backend/tests/test_api.py, frontend/** config, config/config.yaml.
- Artifacts: ml/artifacts/{feature_schema,label_mapping,family_mapping}.json,
  ml/artifacts/inference/*, ml/evaluation/results/baseline_metrics_{random,temporal}.json,
  data/processed/dev_{random,temporal}_train.parquet(.meta.json), data/network_ids.db.

### Work Performed

- Ran the full 8-check audit. All checks PASS (details below).
- Re-ran the test suites: ml (13 passed), backend (4 passed), frontend build PASS.
- Ran a live end-to-end API call against uvicorn: health OK, predict 200 with the
  correct label (DoS Hulk), 422 on missing feature, 422 on invalid value, and the
  prediction persisted to SQLite.
- Verified the feature contract: 77 features, identical order across
  preprocess.py CANONICAL_FEATURE_COLUMNS, feature_schema.json,
  inference/feature_order.json and model_metadata.json; equals raw parquet order
  minus the duplicate column (Fwd Header Length.1), re-verified bit-for-bit.
- Verified label handling: raw labels contain U+FFFD (0xfffd); canonical hyphen
  forms and label/family mapping JSONs are deterministic and match labels.py.
- Verified dev subsets: 300k each (in the 200-500k target range), seed 42,
  class-aware capping, minority classes retained, .meta.json records before/after
  counts; no temporal leakage (dev_temporal_train has exactly 12 Mon-Thu classes,
  NO Bot/DDoS/PortScan).
- Verified baseline_metrics_{random,temporal}.json contain the complete metric set
  (binary + multiclass macro/weighted F1, per-class, confusion matrix).
- Verified model_metadata.json marks the inference artifact as provisional
  phase-1-baseline with a note that final model selection happens in Phase 2.
- Verified SQLite: all 6 PRD §41 tables exist with coherent schemas.
- Confirmed the API schema exposes only Phase-1 fields.

### Audit Decision

PHASE 1 GATE: VALIDATED. Evidence in docs/PHASES/PHASE_1.md and
docs/IMPLEMENTATION_STATUS.md.

### Files Modified

- docs/PHASES/PHASE_1.md (gate evidence + decision)
- docs/IMPLEMENTATION_STATUS.md (governance docs -> VALIDATED, audit note)
- docs/HANDOFF.md (audit summary, known issues)
- docs/BUG_LOG.md (BUG-003 added + fixed)

### Commands Executed

```text
python -m pytest ml/tests -q                              # 13 passed
python -m pytest backend/tests -q                         # 4 passed
cd frontend && npm run build                              # PASS
python -m uvicorn backend.app.main:app --port 8021        # live health + predict
```

### Testing / Validation

- ml tests: 13 passed in 153.16s (one benign StandardScaler feature-name
  UserWarning). backend tests: 4 passed in 28.04s.
- Live HTTP E2E: health returned model_loaded=true, feature_count=77; predict on a
  known DoS Hulk flow returned classification=MALICIOUS, label=DoS Hulk (== truth),
  confidence 0.9999, model_version phase-1-baseline, and persisted a row.
- Random-experiment XGB metrics (final Phase-1 inference model): binary acc 0.9979,
  multiclass acc 0.9987, macro-F1 0.8877. Temporal multiclass macro-F1 ~0.05 is the
  expected unseen-Friday-classes generalisation gap, not a defect.

### Problems Encountered

- BUG-003 (FIXED this session): docs/SPRINT_LOG.md was not valid UTF-8 - 4 stray
  cp1252 bytes (0xA7) mixed into an otherwise UTF-8 file. Normalised the file to
  valid UTF-8 (surrogateescape decode, map each lone byte to its UTF-8
  equivalent, re-encode); byte round-trip asserted. All other docs were already
  valid UTF-8.
- BUG-004 (FIXED this session): after BUG-003, appending this entry truncated
  docs/SPRINT_LOG.md. Root cause: the append script's Python string literal
  contained the literal characters backslash-u-d-c-a-7 which Python parsed as an
  escape (lone surrogate), causing UnicodeEncodeError on write; Path.write_text
  had already truncated the file. The 4 prior entries were lost from disk. Recovery:
  no git, no VSS (admin required), no OneDrive conflict copies, no File History.
  The full 4-entry content was recovered from the opencode session database
  (C:\Users\BIT\.local\share\opencode\opencode.db), which stores every tool call
  and output: entries 1-3 from the completion agent's pre-append read, entry 4
  from its Add-Content command (clean intended text; the on-disk copy had
  PowerShell backtick-escape corruption). File restored to 4 valid entries and
  this entry appended atomically (write to temp file + os.replace).

### Unresolved Issues

- None blocking Phase 1.
- Temporal multiclass generalisation gap is expected (DATA_ML_CONTRACT §18).
- Thresholds in config/config.yaml remain placeholders until Phase-2
  calibration (PRD §57).

### Next Recommended Action

Begin Phase 2: Isolation Forest anomaly detector (no scaling) on the random
dev subset, anomaly-threshold calibration on random/test (record calibrated
values in config + DECISIONS), then final supervised model selection
(RF vs XGBoost) with full metrics. Update PHASE_2.md before coding.

## [2026-08-09 23:55] --- Phase-2 implementation complete (final supervised, anomaly, hybrid, risk, SHAP, benign baselines, API contract, E2E gate)

### Objective

Complete ALL Phase-2 implementation tasks end-to-end (no partial handoff):
final supervised model selection, Isolation Forest anomaly detector with
FPR-constrained threshold calibration, unknown/unseen anomaly simulation,
hybrid decision layer, transparent risk engine, SHAP local explanations,
benign baselines, Phase-2 API contract, tests, E2E gate, and config
calibration. STOP after Phase 2 (no Phase-3 work).

### Phase

Phase 2 --- Final Detection Intelligence (PRD §58). Pre-task:
clean temp recovery files, add UTF-8-safe atomic-write rule to AGENTS.md,
verify Phase 1.

### Ahead-of-Session Pre-Tasks (Completed)

- Deleted all 30 leftover recovery scripts in Temp/opencode (directory empty).
- Added the UTF-8-safe atomic-write rule to AGENTS.md core rules (encode
  complete new content first, temp file + os.replace, re-read + assert;
  never truncate append-only logs in place; no literal \u / \U escapes).
- Phase-1 smoke check PASS: `python -m pytest ml/tests backend/tests -q` =
  17 passed; 77-feature order consistent across schema/artifact/preprocess;
  temporal dev subset = 12 classes (no Bot/DDoS/PortScan leak); API health
  feature_count 77. No Phase-1 reset performed.

### Supervised Model Selection

- ml/training/select_supervised.py (new): 6 light RF/XGBoost variants,
  binary + multiclass, random + temporal experiments, full PRD §47 metrics.
  Results in ml/evaluation/results/supervised_selection_{random,temporal}.json.
- Random/test: xgb_200 macro-F1 0.8898, weighted-F1 0.9988, FP rate 0.00143
  (best); rf_baseline 0.8156/0.9983; rf_200 0.8153/0.9983; rf_depth
  0.7941/0.9966; xgb_baseline 0.8877/0.9987; xgb_lr 0.8798/0.9986.
- Per-class recall: xgb_200 strong on rare classes (Web Attack - Brute Force,
  SQL Injection, XSS, Infiltration); Random Forest scored 0.0 on Web Attack -
  Sql Injection => XGBoost chosen.
- Temporal/test: all models macro-F1 ~0.0533 (expected generalisation gap for
  Friday-only classes; PRD "random vs temporal distinct experiments").

### Final Supervised Model (DEC-007)

- ml/training/train_final_supervised.py (new): XGBoost XGBClassifier
  n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8,
  colsample_bytree=0.8, seed 42; trained on dev_random_train.parquet (300k).
- Artifacts: ml/artifacts/supervised_model.joblib + supervised_model_metadata.json.
- Random/test validation: acc 0.9987, macro-F1 0.8898, weighted-F1 0.9988
  (wrote ml/evaluation/results/final_supervised_random.json).

### Isolation Forest + Threshold (DEC-008)

- ml/training/train_isolation_forest.py (new): IsolationForest(200 ests,
  contamination auto, seed 42) fit on 88,314 benign rows of
  dev_random_train.parquet (no scaling).
- Threshold calibrated on random_3way/validation (282,788 rows), NEVER on
  reported test (PRD threshold calibration). Initial max-F1 sweep -> FPR 0.61
  (Friday attack-skewed) => switched to FPR-constrained max F1 (FPR <= 5%).
- Calibrated threshold = -0.0928 (validation: F1 0.4272, FPR 0.0214).
- Reported on the DISJOINT random_3way/test: precision 0.7662, recall 0.2951,
  F1 0.4261, FPR 0.0221. Honest limitation, not hidden.
- config/config.yaml: anomaly_threshold -> -0.0928 (atomic replace).

### Unknown / Unseen Anomaly Simulation (PRD §46, Option B)

- ml/training/run_unknown_experiment.py (new): temporal Friday-only classes
  (12 Mon-Thu train / 4 Fri test). Supervised model + IF both trained only
  on Mon-Thu; PortScan/DDoS/Bot are unseen at train time. Threshold
  calibrated on temporal_3way/validation, reported on temporal_3way/test.
- Wording is ALWAYS "unseen / unknown anomaly simulation", never "zero-day".
- Findings (honest, file unknown_experiment_temporal.json):
  - DDoS -> KNOWN_ATTACK via generalization as DoS Hulk (volumetric similarity),
    IF catches 16.9% at FPR<=5%.
  - PortScan -> 99.9% high-confidence BENIGN (feature-structurally identical
    to benign); Bot -> 100% high-confidence BENIGN; IF catches only 7.5% of
    all unseen attacks at FPR<=5%.
  - Bug caught during work and FIXED: the first unfinished index passed the
    TRUE label into the hybrid instead of the PREDICTED label (unintended) =>
    corrected to use predicted label + confidence (PRD §10), re-ran.

### Hybrid Decision + Risk + Explainability

- ml/hybrid/decision.py (new): deterministic PRD §10 layer, config-driven
  HybridThresholds; defaults = calibrated config values.
- ml/hybrid/risk.py (new): transparent PRD §11 formula severity *
  (0.5 + 0.5*confidence) + anomaly term; bounded 0..100; config-driven
  family severity + thresholds (medium/high/critical 40/65/85). Verified
  PRD §11 example DDoS @ 0.97 -> CRITICAL. BENIGN keeps LOW regardless of
  the supervised label family (regression test added).
- ml/hybrid/shap_explainer.py (new): SHAP local explanations. **Selection/decision
  note (DEC-009):** the installed SHAP package 0.49.1 cannot parse XGBoost 3.2.0
  multiclass vector base_score (ValueError) -> used XGBoost's NATIVE TreeSHAP
  path (booster.predict(pred_contribs=True)) which runs the identical
  algorithm and was verified (sum = margin for all 15 classes). ~0.13 s per flow.
- ml/hybrid/baselines.py (new): benign baselines from the 88,314 benign rows
  -> ml/artifacts/benign_baselines.json (median/mean/p25/p75/std for the
  10 config-listed features). PRD §13.

### Backend / Contracts

- backend/app/services/predictor.py -> PhasePredictor: supervised + IF +
  hybrid + risk + SHAP; loads real thresholds from config/config.yaml.
- backend/app/schemas/predict.py -> Phase-2 response (prediction_id,
  classification, label, family, confidence, anomaly_score, risk_level,
  risk_score, top_features[{feature, shap_value, direction}]); health reports
  phase-2, feature_count 77.
- backend/app/db/models.py: Prediction gains anomaly_score, risk_level,
  risk_score, top_features. SQLite dev DB rebuilt (old Phase-1 schema).
- backend/app/api/predict.py: persists all phase-2 fields.
- config/config.yaml: known_confidence_threshold 0.75 (validated: random/test
  acc 0.9991 at conf >= 0.75; only 531/721 errors above 0.75), anomaly
  threshold -0.0928, calibration criterion + max_fpr, severity table.

### Tests & Validation

- ml/tests/test_hybrid.py (14) - hybrid boundaries, PRD"risk monotonicity,
  BENIGN floor. ml/tests/test_shap.py (3) - top-5 ordering, feature names,
  baseline artifact. ml/tests/test_predictor.py (3) - full contract, hybrid
  vs artifacts consistency, real-row anomaly separation (DoS Hulk mean <
  benign mean score). backend/tests/test_api.py (4) - health phase-2,
  predict phase-2 contract incl. top_features, missing/extra 422.
- Full suite: `python -m pytest ml/tests backend/tests -q` -> 37 passed
  (136.7s; one benign StandardScaler feature-name warning).
- Phase-2 E2E gate (real uvicorn on 127.0.0.1:8765, real API): benign -> 
  BENIGN/LOW; DoS H2 -> KNOWN_ANNO/CRITICAL (risk 100); SSH-Patator ->
  KNOWN_ANNO/HIGH; Port-Scan -> KNOWN_ANNO/MEDIUM; DDoS -> KNOWN_ANNO/CRITICAL
  (risk 90); every response carried the full Phase-2 JSON contract. Note a
  low-confidence Web-Attack miss now returns BENIGN/LOW as expected (fixed).

### Documentation / Governance Updates

- docs/DECISIONS.md: DEC-007 (final model), DEC-008 (IF + FPR constraint),
  DEC-009 (native TreeSHAP), DEC-010 (hybrid/risk config contract).
- docs/IMPLEMENTATION_STATUS.md, docs/HANDOFF.md, docs/PHASES/PHASE_2.md,
  docs/TESTING.md updated to Phase-2 VALIDATED.
- docs/DATA_ML_CONTRACT.md unchanged (threshold-driven source: config).

### Problems Encountered

- shap 0.49.1 vs xgboost 3.2.0 base_score incompatibility -> native TreeSHAP
  (DEC-009).
- max-F1 calibration on attack-skewed Friday validation -> FPR-constrained
  max-F1 (config-driven, DEC-008).
- hybrid used true label instead of predicted label (unknown experiment) ->
  fixed with the deterministic, PRD-conformant layering.
- old SQLite schema lacked phase-2 columns -> rebuilt dev DB.
- risk-engine attribute-name cl (threshold vs anomaly_threshold) -> fixed.
- baseline.py used a 2D where on a list (`columns`) -> fixed via index().
- config placeholders replaced with calibrated/validated values.

### Unresolved Issues

- Honest limitation (NOT a defect): benign-only isolation forest has low
  anomaly recall (7.5% at FPR<=5%) for structurally-benign unseen classes.
- Temporal generalisation gap (macro-F1 ~0.05) remains the documented.

### Next Recommended Action

Phase 2 COMPLETE and VALIDATED (gate decision recorded in
docs/PHASES/PHASE_2.md). Do not start Phase 3 without the user's go-ahead.
Next agent: confirm utilities and read the new IMPLEMENTATION_STATUS.md.

## [2026-08-09] --- Phase-2 closure audit: hybrid rescue fix, TreeSHAP additivity, IF sensitivity, E2E re-run (PHASE 2 CLOSED)

### Objective

Final scientific/methodological closure audit of Phase 2 (no new feature
work): verify the supervised-selection evidence, fix the hybrid BENIGN-rescue
semantics, verify native TreeSHAP correctness, run a controlled IsolationForest
sensitivity experiment, scan terminology, then run the full regression and
record one concise entry. End with a single PASS/FAIL gate decision.

### Phase

Phase 2 --- Final Detection Intelligence. Gate decision at the bottom.

### Findings / Fixes

- HYBRID BUG (HIGH, BUG-007): `hybrid_decision` returned BENIGN for a
  high-confidence BENIGN prediction before consulting the anomaly detector,
  masking suspicious signals. Fixed: KNOWN_ATTACK only when the predicted
  label is malicious AND confidence >= 0.75; the anomaly rescue then runs for
  every other flow; BENIGN is the final fallback. `run_unknown_experiment.py`
  now delegates to the shared `hybrid_decision`. Regression test
  `test_high_confidence_benign_rescued_by_anomaly` added.
- Supervised selection (DEC-007) verified against all six PRD §33
  criteria in supervised_selection_{random,temporal}.json. xgb_200 wins
  macro-F1 (0.8898 vs rf_baseline 0.8156), weighted-F1 (0.9988 vs 0.9983),
  binary FP rate (0.00143 vs 0.00166), rare-class recall (Sql Injection 0.667
  vs 0.0), and inference cost (4.23 s vs 7.04 s per 565,576 flows); loses only
  one-time train time (84 s vs 19 s). Temporal FP rate lowest for xgb_200
  (0.00037) — used as a generalisation diagnostic (DEC-004), not selection.
- TreeSHAP: added `test_shap_additivity_across_all_classes`
  (sum(contributions)+bias == margin for all 15 classes) and
  `test_shap_explainer_uses_predicted_class` (explainer ranks the PREDICTED
  class's contributions); fixed the `DEC-00X` docstring placeholder to DEC-009.
- IF sensitivity (`ml/training/if_sensitivity.py`, new): 4 configs varying
  n_estimators / max_samples / max_features, seed 42 fixed, same FPR<=5%
  calibration (random_3way/validation; temporal_3way/validation). Random/test
  F1 0.426-0.430 across configs; aggregate unseen (Friday) flag rate
  0.1685-0.1716. Deployed config kept: the low unseen recall is STRUCTURAL,
  not a tuning artifact. Threshold trade-off table written (no threshold
  reaches high unseen recall at usable FPR). max_samples auto == 256 for
  these fit sizes, so configs 1 and 3 coincide by construction (a protocol
  determinism check).
- Unknown/unseen experiment re-run with the corrected hybrid: benign flows
  flagged by IF on Friday test now surface as UNKNOWN_SUSPICIOUS (7,319, vs 4
  before); Bot 13/940 rescued; PortScan 11/79,318; DDoS unchanged (its
  flagged flows were already KNOWN_ATTACK via DoS Hulk generalisation).
- Terminology scan: clean. Every "zero-day" occurrence in docs/code is a
  prohibitive rule; no overclaims in backend, frontend, docs, or training
  code. Wording stays "unseen / unknown anomaly simulation".

### Regression / Validation

- `python -m pytest ml/tests backend/tests -q` -> 40 passed (was 37; +1
  hybrid regression, +2 SHAP tests). One benign StandardScaler feature-name
  warning (pre-existing).
- Live E2E on real uvicorn 127.0.0.1:8765 -> PASS: benign BENIGN/LOW(2.5),
  DoS H2 KNOWN/CRITICAL(100), SSH-Patator KNOWN/HIGH(70), PortScan
  KNOWN/MEDIUM(50), DDoS KNOWN/CRITICAL(90); every response carried the full
  Phase-2 contract. (`shap_base_value` is computed but not in the API schema.)

### Files Changed

`ml/hybrid/decision.py`, `ml/tests/test_hybrid.py`, `ml/tests/test_shap.py`,
`ml/training/run_unknown_experiment.py`, `ml/training/if_sensitivity.py` (new),
`ml/evaluation/results/unknown_experiment_temporal.json` (re-generated),
`ml/evaluation/results/if_sensitivity.json` (new). Governance docs updated
(BUG_LOG BUG-007, DECISIONS DEC-007/DEC-010, TESTING, PHASE_2, IMPLEMENTATION_STATUS, HANDOFF).

### Unresolved Issues

- None blocking. Honest limitation (not a defect): the benign-only Isolation
  Forest provides limited detection coverage for some temporally unseen attack
  behaviours under the chosen false-positive constraint (PRD §34/§46).
  No Autoencoder or additional model added (PRD §35).

### Gate Decision

**PHASE 2 FULLY CLOSED --- READY FOR PHASE 3.** Phase 3 (replay engine,
incident grouping, Security Monitor UI, Cytoscape) is NOT started; await an
explicit user go-ahead.

### Next Recommended Action

Phase-3 planning per PRD §69 (do not implement before the baseline
planning gate). Next agent: read AGENTS.md, the PRD, IMPLEMENTATION_STATUS.md,
HANDOFF.md, PHASE_2.md, and the latest DECISIONS.md entries.


---

## [2026-08-09] - BUG-005 runtime-purity closure: permanent regression tests, rescue summary, e2e evidence (A3/A4/A5)

### Summary

Closed the ground-truth contamination class of bugs permanently. BUG-005
(unknown experiment passing the TRUE label into the hybrid) was already
fixed in code; this session pins the invariant with permanent regression
tests and adds machine-readable rescue + real-inference evidence.

### What Changed

- Runtime contract regression tests (A5) in ml/tests/test_predictor.py (now
  6 tests):
  - 	est_predictor_signature_has_no_ground_truth_argument -- predict()'s
    signature rejects any truth/label/y/ground_truth/true_label parameter.
  - 	est_predict_ignores_extra_metadata_keys -- identical feature vector +
    extra metadata == identical prediction, classification, risk, top-features.
  - 	est_missing_and_extra_features_rejected_independently_of_label --
    extra/synthetic ground-truth keys raise PredictorError, so inference is a
    pure function of canonical features.
- Rescue/summary scorecard (A3): ml/evaluation/results/unknown_rescue_summary.json
  derived from unknown_experiment_temporal.json: IF unseen flag rate (
  aggregate 0.0750) vs hybrid incremental rescue rate (0.0002); per-class Bot
  0.0138 rescued, DDoS 0 (already KNOWN_ATTACK via DoS Hulk similarity), PortScan
  0.0001.
- End-to-end real-inference evidence (A4): ml/evaluation/results/
  e2e_evidence_phase2.json -- 6 real rows from random_3way/test through the
  FULL Phase-2 pipeline: benign (BENIGN/LOW 2.5), DoS Hulk (KNOWN/CRITICAL
  92.7), DDoS (KNOWN/CRITICAL 90.0), SSH-Patator (KNOWN/HIGH 70.0), PortScan
  (KNOWN/MEDIUM 50.0; resolves the earlier reported 'PortScan -> MEDIUM(50)'
  to the real runtime classification), plus a real UNKNOWN_SUSPICIOUS benign
  candidate (anomaly-only rescue, HIGH 72.9). Each record stores
  evaluation_truth_label for scoring ONLY; predict() never receives it
  (BUG-005).

### Files Changed

ml/tests/test_predictor.py, ml/evaluation/record_e2e_evidence.py (new),
ml/evaluation/results/e2e_evidence_phase2.json (new),
ml/evaluation/results/unknown_rescue_summary.json (new). Governance docs
updated (BUG_LOG BUG-005 regression tests, IMPLEMENTATION_STATUS).

### Validation

- python -m pytest ml/tests/ -q -> 39 passed (was 36; +3 predictor tests).
- python -m pytest backend/tests -q -> 4 passed. Combined: 43 passed.
- python -m ml.evaluation.record_e2e_evidence wrote e2e_evidence_phase2.json
  (6 records); regenerated BOM-free and re-read as valid JSON.

### Unresolved Issues

- None new. Honest limitation carried forward (see HANDOFF): benign-only IF
  has limited recall on structurally-benign flows; PortScan/Bot near-zero.

---

## [2026-08-10] - Phase-3 backend hardening: incident boundary determinism, enriched detail contract, extended E2E gate (A4/A5/A6/A3)

### Summary

Hardened the Phase-3 backend engine evidence and closed two replay-test gaps found during a full-suite pass:

- A4 incident boundary determinism: added `test_window_boundary_delta_equals_window_still_joins` in backend/tests/test_incidents.py to pin the INCLUSIVE window rule (delta == window joins; delta > window supersedes) that the restart test had been relying on implicitly.
- A5 enriched incident-detail contract: incident detail now exposes `anomaly_score`, `top_features` (persisted SHAP) and `baseline_features` (baseline feature subset) for every flow, plus a dominant-flow summary confidence; added `test_incident_detail_enriched_from_prediction`. Added the benign baselines endpoint (`GET /api/baselines/benign`) with `test_benign_baselines_endpoint` (PRD §13 behaviour-vs-normal input for Incident Detail UI).
- A6 replay determinism fixes: `test_replay_truth_label_never_enters_inference` now accounts for the two inference passes per suspicious flow (no-SHAP + SHAP), so the seen-feature count is correct (24); `test_restart_after_stopped` now leaves the pacing gate open on restart so the 40-flow service run completes in-test, and asserts counters reset monotonically.
- A3 extended live E2E gate: backend/tests/e2e_replay_phase3.py now also replays dos_or_ddos (8/8 KNOWN_ATTACK -> grouped CRITICAL DoS incident, flow_count 8, per-flow persisted SHAP + baseline subset in detail) and unknown (4/4 UNKNOWN_SUSPICIOUS -> 1 incident), plus the benign-baselines contract. Evidence written to ml/evaluation/results/e2e_replay_phase3.json.

### Files Changed

backend/tests/test_incidents.py, backend/tests/test_replay.py, backend/tests/test_replay_api.py, backend/tests/e2e_replay_phase3.py. Governance docs updated (IMPLEMENTATION_STATUS, PHASE_3, HANDOFF).

### Validation

- python -m pytest backend/tests -q -> 48 passed (was 36).
- python -m pytest ml/tests backend/tests -q -> 87 passed (was 79).
- python -m backend.tests.e2e_replay_phase3 -> PASS (portscan 8/8 -> MEDIUM incident; normal 0 suspicious/0 incidents; dos_or_ddos 8/8 -> CRITICAL incident risk 92.67; unknown 4/4 UNKNOWN_SUSPICIOUS -> 1 incident; benign baselines 10 features).

### Unresolved Issues

- None new.

## [2026-08-10] - Phase-3 frontend closure: Security Monitor, Communication Graph, Incident Detail + full Phase-3 gate (UI + contract gap)

### Summary

Completed and validated the entire Phase-3 UI stack on top of the frozen
Phase-3 backend engine, then closed the Phase-3 gate end-to-end through the
real API and a real browser:

- Security Monitor (`frontend/src/pages/SecurityMonitor.tsx`): replay controls
  (scenario/speed/start/pause/resume/stop + status), summary cards, live
  traffic table, attack-activity timeline + risk distribution (Recharts),
  Cytoscape communication graph, incident list.
- Incident Detail (`IncidentDetail.tsx`): summary, evidence table, SHAP top
  features, behaviour-vs-baseline (via `GET /api/baselines/benign`), incident
  graph. Incidents hub page + Predict demo tab; useState nav (no router).
- Contract gap (the only justified backend change): `GET /api/replay/flows`
  serves newest-first persisted replay rows for the live traffic table with
  `ReplayFlowOut`/`ReplayFlowsOut`; `Prediction` gained side-car columns
  (source, destination, service_port, seq, replay_time) populated by replay
  persist. 2 new API tests.
- BUG-009 found during live-browser E2E: Cytoscape never initialised when the
  flow list was empty because the mount-only effect ran before the ref
  container existed. Fixed by always mounting the container div with an overlay
  empty-state message; re-verified via headless Edge CDP (3 canvases paint).

### Files Changed

frontend/src/{App.tsx, api/{types,client,usePolling}.ts,
components/{ReplayControls,SummaryCards,TrafficTable,AttackTimeline,
RiskDistribution,CommGraph,IncidentList,ui}.tsx, lib/graph.ts,
pages/{SecurityMonitor,IncidentDetail,IncidentsPage}.tsx};
frontend/package.json (+ recharts@3.10.1, cytoscape@3.34.0, @types/cytoscape);
backend/app/{db/models.py,database.py,services/replay.py,schemas/replay.py,
api/replay.py}; backend/tests/test_replay_api.py;
backend/tests/e2e_replay_phase3.py (recent-flows assertions); governance docs.

### Validation

- python -m pytest backend/tests -q -> 50 passed (was 48; +2 recent-flows).
- python -m pytest ml/tests backend/tests -q -> 89 passed (was 87).
- python -m backend.tests.e2e_replay_phase3 -> PASS (now also asserts the
  /api/replay/flows feed contract: newest-first rows, 422 on limit clamp).
- npm run build (frontend/) -> PASS (tsc -b + vite build; sized-chunk warning only).
- Headless Edge CDP UI E2E -> PASS, zero console errors: replay start->COMPLETED,
  RUNNING/PAUSE/RESUME via live buttons, traffic table fill, charts + graph
  paint, incident list -> detail (SHAP + baseline). Evidence:
  C:/Users/BIT/AppData/Local/Temp/opencode/ui_e2e_report.json and
  ui_e2e_interactions.json.

### Unresolved Issues

- None new. Vite >500 kB chunk warning (cytoscape+recharts) is cosmetic at this scale.

---

## [2026-08-10] Phase-3.5 hardening + Phase 3 freeze (BUG-010, BUG-011)

### What Changed

- **BUG-010 fixed (single-pass replay SHAP):** new `Phase2Predictor.explain(features)`
  runs only the SHAP block (output identical to `predict(with_shap=True)`, same
  top-5 native TreeSHAP). `ReplayService._predict_one` now scores once and calls
  `explain()` for suspicious flows — no more full-pipeline double execution
  per attack flow (was 24 `predict` calls for 12 suspicious flows).
- **BUG-011 fixed (run-scoped monitor views):** `ReplayService` stamps every
  replayed `Prediction`/`Incident` row with a per-run `run_id` (uuid hex;
  additive columns + migration). `GET /api/replay/flows?run_id=` and
  `GET /api/incidents?run_id=` scope to a run; Security Monitor passes
  `status.run_id`; Incidents page omits it (full history). Sequential-replay
  evidence: VERDICT=MIXED (before) -> VERDICT=ISOLATED (after).
- **Decisions:** DEC-015 (run-scoping), DEC-016 (single-pass explain). Logged
  BUG-010 / BUG-011 in BUG_LOG.md.
- **Phase 3 FROZEN** — engine + UI + hardening all VALIDATED.

### Files Changed

`backend/app/services/predictor.py`, `backend/app/services/replay.py`,
`backend/app/api/{replay,incidents}.py`, `backend/app/db/{models,database}.py`,
`ml/evaluation/{phase35_evidence_before,phase35_evidence_after}.py`,
`ml/evaluation/results/phase35_evidence_{before,after}.json`,
`ml/tests/test_predictor.py`, `backend/tests/{test_replay,test_replay_api}.py`,
`backend/tests/e2e_replay_phase3.py`,
`frontend/src/{pages/SecurityMonitor.tsx,api/{client,types}.ts}`, governance docs.

### Validation

- Full suite `python -m pytest ml/tests backend/tests -q` -> 91 passed (was 89).
- `ml/tests/test_predictor.py` (7), `backend/tests/test_replay_api.py` (14).
- Live uvicorn E2E gate -> PASS (incl. sequential-run isolation).
- `npm run build` (frontend/) -> PASS.
- Real-browser (headless Edge CDP) sequential replay E2E -> PASS, zero console
  errors: table repaints to current-run rows; Incidents hub shows 0 for a run
  with no incidents; prior run's incident history preserved unscoped.

### Unresolved Issues

- None new. Vite >500 kB chunk warning (cytoscape+recharts) is cosmetic at this
  scale. Phase 4/5 not authorized.

---

## [2026-08-10] BUG-012 fix — restart after STOPPED raced the stale worker thread

### What Changed

`ReplayService.start()` now joins any still-alive previous worker thread
(outside `_lock`) before resetting counters and spawning a fresh run, plus a
concurrent-start recheck. `stop()` was only synchronous on the STATE; the
worker could still be mid-`predict`/`persist`, and an immediate restart let it
race the new run on the same counters/DB. Pre-existing engine race (DEC-013),
surfaced under full-suite load as `processed == 41` in
`test_restart_after_stopped`.

### Files Changed

`backend/app/services/replay.py` (`start`), `backend/tests/test_replay.py`
(+`test_restart_waits_for_stale_worker_before_resetting`).

### Validation

- New regression test passes; module `test_replay.py` 17 passed.
- Full suite `python -m pytest ml/tests backend/tests -q` -> 92 passed, twice.
- Live uvicorn E2E gate re-run PASS.

### Unresolved Issues

- None new.


---

## [2026-08-13] Phase-3 frontend UX pass — recovery reconciliation + completion

### Context

Recovery brief asked to audit partial prior UX work and finish the Phase-3
frontend UX pass. Recovery audit (no git history available) classified the
current frontend: shell/nav, runtime-generated security verdict, UNKNOWN
semantics, incident list/detail, SHAP framing and benign-baseline blocks were
already in good shape (KEPT as-is); Predict/Playground/Model Lab surfaces were
already absent from navigation. Remaining defects were fixed surgically.

### What Changed

- Header status copy: dropped developer-facing "77 features" (now "System
  ready") — `frontend/src/App.tsx`.
- Anomaly threshold: single shared `ANOMALY_THRESHOLD` / `isAnomalyFlagged()`
  in `frontend/src/components/ui.tsx` (mirrors `inference.anomaly_threshold`
  in config/config.yaml); replaced duplicated magic `-0.0928` in
  `TrafficTable.tsx` + `IncidentDetail.tsx`.
- Replay Activity timeline (`AttackTimeline.tsx`): benign flows get a minimal
  visible bar so a fully-benign Normal run reads as "traffic analysed, all
  healthy"; Y-axis floored at 1 so benign bars always read as tiny stubs.
- Risk Distribution (`RiskDistribution.tsx`): proper empty state before any
  replay.
- Behaviour-vs-baseline (`IncidentDetail.tsx`): within/outside judgement now
  uses the benign p25-p75 band; below-normal case handled; ratio always shown.
- BUG-013 fixed: `CommGraph.tsx` calls `cy.resize()` before layout on data
  updates (blank map on initial load with restored run).

### Files Changed

`frontend/src/App.tsx`, `frontend/src/components/ui.tsx`,
`frontend/src/components/TrafficTable.tsx`,
`frontend/src/components/AttackTimeline.tsx`,
`frontend/src/components/RiskDistribution.tsx`,
`frontend/src/components/CommGraph.tsx`,
`frontend/src/pages/IncidentDetail.tsx`, governance docs.

### Validation

- `npm run build` (frontend/) -> PASS (tsc + vite).
- Full suite `python -m pytest ml/tests backend/tests -q` -> 92 passed
  (matches frozen baseline exactly).
- Live browser pass over all four scenarios + Incident Detail + Incidents hub:
  Normal = prominent green "No suspicious activity detected" + tiny benign
  bars; PortScan = "Reconnaissance detected" MEDIUM, readable graph labels;
  DoS = "Denial of Service detected" CRITICAL with tall red bars; Unknown =
  "Unrecognized suspicious behavior" HIGH with classifier-vs-anomaly
  explanation, non-contradictory; Incident Detail hero + SHAP ("model
  contributions, not causal explanations") + baseline ratios all render.
  Zero console errors. BUG-013 re-check PASS.

### Unresolved Issues

- None new. Vite >500 kB chunk warning remains cosmetic (cytoscape +
  recharts). Phase 4/5 not authorized.


## [2026-10-31] Approved implementation - Milestone 1 Task 1 replay lifecycle

### What and why
Reopened only the approved Phase-3 reliability defects (DEC-017 / BUG-014).
Terminal FAILED state replaces infinite retry; rollback/close covers session,
inference, SHAP, flush, flow commit and final commit failures. Restart checks
actual worker exit after timed join; shutdown wakes/drains the worker. Counters
advance only after commit. API 409 is reserved for lifecycle conflicts.

### Files
backend/app/services/replay.py; backend/app/api/replay.py;
backend/app/schemas/replay.py; backend/app/main.py;
backend/tests/test_replay_failures.py; governance documents.

### Commands and validation
New tests run before implementation: 8 failed for the original lifecycle defects;
then 6 API/lifespan cases failed before their fixes. Related suite command:
python -m pytest backend/tests/test_replay_failures.py backend/tests/test_replay.py
backend/tests/test_replay_api.py backend/tests/test_incidents.py -q -p no:cacheprovider
=> 62 passed. Live gate: imported backend.tests.e2e_replay_phase3.main with OUT
redirected to a temp path => PASS, all original scenarios and sequential isolation.
Full suite attempted: 92 passed, 7 failed, 7 errors, exclusively dataset socket
access blocked by sandbox; no tests altered/skipped to accommodate that failure.
Network-enabled full regression: 106 passed in 250.99s. Two additional cleanup
regressions were then added. A concurrent targeted run had two 2-second worker
wait failures under dataset-load contention; the isolated targeted rerun verifies
the worker behavior without overlapping the heavy suite. git diff --check passed.

### Invariants
No models, dataset/preprocessing, thresholds, risk, SHAP or fixture changes.
Artifact SHA256: supervised 9067a808b7159a87918571f74cde1ccb54cbd652818c3816c10f6e66be85bd41;
IF 89efc5a382c97e55aa40d0bd714e3cbd4511f7fa08312dcf0a09f36e3724c176.

### Remaining
Task 2 readiness/frontend state; Task 3 graph/explanation corrections; evaluation,
scenario provenance, Playground backend/UI. No push before complete verified scope.

## [2026-10-31] Batch 2 - Milestone 1 Task 2 readiness and run-scoped UI

### Changes and rationale
Health retains prior fields and adds readiness/message; raw artifact paths are
not exposed. Header checks model_loaded and refreshes health every 5 seconds.
Start is disabled while inference is unavailable. FAILED has explicit UI copy
and recovery controls. Monitor stores status/evidence together, clears on new
or absent run_id, derives graph from current flows, invalidates late responses,
and cancels stale updates on unmount. Incidents history remains unscoped.

### Files
backend/app/main.py, schemas/predict.py, tests/test_readiness.py;
frontend/src/App.tsx, api/client.ts, api/types.ts, components/ReplayControls.tsx,
components/SecurityStatus.tsx, pages/SecurityMonitor.tsx.

### Validation
Readiness tests failed before changes (missing fields), including schema round
trip before schema fix. Final focused command: python -m pytest
backend/tests/test_readiness.py backend/tests/test_replay_failures.py
backend/tests/test_replay_api.py -q -p no:cacheprovider => 32 passed (5.85s).
TypeScript: node node_modules/typescript/bin/tsc --noEmit --incremental false PASS.
Production: node node_modules/vite/bin/vite.js build PASS (11.62s); existing
>500 kB bundle warning retained. Browser via Vite :5174 + real Uvicorn :8000
with disposable SQLite: missing models => actionable warning/disabled Start;
ready recovery; PortScan -> Normal cleared old table/graph/incidents; backend
restart => idle Monitor empty while Incidents history remained accessible;
controlled inference failure => FAILED with enabled Start; subsequent Normal
completed. Delayed-response probe held old PortScan /flows via temporary test
middleware, started Normal, released old response => Normal evidence stayed
isolated. No console errors in final successful recovery. No test middleware
or fault hooks added to production. No model/threshold changes. Nothing pushed.

### Remaining
Task 3 graph/semantics/threshold evidence. Then Milestones 2-4. Phase 1/2 model
research remains frozen; approved reliability and Playground work remains active.

## [2026-10-31] Batch 3 - Milestone 1 Task 3 graph and evidence semantics

### Changes
Boolean Cytoscape selectors now match actual edge attributes. Host/service/edge
selection resolves actual flow identifiers. Unknown explanations distinguish
benign predictions from low-confidence malicious predictions. Risk chart values
match persisted risk; benign baseline is labeled middle-50% reference band,
with undefined zero-median ratios. Synthetic scenario metadata is visibly labeled.
Prediction.anomaly_threshold is an additive nullable column, snapshotted at
inference, exposed in prediction/feed/incident evidence, and consumed by UI.
Legacy missing thresholds remain NULL/unavailable, never guessed/backfilled.
Shared display helpers and a Node built-in frontend test command added; no deps.

### Files
backend app api/{predict,replay,incidents}.py, db/{database,models}.py,
schemas/{predict,replay,incidents}.py, services/replay.py; tests/test_replay_api.py,
tests/test_threshold_history.py; frontend package.json, api/types.ts,
components/{CommGraph,AttackTimeline,SecurityStatus,TrafficTable,ui}.tsx,
lib/{graph,detection}.ts, pages/{SecurityMonitor,IncidentDetail}.tsx,
tests/{graph,detection}.test.mjs; governance.

### Validation
New graph/selection and threshold API tests failed before implementation;
new anomaly/unknown helpers were test-first. Node test transpilation target
corrected to ES2020 to match project tsconfig (default ES5 lost Map iterators).
67 related Python tests PASS (9.99s); 2 migration/real-predict tests PASS (5.83s).
4 frontend logic/Cytoscape tests PASS; TypeScript PASS; production build PASS
(12.33s; existing bundle-size warning). Live Uvicorn original four-scenario and
sequential-run gate PASS with temporary evidence output. Browser: high-risk edge
visibly red, synthetic metadata label visible, UNKNOWN detail shows supervised
BENIGN SHAP correctly, reference-band copy and recorded anomaly flags render;
zero console errors. Pointer-based service selection was inconclusive while the
existing graph re-layouts on polls; service/edge counting verified by unit tests.
Model and config SHA256 unchanged from Batch 1; no retraining/tuning.

### Remaining
Milestone 1 approved corrections complete. Next Milestone 2 reporting, locked-model
comparison and provenance/small scenarios; Playground not yet started. Graph
layout motion remains presentation polish, not a new redesign task. Nothing pushed.

## [2026-10-31] Batch 4 - Milestone 2 Task 4 evaluation reporting

Corrected current README/data contract/Phase-2/context reporting and added
EVALUATION_PROTOCOL.md. Historical JSON/logs preserved. Verified source JSON
assertions: final CM 539/454265, selection test n=565576, binary FP=651, sensitivity
aggregate min/max=0.074955/0.076569. No application behavior or model changes.
Validation: UTF-8 re-read of every document; numeric assertions PASS. Next Task 5
implements the locked-artifact shared-cohort report; Playground not started.

## [2026-10-31] Batch 5 - Milestone 2 Task 5 frozen hybrid comparison

Added ml/evaluation/evaluate_hybrid.py and ml/tests/test_evaluation.py. Same full
random_3way/test rows scored by frozen XGBoost, supervised gate, IF and shared
hybrid function. Records metrics, supports, per-class detection/name correctness,
rescue/false-alert costs, cohort/model/config hashes, parameters, seed, versions.
No full-cohort SHAP; fixture batch output parity verified against real predictor.
Binary confusion matrices now explicitly retain [0,1] on single-class input;
all callers inspected and use that canonical binary contract.

TDD: 4 evaluator tests failed before module; single-class warning regression
failed before fixed labels. 21 related tests passed (7.62s, no warnings).
Executed python -m ml.evaluation.evaluate_hybrid with network permission twice
(second run adds complete parameter provenance): n=282788, hybrid FPR .0231363,
recall .9975564; rescue 2 malicious / 138 gate misses, +5011 benign alerts.
Report is new locked_hybrid_random.json; all historical JSON retained. Artifact
and threshold hashes verified unchanged. Numeric assertions and UTF-8 docs pass.
No UI/runtime model changes. Next: scenario provenance and at most SSH/FTP/web
fixtures. Nothing pushed; current limitations intentionally retained.

## [2026-10-31] Batch 6 - Milestone 2 Task 6 scenario provenance/library

Code commit: 3c4aef4. Added prepare_scenarios.py, scenario tests/manifest and 8-row
SSH/FTP/web fixtures. Original four fixture vectors, side-cars, sequence and truth
preserved by explicit before/after equality assertions. Per-record pinned row
locator, feature SHA256, equivalent-row count and exact training-feature matches
are disclosed. Legacy locators explicitly mean first equivalent row, not a
recovered original ID. New selection excludes exact deployed-training/within-set
feature matches and uses no predictions. Loader validates canonical keys, finite
numbers, ports and pacing; replay lookup rejects unregistered paths. Test stubs
now use canonical keys; truth-isolation assertion was strengthened accordingly.

TDD: 7 new tests failed before changes. Final focused scenario/replay/API/failure
suite 57 passed (9.62s). Pinned dataset preparation and deterministic-order rerun
passed. Original Uvicorn replay gate PASS (temporary evidence). Real new inference:
SSH 8 known; FTP 8 known; web 4 known and 4 benign misses retained. New fixtures
have no exact training matches. Legacy PortScan 5/8 and DoS/DDoS 1/8 match training
features; these are preserved demo fixtures, not independent performance evidence.

Files: backend services/scenarios.py and replay.py, tests/test_scenarios.py,
test_replay.py, test_replay_api.py; ml/evaluation/prepare_scenarios.py;
data/scenarios/*.json, data/processed/scenario_provenance.json; current docs.
Initial documentation command had a quoting SyntaxError before any write; fixed
with complete UTF-8 content prepared before atomic replacement/re-read. Historical
logs kept. No models, thresholds, preprocessing or inference semantics changed.
Milestone 2 complete within agreed scope. Next approved Task 7 Playground profile
rules, then execution/scoring/UI. Nothing pushed.

## [2026-10-31] Batch 7 - Milestone 3 Task 7 validated profiles and rules

Added strict ProfileRequest/ScenarioPlan/ProfileOut schemas, deterministic suite
selection, and POST /api/playground/profile with existing PlaygroundProfile table.
No model required to preview/save profiles. Profiles reject extra target fields,
normalize service duplicates/order, expose missing scenarios and unsupported DB/
file-sharing services. Every suite includes benign control + benign anomaly
challenge, explicitly not unknown-attack validation. Rules: SSH/FTP enabled;
public web enabled; DoS for public services or 50+ scale; PortScan for lab/small
organisation or >10 scale. These are scenario relevance rules, not real discovery.

Files: backend/app/{schemas,services,api}/playground.py; main.py router registration;
backend/tests/test_playground.py. Four tests failed before implementation. Targeted
profiles/scenarios/replay API/readiness suite: 30 passed in 7.53s. Profile persisted
through actual TestClient + isolated SQLite and matched canonical request. No new
tables/dependencies; no Monitor/incident/model changes. No UI or run endpoint yet.
Next: Task 8 bounded execution, persisted assessment, failure/interruption handling.

## [2026-10-31] Batch 8 - Milestone 3 Task 8 persisted assessments

Implemented bounded synchronous suites (maximum 64 flows), same frozen predictor,
separate PlaygroundRun/Result persistence, saved profile/suite/artifact hashes and
metadata/threshold/risk/scoring snapshots and per-flow truth/features/provenance/
outputs. Truth is used for evaluation accounting only. No Monitor writes.
Score = 100 * (0.5 mean attack-scenario recall + 0.5 pooled benign specificity).
Weights live in config/config.yaml; inference config sections unchanged. Missing
selected scenarios suppress score; no attack evidence makes it not applicable.
Unknown benign challenge counts false alerts, never attack detection. Weakest and
strongest tested areas use observed per-scenario recall/specificity averages.
Failed inference/result commits produce failed persisted runs with no score;
startup marks interrupted running records failed once. Permanent database failure
returns 503; durability cannot be promised while SQLite is unavailable.

Files: backend/app/{services,schemas,api}/playground.py, main.py startup hook,
config/config.yaml; backend/tests/test_playground_api.py. Initial red tests: six
failed, one passed. Final command: python -m pytest backend/tests/test_playground_api.py
backend/tests/test_playground.py backend/tests/test_replay_api.py
backend/tests/test_replay_failures.py backend/tests/test_readiness.py -q
-p no:cacheprovider --tb=short -> 46 passed in 12.29s. Original HTTP replay gate
backend.tests.e2e_replay_phase3 with temporary evidence path PASS. Web profile real
model workflow: 12 detected, 4 missed, 4 false alerts, score 70.83. GET reproduces
saved results, no Prediction/Incident changes. git diff --check PASS.
Milestone 3 complete; frontend and final verification remain. No push yet.

## [2026-10-31] Batch 9 - Milestone 4 Task 9 Playground interface

Added Playground navigation/page, short validated environment questionnaire,
deterministic suite preview, bounded run action, saved-result retrieval, actual
outcome counts/matrix, risk distribution, score/formula, strongest/weakest areas,
coverage/unsupported services and selectable flow explanations. Profile edits
clear previous preview/results; busy actions disable repeated submissions. Model
readiness gates execution. Saved run ID retrieves historical assessment without
recomputing it. Notices distinguish prepared simulations, unknown benign anomaly
false alerts, legacy exact-training matches, synthetic sidecars and real networks.
TreeSHAP remains supervised-only and stored only for suspicious decisions as replay.
Reused RiskDistribution with narrowed required prop (risk_level only); no fake IDs.

Files: frontend/src/pages/Playground.tsx, App.tsx, api/{client,types}.ts,
components/RiskDistribution.tsx, lib/detection.ts, tests/detection.test.mjs.
New outcome test failed first (helper missing). Final 5 Node tests PASS; TypeScript
--noEmit --incremental false PASS; Vite production build PASS (existing >500kB
bundle warning retained). Initial typecheck found unsupported replaceAll; corrected
to target-compatible replacement. No dependency changes.
Live browser on Vite 5174 + Uvicorn 8000 disposable SQLite: Home 2 scenarios, score
not applicable, 4 false alerts; public web + database 4 scenarios, uncovered database,
12 detected / 4 missed / 4 FP, 70.83 score; edits clear old result; persisted reload
matches; missing saved run shows 404 and clears prior assessment; missed web flow
and benign anomaly SHAP inspected. Screenshot saved outside repo. One transient
HMR missing-module error occurred while adding files; final compile/build succeeds.
Task 9 complete. Task 10 full-suite, invariant review and final docs/push pending.
