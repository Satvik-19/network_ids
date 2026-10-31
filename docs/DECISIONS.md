# DECISIONS.md — Architecture / Implementation Decision Records

Lightweight ADRs. Use this when an implementation decision could affect
future work. Do NOT create records for trivial variable names or ordinary
coding choices.

If a decision changes a previous one, mark the old record **SUPERSEDED**
rather than deleting it.

Typical topics: exact dataset config/version, label mapping, development
sampling strategy, feature schema, model artifact format, calibrated
thresholds, final supervised model selection, unknown/unseen evaluation
experiment, API contract changes, database schema decisions, incident
grouping rules.

Format:

```markdown
## DEC-XXX — Title

Date:
Status: PROPOSED | ACCEPTED | SUPERSEDED | REJECTED
Phase:

### Context
### Decision
### Reasoning
### Alternatives Considered
### Consequences
### PRD Compatibility
### Files / Components Affected
```

---

## Expected ADR topics (substantive decisions only)

Future ADRs in this file should cover substantive, implementation-affecting
decisions, for example:

- Dataset revision / exact HF config + split names selected (random and
  temporal).
- How the temporal (Mon–Thu train / Fri test) split is provided by the
  dataset and consumed.
- Development sampling strategy (subset size, ratios, seed, minority-class
  handling).
- Label set and the canonical label → family mapping.
- Preprocessing contract (non-finite handling, dropped columns, scaling per
  model family).
- Feature schema and canonical feature ordering.
- Model artifact format and versioning.
- Final supervised model selection (RF vs XGBoost) with metric evidence.
- Anomaly threshold calibration and the unknown/unseen experiment choice.
- Hybrid decision, risk, and incident-grouping thresholds (after
  calibration).
- Inference / API output contract.

The bootstrap session is recorded as engineering history in
`docs/SPRINT_LOG.md`, not as an ADR — it was session scope, not an
architectural decision.

---

## DEC-001 — CICIDS2017 dataset source: locked HF revision + configs

Date: 2026-08-09
Status: ACCEPTED
Phase: 1

### Context

Per PRD §27–28, the project uses the cleaned Hugging Face derivative
`lacg030175/CICIDS2017` as its convenience dataset (always citing the original
CICIDS2017/UNB source). The PRD (§28) states exact counts and structure "must
be read from the version used during implementation", so the revision, configs,
row counts, schema, labels, and the temporal-split mechanism had to be verified
empirically before any preprocessing work.

### Decision

Lock the dataset to:
- **Revision (sha):** `d071fd53782d9ca7cdc15173b8ceb858fea04628`
  (last modified 2026-04-02).
- **Storage:** Parquet, one file per (config, split).
- **Configs used:** `random` (80/20 stratified) and `temporal`
  (train = Mon–Thu, test = Fri). 3-way variants (`random_3way`,
  `temporal_3way`) available if a holdout validation set is needed.
- **Schema:** 80 columns = 78 numeric features + `Label` (15-class string) +
  `label` (binary int64: 0=BENIGN, 1=attack).
- **Temporal mechanism:** precomputed partition (no timestamp column) — see
  `docs/DATA_ML_CONTRACT.md` §18.
- **Label set:** 15 classes, verified (see `docs/DATA_ML_CONTRACT.md` §8).

### Reasoning

These were verified empirically against the live dataset and the HF dataset
card rather than assumed. Pinning the revision guarantees reproducibility
(two agents will load identical bytes). Recording the temporal mechanism
prevents a later agent from wrongly hunting for a timestamp column.

### Alternatives Considered

- Official CICIDS2017 MachineLearningCSV verbatim. **Rejected** as the primary
  source: PRD §28 designates the HF derivative as the convenience layer; the
  official CSVs remain the fallback if derivative validation fails (it did
  not).
- Reconstruct temporal split from a timestamp column. **Rejected:** the schema
  has no timestamp column; the split is precomputed by config.
- Use `temporal_valid` (mentioned on the dataset card). **Rejected:** that
  config is not packaged in this derivative; `temporal`/`temporal_3way` cover
  the need.

### Consequences

- All Phase-1–2 ML code must load via this revision and these configs.
- The dev-subset and feature-schema work proceeds against the verified schema.
- The duplicate `Fwd Header Length` / `Fwd Header Length.1` must be resolved
  in preprocessing (see bug note in BUG_LOG.md as a data-quality item).

### PRD Compatibility

Fully compatible (PRD §27–29).

### Files / Components Affected

`ml/preprocessing/dataset.py`, `ml/preprocessing/inspect_dataset.py`,
`config/config.yaml`, `docs/DATA_ML_CONTRACT.md`,
`data/processed/dataset_inspection_cicids2017.json`.

---

## DEC-002 — HF loader: positional config is canonical; `config_name=` keyword is an API quirk

Date: 2026-08-09
Status: ACCEPTED
Phase: 1

