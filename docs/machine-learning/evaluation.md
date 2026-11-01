# Evaluation methodology, results and limitations

## Evidence register and separation

Saved result JSON under `ml/evaluation/results/` is the metric source. Scripts in `ml/evaluation/` and `ml/training/` define the experiment protocols. Four result types must remain separate:

1. **Supervised binary and multiclass benchmarks:** standalone candidate/model metrics on the dataset's split.
2. **Isolation Forest evaluation:** anomaly flags at a calibrated threshold, independent of supervised classification.
3. **Locked runtime comparison:** raw supervised, confidence-gated supervised, IF and hybrid outputs on one identical random 3-way test cohort using frozen model bytes and runtime thresholds.
4. **Playground/replay fixtures:** tiny integration scenarios with provenance and deliberately visible support; not population performance estimates.

No accuracy or F1 from one type should be presented as another type's result.

## Dataset experiments

The pinned derivative is `lacg030175/CICIDS2017`, revision `d071fd53782d9ca7cdc15173b8ceb858fea04628`. The class-aware development subset has 300,000 rows and seed 42. Canonical preprocessing yields 77 features and 15 labels. The random and temporal configurations are distinct:

| Experiment | Train/evaluation definition | Evaluation support |
|---|---|---:|
| Random | Stratified random split; candidate result uses `random/test` | 565,576 |
| Temporal | Monday–Thursday training, Friday test | 702,718 |
| IF random 3-way | benign development rows fit; threshold from `random_3way/validation`; report `random_3way/test` | 282,788 |
| Shared locked random 3-way | Frozen artifacts and thresholds; same `random_3way/test` rows for every detection rule | 282,788 |

The supervised selection used six variants on the random test partition and final artifact results are reported on that same partition. This is test-set reuse. Temporal evaluation also has a limitation: the unseen classes are absent from supervised training but present in labeled Friday threshold calibration; within-Friday chronological ordering is not established. All-class macro metrics include classes with zero support in the temporal set.

## Supervised results

From `baseline_metrics_random.json` and `final_supervised_random.json`:

| Model and task | Accuracy | Precision | Recall | F1 | ROC-AUC | Support |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression, binary | 0.867286 | 0.597882 | 0.994637 | 0.746836 | 0.975901 | 565,576 |
| Random Forest, binary | 0.998548 | 0.993268 | 0.999398 | 0.996323 | 0.999716 | 565,576 |
| XGBoost baseline, binary | 0.997889 | 0.989666 | 0.999713 | 0.994664 | 0.999891 | 565,576 |
| Logistic Regression, multiclass | 0.946981 | — | — | macro 0.534399 / weighted 0.951378 | — | 565,576 |
| Random Forest, multiclass | 0.998281 | — | — | macro 0.815597 / weighted 0.998316 | — | 565,576 |
| XGBoost baseline, multiclass | 0.998665 | — | — | macro 0.887701 / weighted 0.998681 | — | 565,576 |
| Final XGBoost `xgb_200`, multiclass | 0.998725 | macro 0.897322 | macro 0.894492 | macro 0.889830 / weighted 0.998757 | — | 565,576 |

The binary candidate rows are separately trained binary classifiers. They are not the deployed three-class hybrid. Final multiclass accuracy is high in a benign-dominated cohort; macro-F1 gives rare classes more influence and is notably lower. Final random supports include Heartbleed 2, Infiltration 5, SQL Injection 3, XSS 126, Web Attack Brute Force 290, Bot 376, SSH-Patator 1,211, and FTP-Patator 1,595. Apparent near-perfect scores at support 2 or 5 are unstable estimates, not proof of broad generalization. The saved `final_supervised_random.json` contains all per-class precision/recall/F1/support and the confusion matrix.

Temporal XGBoost baseline result from `baseline_metrics_temporal.json` (100 trees). This is the temporal baseline experiment, not the deployed `xgb_200` artifact; the deployed final model was trained on the random subset and has no matching final-model temporal evaluation artifact:

| Metric | Value |
|---|---:|
| Accuracy | 0.588909 |
| Macro-F1 (all 15 labels, including zero-support labels) | 0.053316 |
| Weighted-F1 | 0.471086 |
| Friday support: BENIGN / Bot / DDoS / PortScan | 413,933 / 1,956 / 128,025 / 158,804 |

In this temporal split, most classes in the fixed 15-label output have zero support because they are absent from Friday. The scores show weak time-shift generalization in this experiment. They do not show performance on arbitrary future traffic.

## Isolation Forest results

The runtime IF was fit on 88,314 benign development-training rows. Its random threshold is calibrated on `random_3way/validation` to maximize F1 under FPR ≤ 5%. The reported `random_3way/test` metrics at -0.092803 (config rounds to -0.0928) are:

| TP | FP | FN | TN | Precision | Recall | F1 | FPR |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 16,422 | 5,011 | 39,234 | 222,121 | 0.766202 | 0.295063 | 0.426053 | 0.022062 |

The score is the IF raw `decision_function`, not a probability. Temporal unseen experiment `unknown_experiment_temporal.json` uses a separate threshold of -0.115716 calibrated using Friday validation, so its metrics are a separate protocol and not the runtime -0.0928 threshold result.

