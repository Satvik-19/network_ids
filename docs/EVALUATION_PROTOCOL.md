# Evaluation interpretation and approved comparison protocol

## Historical evidence (retained)

Supervised candidates: 300k class-aware random/train subset, seed 42; six variants
compared on random/test (565,576), then chosen model reported on the same test.
This is reused development evidence, not an untouched post-selection estimate.
Final multiclass confusion matrix: 539 false positives / 454,265 benign records
= 0.0011865321. Separate xgb_200 binary model: 651 / 454,265 = 0.0014330842.
Neither figure includes the runtime confidence gate plus anomaly rescue.

Random IF report: random_3way/test (282,788), calibrated on its validation split;
reported threshold -0.092803 differs slightly from rounded runtime -0.0928.
Temporal experiment: separate models fit Mon–Thu, calibrated on labeled Friday
validation, assessed on Friday test. Novel classes are absent from supervised
fitting but present in anomaly-threshold calibration. No timestamps establish
ordering within Friday halves. All-15-class macro F1 includes zero-support classes.
Sensitivity aggregate recall 0.074955–0.076569; DDoS recall 0.1685–0.1716.
Native SHAP explains supervised class contributions, never IF or attack causation.
Rare-class metrics must include support (e.g. SQL Injection n=3, Heartbleed n=2).

## Locked-artifact comparison (Milestone 2)

Use the complete pinned random_3way/test partition for every method, canonical
77-feature preprocessing, current artifact bytes, confidence 0.75 and anomaly
threshold -0.0928 from config. Do not fit, select, calibrate, or overwrite models.
Report raw XGBoost derived binary detection, confidence-gated supervised alerts,
standalone IF flags, and combined hybrid on identical rows. Distinguish alerting
from correct class naming. Record TP/FP/TN/FN, FPR, precision/recall/F1, supports,
per-class detection, incremental malicious rescues and added benign false alerts.
ROC-AUC belongs only to a defined continuous score; no invented hybrid probability.

Record dataset revision, split, row count, ordered cohort hash, config/model
hashes, effective thresholds and dependency versions. Batch outputs must match
single-flow predictor decisions on committed fixtures. Avoid full-cohort SHAP.
This cohort overlaps historical evaluation/calibration history; the new comparison
measures locked-system behavior, not a newly untouched final benchmark.

## Scenario interpretation

Prepared fixtures demonstrate integration, not representative detection rates.
Current normal fixtures were selected to produce benign verdicts; unknown contains
benign anomaly false alerts. Neither is an unbiased performance cohort. Synthetic
addresses/display ports/times are presentation metadata. Unknown fixture must not
receive unknown-attack detection credit. Playground scores describe only its tiny
selected scenario suite; coverage and false alerts remain visible.

## Retained limitations

Weak unseen recall, tiny minority support, prior test reuse, derivative provenance
and benchmark-era limitations remain. New datasets, retraining, threshold search,
stronger unknown-attack research and full Model Lab are outside this batch.

## Locked-artifact comparison executed - 2026-10-31

Entire random_3way/test, n=282788. No fit/tuning. Report:
ml/evaluation/results/locked_hybrid_random.json (hashes, params, seed, versions).

| Method | Precision | Recall | F1 | Benign FPR |
|---|---:|---:|---:|---:|
| XGBoost raw multiclass -> binary | .995172 | .999874 | .997517 | .001189 |
| Confidence-gated supervised | .995624 | .997520 | .996571 | .001074 |
| Standalone IF | .766202 | .295063 | .426053 | .022062 |
| Hybrid | .913534 | .997556 | .953698 | .023136 |

IF rescue adds 2 malicious detections among 138 missed by the confidence gate,
and 5011 benign false alerts. Relative to raw XGBoost, hybrid also loses recall
through confidence gating. This is a measured limitation, not justification to
silently change the approved thresholds or models. These figures describe one
reused random cohort, not temporal novelty or live-network performance.
