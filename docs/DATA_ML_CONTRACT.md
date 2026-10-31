# DATA_ML_CONTRACT.md — Canonical Implementation-Level Contract

This is the **canonical contract** between:

```text
dataset / preprocessing  →  training  →  artifact persistence  →  backend inference
```

It is populated ONLY with values proven by actual dataset inspection. Where
inspection has not yet happened, entries are marked
**`TBD — requires validation`**.

**IMPORTANT (PRD §28, §29, §66):**
- Do not invent actual values before dataset inspection proves them.
- Never silently remove rare classes.
- Never assume the label hierarchy before inspecting the actual cleaned
  label set (the PRD §8 hierarchy is illustrative).
- Random and temporal splits must remain distinct experiments.

Status legend: `[TBD]` = not yet validated, `[SET]` = validated and locked
(record the validating sprint-log entry).

---

## 1. Dataset source / version

- **Official source:** CICIDS2017, Canadian Institute for Cybersecurity, UNB
  (https://www.unb.ca/cic/datasets/ids-2017.html) — PRD §27. `[SET]`
- **Convenience derivative:** Hugging Face `lacg030175/CICIDS2017`
  (https://huggingface.co/datasets/lacg030175/CICIDS2017) — PRD §28. `[SET]`
- **Revision used (verified):** `d071fd53782d9ca7cdc15173b8ceb858fea04628`,
  last modified 2026-04-02. `[SET]`
- **Storage format:** Parquet, one file per (config, split). Verified.
- **License / citation:** CC BY 4.0; cite original CICIDS2017 paper
  (Sharafaldin, Lashkari & Ghorbani, 2018) per PRD §28. `[SET]`

## 2. Dataset configurations / splits

Verified 2026-08-09. Configs present (via `get_dataset_config_names`):
`random`, `random_3way`, `standard`, `temporal`, `temporal_3way`. `[SET]`

**Random (`random`):** 80/20 stratified — PRD §26A. `[SET]`

```text
train: 2,262,300   test: 565,576     (total 2,827,876)
```

**Random 3-way (`random_3way`):** stratified train/val/test. `[SET]`

```text
train: 2,262,300   validation: 282,788   test: 282,788   (total 2,827,876)
```

> **3-way caveat (verified):** `random_3way/test` and `temporal_3way/test`
> contain a tiny `Heartbleed` residue (2 and 0 rows respectively in the 3-way
> split). The `random`/`temporal` 2-way configs are cleaner for the primary
> 80/20 evaluation; use a 3-way config only when a holdout validation set is
> genuinely needed, and document the choice in DECISIONS.md.

**`standard` config:** present with identical row counts and label sets to
`temporal` — treated as an alias. **There is NO `standard_3way` config**
(verified via `get_dataset_config_names`). The `temporal_valid` config from
the dataset card is NOT packaged in this derivative; use `temporal`
(train=Mon–Thu, test=Fri) as the temporal config. `[SET]`

**Temporal (`temporal`):** Train Monday–Thursday / Test Friday — PRD §26B.
`[SET]` Counts verified:

```text
train: 2,125,158   test: 702,718     (total 2,827,876)
```

**Temporal 3-way (`temporal_3way`):** train = Mon–Thu; validation + test are
equal halves of Friday. `[SET]`

```text
train: 2,125,158   validation: 351,359   test: 351,359   (total 2,827,876)
```

## 2a. Development-subset strategy (for Phase 1)

Per PRD §29: build a **class-aware ~200k–500k** development subset rather than
training on the full 2.8M. Implemented in `ml/preprocessing/subset.py`
(`build_dev_subset`): start from a source (config, split); retain ALL minority
attack rows (below `per_class_cap`); cap over-represented classes to
`per_class_cap`; then downsample only `BENIGN` to fill the `target` remainder.
Never drop any attack class. `[SET — see DEC-004]`

Concrete Phase-1 configuration (locked):

```text
target        300,000     (within PRD §29 range 200k–500k)
per_class_cap  60,000
cap_floor       8,000     (classes below this kept fully)
seed             42
```

Materialised subsets (row counts + per-class before/after are recorded in
each `.meta.json`):

```text
data/processed/dev_random_train.parquet     300,000 rows
  BENIGN 88,314 · DDoS 60,000 · DoS Hulk 60,000 · PortScan 60,000 · capped:
  BENIGN, DDoS, DoS Hulk, PortScan (all 15 classes retained)

data/processed/dev_temporal_train.parquet   300,000 rows
  BENIGN 202,353 · DoS Hulk 60,000 · capped: BENIGN, DoS Hulk
  NOTE: temporal/train contains only 12 classes (no Bot/DDoS/PortScan —
  those are Friday attacks, see §18).
```

## Temporal-split mechanism (VERIFIED — TESTING.md §"do not assume")

The dataset provides the Monday–Thursday/Friday split as **distinct config +
precomputed split files** — NOT a timestamp column. The 80 columns contain NO
`Timestamp` field; there is no `day`/`week` column. The temporal boundary is
baked into how the dataset authors partitioned the Parquet files.
`[SET — mechanism confirmed by inspection]`

## 3. Observed row counts

- PRD §28 card reports roughly: Temporal Train ~2.125M / Test ~0.703M;
  Random Train ~2.262M / Test ~0.566M.
- **Observed counts for the version used:** `[SET — verified]`
  - random/train: 2,262,300 · random/test: 565,576
  - temporal/train: 2,125,158 · temporal/test: 702,718
- Development subset size: target 300,000 class-aware flows (PRD §29),
  seed 42. See §2a. `[SET]`

## 4. Raw columns in the cleaned dataset

`[SET — verified via parquet schema]` All configs share the same schema:
**80 columns = 78 numeric features + `Label` (string) + `label` (int
binary 0/1).** No row-id/index column, no timestamp column.

Key observations:
- `Destination Port` is int64; most count/ratio features are int64 or
  float64.
- Dtype counts (verified, per partition): **int64 ×55 (54 features + `label`),
  float64 ×24 (features), large_string ×1 (`Label`)**. Total 80.
- **`Fwd Header Length` and `Fwd Header Length.1` are bit-for-bit identical**
  (verified equal on all four canonical partitions) — a known CICFlowMeter
  duplicate. One must be dropped during preprocessing to avoid a
  duplicate-feature defect. `[SET]` (see §5, BUG-001)
- **No NaN / inf values in any numeric column** on any canonical partition
  (verified). The non-finite safety-net in preprocessing (§12) never fires
  on the canonical data.

Full column list (exact order, names as published) — first 10 shown; the
complete canonical list is stored in `ml/artifacts/feature_schema.json`
(77 canonical features, version 1.0):

```text
Destination Port            int64
Flow Duration               int64
Total Fwd Packets           int64
Total Backward Packets      int64
Total Length of Fwd Packets int64
Total Length of Bwd Packets int64
Fwd Packet Length Max       int64
Fwd Packet Length Min       int64
Fwd Packet Length Mean      float64
Fwd Packet Length Std       float64
... (78 features total; 77 after dropping the duplicate) ...
Label                       large_string   (15-class attack string)
label                       int64          (binary: 0=BENIGN, 1=attack)
```

## 5. Dropped features and reasons

`[SET — verified]` One feature is dropped in preprocessing:

```text
Fwd Header Length.1   Bit-for-bit duplicate of "Fwd Header Length"
                      (CICFlowMeter duplicate retained by the publisher).
                      Kept column: "Fwd Header Length". (BUG-001)
```

No other columns are dropped. Canonical model-input feature count: **77**.

## 6. Target columns

- **Binary target:** `label` int64 — 0 = BENIGN, 1 = MALICIOUS (any attack).
  `[SET — verified]`
- **Multiclass / fine-grained target:** `Label` string, 15 classes (§8),
  encoded to int via the canonical mapping in
  `ml/artifacts/label_mapping.json` (`LABEL_TO_INT` in
  `ml/preprocessing/labels.py`). `[SET — verified]`

## 7. Binary labels

- `BENIGN`, `MALICIOUS` (PRD §8). In the cleaned dataset the binary column is
  `label` (int64, 0/1). Canonical string forms in the Phase-1 response:
  `BENIGN` / `MALICIOUS`. `[SET — verified]`

## 8. Fine-grained labels (VERIFIED — full set, 15 classes)

Observed across ALL configs. `[SET]` The 15-class set is:

```text
 0 BENIGN
 1 Bot
 2 DDoS
 3 DoS GoldenEye
 4 DoS Hulk
 5 DoS Slowhttptest
 6 DoS slowloris                (note: lowercase 'slowloris')
 7 FTP-Patator
 8 Heartbleed
 9 Infiltration
10 PortScan
11 SSH-Patator
12 Web Attack - Brute Force     (U+FFFD replaced by hyphen; see below)
13 Web Attack - Sql Injection    (Sql capitalised)
14 Web Attack - XSS
```

> **Label character caveat (verified 2026-08-09):** the raw parquet labels
> for the three Web Attack classes contain a **U+FFFD replacement character**
> (`Web Attack \ufffd Brute Force`, etc.) — NOT an en-dash as previously
> documented. `normalize_label()` in `ml/preprocessing/labels.py` maps the
> raw strings to the ASCII `"Web Attack - ..."` forms shown above. The
> canonical labels are deterministic, ASCII-safe, and persisted in
> `ml/artifacts/label_mapping.json`.

`label` is binary (0=BENIGN, 1=attack). `Label` is the 15-class string.
The canonical integer encoding is alphabetical over the 15 canonical labels
(`ml/preprocessing/labels.py::LABEL_TO_INT`, persisted in
`ml/artifacts/label_mapping.json`). `[SET — verified]`

## 9. Attack-family mapping (derived from the verified label set)

Generated from the actual cleaned labels (PRD §8) — NOT assumed. `[SET]`
Implemented in `ml/preprocessing/labels.py::FAMILY_MAP` and persisted in
`ml/artifacts/family_mapping.json`.

```text
BENIGN            → BENIGN

Denial of Service (DoS/DDoS)
  DoS Hulk
  DoS GoldenEye
  DoS slowloris
  DoS Slowhttptest
  DDoS

Brute Force
  FTP-Patator
  SSH-Patator

Reconnaissance
  PortScan

Web Attack
  Web Attack - Brute Force
  Web Attack - Sql Injection
  Web Attack - XSS

Botnet
  Bot
```

`Heartbleed` and `Infiltration` exist in the dataset but are extremely rare
(≤60 rows each in random train). In the current mapping each is its own
family (`Heartbleed → Heartbleed`, `Infiltration → Infiltration`); treat as
their own rare categories. The display family logic is a presentation-layer
concern; the ML label set is the 15 classes above.

## 8a. Attack-rate anchor (from the verified label distribution)

Random-train label counts (top 5, verified):

```text
BENIGN        1,817,055   (80.3%)
DoS Hulk        183,866    ( 8.1%)
PortScan        126,969    ( 5.6%)
DDoS            102,724    ( 4.5%)
DoS GoldenEye     8,195    ( 0.36%)
```

Overall attack rate in random train ≈ 19.7%. This is the anchor for the
class-imbalance discussion (PRD §29).

## 10. Development sampling strategy

- Strategy: class-aware representative subset (PRD §29). Dominant BENIGN
  downsampled; minority attacks retained where feasible; sampling ratio
  documented. Implemented in `ml/preprocessing/subset.py`.
- **Exact ratios + random seed:** `[SET — DEC-004]`
  - target = 300,000; per_class_cap = 60,000; cap_floor = 8,000; seed = 42.
  - Algorithm: keep all classes with count ≤ cap in full; cap classes
    > cap down to cap (except BENIGN); fill the remainder with sampled
    BENIGN. Deterministic given seed.
  - Materialised: `dev_random_train.parquet` and `dev_temporal_train.parquet`
    (see §2a for counts and `.meta.json` for full before/after).

## 11. Preprocessing rules

`[SET — implemented in ml/preprocessing/preprocess.py]`

1. Column validation (expected raw columns must exist).
2. Duplicate-column cleanup: drop `Fwd Header Length.1` (keep `Fwd Header
   Length`) — §5.
3. Non-finite handling: `inf/-inf → NaN → 0.0` fill (safety net; canonical
   data has none — §4).
4. Label normalisation (raw → canonical, §8) + family mapping (§9).
5. Canonical feature ordering (77 features, matches `feature_schema.json`).
6. Scaling only for Logistic Regression; scaler fit on TRAIN ONLY (§13).

No leakage from held-out test data. Deterministic and stateless.

## 12. Non-finite handling

`[SET — verified]` Implemented in `clean_numeric()`: replace `+inf/-inf`
with NaN, then fill NaN with a constant (0.0). No fitted state. Observed
canonical data has **zero** NaN/inf on all four partitions, so the fill is a
safety net, not a data transformation.

## 13. Scaling rules

- **Random Forest / XGBoost (final supervised candidates):** do NOT
  standardise by default (PRD §30, §32). Tree models are scale-invariant.
- **Logistic Regression (baseline):** scaling IS required. The scaler is
  **fit on training data only** (`fit_scaler` in preprocess.py) and applied
  at inference. `StandardScaler` used; persisted alongside LR artifacts.
  `[SET — verified in Phase-1 baselines]`
- **Isolation Forest (anomaly, Phase 2):** no scaling required by default
  (see prior note). Only revisit with experiment evidence + a DECISION.
- **No leakage:** any scaler is fit on training data only (PRD §30).

## 14. Feature ordering

`[SET — verified]` Canonical order = raw parquet column order (78 features)
minus the dropped duplicate `Fwd Header Length.1` → 77 features. Exact order
is defined by `CANONICAL_FEATURE_COLUMNS` in `ml/preprocessing/preprocess.py`
and persisted in `ml/artifacts/feature_schema.json` (version 1.0) and
`ml/artifacts/inference/feature_order.json`. Training, evaluation, and the
API all consume the same ordering — no reordering drift.

## 15. Feature schema (`feature_schema.json`)

`[SET — created]` `ml/artifacts/feature_schema.json` (version 1.0):
77 features, each `{name, index, dtype: "float64"}`, plus `dropped_features`
(§5) and `target_columns`. No PCA in the final explainable runtime model
(PRD §31).

## 16. Class imbalance handling

`[SET — Phase-1 choices]` RF uses `class_weight="balanced"`. LR uses default
(imbalanced) weights. XGBoost (Phase-1 baseline) uses default weights with
no explicit class weighting — the multiclass default uses `softprob` and the
dataset is heavily dominated by BENIGN. The development subset (§10) itself
rebalances dominant classes deterministically. Phase-2 final model selection
will re-examine weighting with metrics (PRD §32).

## 17. Random split contract

- 80/20 stratified (PRD §26A), provided as a precomputed `random` config
  (no stratification seed of our own — the dataset authors' split is used
  as-is). `[SET — verified]`
- Development subsets drawn from `random/train` (seed 42) — see §10.
- Temporal split: see §18. Random and temporal experiments are kept
  strictly distinct (PRD §26, §47).

## 18. Temporal split contract (VERIFIED)

- **Mechanism:** the HF dataset provides the Monday–Thursday/Friday split as
  a **precomputed config + split partition**, NOT via any row-level timestamp.
  The 80-column schema has NO `Timestamp` column. `[SET — verified by
  inspecting the full parquet schema and file layout]`
- **Config / splits used:** `temporal` config.
  - `temporal/train` = Monday–Thursday traffic (2,125,158 rows).
  - `temporal/test` = Friday traffic (702,718 rows).
  - The dagger (`temporal_3way`) further splits Friday into
    `validation` (351,359) + `test` (351,359). `[SET]`
- **Temporal metadata available in the dataset:** NONE beyond the partition.
  There is no timestamp, day, or week column in the schema — the chronology
  is entirely pre-partitioned by the dataset authors. `[SET — verified]`
- **Edge fact:** `temporal/train` contains only 12 classes (Mon–Thu attacks:
  DoS variants, FTP/SSH-Patator, Web Attacks, Infiltration, Heartbleed);
  `temporal/test` contains only 4 classes (BENIGN, PortScan, DDoS, Bot).
  The temporal test set deliberately holds out unseen attack types.
  `[SET — verified via label distribution diff]`
- **Evaluation note (Phase-1 baselines):** the temporal experiment trains on
  the 12-class Mon–Thu subset and evaluates against the 4-class Friday test.
  Bot/DDoS/PortScan are UNSEEN at multiclass training time, so temporal
  multiclass metrics reflect the generalisation gap (accuracy ~0.58–0.59,
  low macro-F1). This is the intended harder evaluation (PRD §26B); do not
  force the final runtime model to use the temporal artifact.

## 19. Model input format

- **Expected input to supervised + anomaly models:** a single flow encoded as
  a numeric feature vector in the canonical order, no label, no PCA.
- **Exact schema/shape:** `[SET — verified]` (1, 77) float64 in the canonical
  order (`feature_schema.json`). Built by `preprocess_frame()` (unscaled for
  RF/XGBoost; scaled by train-fitted StandardScaler for LR).

## 20. Persisted artifacts (`ml/artifacts/`, PRD §56)

Phase-1 artifacts created and validated:

```text
ml/artifacts/
├── feature_schema.json       77 features, version 1.0, dropped_features
├── label_mapping.json        canonical label -> int (15 classes)
├── family_mapping.json       canonical label -> display family
├── baselines/                Phase-1 per-experiment models (joblib)
│   ├── random_{lr,rf,xgb}_{binary,multiclass}.joblib   (+ scalers for lr)
│   └── temporal_{lr,rf,xgb}_{binary,multiclass}.joblib (+ scalers for lr)
├── inference/                promoted Phase-1 inference model
│   ├── model.joblib          xgb-multiclass (random experiment)
│   ├── model_metadata.json   provenance, feature order, classes, families
│   └── feature_order.json    77 canonical feature names (API order)
├── supervised_model.joblib   Phase-2 final supervised model (xgb m·200, random)
├── supervised_model_metadata.json   provenance, params, thresholds, metrics
├── isolation_forest.joblib   Phase-2 anomaly detector (benign-only fit)
├── isolation_forest_metadata.json  provenance + calibration info
└── benign_baselines.json     Phase-2 benign behaviour baselines (PRD §13)

ml/evaluation/results/baseline_metrics_{random,temporal}.json
    metrics per model/task (accuracy, precision, recall, F1, macro/weighted
    F1, per-class, confusion matrix, ROC-AUC for binary, train/inference
    timings)

ml/evaluation/results/  (Phase 2)
    supervised_selection_{random,temporal}.json  model comparison
    final_supervised_random.json                 final model metrics
    anomaly_calibration_random.json              threshold calibration sweep
    anomaly_evaluation_random.json               anomaly metrics on test
    unknown_experiment_temporal.json             unseen-anomaly simulation
```

## 21. Artifact version metadata (`model_metadata.json`)

Must record (PRD §56): dataset identity/version, configuration, split, sample
size, sampling strategy, random seed, labels, transformations, feature
order, model parameters, evaluation conditions, metrics.

- **Phase-1 implementation:** `ml/artifacts/inference/model_metadata.json`
  records dataset id/revision, training subset, feature count + order,
  classes, family map, phase, and source artifact. Full per-model parameter +
  metrics provenance lives in `ml/evaluation/results/baseline_metrics_*.json`
  and `ml/training/train_baseline.py` (params are fixed constants there).
- **Phase-2 implementation:** `ml/artifacts/supervised_model_metadata.json`
  and `ml/artifacts/isolation_forest_metadata.json`
  record dataset id/revision/training split, modelling params, feature order,
  calibration criterion + threshold, evaluation metrics, and phase.
  `[SET for Phase 1 + Phase 2]`

## 22. Inference output contract

Phase 1 (locked, implemented in `backend/app/schemas/predict.py`):

```json
{
  "prediction_id": 1,
  "classification": "BENIGN | MALICIOUS",
  "label": "DDoS",
  "family": "Denial of Service",
  "confidence": 0.9876,
  "model_name": "xgb-multiclass (random experiment)",
  "model_version": "phase-1-baseline"
}
```

- Phase 1 returns ONLY baseline supervised fields. Anomaly score, risk, and
  SHAP top-features are Phase-2 outputs and are deliberately NOT fabricated.

Phase 2 (validated, implemented in `backend/app/schemas/predict.py`):

```json
{
  "prediction_id": "...",
  "classification": "BENIGN | KNOWN_ATTACK | UNKNOWN_SUSPICIOUS",
  "label": "supervised canonical label, including BENIGN for anomaly rescue",
  "family": "family of the supervised label, retained for all hybrid outcomes",
  "confidence": 0.0,
  "anomaly_score": 0.0,
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "risk_score": 0.0,
  "top_features": [
    {"feature": "...", "shap_value": 0.0, "direction": "pushes_towards | pushes_against"}
  ]
}
```

- **Final canonical field names + types + enum values:** locked (Phase-2
  validated 2026-08-09; contract implemented + tested). Hybrid outcome
  semantics are PRD §10; risk levels map from `risk_score` via config
  thresholds (medium/high/critical 40/65/85); `risk_score` formula is
  config-driven (severity * (0.5 + 0.5*confidence) + anomaly term).

## 23. Benign baseline format (`benign_baselines.json`, PRD §13)

- Descriptive statistics (e.g., median) for selected important features
  derived from **benign training traffic only**, used for human-readable
  "vs normal" comparisons (PRD §13). `[SET — principle]`
- **Schema + selected features + statistic choice:** locked (Phase 2
  validated 2026-08-09): `ml/artifacts/benign_baselines.json` computed from
  the 88,314 benign rows of the random train split for the 10 features in
  `config/config.yaml` → `inference.baseline_features`
  (Flow Duration, Flow Packets/s, Flow Bytes/s, Packet Length Mean/Std,
  Total Length Fwd/Bwd Packets, Average Packet Size, Flow IAT Mean,
  Active Mean), each with median/mean/p25/p75/std/n. Built by
  `ml/hybrid/baselines.py`.

---

## Change control

Any change to a `[SET]` value requires:

1. a new entry in `docs/DECISIONS.md`,
2. an appended `docs/SPRINT_LOG.md` entry with evidence,
3. an update to this file, and
4. (if it affects the API) an update to the inference output contract.

## Reporting correction and evidence threshold - 2026-10-31

DEC-019 and EVALUATION_PROTOCOL.md supersede inconsistent historical split/FPR
claims; no data or experiment outputs were replaced. The selection script used
random/test, not random_3way/test. Effective anomaly_threshold is now recorded
with new prediction/feed/incident evidence (DEC-018); legacy values remain NULL.
Supervised and IF metadata do not by themselves contain every claimed calibration
field: configuration and result reports supply the remaining provenance.
