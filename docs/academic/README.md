# Academic submission and demonstration guide

This guide is a fact-based preparation aid. It is not a completed college report and does not supply an invented literature review. The references below were verified against the dataset publisher and publication metadata; add other sources only after reading and verifying them.

## Synopsis material

### Title

**AI-Powered Network Intrusion Detection and Security Evaluation System**

### Problem statement

Network flow records are numerous and their feature values are difficult to interpret manually. A useful academic prototype should identify known attack patterns, surface some unusual flow behavior, preserve evidence for review and explain what the supervised model used. Evaluation also needs to expose weaknesses under rare-class imbalance and time-shifted traffic instead of relying on one aggregate accuracy score.

### Motivation

This project studies whether a compact, CPU-friendly supervised classifier and benign-trained anomaly detector can be combined with transparent decision rules and an interface that helps a reviewer inspect records and limitations. It is a controlled flow-record experiment using CICIDS2017, not a live network protection service.

### Objectives

1. Build deterministic preprocessing for a pinned CICIDS2017 derivative and canonical feature schema.
2. Compare Logistic Regression, Random Forest and XGBoost baselines, preserving binary/multiclass and random/temporal distinctions.
3. Implement XGBoost known-class prediction with an Isolation Forest anomaly signal and a deterministic hybrid output.
4. Provide local supervised-model feature contributions, benign feature baselines and transparent risk scoring.
5. Replay prepared flow scenarios, group suspicious flows into persisted incidents and display evidence in a web interface.
6. Provide a deterministic profile-based Playground using prepared scenarios and report coverage, misses and false alerts with explicit simulation limits.

### Scope and methodology

The training/evaluation source is `lacg030175/CICIDS2017`, pinned to revision `d071fd53782d9ca7cdc15173b8ceb858fea04628`. Preprocessing drops a duplicated feature, normalizes labels, handles non-finite values and fixes 77-feature order. A seed-42 300,000-row class-aware development subset supports model training. The supervised runtime model is XGBoost multiclass. Isolation Forest is fitted on 88,314 benign development records; its runtime threshold comes from validation under an FPR constraint. Prediction follows a confidence-first known-attack rule, then anomaly threshold, then benign. Local XGBoost native TreeSHAP is shown for suspicious model predictions. Prepared records enter the existing predictor through replay or Playground; SQLite stores predictions/incidents or separate Playground snapshots.

See [ML pipeline](../ml-pipeline.md), [architecture](../architecture.md), [evaluation](../machine-learning/evaluation.md), and [database/API](../backend-reference.md) for exact implementation detail.

### Implemented outcomes and limitations

Implemented outcomes include a local monitor, deterministic replay, persisted incident evidence, a three-view navigation experience, local model explanations, and a bounded scenario-based Playground. The project does not implement live packet capture, active scanning, mitigation, real-network certification or reliable zero-day identification. Random results reuse test data during selection; temporal generalization is poor; rare class support is small; Playground fixtures are not representative performance samples. Report those constraints alongside results.

### Future scope

Potential future research may study stronger independent scenario provenance, broader temporal protocols, more representative data or live feature extraction after schema compatibility work. Live packet capture, automated mitigation, external integrations, drift monitoring and the full Model Evaluation Lab remain deferred; none is necessary to describe the current implementation.

## Final report chapter outline

| Chapter | Suggested content and evidence |
|---|---|
| 1. Introduction | IDS context, problem, motivation, objectives and explicit scope. Use [overview](../project-overview.md). |
| 2. Literature review | Discuss research on flow-based intrusion detection, CICIDS2017 provenance/critique, supervised tree models, anomaly detection, imbalance/temporal evaluation and explainability. Use the verified starting references below and cite only papers the team has read. |
| 3. Problem formulation and requirements | Flow-level inputs/outputs, three verdict semantics, functional requirements, ethical boundaries and non-goals. See [overview](../project-overview.md) and the [PRD](../../Network_IDS_Security_Evaluation_PRD.md). |
| 4. System design | Component architecture, REST boundaries, process model, persistence relationships and UI workflows. Use [architecture](../architecture.md), [backend reference](../backend-reference.md) and [diagrams](../diagrams.md). |
| 5. Dataset and preprocessing | Source/revision, provenance, splits, class support, 77 features, duplicate removal, normalization, non-finite policy and subset seed. See [ML pipeline](../ml-pipeline.md) and `docs/DATA_ML_CONTRACT.md`. |
| 6. Machine-learning methodology | Candidate models, selected XGBoost params, benign-only Isolation Forest, calibration, hybrid thresholds, risk and SHAP semantics. See [ML pipeline](../ml-pipeline.md). |
| 7. Implementation | FastAPI services, SQLite persistence, replay/incident lifecycle, React screens, graph semantics and Playground scenario selector. See [backend](../backend-reference.md) and [frontend](../frontend-and-playground.md). |
| 8. Testing | Unit/API/integration/frontend test layers and exact commands/results. Distinguish historical validation from reruns for submission. See [testing guide](../testing.md). |
| 9. Results and discussion | Separate supervised, anomaly, hybrid, temporal and fixture results; include supports and confusion matrix/rare classes; discuss test reuse, false alerts and temporal weakness. See [evaluation](../machine-learning/evaluation.md). |
| 10. Limitations and threats to validity | Dataset/derivative limits, leakage/test reuse risk, minority support, calibration, fixture overlap, no live capture, no zero-day claim and SHAP non-causality. |
| 11. Conclusion and future work | Summarize implemented scope; future work should be framed as planned research, not shipped functionality. |
| References | Cite original CICIDS2017 dataset/paper and verified primary sources for methods/software. Keep exact revision/access date and institution citation style. |

