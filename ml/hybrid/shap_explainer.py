"""SHAP local explanations (PRD §12).

Produces per-flow feature attributions for the final tree-based supervised
model. Only LOCAL explanations are produced (PRD §36) — one row in, top-k
feature contributions out. Raw SHAP values stay available for the API /
UI technical section.

Implementation note (DEC-009): the SHAP values are computed with XGBoost's
native TreeSHAP path (``booster.predict(pred_contribs=True)``) rather than
``shap.TreeExplainer``. SHAP 0.49.1 — the latest available release — cannot
parse XGBoost 3.2.0's multiclass ``base_score`` vector, raising
``ValueError: could not convert string to float``. The native path runs the
identical tree-path-dependent SHAP algorithm and its output was verified to
equal the model margin exactly (sum of contributions + bias == raw margin for
all 15 classes). This keeps the project dependency-safe and CPU-first
(PRD §61) while preserving the PRD §12 explainability contract.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "ml" / "artifacts"


class ShapExplainer:
    """Lazy wrapper around the final supervised model's TreeSHAP path."""

    def __init__(self, artifacts: Path = ARTIFACTS) -> None:
        self.artifacts = Path(artifacts)
        self.model_path = self.artifacts / "supervised_model.joblib"
        self._loaded = False

    def _load(self):
        import joblib

        from ml.preprocessing.labels import INT_TO_LABEL

        if not self._loaded:
            self._model = joblib.load(self.model_path)
            self._class_names = [INT_TO_LABEL[int(c)] for c in self._model.classes_]
            self._loaded = True
        return self._model

    def explain(self, X_row: np.ndarray, top_k: int = 5) -> dict:
        """Explain one flow.

        Args:
            X_row: 1-D array of the 77 canonical feature values (raw, unscaled).
            top_k: number of top contributing features to return.

        Returns:
            {
              "predicted_class": str,
              "base_value": float,
              "top_features": [{"feature": str, "shap_value": float,
                                "direction": "pushes_towards"|"pushes_against"}],
              "n_features_explained": int,
            }
        """
        import xgboost as xgb

        from ml.preprocessing.preprocess import CANONICAL_FEATURE_COLUMNS

        model = self._load()
        X2 = np.asarray(X_row, dtype="float64").reshape(1, -1)
        proba = model.predict_proba(X2)[0]
        pred_idx = int(np.argmax(proba))
        pred_class = self._class_names[pred_idx]

        dmat = xgb.DMatrix(X2)
        contrib = model.get_booster().predict(dmat, pred_contribs=True)
        # contrib shape: (1, n_classes, n_features+1); last column = bias.
        class_sv = contrib[0, pred_idx, :-1]
        bias = float(contrib[0, pred_idx, -1])

        order = np.argsort(np.abs(class_sv))[::-1][:top_k]
        top = []
        for i in order:
            val = float(class_sv[i])
            top.append({
                "feature": CANONICAL_FEATURE_COLUMNS[int(i)],
                "shap_value": round(val, 6),
                "direction": "pushes_towards" if val > 0 else "pushes_against",
            })

        return {
            "predicted_class": pred_class,
            "base_value": round(bias, 6),
            "top_features": top,
            "n_features_explained": int(X2.shape[1]),
        }
