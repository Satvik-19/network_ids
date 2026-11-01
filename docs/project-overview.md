# Project overview and scope

## Problem and intended use

Network flow datasets can contain far more records than a person can inspect one by one. This project applies a small, reproducible detection pipeline to flow-level feature records and makes its outputs reviewable: supervised class, confidence, anomaly score, a deterministic final category, risk indicator, incident evidence and local model-feature contributions.

The intended use is an academic demonstration and evaluation of a flow-based IDS design. The local UI is aimed at students, lab administrators and small-environment operators exploring the behavior of a detector. It is not an operational sensor, a certified risk assessment or a production SOC.

## Implemented modules

| Module | Status and behavior |
|---|---|
| Security Monitor | Implemented. Replays prepared flows; shows run status, current-run evidence, risk/timeline charts, incidents and host communication graph. |
| Incident history/detail | Implemented. Lists persisted groups and presents linked flow evidence, model contributions and baseline feature values. |
| Security Playground | Implemented first version. Profiles select deterministic prepared suites; a bounded synchronous run stores outcome counts, coverage and explanations. |
| Model Evaluation Lab | Not implemented. Evaluation scripts and saved JSON are present, but there is no Lab screen. |

## Scope boundaries

Inputs are precomputed flow feature vectors. Scenario endpoint IPs and ports are fixture metadata, not evidence from a live installation. The host graph draws only source-to-destination relationships present in those records, and uses ports/protocol as flow metadata rather than independent hosts. Replay time is synthetic. No online capture, scanner, attack generator, mitigation, live response, authentication or multi-host deployment is provided.

`UNKNOWN_SUSPICIOUS` means the supervised branch did not produce a qualifying known malicious verdict and the anomaly threshold was crossed. It can apply to benign flows; it is not a name for a new attack and does not prove compromise. Playground readiness summarizes selected fixture outcomes and is not an assessment of the user's network.

## Terminology

- **Flow:** one feature record from the dataset/fixture.
- **Supervised prediction:** XGBoost top predicted label and confidence.
- **Anomaly score:** Isolation Forest `decision_function`; lower is more anomalous, and it is not a probability.
- **Hybrid classification:** the ordered rules in [ML pipeline](ml-pipeline.md).
- **Replay run:** one fixture pass identified by a run ID, isolated in the Monitor evidence feed.
- **Scenario coverage:** selected fixture flow support actually evaluated, not percentage of a real environment covered.
- **False alert:** a fixture row whose ground-truth label is benign but final hybrid classification is suspicious.

## Current phase

Phase 4's approved first Playground workflow is complete and was validated in the recorded 2026-10-31 checks. The UI redesign is also implemented. Phase 5 work such as the Model Evaluation Lab and expanded research is deferred. See [implementation status](IMPLEMENTATION_STATUS.md), [phase 4 record](PHASES/PHASE_4.md), and [testing record](testing.md).