## Recommended PPT sequence

| Slide | Message and content | Suggested visual / source |
|---|---|---|
| 1. Title | Project, team, department and institution template. | No unsupported performance badge. |
| 2. Problem | Why flow inspection is difficult; define the academic problem. | One simple many-records-to-review flow. [Overview](../project-overview.md) |
| 3. Objectives and scope | What the prototype attempts and excludes. | Scope list: prepared flow records; no live capture or mitigation. |
| 4. Existing approaches and motivation | Literature-backed supervised/anomaly/explainability patterns. | Add citations researched by team; do not use uncited generic claims. |
| 5. Proposed system | Show user-visible monitor, incident investigation and Playground. | Actual application screenshots, clearly identified as screenshots. |
| 6. Architecture | Offline ML and local app relationship. | [System diagram](../architecture.md). |
| 7. Dataset and preprocessing | Dataset revision, split definitions, feature count, labels/support. | A compact provenance/split table. [Evaluation](../machine-learning/evaluation.md). |
| 8. ML methodology | XGBoost, benign-only IF and model output types. | [Training diagram](../diagrams.md#training-and-evaluation). |
| 9. Hybrid decision logic | Exact confidence-first/anomaly-second decision. | [Flow diagram](../diagrams.md#flow-scoring-and-hybrid-decision). |
| 10. Explainability | What the signed SHAP contribution represents and does not. | Actual incident explanation screenshot; note predicted XGBoost class only. |
| 11. Application demonstration | Run one prepared replay, select incident, inspect connection and feature evidence. | Use [demo guide](../demo-guide.md). |
| 12. Results | Separate supervised random, temporal, IF and locked hybrid tables. Include supports. | [Evaluation tables](../machine-learning/evaluation.md). |
| 13. Playground | Profile selection, selected scenarios, coverage, false alerts, score qualification. | Actual saved run screenshot; label scenario simulation. |
| 14. Limitations | Temporal degradation, tiny rare support, false alerts, fixture overlap, no live traffic. | Include figures rather than hiding caveats. |
| 15. Conclusion and future scope | What was implemented; what remains deferred/research. | Distinguish Phase 5 ideas from present system. |

## Viva question bank

### Networking and IDS

**Q: What does one input record represent?**

A: A flow-level feature record, not a packet stream. The runtime consumes 77 numeric CICIDS2017 features. Replay fixtures also include source/destination and service port metadata for display and incident grouping.

**Q: Does the graph show the physical network?**

A: No. It shows directed source-to-destination endpoints that occur in the fixture rows. Fixture addresses are synthetic metadata; ports are connection details, not host nodes.

**Q: Is this a live IDS?**

A: No. It scores prepared flow records through replay or the bounded Playground workflow. It does not capture packets, inspect a live interface or block traffic.

### Dataset and preprocessing

**Q: Why CICIDS2017?**

A: It is the project's selected benchmark source with labeled flow features. The implementation uses a pinned cleaned derivative for convenient Parquet splits and records its revision; claims must be limited to this source and its split conditions.

**Q: Why 77 features?**

A: The source feature columns include a duplicate `Fwd Header Length.1`, verified bit-for-bit against `Fwd Header Length`; preprocessing removes the duplicate and uses a canonical 77-feature order.

**Q: What happens to NaN/inf?**

A: Preprocessing replaces infinities with NaN and fills non-finite values with zero. Labels are normalized to the observed 15 canonical classes. Model input names are validated and reordered canonically.

**Q: How do you prevent data leakage?**

A: The supervised model uses a class-aware training subset; the LR scaler is fitted on train only; IF threshold calibration uses a validation split separate from its reported test split. However, supervised candidate selection and final reporting reused random/test, which is explicitly a limitation. The temporal protocol also calibrates on Friday validation, so it is not a strict real-time chronology experiment.

### Models and hybrid logic

**Q: Why XGBoost?**

A: It is the selected CPU-capable tree classifier for tabular flow features. Selection considered macro/weighted F1, class recall, false positives, temporal performance and cost; it was not selected solely by accuracy. The runtime model is multiclass `xgb_200`.

**Q: Why Isolation Forest?**

A: It provides a lightweight anomaly score fitted on benign training flows. It flags deviations but cannot name a novel attack. In the recorded temporal unseen experiment, recall was only 7.5% at 3.5% FPR.

**Q: How does the hybrid decision work?**

A: First, a non-benign XGBoost label with confidence at least 0.75 becomes `KNOWN_ATTACK`. Otherwise, an Isolation Forest score below -0.0928 becomes `UNKNOWN_SUSPICIOUS`. All other flows become `BENIGN`. The score is raw `decision_function`; smaller means more anomalous and it is not a probability.

**Q: Does unknown suspicious mean zero-day?**

A: No. It is a thresholded anomaly alert when the known-attack rule did not apply. It can be benign and the prepared unknown fixture is explicitly benign. The experiment does not establish real zero-day detection.

**Q: What is risk score?**

A: A deterministic, configured 0–100 project prioritization measure based on family severity, supervised confidence and anomaly contribution. Its levels are presentation categories, not an industry standard.

### Explainability and metrics

**Q: What does SHAP explain?**

A: XGBoost native TreeSHAP contributions for the supervised predicted class's raw margin. Contributions are signed and sum with the bias to that margin. They do not explain Isolation Forest, the hybrid rules, causal attack mechanisms, or a probability change.

**Q: Why report macro-F1?**

A: Weighted/accuracy metrics are dominated by frequent classes. Macro-F1 gives classes equal weight, but needs support alongside it; for example SQL Injection support is 3 and Heartbleed support 2 in the saved random test.

**Q: Why are random results so much better than temporal results?**

A: The temporal split evaluates Friday traffic after Monday–Thursday training and has classes absent from training. The saved XGBoost temporal accuracy is about 0.589 and 15-class macro-F1 about 0.053. This is evidence of weak generalization for this experiment, not universal future performance.

**Q: Does hybrid improve the standalone model?**

A: Not generally. On the locked shared random cohort, the hybrid recovers only 2 of 138 supervised-gate misses while adding 5,011 benign alerts. Its FPR is 0.023136. This trade-off is a limitation, not a blanket improvement claim.

### Software architecture and Playground

**Q: Why FastAPI and SQLite?**

A: They provide a small local REST API and file-based persistence for a student-scale prototype. SQLite stores prediction evidence, grouped incidents and Playground snapshots; the training dataset stays in Parquet.

**Q: How are incidents grouped?**

A: Only suspicious replay outcomes enter groups. Key includes classification, family, source and destination; service port is excluded for Reconnaissance so a multi-port scan is not split. Same key joins within the configured interval from group start. Aggregated evidence and links to prediction rows are persisted.

**Q: How does Playground personalization work?**

A: A validated profile applies deterministic rules to choose available prepared scenario JSON files. Those rows pass through the same predictor, then ground truth is compared after inference. Results show counts, coverage, false alerts/misses and a configured score when both benign and malicious supports exist.

**Q: Is Playground readiness an assessment of a real network?**

A: No. It describes only selected tiny fixtures; no target IP, scan or live check occurs. Coverage is fixture execution coverage.

**Q: What are key limitations?**

A: Benchmark representativeness, test-set reuse in model selection, poor temporal generalization, rare supports, IF false alerts/low recall, small scenario fixture overlap, no live capture, and non-causal model explanations.

## Verified academic references

1. I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization,” *Proceedings of the 4th International Conference on Information Systems Security and Privacy (ICISSP)*, 2018, pp. 108–116, DOI: [10.5220/0006639801080116](https://doi.org/10.5220/0006639801080116). This is the paper the CIC dataset publisher asks dataset users to cite.
2. G. Engelen, V. Rimmer, and W. Joosen, “Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study,” *2021 IEEE Security and Privacy Workshops (SPW)*, 2021, DOI: [10.1109/SPW53761.2021.00009](https://doi.org/10.1109/SPW53761.2021.00009). This study reports issues in traffic generation, flow construction, feature extraction and labeling and describes a corrected/reprocessed version. The project's pinned Hugging Face derivative is not asserted to be that corrected version; its lineage must be verified before making such a claim.
3. Canadian Institute for Cybersecurity, [Intrusion Detection Evaluation Dataset (CICIDS2017)](https://www.unb.ca/cic/datasets/ids-2017.html), dataset description and attack schedule. Cite the actual derivative/revision used separately: [`lacg030175/CICIDS2017` at the pinned revision](https://huggingface.co/datasets/lacg030175/CICIDS2017/tree/d071fd53782d9ca7cdc15173b8ceb858fea04628).

The first two references provide an appropriate dataset-provenance and dataset-quality discussion starting point. They do not replace a literature review of the selected model methods; add verified method sources if the report discusses those algorithms in depth.

## Demonstration sequence

Follow the [step-by-step demo guide](../demo-guide.md). Prepare model artifacts and start backend/frontend first. Prefer a PortScan replay to demonstrate suspicious grouping and detail; show the endpoint graph, flow evidence, SHAP and baseline caveat; then run a public web Playground profile and explicitly explain the fixture limits and result categories. Keep a Normal replay available as a benign baseline and avoid claiming the UI represents current real network traffic.