### Context

The prior session documented the `load_dataset_builder` / streaming
`config_name` failure as a HF bug and therefore loaded parquet files
directly via `hf://`. Recovery verification showed the diagnosis was wrong.

### Decision

- `load_dataset("lacg030175/CICIDS2017", "temporal", revision=<pinned>)`
  (config passed positionally) is canonical and works on datasets 5.0.1,
  both normal and streaming.
- The `config_name=` keyword form raises
  `TypeError: ... got multiple values for keyword argument 'config_name'`
  because the packaged `ParquetCicids2017` builder supplies the argument
  twice. Classified as an API-argument quirk of this derivative, NOT an HF
  defect.
- `ml/preprocessing/dataset.py` keeps loading the parquet files directly via
  `hf://` (deterministic, efficient, identical rows) and documents both
  facts in its docstring.

### Reasoning

Direct parquet loading is already correct and avoids the extra HF machinery;
the docstring must no longer mislead future agents about a "HF builder bug".

### Alternatives Considered

- Switch `load_split` to the HF API. Rejected: no benefit for Phase-1, adds a
  dataset-cache dependency for the same rows.

### Consequences

- `docs/DATA_ML_CONTRACT.md` §1/§2 unchanged (revision/configs verified
  again).
- BUG-002 recorded in `docs/BUG_LOG.md` as WONTFIX with the corrected
  classification.

### PRD Compatibility

Fully compatible (PRD §28 convenience derivative).

### Files / Components Affected

`ml/preprocessing/dataset.py` (docstring), `docs/BUG_LOG.md`,
`docs/DATA_ML_CONTRACT.md`.

---

## DEC-003 — Canonical label set uses ASCII hyphens, not en-dashes

Date: 2026-08-09
Status: ACCEPTED
Phase: 1

### Context

The raw parquet labels for the three Web Attack classes contain a U+FFFD
replacement character (`Web Attack \ufffd Brute Force`, etc.), not an
en-dash as the earlier contract claimed. Verified via codepoint dump on all
canonical partitions.

### Decision

- Normalise the three raw Web Attack labels to ASCII hyphen + space forms:
  `Web Attack - Brute Force`, `Web Attack - Sql Injection`, `Web Attack - XSS`.
- Canonical 15-class set + integer encoding defined in
  `ml/preprocessing/labels.py` (`normalize_label`, `LABEL_TO_INT`) and
  persisted in `ml/artifacts/label_mapping.json` and
  `ml/artifacts/family_mapping.json`.

### Reasoning

Deterministic, ASCII-safe, stable canonical strings are needed for the JSON
contracts, the API response, and reproducible encoding across agents.

### Alternatives Considered

- Keep raw U+FFFD strings. Rejected: non-printable, unstable across
  toolchains, and misleading.
- Use en-dash to match the illustrative PRD §8. Rejected: PRD §8 is
  illustrative only; the observed bytes are authoritative (PRD §28/§29).

### Consequences

- All code, artifacts, and docs use the canonical hyphen forms.
- `docs/DATA_ML_CONTRACT.md` §8/§9 corrected (previously claimed en-dash).

### PRD Compatibility

Fully compatible (PRD §8 illustrative, §28/§29 empirical verification).

### Files / Components Affected

`ml/preprocessing/labels.py`, `ml/artifacts/label_mapping.json`,
`ml/artifacts/family_mapping.json`, `docs/DATA_ML_CONTRACT.md`.

---

## DEC-004 — Class-aware development subset: 300k target, seed 42

Date: 2026-08-09
Status: ACCEPTED
Phase: 1

### Context

PRD §29 requires a class-aware ~200k–500k development subset, minority
classes retained, deterministic sampling, recorded seed.

### Decision

- Implement `build_dev_subset` in `ml/preprocessing/subset.py`:
  keep all classes with count ≤ per_class_cap in full; cap classes above
  per_class_cap to it (except BENIGN); fill the remainder with BENIGN;
  deterministic given seed.
- Locked parameters: target = 300,000; per_class_cap = 60,000;
  cap_floor = 8,000; seed = 42.
- Materialise (already done, verified):
  - `data/processed/dev_random_train.parquet` (300k; BENIGN 88,314,
    DDoS/DoS Hulk/PortScan 60,000 each; capped: BENIGN/DDoS/DoS Hulk/PortScan)
  - `data/processed/dev_temporal_train.parquet` (300k; BENIGN 202,353,
    DoS Hulk 60,000; capped: BENIGN/DoS Hulk; 12 classes — no Friday attacks)
- Each subset writes `.meta.json` with source, seed, counts before/after,
  retained/capped lists.

### Reasoning

Produces a balanced-but-honest training set: rare classes kept, dominant
classes reduced, fully reproducible, no silent class removal.

### Alternatives Considered

- Full 2.8M training. Rejected: exceeds the student-scale, CPU-friendly
  design and PRD §29's explicit subset requirement.