## Locked shared-cohort comparison

`locked_hybrid_random.json` compares frozen artifacts at confidence threshold 0.75 and anomaly threshold -0.0928, on the same 282,788-row `random_3way/test` cohort. No fitting or threshold tuning is performed in this comparison.

| Rule | Precision | Recall | F1 | Benign FPR | TP / FP / FN / TN |
|---|---:|---:|---:|---:|---|
| Raw XGBoost multiclass output mapped to malicious/benign | 0.995172 | 0.999874 | 0.997517 | 0.001189 | 55,649 / 270 / 7 / 226,862 |
| Confidence-gated supervised | 0.995624 | 0.997520 | 0.996571 | 0.001074 | 55,518 / 244 / 138 / 226,888 |
| Isolation Forest alone | 0.766202 | 0.295063 | 0.426053 | 0.022062 | 16,422 / 5,011 / 39,234 / 222,121 |
| Combined hybrid | 0.913534 | 0.997556 | 0.953698 | 0.023136 | 55,520 / 5,255 / 136 / 221,877 |

Relative to the confidence-gated rule, the hybrid rescues 2 of 138 missed malicious rows and adds 5,011 benign alerts. These results are for that reused random cohort only. This is a measured trade-off, not evidence that the hybrid improves all metrics or detects unknown attacks reliably.

## Unseen-class experiment

The recorded experiment holds Bot, DDoS and PortScan out of supervised training, but uses labeled Friday validation for anomaly calibration, then evaluates on Friday test. Isolation Forest flags 10,832 of 144,393 unseen malicious flows (recall 0.075017, FPR 0.035363, precision 0.596772, F1 0.133281). Hybrid incremental rescue uses a different denominator: only the 103,601 unseen malicious flows not already classified as a known attack; 24 were escalated to `UNKNOWN_SUSPICIOUS` (0.000232). These distinct rates must not be conflated. Per-class flag rates are rounded in the result file; aggregate true-positive count is the exact source.

This is an unseen/unknown anomaly simulation, **not zero-day detection**. The anomaly detector misses most unseen rows, particularly PortScan in the recorded temporal experiment.

## Replay and Playground evidence

Seven fixtures contain 52 feature records total: 8 each for normal, PortScan, DoS/DDoS, FTP, SSH and web, plus 4 benign anomaly-challenge records. New SSH/FTP/web fixtures have no exact feature matches to deployed-training records. Five of eight PortScan and one of eight DoS/DDoS vectors have exact feature matches against deployed training. For legacy vectors, provenance identifies equivalent feature rows, not original row identities or proof those rows crossed a split. Synthetic address/port/time metadata is not recovered capture metadata.

The unknown fixture is **benign**. It is used to expose anomaly-related false alerts, never to award unknown attack detections. Example public-web profile evaluates 4 scenarios (28 flows): 12 malicious detections, 4 misses and 4 benign false alerts; score 70.83 under current formula. The 7-scenario lab example covers 52 rows and produced 36 detections, 4 misses, 4 false alerts, score 78.33. Home/internal with only benign controls has no readiness score because there is no malicious support. See [Playground rules and profile suite](../frontend-and-playground.md).

The score is `100 * (detection_weight * mean attack-scenario recall + false_alert_weight * pooled benign specificity)`, using configured weights 0.5 and 0.5. Coverage counts selected/executed prepared scenarios; it does not measure real network completeness. Database and file-sharing service selections have no prepared scenario coverage.

## Limitations and valid conclusions

- CICIDS2017 and its cleaned derivative have benchmark-specific distributions and known dataset limitations.
- Published analysis has identified CICIDS2017 flow construction, extraction and labeling concerns and describes a corrected/reprocessed version. This project uses the separately pinned `lacg030175/CICIDS2017` derivative; equivalence to the corrected data is not established here. See the [publisher's dataset page](https://www.unb.ca/cic/datasets/ids-2017.html) and Engelen et al., [DOI 10.1109/SPW53761.2021.00009](https://doi.org/10.1109/SPW53761.2021.00009).
- Random-split metrics are optimistic development evidence because of candidate selection/test reuse.
- Temporal scores are poor; the split has no within-Friday chronological guarantee and calibration includes the held-out class families in Friday validation.
- Severe class imbalance makes aggregate accuracy misleading. Rare class support must accompany per-class metrics.
- IF false positives and low recall remain meaningful operational limitations. `UNKNOWN_SUSPICIOUS` does not establish novel-attack identification.
- Playground/replay fixture scores are tiny, selected examples with some known feature overlap; they are integration demonstrations, not general performance estimates.
- The app consumes feature rows; it has no packet capture or real-time network interface.
- Native SHAP is a model attribution, not causality or hybrid-rule explanation.
- A communication graph is an endpoint relationship view, not reconstructed physical topology.

Reproducible scripts and evidence are indexed in [ML pipeline](../ml-pipeline.md), [evaluation protocol](../EVALUATION_PROTOCOL.md), and [the result directory](../../ml/evaluation/results/).
