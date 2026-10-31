# BUG_LOG.md — Bug Register

Maintain bugs with enough information for another agent to reproduce them.
Do not log trivial temporary syntax errors unless they exposed a meaningful
implementation issue.

Format:

```markdown
## BUG-XXX — Title

Status: OPEN | INVESTIGATING | FIXED | WONTFIX
Detected:
Phase:
Severity:

### Symptoms
### Expected Behaviour
### Actual Behaviour
### Reproduction
### Relevant Files
### Root Cause
### Fix
### Validation
### Regression Test
### Notes
```

Severity guide: `CRITICAL` (blocks a completion gate / data leakage),
`HIGH` (wrong results / broken contract), `MEDIUM` (degraded behaviour),
`LOW` (cosmetic / minor).

---

## BUG-001 — Duplicate feature column: `Fwd Header Length` vs `Fwd Header Length.1`

Status: FIXED
Detected: 2026-08-09
Phase: 1
Severity: MEDIUM

### Symptoms

The cleaned CICIDS2017 schema (all configs) contains two columns
`Fwd Header Length` and `Fwd Header Length.1` that are **bit-for-bit
identical** (verified equal across all canonical partitions:
random/train 2,262,300 rows; random/test 565,576; temporal/train 2,125,158;
temporal/test 702,718).

### Expected Behaviour

Each flow feature appears once; preprocessing yields a unique feature set.

### Actual Behaviour

A duplicated feature doubles one signal and would silently corrupt feature
importance / SHAP attribution if both are fed to the model.

### Reproduction

```python
from ml.preprocessing.dataset import LoadConfig, load_split
df = load_split(LoadConfig(config="random", split="test",
                columns=["Fwd Header Length", "Fwd Header Length.1"]))
assert df["Fwd Header Length"].equals(df["Fwd Header Length.1"])  # True
```

### Relevant Files

- `data/processed/dataset_inspection_cicids2017.json` (dup_fwd_header_length_equal: true)
- `ml/preprocessing/preprocess.py` (DUPLICATE_COLUMNS, drops the column)
- `ml/artifacts/feature_schema.json` (dropped_features section)

### Root Cause

CICFlowMeter emits a duplicated "Fwd Header Length" field; the parquet
publisher kept both columns rather than deduplicating.

### Fix

Phase-1 preprocessing drops `Fwd Header Length.1` (keeps
`Fwd Header Length`). Recorded in `feature_schema.json`
(`dropped_features`) and `DATA_ML_CONTRACT.md` §5. Canonical feature set is
now exactly 77 numeric features.

### Validation

- `ml/preprocessing/preprocess.py` drops the duplicate in `preprocess_frame`.
- Preprocessing invariant tests assert 77 unique canonical columns.
- Feature schema artifact matches `CANONICAL_FEATURE_COLUMNS` exactly.

### Regression Test

`ml/tests/test_preprocessing.py::TestPreprocess::test_duplicate_dropped_not_kept`
and `test_no_canonical_duplicates` and `test_feature_schema_matches_artifact`.

### Notes

Resolved in preprocessing; this was a data-quality/design item, not an
application bug. Raw parquet files are NOT modified.

---

## BUG-002 — HF `config_name=` keyword raises TypeError (misclassified as HF bug)

Status: WONTFIX (classification corrected; working path documented)
Detected: 2026-08-09
Phase: 1
Severity: LOW

### Symptoms

`datasets.load_dataset("lacg030175/CICIDS2017", config_name="temporal", ...)`
raises:
`TypeError: ...ParquetCicids2017() got multiple values for keyword argument 'config_name'`.

### Expected Behaviour

Either the keyword form works, or the error is understood as an API-argument
quirk rather than a builder defect.

### Actual Behaviour

The keyword form is rejected; the **positional** config form works:
`load_dataset("lacg030175/CICIDS2017", "temporal", revision=<pinned>,
split="train")` (datasets 5.0.1). Streaming also works with positional config.

### Reproduction

```python
import datasets
datasets.load_dataset("lacg030175/CICIDS2017", "temporal", revision="d071fd...")
```

### Relevant Files

`ml/preprocessing/dataset.py` (loader docstring corrected; direct `hf://`
parquet path remains the efficient default — identical rows either way).

### Root Cause

The packaged `ParquetCicids2017` builder of this derivative passes
`config_name` through both its generated signature and the packaged-builder
YAML, so the keyword argument is supplied twice. Not an HF `datasets` defect.

### Fix

Use the positional config form (canonical), or load the parquet files
directly via `hf://` (efficient default used by `load_split`).