### Consequences

- Baselines train on the subsets; the temporal subset cannot contain
  Friday-only classes by construction (documented).

### PRD Compatibility

Fully compatible (PRD §29).

### Files / Components Affected

`ml/preprocessing/subset.py`, `data/processed/dev_*.parquet(.meta.json)`,
`config/config.yaml` (subset_target/random_seed already match),
`docs/DATA_ML_CONTRACT.md` §2a/§10, `docs/IMPLEMENTATION_STATUS.md`.

---

## DEC-005 — Feature schema locked: 77 canonical features, `Fwd Header Length.1` dropped

Date: 2026-08-09
Status: ACCEPTED
Phase: 1

### Context

The raw schema has a bit-for-bit duplicated `Fwd Header Length.1` column
(BUG-001) and the model input must have a single canonical feature order.

### Decision

- Canonical features = raw 78 minus `Fwd Header Length.1` = 77, in raw
  parquet order (which is identical across partitions).
- Locked in `ml/artifacts/feature_schema.json` (version 1.0,
  `{name, index, dtype: float64}`) and
  `ml/artifacts/inference/feature_order.json`.
- Preprocessing validates raw columns, drops the duplicate, normalises
  non-finite values (safety net; canonical data has none), and reorders to
  the canonical order.

### Reasoning

Deterministic input shape for training, evaluation, and the API; prevents
the duplicate-feature corruption of feature importance / SHAP.

### Alternatives Considered

- Keep both columns. Rejected: corrupts importance/SHAP (BUG-001).

### Consequences

- All Phase-1+ code consumes the 77-feature contract.
- The API validates request features against the canonical order.

### PRD Compatibility

Fully compatible (PRD §30/§31, no PCA in final explainable model).

### Files / Components Affected

`ml/preprocessing/preprocess.py`, `ml/artifacts/feature_schema.json`,
`ml/artifacts/inference/feature_order.json`, `docs/DATA_ML_CONTRACT.md` §5/§14/§15,
`docs/BUG_LOG.md` (BUG-001 FIXED).

---

## DEC-006 — Phase-1 inference model: XGBoost multiclass (random experiment)

Date: 2026-08-09
Status: ACCEPTED
Phase: 1

### Context

The Phase-1 completion gate needs one saved baseline supervised model that
`POST /api/predict` loads end-to-end. Final model selection is explicitly a
Phase-2 task.

### Decision

- Promote `random/xgb/multiclass` (weighted-F1 0.9987, macro-F1 0.8877 on
  random/test) to `ml/artifacts/inference/model.joblib` with
  `model_metadata.json` + `feature_order.json`.
- The API serves this Phase-1 baseline; the response contains only baseline
  fields (no fabricated anomaly/risk/SHAP).

### Reasoning

XGBoost multiclass had the best Phase-1 metrics on in-distribution
(random) evaluation; random is the correct experiment for a runtime model
(the temporal artifact is a generalisation diagnostic, DEC-004 §18).

### Alternatives Considered

- RF multiclass (wF1 0.9983). Close; XGBoost chosen on wF1 + macro-F1.
- Temporal artifact. Rejected: deliberately missing Friday classes.

### Consequences

- Phase-1 API uses the promoted artifact; Phase 2 re-selects the final model
  with full evaluation evidence.

### PRD Compatibility

Fully compatible (PRD §58 Phase-1 gate; §32 final selection deferred).

### Files / Components Affected

`ml/training/export_inference_model.py`, `ml/artifacts/inference/*`,
`backend/app/services/predictor.py`, `docs/DATA_ML_CONTRACT.md` §20–22.


---

## DEC-007 — Final supervised model: XGBoost n_estimators=200 (random)

Date: 2026-08-09
Status: ACCEPTED
Phase: 2

### Context

Phase-2 completion gate requires one saved final supervised model for runtime, selected by a documented selection experiment and evaluated on a test set disjoint from fit and calibration.

### Decision

- Select the random experiment xgb multiclass n_estimators=200 variant (supervised_selection_random.json): macro-F1 0.8898, weighted-F1 0.9988, FP rate 0.00143 on random_3way/test.
- Promote to ml/artifacts/supervised_model.joblib + supervised_model_metadata.json (feature_order = schema order, 77).
- Validation on the DISJOINT random_3way/test: accuracy 0.9987, macro-F1 0.8898, weighted-F1 0.9988.

### Reasoning

