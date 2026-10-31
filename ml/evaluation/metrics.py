"""metrics.py — Reusable evaluation metric computation.

Captures the PRD §47 metrics for Phase-1 baselines:
- Binary: accuracy, precision, recall, F1, ROC-AUC, confusion matrix.
- Multiclass: accuracy, macro/weighted F1, per-class precision/recall/F1,
  confusion matrix.
Results are serialisable to JSON for the Model Lab and documentation.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_binary(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob_positive: Optional[np.ndarray] = None,
    *,
    positive_label: int = 1,
) -> dict:
    """Binary 0/1 targets (BENIGN/attack); probabilities support ROC-AUC."""
    out: dict = {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
        ),
        "f1": float(
            f1_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
        ),
    }
    if y_prob_positive is not None and len(np.unique(y_true)) > 1:
        try:
            out["roc_auc"] = float(roc_auc_score(y_true, y_prob_positive))
        except ValueError:
            out["roc_auc"] = None
    else:
        out["roc_auc"] = None
    out["confusion_matrix"] = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return out


def evaluate_multiclass(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: List[str],
    *,
    digits: int = 4,
) -> dict:
    """Multiclass metrics with per-class report."""
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(labels))),
        target_names=labels,
        output_dict=True,
        zero_division=0,
    )
    out: dict = {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(report["macro avg"]["precision"]),
        "macro_recall": float(report["macro avg"]["recall"]),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_precision": float(report["weighted avg"]["precision"]),
        "weighted_recall": float(report["weighted avg"]["recall"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "per_class": {
            label: {
                "precision": report[label]["precision"],
                "recall": report[label]["recall"],
                "f1": report[label]["f1-score"],
                "support": int(report[label]["support"]),
            }
            for label in labels
        },
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=list(range(len(labels)))
        ).tolist(),
    }
    return out


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