### Validation

Verified on datasets 5.0.1 with the pinned revision (see DEC-002).

### Regression Test

Not applicable (no code path uses the keyword form).

### Notes

Corrected the prior agent's misdiagnosis in `dataset.py`'s docstring and in
`docs/DECISIONS.md` DEC-002.

---

## BUG-003 — SPRINT_LOG.md was not valid UTF-8 (mixed encoding)

Status: FIXED
Detected: 2026-08-09 (Phase-1 audit)
Phase: 1
Severity: LOW

### Symptoms

`docs/SPRINT_LOG.md` could not be decoded as UTF-8:
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa7 in position ...`.
The file was mostly UTF-8 but contained 4 stray cp1252 `0xA7` (§) bytes
where an em-dash/section-sign had been written under a cp1252 console, so
every UTF-8 reader failed on it.

### Expected Behaviour

Every repository doc decodes as UTF-8 (the other docs do, verified).

### Actual Behaviour

A UTF-8 `read_text` raised on SPRINT_LOG.md, breaking the append-only
history the AGENTS.md read-order depends on.

### Reproduction

```python
Path("docs/SPRINT_LOG.md").read_text(encoding="utf-8")
# UnicodeDecodeError: byte 0xa7 in position ...
```

### Relevant Files

`docs/SPRINT_LOG.md`

### Root Cause

Mixed byte encodings were written into the file (cp1252 section signs
embedded in an otherwise UTF-8 document) across sessions using different
console encodings.

### Fix

Normalised the file to valid UTF-8: decoded with `errors="surrogateescape"`,
mapped the 4 lone `\udca7` surrogates to `\xa7`, re-encoded as UTF-8. No
entry text was altered at that point (4 entries preserved, 30 em-dashes
intact). NOTE: the file was later truncated by the BUG-004 append failure
and then fully restored; see BUG-004.

### Validation

- `Path("docs/SPRINT_LOG.md").read_text(encoding="utf-8")` now succeeds.
- Round-trip assert on decode/encode passed.
- All 4 historical entries still parse; all `§` references now real UTF-8.
- After BUG-004 recovery, re-verified: 4 entries restored + audit entry 5
  appended, valid UTF-8, no control characters or lone surrogates.

### Regression Test

Manual (documentation file): a future `read_text(encoding="utf-8")` on
SPRINT_LOG.md must not raise.

### Notes

Documentation-only fix; no code, artifact, or data change. The subsequent
truncation and recovery are documented in BUG-004.

---

## BUG-004 — SPRINT_LOG.md truncated by failed append write (unicode escape in script)

Status: FIXED
Detected: 2026-08-09 (Phase-1 audit, appending audit entry)
Phase: 1
Severity: HIGH (data-loss incident in governance history)

### Symptoms

After the BUG-003 fix, an attempt to append the audit entry to
`docs/SPRINT_LOG.md` destroyed the file: it was truncated to a 5,220-byte
fragment containing only the start of the new entry. The 4 historical
entries (bootstrap, corrections, lead agent, completion agent) were lost
from disk.

### Expected Behaviour

Appending an entry must never destroy existing history.

### Actual Behaviour

The append script raised
`UnicodeEncodeError: 'utf-8' codec can't encode character '\udca7' in
position 24242: surrogates not allowed`, and `Path.write_text` (which opens
the target with `'w'`, truncating before writing) left the file truncated.

### Reproduction

The append script's triple-quoted entry text contained the literal
characters `\udca7` (in prose describing the BUG-003 fix). Python parsed
`\u...` inside a non-raw string literal as a unicode escape, producing a
lone surrogate U+DCA7, which UTF-8 cannot encode.

### Relevant Files

- `docs/SPRINT_LOG.md` (restored)
- `C:\Users\BIT\AppData\Local\Temp\opencode\append_sprint.py` (faulty
  script, superseded)

### Root Cause

Two compounding causes:
1. `Path.write_text` truncates the destination before encoding the new
   content, so any encoding failure mid-write leaves a damaged file.
2. The append script used a plain (non-raw) triple-quoted Python string that
   contained the literal text `\udca7`; Python interpreted it as an escape
   (lone surrogate) that UTF-8 rejects.

### Fix

- Rebuilt `docs/SPRINT_LOG.md` from authoritative sources in the opencode
  session database (`C:\Users\BIT\.local\share\opencode\opencode.db`),
  which stores every tool call and its output: entries 1–3 from the
  completion agent's pre-append full read; entry 4 from the completion
  agent's `Add-Content` command text (the clean intended text — the on-disk
  copy had been corrupted by PowerShell backtick-escape processing, e.g.
  `` `b `` -> backspace, `` `f `` -> form feed).
- Appended the audit entry atomically: write to a temp file in the same
  directory, then `os.replace`; the new entry avoids raw `\u...` literal
  text (describes it as "backslash-u-d-c-a-7").
- No git backup, Volume Shadow Copy (requires admin), OneDrive conflict copy,
  or File History existed for this file; the opencode DB was the only
  recovery source.

### Validation

- Restored file: 4 entries, 34 `§`, 30 em-dashes, 0 control characters
  (0x08/0x0C/0x0D), 0 lone surrogates — matching the pre-truncation
  fingerprint.
- Post-append: 5 entries, valid UTF-8, 26,735 bytes, last line matches the
  intended entry-5 closing line.
- Entry 4 content diffed against the DB-captured on-disk read: 100% of
  substantive lines match (differences are only the restored backticks and
  proper `§`).

### Regression Test

- Documentation append pattern: use atomic write (temp file + `os.replace`)
  and verify the file re-reads as valid UTF-8 with the expected entry count
  after every append.
- Never include literal `\u`/`\U` text in a non-raw Python string that will
  be encoded to UTF-8.

### Notes

Incident fully recovered with zero content loss (verified against the
DB-captured reads). Lesson recorded in `docs/SPRINT_LOG.md` audit entry and
this register.

---

## BUG-005 — Unknown/unseen experiment passed the TRUE label into the hybrid

Status: FIXED
Detected: 2026-08-09
Phase: 2
Severity: HIGH

### Symptoms

First run of the Phase-2 unknown/unseen simulation reported impossible
per-class hybrid outcomes (e.g. every temporal unseen class looked perfectly
handled, contradicting the low Isolation-Forest anomaly scores).

### Expected Behaviour

The hybrid receives the SUPERVISED PREDICTED label + confidence, never the
ground-truth label (PRD §10 logic: the runtime has no labels).

### Actual Behaviour

The hybrid path received the true/generated label while the confidence came
from the supervised model, so KNOWN_ATTACK was returned for flow classes
that the model actually predicted as BENIGN — inflating the honest metrics.

### Reproduction

Run `ml/evaluation/results/unknown_experiment_temporal.json` with the old
`run_unknown_experiment.py` prior to the fix; the hybrid row counts reflected
ground truth, not predictions.

### Relevant Files

`ml/training/run_unknown_experiment.py`, `ml/hybrid/decision.py` (unchanged:
always consumed its `label` argument as the classifier output).

### Root Cause

Script wiring error: the experiment passed the test partition's y-vector into
the hybrid call instead of the model's own predictions.

### Fix

Pass `y_pred_codes[i]` (supervised prediction) as the `label`; documented in
the script (`# Hybrid uses the SUPERVISED PREDICTED label + confidence
(PRD  10), never the ground-truth label.`).

### Validation

- Re-ran the experiment; final honest outcomes are in
  `ml/evaluation/results/unknown_experiment_temporal.json`.
- Cross-checked per-flow predicted-label distribution (DDoS ->
  KNOWN_ATTACK via DoS-Hulk similarity; PortScan/Bot -> high-confidence
  BENIGN), matching the raw model behaviour.

### Regression Test

`ml/tests/test_predictor.py` permanent regression tests (2026-08-09,
BUG-005 closure): `test_predictor_signature_has_no_ground_truth_argument`
(signature rejects any truth/label parameter),
`test_predict_ignores_extra_metadata_keys` (identical features + extra
metadata == identical prediction/classification/risk),
`test_missing_and_extra_features_rejected_independently_of_label`
(extra/synthetic ground-truth keys raise `PredictorError`, so runtime
inference is a pure function of canonical features only). `ml/tests/test_hybrid.py`
asserts the hybrid takes a generic `label` input; the unknown experiment reads
supervised_predicted_labels rather than the y-vector.

### Notes

The ranking of "unseen class risk" changed materially after the fix —
always trust the corrected file; treat the first run's numbers as
invalid (not re-used in any governance doc).
Runtime-purity evidence is independently recorded in
`ml/evaluation/results/e2e_evidence_phase2.json` (A4): per-evidence
`evaluation_truth_label` is stored for scoring ONLY; `predictor.predict()`
never receives it.


---

---

## BUG-006 — SHAP 0.49.x cannot parse XGBoost 3.2 multiclass base_score

Status: FIXED (worked around, documented as DEC-009)
Detected: 2026-08-09
Phase: 2
Severity: MEDIUM

### Symptoms

`shap.TreeExplainer(model)` on the Phase-2 XGBoost multiclass model raised:
`ValueError: could not convert string to float: '[3.603...E0,...]'` —
the SHAP package cannot read xgboost 3.2's vector `base_score`.

### Expected Behaviour

Phase 2 requires per-flow SHAP local attribution (PRD  12).

### Actual Behaviour

The `shap` wrapper is incompatible with the installed xgboost (3.2.0,
vector base_score); could not derive an explanation through that path.

### Relevant Files

`ml/hybrid/shap_explainer.py`.

### Root Cause

Upstream SHAP 0.49.x (latest at time of work) parses model params for a
single scalar `base_score`; XGBoost 3.2 multiclass stores it as a vector
string, breaking SHAP's import.

### Fix (decision)

Used XGBoost's NATIVE TreeSHAP path
`booster.predict(dmat, pred_contribs=True)` (BaseMargin=True),
verified by assert sum(contributions)+bias == margin for every class. This
is the exact algorithm SHAP wraps, so no explanation methodology change.
(DEC-00 -> see docs/DECISIONS.md DEC-009.)

### Validation

`ml/tests/test_shap.py` (3 passed): top-5 ordering, feature names,
base value; sum check over the 15 classes passes in CI test run.
~0.13 s per flow on the phoenix-test slide.

### Regression Test

`test_shap_returns_top_features` (still part of the suite).

### Notes

The dependency-free native path also avoids pinning/incompatible SHAP
versions in the runtime container.

---

## BUG-007 — Hybrid short-circuited before the anomaly rescue for high-confidence BENIGN

Status: FIXED
Detected: 2026-08-09 (Phase-2 closure audit)
Phase: 2
Severity: HIGH

### Symptoms

The hybrid layer returned BENIGN for a high-confidence BENIGN supervised
prediction even when the anomaly detector flagged the flow as suspicious, so
structurally-benign-but-suspicious flows never surfaced as
UNKNOWN_SUSPICIOUS.

### Expected Behaviour

PRD §10 closure semantics: KNOWN_ATTACK only when the supervised label is a
malicious class AND confidence >= threshold; then the anomaly rescue runs for
every remaining flow (including high-confidence BENIGN) ->
UNKNOWN_SUSPICIOUS; otherwise BENIGN.

### Actual Behaviour

`hybrid_decision` returned early on confidence alone:
`if confidence >= threshold: return KNOWN_ATTACK if label != "BENIGN" else BENIGN`,
so a high-confidence BENIGN prediction with a suspicious anomaly score was
classified BENIGN and the anomaly signal was masked.

### Reproduction

`hybrid_decision(confidence=0.99, label="BENIGN", anomaly_score=-0.5,
thresholds=TH)` returned BENIGN before the fix.

### Relevant Files

`ml/hybrid/decision.py`, `ml/tests/test_hybrid.py`,
`ml/training/run_unknown_experiment.py` (duplicated `_hybrid` helper).

### Root Cause

The early-return branch keyed on confidence only, not on the combination
`label != "BENIGN" AND confidence >= threshold`.

### Fix

Reordered the gates: KNOWN_ATTACK requires a malicious predicted label AND
confidence >= threshold; the anomaly rescue then runs for all other flows;
BENIGN is the final fallback. `run_unknown_experiment.py` now delegates to the
single shared `hybrid_decision`.

### Validation

- Re-ran `python -m ml.training.run_unknown_experiment`: benign hybrid
  outcomes on Friday test moved from 4 to 7,319 UNKNOWN_SUSPICIOUS (all
  IF-flagged benign flows now surfaced); Bot 940 -> 927 BENIGN + 13
  UNKNOWN; PortScan +11 UNKNOWN; DDoS unchanged (its flagged flows were
  already KNOWN_ATTACK via DoS Hulk).
- Full suite `python -m pytest ml/tests backend/tests -q` -> 40 passed.

### Regression Test

`ml/tests/test_hybrid.py::test_high_confidence_benign_rescued_by_anomaly`
(confidence=0.99, label=BENIGN, anomaly=-0.5 -> UNKNOWN_SUSPICIOUS).

### Notes

DEC-010 already documented the correct ordering; the implementation now
matches the recorded decision.

---

## BUG-007 — Hybrid short-circuited before the anomaly rescue for high-confidence BENIGN

Status: FIXED
Detected: 2026-08-09 (Phase-2 closure audit)
Phase: 2
Severity: HIGH

### Symptoms

The hybrid layer returned BENIGN for a high-confidence BENIGN supervised
prediction even when the anomaly detector flagged the flow as suspicious, so
structurally-benign-but-suspicious flows never surfaced as
UNKNOWN_SUSPICIOUS.

### Expected Behaviour

PRD §10 closure semantics: KNOWN_ATTACK only when the supervised label is a
malicious class AND confidence >= threshold; then the anomaly rescue runs for
every remaining flow (including high-confidence BENIGN) ->
UNKNOWN_SUSPICIOUS; otherwise BENIGN.

### Actual Behaviour

`hybrid_decision` returned early on confidence alone:
`if confidence >= threshold: return KNOWN_ATTACK if label != "BENIGN" else BENIGN`,
so a high-confidence BENIGN prediction with a suspicious anomaly score was
classified BENIGN and the anomaly signal was masked.

### Reproduction

`hybrid_decision(confidence=0.99, label="BENIGN", anomaly_score=-0.5,
thresholds=TH)` returned BENIGN before the fix.

### Relevant Files

`ml/hybrid/decision.py`, `ml/tests/test_hybrid.py`,
`ml/training/run_unknown_experiment.py` (duplicated `_hybrid` helper).

### Root Cause

The early-return branch keyed on confidence only, not on the combination
`label != "BENIGN" AND confidence >= threshold`.

### Fix

Reordered the gates: KNOWN_ATTACK requires a malicious predicted label AND
confidence >= threshold; the anomaly rescue then runs for all other flows;
BENIGN is the final fallback. `run_unknown_experiment.py` now delegates to the
single shared `hybrid_decision`.

### Validation

- Re-ran `python -m ml.training.run_unknown_experiment`: benign hybrid
  outcomes on Friday test moved from 4 to 7,319 UNKNOWN_SUSPICIOUS (all
  IF-flagged benign flows now surfaced); Bot 940 -> 927 BENIGN + 13
  UNKNOWN; PortScan +11 UNKNOWN; DDoS unchanged (its flagged flows were
  already KNOWN_ATTACK via DoS Hulk).
- Full suite `python -m pytest ml/tests backend/tests -q` -> 40 passed.

### Regression Test

`ml/tests/test_hybrid.py::test_high_confidence_benign_rescued_by_anomaly`
(confidence=0.99, label=BENIGN, anomaly=-0.5 -> UNKNOWN_SUSPICIOUS).

### Notes

DEC-010 already documented the correct ordering; the implementation now
matches the recorded decision.

---

## BUG-008 — Pre-built "normal" scenario contained an anomaly-flagged benign flow

### Symptoms

`data/scenarios/normal.json` (initial build) contained one benign flow the
whole pipeline classified UNKNOWN_SUSPICIOUS, so replaying "normal" created an
incident, contradicting the PRD "strictly benign profile -> no incident".

### Reproduction

Run `build_scenarios.py` with plain first-N BENIGN rows, then replay the
scenario.

### Relevant Files

`ml/evaluation/build_scenarios.py`, `dataset` random_3way/test BENIGN rows.

### Root Cause

"BENIGN" truth rows are not homogeneous under the hybrid: the benign-only
Isolation Forest flags a small share of structurally-normal benign flows
(Phase-2 documented limitation), and those become UNKNOWN_SUSPICIOUS.

### Fix

The normal scenario now selects real held-out BENIGN rows that the SHARED
predictor classifies as strictly BENIGN (deterministic first-hit scan using
`with_shap=False`); the fixture is committed so it can never drift.

### Validation

- Rebuilt scenarios: normal = 8/8 BENIGN, portscan = 8/8 KNOWN_ATTACK,
  dos_or_ddos = 8/8 KNOWN_ATTACK, unknown = 4/4 UNKNOWN_SUSPICIOUS
  (expected, by design).
- Live uvicorn gate: normal replay 0 suspicious / 0 incidents.

### Regression Test

`backend/tests/e2e_replay_phase3.py` asserts normal replay creates no
incidents; scenario fixtures themselves are committed/versioned.

## BUG-009 — Cytoscape graph never initialised when the flow list started empty

Status: FIXED
Detected: 2026-08-10 (live-browser UI E2E)
Phase: 3
Severity: MEDIUM

### Symptoms

The Communication Graph box rendered as blank (no canvas) on first load and
after the initial empty state, even after traffic had been replayed and
`graphData` was populated.

### Expected Behaviour

Cytoscape initialises once (container exists at mount) and re-lays-out on data
changes; the graph paints nodes/edges whenever flows exist.

### Actual Behaviour

`document.querySelectorAll('canvas')` returned 0 (checked via headless CDP)
on a populated monitor. In `CommGraph.tsx` the mount-only effect
(`useEffect(..., [])`) ran while the empty-state placeholder `<div>` was
rendered — the ref container `<div>` did not exist yet, so
`containerRef.current` was null and the effect returned early. Dependencies
being `[]`, it never ran again, `cyRef.current` stayed null, and the
data-update effect bailed too.

### Reproduction

Open the Security Monitor with zero replayed flows, then start a replay; the
graph section stays blank. Verified with headless Edge via CDP
(`hasCanvases=0`).

### Relevant Files

`frontend/src/components/CommGraph.tsx`.

### Root Cause

Conditional rendering swapped the placeholder (no ref) and container (ref)
between renders, so the mount-time ref was `null` on the empty state; the
mount effect was a no-op and never retried.

### Fix

Always render the Cytoscape container div; overlay an absolutely-positioned
empty-state message instead of switching the subtree. The always-mounted ref
guarantees the mount-only effect always sees a real container.

### Validation

- `npm run build` PASS.
- Headless Edge CDP E2E re-run PASS: `canvases=3` on a populated monitor,
  zero console errors, node/edge selection still wired.

### Regression Test

Manual (UI): the CommGraph container is mounted even with zero flows, and a
live replay produces canvases. Documented in PHASE_3.md / HANDOFF.

### Notes

This class of bug (mount-only effect + conditionally-rendered ref target) is
why the Phase-3 UI gate is now validated through a real browser, not just the
frontend build.

---

## BUG-010 — Replay ran the full Phase-2 pipeline twice per suspicious flow

Status: FIXED
Detected: 2026-08-10 (Phase-3.5 hardening audit)
Phase: 3
Severity: MEDIUM (runtime duplication; output correct)

### Symptoms

`ReplayService._predict_one` scored every non-BENIGN flow with TWO full
`Phase2Predictor.predict` calls: the first with `with_shap=False`, then a
second with `with_shap=True` that re-ran the whole supervised + IsolationForest
+ hybrid + risk stack purely to obtain the SHAP block. Attack flows cost ~2x
the compute of a single pipeline pass.

### Expected Behaviour

Run the supervised/anomaly/hybrid/risk pipeline exactly once per flow and
attach SHAP to suspicious flows without re-running the pipeline.

### Actual Behaviour

Two pipeline executions per suspicious flow. `RecorderPredictor` in
`test_replay.py` recorded 24 `predict` calls for 12 suspicious flows.

### Reproduction

Inspect `backend/app/services/replay.py::_predict_one` (pre-fix): two
`predict` calls, one per SHAP mode.

### Relevant Files

`backend/app/services/replay.py`, `backend/app/services/predictor.py`,
`ml/hybrid/shap_explainer.py`.

### Root Cause

`predict(with_shap=True)` lumps SHAP into the full pipeline; the caller had no
way to ask for SHAP alone, so the second pass recomputed everything.

### Fix

Add `Phase2Predictor.explain(features)`: validates + builds the canonical
feature row, then runs ONLY the SHAP block — producing exactly the same
output as the `with_shap=True` path of `predict` (same top-5 native
TreeSHAP explain). `_predict_one` now scores once and calls `explain()` for
suspicious flows.

### Validation

- `ml/tests/test_predictor.py::test_explain_matches_predict_shap`:
  `explain(features)` SHAP block === `predict(features, with_shap=True)` SHAP block.
- Full suite `python -m pytest ml/tests backend/tests -q` -> 91 passed.
- Live uvicorn E2E gate PASS — SHAP still persisted on suspicious evidence.

### Regression Test

`test_explain_matches_predict_shap`; `test_replay_truth_label_never_enters_inference`
updated to the single-pass contract (12 `predict` + 12 `explain`; canonical
feature keys only).

### Notes

The truth-isolation invariant (BUG-005 / DEC-010) is unchanged: inference
inputs remain exactly the canonical 77 features; `explain` is not a model
input path.

---

## BUG-011 — Monitor live feed + incidents mixed evidence across sequential replays

Status: FIXED
Detected: 2026-08-10 (Phase-3.5 hardening audit, sequential-replay evidence)
Phase: 3
Severity: HIGH (Monitor showed stale evidence as current after a second replay)

### Symptoms

Running two replays sequentially on one server (PortScan -> COMPLETED ->
Normal -> COMPLETED) left the Security Monitor presenting stale evidence as
current: `GET /api/replay/flows` still returned the 8 PortScan rows below the
8 Normal rows, and `GET /api/incidents` still listed the PortScan incident even
though the current run had produced none. Evidence pre-fix:
`ml/evaluation/results/phase35_evidence_before.json` -> VERDICT=MIXED.

### Expected Behaviour

The Monitor's live traffic table, graph, timeline and incident side panel must
show ONLY the current replay run's evidence; the Incidents page retains full
history.

### Actual Behaviour

Both queries filtered only `source_config LIKE 'replay:%'` (flows) or returned
all rows (incidents), with no replay-run scoping.

### Reproduction

`ml/evaluation/phase35_evidence_before.py` — sequential portscan -> normal on
one uvicorn (temp DB). VERDICT=MIXED: 16 feed rows (8 normal + 8 portscan) and
a stale portscan incident present after the normal run.

### Relevant Files

`backend/app/api/{replay,incidents}.py`, `backend/app/services/replay.py`,
`backend/app/db/{models,database}.py`,
`frontend/src/pages/SecurityMonitor.tsx`, `frontend/src/api/{client,types}.ts`.

### Root Cause

Persisted `Prediction`/`Incident` rows carried no replay-run identity, so the
feed/incidents queries could not isolate the current run.

### Fix

Run-scoping (DEC-015): `ReplayService` generates a `run_id` (uuid hex) at each
`start()` and persists it on every `Prediction` and `Incident` row it writes
(additive columns + additive migration in `_migrate_schema`).
`GET /api/replay/flows?run_id=` and `GET /api/incidents?run_id=` filter by run;
the Security Monitor passes the current `status.run_id`; the Incidents page
omits the filter (full history). Incident aggregation remains per-run (fresh
grouper per `_run`).

### Validation

- `ml/evaluation/phase35_evidence_after.py` -> VERDICT=ISOLATED: normal run feed
  = only Normal rows; normal-run incidents = 0; portscan run still 1 incident;
  unscoped list intact (history preserved).
- Live uvicorn E2E gate now asserts sequential-run isolation.
- Real-browser (headless Edge CDP) sequential replay E2E PASS: the table
  repaints to Normal-only rows, Incidents hub shows 0, zero console errors.

### Regression Test

`backend/tests/test_replay_api.py::test_run_scoped_flows_and_incidents_isolate_sequential_runs`
plus the sequential-isolation block in `backend/tests/e2e_replay_phase3.py`.

### Notes

Run-scoping is evidence-VIEW scoping only; persisted incidents remain
historical evidence. The Incidents page intentionally queries unscoped so the
audit trail is never hidden by the current run.

---

## BUG-012 — Restart after STOPPED raced the still-draining worker thread

Status: FIXED
Detected: 2026-08-10 (full-suite load; Phase-3.5 closure)
Phase: 3
Severity: MEDIUM (timing-dependent counter/evidence corruption on stop->start)

### Symptoms

Under load, `test_restart_after_stopped` intermittently failed with
`processed == 41` for a 40-flow scenario: restarting on the same service right
after `stop()` let the OLD worker thread keep running into the NEW run.

### Expected Behaviour

A `start()` after `STOPPED`/`COMPLETED` must begin a clean, isolated run with
its own counters, grouper and DB session — the previous worker thread must be
fully gone.

### Actual Behaviour

`stop()` sets the STATE synchronously, but the worker thread can still be
mid-`predict`/`persist` for a beat. If `start()` ran in that window it spawned
a SECOND thread; the stale thread then re-checked state (now RUNNING for the
new run), continued looping, and raced the fresh thread on the same
`self._processed`/grouper/DB — e.g. one extra processed flow, or worse,
interleaved evidence under the new `run_id`.

### Reproduction

`test_replay.py::test_restart_waits_for_stale_worker_before_resetting` —
a blocking `predict` pins the worker mid-flow; `stop()` then an immediate
`start()`. With the join removed (pre-fix) the run diverges
(VERDICT=RACE-REPRODUCED).

### Relevant Files

`backend/app/services/replay.py` (`start`), `backend/tests/test_replay.py`.

### Root Cause

`start()` reset counters and spawned a new thread without ensuring the prior
worker thread had exited; the thread-lifetime guard existed for the STATE only,
not the THREAD.

### Fix

`start()` now joins any still-alive previous worker thread (outside the
`_lock`, since the worker needs the lock to exit) before resetting counters and
spawning the new one. A concurrent-start guard re-checks the state after the
join so a racing caller gets a 409.

### Validation

- New regression test passes (module `test_replay.py` 17 passed).
- Full suite `python -m pytest ml/tests backend/tests -q` -> 92 passed, twice
  (stable under full load; previously flaky).
- Live uvicorn E2E gate PASS after the change (restart path unchanged in
  behaviour for completed runs).

### Regression Test

`test_restart_waits_for_stale_worker_before_resetting`; existing
`test_restart_after_stopped` / `test_restart_after_completed_and_no_inactive_residue`
still pass.

### Notes

Pre-existing engine race (since DEC-013 replay engine), surfaced during the
Phase-3.5 full-suite closure. Unrelated to the run-scoping change (BUG-011).


---

## BUG-013 — Communication Map painted blank on page load with a restored completed run

### Status

FIXED (2026-08-13)

### Symptom

Hard-reloading the Security Monitor while the backend held a COMPLETED replay
run showed the Communication Map panel as an empty dark canvas even though
flows were fetched and the graph data model was populated. The graph only
painted after starting a fresh replay.

### Root Cause

`CommGraph` re-ran its Cytoscape layout on data updates without re-reading
the container size. When the data arrived right after first mount, the layout
could be computed against stale/zero container dimensions captured at
initialisation, leaving all nodes off the visible canvas.

### Fix

`frontend/src/components/CommGraph.tsx` calls `cy.resize()` in the data-update
effect before removing/re-adding elements and running the layout, so layout
always uses the real container dimensions.

### Validation

Hard reload with a COMPLETED run: graph renders host + service nodes with
readable IP/port labels (browser re-check 2026-08-13). Full four-scenario browser
pass with zero console errors.

### Notes

Frontend-only presentation defect found during the Phase-3 UX pass browser
validation. No backend/ML impact. Related lineage: BUG-009 (Cytoscape init
lifetime).


## BUG-014 - Replay errors retried forever; transactions and timed joins were unsafe

Status: FIXED (targeted regressions and real replay gate passed)
Detected: repository audit; implemented 2026-10-31
Phase: approved reliability prerequisite
Severity: HIGH

Persistent prediction/SHAP/persistence failures retried the same sequence;
session creation/final commit exceptions escaped the worker; a timed join could
reset counters before the previous worker exited. Incident count also advanced
before commit. The worker now reports FAILED, rolls back, closes, counts only
committed evidence, and rejects restart while a prior worker is alive. Application
shutdown wakes/drains paused workers. Unexpected API errors no longer become 409.

Validation: 14 targeted failure/API/lifespan cases; 62 related backend tests
passed; real Uvicorn gate over original four fixtures passed. Full dataset-backed
suite initially blocked by sandbox sockets (WinError 10013); network-enabled full suite passed: 106 tests in 250.99s.
Regression file: backend/tests/test_replay_failures.py.
Limitation: failed runs retain already committed incidents; final end markers
may remain unset when the finalization transaction fails. No history is deleted.

## BUG-015 - False readiness and stale Monitor evidence

Status: FIXED (2026-10-31)
Severity: HIGH for misleading readiness; MEDIUM for stale evidence.
Header ignored model_loaded; no-run queries returned history; empty flow lists
retained old graph; late requests could restore a prior run. Health/UI now check
inference readiness and invalidate/clear run-scoped snapshots. See Batch 2 sprint
entry for missing-model, delayed-response, restart/history and recovery evidence.

## BUG-016 - Graph risk selectors and evidence display semantics

Status: FIXED (2026-10-31)
Severity: MEDIUM
String true selectors never matched boolean edge fields; service/edge selection
looked up wrong relations; UNKNOWN text always assumed BENIGN; UI guessed anomaly
thresholds and showed benign risk zero. Corrected with boolean selectors, tested
flow selection, actual label wording, persisted thresholds and recorded risk.
Validation: 69 Python checks, 4 frontend tests, build/TS, real replay gate and
browser risk-color/detail checks passed. Legacy threshold remains unavailable.

## BUG-017 - Legacy demo vectors overlap deployed training features

Status: WONTFIX (preserve approved demo behavior; disclose limitation)
Detected: 2026-10-31 provenance check
Legacy PortScan 5/8 and DoS/DDoS 1/8 vectors match deployed training features.
Published split membership does not establish feature independence or original
row identity. New fixtures exclude matches; originals remain demo evidence, never
an unbiased estimate. See data/processed/scenario_provenance.json.