- Best macro-F1 among 6 light variants; chosen on macro-F1 and rare-class recall, not on accuracy alone (Random Forest scored 0.0 macro on the rarest class Web Attack Sql Injection).
- Random experiment, not temporal: Friday-only gap (macro-F1 ~0.053 for every model) is a generalisation diagnostic, not a runtime model basis (DEC-004).
- Phase-2 closure audit (2026-08-09): all six PRD §33 criteria verified from
  supervised_selection_random.json / _temporal.json. xgb_200 wins macro-F1
  (0.8898 vs rf_baseline 0.8156), weighted-F1 (0.9988 vs 0.9983), binary FP
  rate (0.00143 vs 0.00166), rare-class recall (Web Attack Sql Injection
  0.667 vs 0.0; Bot 0.992 vs 0.960), and inference cost (4.23 s vs 7.04 s per
  565,576 flows on random/test). The only criterion Random Forest wins is
  one-time train time (19 s vs 84 s), irrelevant for a persisted artifact.
  Temporal experiment kept purely as a generalisation diagnostic (DEC-004):
  xgb_200 has the lowest temporal FP rate (0.00037) of all variants.

### Alternatives Considered

- Random Forest variants (wF1 close): rejected (rare-class recall).
- Temporal artifact: rejected (missing Friday classes).

### Consequences

- Phase-1 inference artifact superseded for runtime; kept on disk.
- XGBoost tree prediction is CPU-friendly (PRD CPU-first principle).

### PRD Compatibility

Compatible with §32, §33, §58.

### Files / Components Affected

`ml/training/select_supervised.py`, `ml/training/train_final_supervised.py`,
`ml/artifacts/supervised_model.joblib`, `supervised_model_metadata.json`,
`ml/evaluation/results/supervised_selection_*.json`,
`ml/evaluation/results/final_supervised_random.json`.


---

## DEC-008 — Isolation Forest + config-driven FPR-constrained threshold

Date: 2026-08-09
Status: ACCEPTED
Phase: 2

### Context

A final anomaly detector must exist (PRD §19, §34) fitted from benign training rows ONLY; its detection threshold must be a documented, config-driven value, not a magic number. Naive max-F1 calibration on attack-skewed validation sets yields an unusable FPR (0.61 on the Friday-only validation).

### Decision

- Fit IsolationForest(n_estimators=200, contamination='auto', random_state=42, n_jobs=-1) on the 88,314 benign rows of dev_random_train.parquet (no scaling).
- Calibration criterion: maximum F1 subject to FPR <= 5% (`anomaly.calibration_criterion: fpr_constrained_max_f1`, `anomaly.max_fpr: 0.05`).
- Threshold calibrated on random_3way/validation (disjoint from test): -0.0928 (validation F1 0.4272, FPR 0.0214).
- Reported on random_3way/test: precision 0.7662, recall 0.2951, F1 0.4261, FPR 0.0221. (Benign-only detector: intentionally honest.)
- config.yaml `anomaly_threshold = -0.0928` (atomic update).

### Reasoning

- Benign-only fit follows PRD; labels must not leak into the anomaly model.
- FPR-constraint keeps the user alert budget under ~2% at the cost of anomaly recall; the hybrid's supervised branch compensates.

### Alternatives Considered

- max-F1 alone: rejected (FPR 0.61).
- Same threshold across experiments: rejected; each experiment calibrates its own.

### Consequences

- `anomaly_score` = IsolationForest decision_function (smaller = more anomalous); flagged when score < threshold.
- Thresholds are config-driven, never imported constants.

### PRD Compatibility

Compatible with §19, §34, §57.

### Files / Components Affected

`ml/training/train_isolation_forest.py`,
`ml/training/isolation_forest_metadata.json`, `ml/artifacts/isolation_forest.joblib`,
`ml/evaluation/results/anomaly_calibration_random.json`, `config/config.yaml`.


---

## DEC-009 — SHAP attribution via XGBoost native TreeSHAP (pred_contribs)

Date: 2026-08-09
Status: ACCEPTED
Phase: 2

### Context

Phase 2 must supply a per-flow SHAP explanation (PR #12). The installed SHAP package (0.49.1, latest) cannot parse XGBoost 3.2.0 multiclass vector base_score and raises `ValueError: could not convert string to float`. Wrapping the model or fabricating SHAP values is not acceptable.

### Decision

- Use XGBoost's native TreeSHAP path `booster.predict(dmat, pred_contribs=True)` instead of the shap library.
- This is the identical exact fast TreeSHAP algorithm the package wraps.
- Verify sum(contributions) + bias == margin for every class 0..14.
- Return top-5 features by |SHAP| for the predicted class, each with feature name, shap_value, direction.

### Reasoning

- Native path is exact, dependency-free, and reproduces the shap methodology; the shap module only fails at the Xenobiotic wrapper layer due to the new base_score format.
- ~0.13 s per flow is acceptable for the academic, per-request explainability contract.

### Alternatives Considered

- shap.TreeExplainer with 0.x: raises on vector base_score.
- Capturing raw base_score: replaced by native path (identical math).

### Consequences

- No new runtime dependency; shap absent from the runtime container tests.
- Top-feature output is reproducible and covered by ml/tests/test_shap.py.

### PRD Compatibility

Compatible with §12 (local-only attribution).

### Files / Components Affected

`ml/hybrid/shap_explainer.py`, `ml/tests/test_shap.py`,`backend/app/services/predictor.py`.


---

## DEC-010 — Hybrid + risk config contract (config-driven, validated)

Date: 2026-08-09
Status: ACCEPTED
Phase: 2

### Context

The hybrid decision layer must implement PR2 §10 semantics deterministically with config-driven thresholds; the risk score must be transparent (PR §11) and reproducible. All thresholds/severities must be config values, not magic numbers.

### Decision

- HybridThresholds from config: known_confidence_threshold = 0.75
  (validated on random_3way/test: acc 0.9991 for conf >= 0.75; only   531/721 errors above 0.75), anomaly_threshold = -0.0928.
- Decision: if supervised conf >= 0.75 and label != BENIGN -> KNOWN_ATTACK; if anomaly flagged and supervised label BENIGN -> UNKNOWN_SUSPICIOUS; else BENIGN. For UNKNOWN the predicted family is dropped (no fabricated family).
- Risk: risk_score = clamp(severity[family] * (0.5 + 0.5*confidence) + 15*anomaly_signal, 0, 100); levels CRITICAL >= 85, HIGH >= 65, MEDIUM >= 40, else LOW; severity table in config (BENIGN 5, Botnet 60, DoS 90, Brute Force 70, Recon 50, Web Attack 80, Heartbleed 95, Infiltration 85, UNKNOWN_SUSPICIOUS 60).
- A BENIGN verdict floors risk to LOW even if the predicted family is an attack (E2E catch); UNKNOWN_SUSPICIOUS uses neutral severity 60.

### Reasoning

- Deterministic gates keep the outcome reproducible and explainable (no randomness at inference).
- Severity/confidence decomposition keeps the score comparable across flows and equal review weight to anomaly signal.

### Alternatives Considered

- ML-based risk value: rejected (PR §11 asks for a transparent formula, no new model).

### Consequences

- Risk(SHAP) families and thresholds live in config/config.yaml; tests cover the BENIGN floor and monotonic severity.
- Phase-2 closure audit (2026-08-09): implementation ordering corrected so the
  anomaly rescue runs for every flow that is not a confident malicious
  prediction (a high-confidence BENIGN verdict no longer masks a suspicious
  anomaly signal); regression test `test_high_confidence_benign_rescued_by_anomaly`
  added (BUG-007 FIXED).

### PRD Compatibility

Compatible with §10, §11.

### Files / Components Affected

`ml/hybrid/decision.py`, `ml/hybrid/risk.py`, `config/config.yaml`,
`ml/tests/test_hybrid.py`, backend response schema.

---

## DEC-011 — Scenario fixtures: real features + synthetic side-car metadata

Date: 2026-08-09
Status: ACCEPTED
Phase: 3

### Context

Replay needs deterministic, reproducible, self-contained scenarios that do
not force a runtime dependency on the HF dataset. The fixtures must feed the
SHARED Phase-2 predictor exactly the 77 canonical feature values inference
consumes, and must not leak evaluation ground truth into the model
(BUG-005/DEC-runtime-purity).

### Decision

- Committed JSON fixtures `data/scenarios/*.json` (schema `scenario/v1`),
  generated ONCE by `ml/evaluation/build_scenarios.py` from real held-out
  random_3way/test rows.
- Each flow stores: `features` = the 77 canonical model inputs; side-car
  `source`/`destination`/`service_port`/`seq` = SYNTHETIC replay metadata used
  only for grouping + UI; `ground_truth_label` = EVALUATION note only.
- The predictor interface never receives source/destination/port/truth: a
  replay flow passes ONLY `features` (regression tests assert exactly this).

### Reasoning

Debuggability, reproducibility, runtime hermeticity. Side-car metadata is how
the UI shows hosts/ports without mixing it into the feature vector.

### Alternatives Considered

- Streaming from HF at runtime: rejected (network dependency, non-reproducible).
- Injecting labels/feature overrides: rejected (feature padding violates the
  77-feature contract).

### Consequences

- `data/scenarios/*.json` committed; runtime loads fixtures only.
- `ground_truth_label` is never a predictor input; guarded by tests.

### PRD Compatibility

Compatible with §7 (replay), §29–34 (data discipline), §42 (replay pipeline).

### Files / Components Affected

`ml/evaluation/build_scenarios.py`, `data/scenarios/*.json`,
`backend/app/services/scenarios.py`.


---

## DEC-012 — Incident grouping: rule key + "port where meaningful" semantics

Date: 2026-08-09
Status: ACCEPTED
Phase: 3

### Context

Phase-3 must convert the raw prediction stream into comprehensible incidents
(PRD §14, §17). Requirement: "group by family + source + destination +
service/port where meaningful + time window; natural multi-flow attacks
(e.g. PortScan) form one incident."

### Decision

- Only KNOWN_ATTACK and UNKNOWN_SUSPICIOUS flows open/extend incidents;
  pure-BENIGN flows never do.
- Grouping key = (classification, family, source, destination[, service_port]).
  `service_port` is included as a discriminator for NON-scanning families but
  EXCLUDED for scanning families (Reconnaissance), so a PortScan touching many
  ports remains ONE incident. This is the deterministic encoding of "service/
  port where meaningful".
- Window: `incidents.grouping_window_seconds` from config (placeholder 30s).
  A flow matching an open key within the window joins it; outside the window
  supersedes it (old incident ended) and opens a new one.
- Aggregates: flow_count, first/last seen, max risk score/level, dominant
  label (highest risk; earliest flow wins ties).

### Reasoning

Deterministic, stateless-enough to unit test exhaustively, and matches the
PRD intent that a scan across many ports is a single investigation.

### Alternatives Considered

- Always include service_port: rejected (would fragment a PortScan).
- Never include service_port: rejected (distinct services on distinct ports
  should surface separately when the family is not scanning).

### Consequences

- Grouping unit tests (16) cover every rule; service persists Incident +
  IncidentFlow rows with per-flow evidence.

### PRD Compatibility

Compatible with §14, §17, §42, §57 (config-driven threshold).

### Files / Components Affected

`backend/app/services/incidents.py`, config `incidents.grouping_window_seconds`,
incident schema/api.


---

## DEC-013 — Replay engine: in-process worker thread + polling status

Date: 2026-08-09
Status: ACCEPTED
Phase: 3

### Context

Replay must expose start/pause/resume/stop and deterministic progress over real
(committed-fixture) flows through the shared Phase-2 predictor, without
introducing WebSockets, message queues, or a job worker per PRD §42 /
ARCHITECTURE_LOCK.

### Decision

- In-process `ReplayService` with a daemon worker thread; controls mutate a
  small state machine guarded by a lock; status is polled via
  `GET /api/replay/status`.
- States: IDLE -> RUNNING | PAUSED -> COMPLETED | STOPPED. Start rejects
  concurrent RUNNING/PAUSED (HTTP 409); speeds {1,5,20} from config affect
  pacing only (`sleep = interval/speed`), pacing injectable for tests so tests
  never sleep on real time.
- Determinism: exact scenario `seq` order; synthetic replay timestamp =
  `scenario base + seq × interval` (never presented as original capture time);
  monotonic counters.
- Every flow runs through the shared Phase-2 predictor; SHAP only for
  suspicious flows (keeps replay fast and the pipeline faithful to PRD §42).

### Reasoning

CPU-only project scale; polling-first (PRD §42); no extra infra. Injectable
pacing keeps the state machine fully unit-testable.

### Alternatives Considered

- WebSockets live-updates: rejected (PRD §42 explicit).
- External queue/celery: rejected (ARCHITECTURE_LOCK).
- Pure synchronous iteration inside a request: rejected (start must return
  immediately so the UI can poll).

### Consequences

- 11 engine unit tests (start/pause/resume/stop/concurrency/determinism/
  pacing) + live uvicorn gate PASS; shared predictor reused via
  `get_predictor()`.

### PRD Compatibility

Compatible with §13, §42, §57.

### Files / Components Affected

`backend/app/services/replay.py`, `backend/app/api/replay.py`,
`backend/app/schemas/replay.py`.

## DEC-014 — Recent-flows live feed contract for the Security Monitor

Date: 2026-08-10
Status: ACCEPTED
Phase: 3

### Context

The Security Monitor live traffic table needs the most recent per-flow replay
evidence (including pure BENIGN rows). Pre-audit found no existing endpoint
served this view — `GET /api/incidents/{id}` is aggregated and only covers
suspicious evidence.

### Decision

- Add `GET /api/replay/flows?limit=` (default 50, 1..500) returning newest-
  first persisted replay `Prediction` rows as `ReplayFlowOut`/`ReplayFlowsOut`.
- Extend `Prediction` with side-car columns `source`, `destination`,
  `service_port`, `seq`, `replay_time`, populated by the replay persist path
  (additive migration).
- The frontend polls this with the same 1.5 s cadence as replay status; the
  traffic table is capped client-side (latest 200) to keep the DOM lean.

### Reasoning

CPU-only scale; polling-first; reuses existing persistence. No WebSockets, no
cache layer — the query is a simple indexed read.

### Alternatives Considered

- Deriving rows from replay status memory: rejected (not persisted survives
  restart; incident detail already needs DB rows).
- Adding a cross-endpoint embed (status carries flows): rejected (status would
  bloat; flows change at a different rhythm).

### Consequences

- 2 new API tests; live E2E gate extended to assert newest-first + limit clamp.
- Frontend typed client gets `recentFlows()`; TrafficTable/AttackTimeline/
  SummaryCards all consume one source of truth.

### PRD Compatibility

Compatible with §7 (traffic stream), §15–16 (monitor views), §42 (polling),
and the data/feature purity boundary (side-car metadata never a model feature,
BUG-005).

### Files / Components Affected

`backend/app/{db/models.py,database.py,services/replay.py,schemas/replay.py,
api/replay.py}`, `backend/tests/test_replay_api.py`,
`backend/tests/e2e_replay_phase3.py`, `frontend/src/api/*`, `TrafficTable.tsx`.

## DEC-015 — Run-scoped monitor views (replay run_id isolation)

Date: 2026-08-10
Status: ACCEPTED
Phase: 3.5 (hardening)

### Context

Sequential replays on one server mixed evidence: the live traffic table and
the incident side panel showed stale rows from the previous run as "current"
(BUG-011). Persisted replay evidence had no run identity to filter on.

### Decision

- `ReplayService` generates a `run_id` (uuid hex) at every `start()` and
  persists it on every replayed `Prediction` and `Incident` row (additive
  columns + additive migration).
- `GET /api/replay/flows?run_id=` and `GET /api/incidents?run_id=` scope the
  view to one run; omitting the param keeps existing behaviour (full history).
- The Security Monitor passes the current `status.run_id`; the Incidents hub
  page omits it so the audit trail stays complete.
- Incident grouping remains per-run (fresh grouper per `_run`), so an incident
  count for the current run already reflected only that run.

### Reasoning

CPU-only scale; reuses the existing persistence + list endpoints; no new
infrastructure. Parametrized filters beat per-entity "current" flags (no
mutable global state, survives restart via persisted rows).

### Alternatives Considered

- In-memory "current run marker" table: rejected (lost on restart; dual source
  of truth with persisted rows).
- New resolving-a-run key endpoint: rejected (the status already returns
  `run_id`; the UI can pass it straight to the feed/incident queries).
- Deleting/scoping the persisted incident history to the current run: rejected
  (incidents are evidence; the Incidents page keeps full history).

### Consequences

- 1 new API test + extended live E2E gate + real-browser sequential E2E PASS.
- Persisted schema grows two nullable additive columns (no backfill needed);
  migration idempotent.
- Frontend typed client exposes optional `run_id` on both queries.

### PRD Compatibility

Compatible with §15–16 (monitor views), §42 (polling). Incidents remain
historical evidence (audit trail preserved).

### Files / Components Affected

`backend/app/services/replay.py`, `backend/app/api/{replay,incidents}.py`,
`backend/app/db/{models,database}.py`, `frontend/src/pages/SecurityMonitor.tsx`,
`frontend/src/api/{client,types}.ts`, `backend/tests/test_replay_api.py`,
`backend/tests/e2e_replay_phase3.py`.

## DEC-016 — Single-pass replay SHAP via Phase2Predictor.explain

Date: 2026-08-10
Status: ACCEPTED
Phase: 3.5 (hardening)

### Context

`_predict_one` ran the whole Phase-2 pipeline twice per suspicious flow: once
without SHAP and again with SHAP (BUG-010), because `predict(with_shap=True)`
bundles SHAP into a full re-prediction.

### Decision

- Add `Phase2Predictor.explain(features)`: builds the canonical feature row
  (same validation/normalisation path as `predict`) and runs ONLY the SHAP
  block (`top_k=5` native TreeSHAP), returning the identical dict structure the
  `with_shap=True` path returns.
- Replay calls `predict()` exactly once per flow, then `explain()` only for
  suspicious/non-BENIGN flows.

### Reasoning

Keep the SHAP contract byte-identical to `predict(with_shap=True)` so no
evidence semantics change while halving replay compute for attack flows. No new
dependencies.

### Alternatives Considered

- Caching SHAP at predict time and discarding on non-suspicious — rejected
  (still pays SHAP cost for benign flows; replay keeps SHAP only for
  suspicious flows per PRD §42).
- Lazy SHAP recompute inside one pipeline — rejected (defeats the fewest-passes
  goal; larger refactor of a frozen Phase-2 file).

### Consequences

- `ml/tests/test_predictor.py` +1 (`test_explain_matches_predict_shap`),
  predictor 7 tests; replay truth-isolation counts updated (12 predict +
  12 explain).

### PRD Compatibility

Compatible with §42 (SHAP only for suspicious flows) and §34 (evidence
purity / explainability preserved).

### Files / Components Affected

`backend/app/services/predictor.py`, `backend/app/services/replay.py`,
`ml/tests/test_predictor.py`, `backend/tests/test_replay.py`.


## DEC-017 - Approved controlled implementation and replay failure policy

Date: 2026-10-31
Status: ACCEPTED (user-approved implementation plan)
Phase: Phase-4 prerequisites; targeted Phase-3 reliability defects reopened.

The user authorized the reviewed four-milestone plan: reliability, evaluation
credibility/provenance, Playground backend/assessment, Playground UI/completion.
No retraining, model replacement, threshold changes, risk/SHAP changes, new
infrastructure, or deferred Phase-5 features are authorized by this decision.

Replay now fails terminally on inference/persistence errors instead of retrying
one record forever. FAILED is an additive lifecycle outcome. Roll back the
failed transaction, retain earlier committed evidence, close sessions, and allow
restart only after the prior worker exits. Successful replay semantics remain.
409 denotes lifecycle conflicts; unavailable inference is 503; unexpected control
errors remain server errors. A shutdown hook drains the existing worker without
loading artifacts merely for shutdown. A stuck native call cannot be forcibly
cancelled; restart is rejected while its worker remains alive.

Files: services/replay.py, api/replay.py, schemas/replay.py, main.py,
backend/tests/test_replay_failures.py. PRD-compatible reliability hardening.

## DEC-018 - Persist effective anomaly thresholds with evidence

Date: 2026-10-31
Status: ACCEPTED (approved plan Task 3)
Prediction carries nullable anomaly_threshold; additive migration preserves old
records with NULL. API fields are additive. UI uses recorded threshold, never a
duplicated constant. No historical threshold is invented. Model decisions, risk
and thresholds themselves remain unchanged. See Batch 3 tests/evidence.

## DEC-019 - Correct historical reporting; retain frozen experiment outputs

Date: 2026-10-31
Status: ACCEPTED (approved Milestone 2 Task 4)
Scripts and saved confusion matrices establish actual populations. Current docs
distinguish binary/multiclass/hybrid, correct split labels and sensitivity recall,
and acknowledge selection/test reuse. Historical JSON and append-only entries are
retained; this correction supersedes conflicting prose in DEC-007/010. No data,
models or decision logic changed. See EVALUATION_PROTOCOL.md.

## DEC-020 - Provenance-backed small scenario library

Date: 2026-10-31
Status: ACCEPTED (approved Task 6)
Preserve original demo vectors and disclose exact-feature overlap separately from
source-row identity. Legacy locators identify first equivalent pinned rows. Three
new 8-row SSH/FTP/web fixtures exclude exact deployed-training matches and are
selected without predictions. Unknown remains a benign anomaly challenge.
Provenance is evaluation metadata and never enters model inputs.

## DEC-021 - Minimal profile relevance rules

Date: 2026-10-31
Status: ACCEPTED (approved Task 7)
SSH/FTP follow enabled services; web attacks require web + public exposure.
DoS follows public services or 50+ scale. PortScan follows lab/small organisation
or non-small scale. Always include benign control and benign anomaly challenge.
Database/file sharing remain uncovered; unknown-attack detection not established.
Profile preview/persistence needs no model; strict inputs contain no network target.

## DEC-022 - Outcome-based bounded Playground assessment

Date: 2026-10-31
Status: ACCEPTED (approved Task 8)
Use existing Playground tables and synchronous <=64-flow requests. Equal configurable
weights combine macro attack-scenario recall and pooled benign specificity. Show raw
counts, missing/unsupported coverage and fixed dataset limitations alongside score.
No score with missing selected scenarios or no malicious/benign evidence. Store
historical context and evidence separately from Monitor; never reinterpret old runs
using new thresholds/weights. Failed/interrupted runs cannot have a success score.

## DEC-023 - Approved frontend console redesign

Date: 2026-10-31
Status: ACCEPTED (explicit user authorization to implement, validate, commit and push)
Apply the installed Network IDS/Hue language to the existing React application:
IBM Plex Sans/Mono, 14px body, charcoal/light surfaces, flat hierarchy and restrained
semantic markers. Preserve React navigation, polling, run isolation, all API calls,
backend/ML behavior, thresholds, fixtures and incident grouping.

Replace the communication graph's force layout with a small React SVG diagram.
Only actual source/destination hosts are nodes. Aggregate each directed host pair;
ports, observed counts and maximum recorded risk belong to connection evidence.
Missing risk remains unavailable, protocol is explicitly unavailable. Fixed lane
slots persist across polling and selection/filter changes; new hosts append.
Two-lane diagrams fit narrow screens; mixed-role diagrams and tables scroll locally.
Keyboard-selectable host controls and connection rows retain access to evidence.
No new dependency or topology inference. The unused existing Cytoscape dependency
is left installed; dependency cleanup and arbitrary large-graph optimization are
outside this redesign.

Risk uses fixed 0-100 axes; distribution remains literal integer counts. Shared
signed SHAP bars use exact stored contributions and a common symmetric scale per
flow, with an aligned zero axis, outlined negatives and explicit raw-margin units.
External skill artifacts stay in their installed location and outside Git. The
frontend's committed tokens are self-contained at runtime. This is Phase 4 visual
completion, not authorization for deferred Phase 5 functionality.
