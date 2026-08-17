"""predictor.py — Phase-2 inference service.

Wires the FINAL artifacts into one deterministic pipeline for a single flow:

    raw features (77 canonical names)
      -> preprocessing (no scaling for XGBoost/IF)
      -> supervised model      (label / family / confidence / probabilities)
      -> Isolation Forest      (anomaly_score)
      -> hybrid decision layer (BENIGN / KNOWN_ATTACK / UNKNOWN_SUSPICIOUS)
      -> risk engine           (LOW / MEDIUM / HIGH / CRITICAL)
      -> SHAP local explanations (top contributing features, PRD §12)

The hybrid/risk thresholds are loaded from config/config.yaml (PRD §57). The
Phase-2 API contract never fabricates fields: every output below is computed
from real artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

from ml.hybrid.decision import HybridThresholds, hybrid_decision
from ml.hybrid.risk import RiskThresholds, risk_score
from ml.hybrid.shap_explainer import ShapExplainer
from ml.preprocessing.labels import family_for
from ml.preprocessing.preprocess import (
    CANONICAL_FEATURE_COLUMNS,
    FEATURE_COUNT,
    clean_numeric,
)

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "ml" / "artifacts"
CONFIG_PATH = ROOT / "config" / "config.yaml"


class PredictorError(RuntimeError):
    pass


class Phase2Predictor:
    """Stateless wrapper around the final supervised + anomaly + hybrid stack."""

    def __init__(
        self,
        artifacts: Path = ARTIFACTS,
        config_path: Path = CONFIG_PATH,
    ) -> None:
        self.artifacts = Path(artifacts)
        self.config = self._load_config(Path(config_path))
        self._load()
        self._shap = ShapExplainer(self.artifacts)

    # ------------------------------------------------------------------ #
    # loading
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_config(path: Path) -> dict:
        if not path.exists():
            raise PredictorError(f"config not found: {path}")
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        if cfg is None or "inference" not in cfg or "risk" not in cfg:
            raise PredictorError("config.yaml missing inference/risk sections")
        return cfg

    def _load(self) -> None:
        sup_path = self.artifacts / "supervised_model.joblib"
        ifa_path = self.artifacts / "isolation_forest.joblib"
        meta_path = self.artifacts / "supervised_model_metadata.json"
        for p in (sup_path, ifa_path, meta_path):
            if not p.exists():
                raise PredictorError(
                    f"Phase-2 artifact missing: {p}. Run train_final_supervised.py "
                    f"and train_isolation_forest.py first."
                )
        self.supervised = joblib.load(sup_path)
        self.isolation_forest = joblib.load(ifa_path)
        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))

        order = self.meta["feature_order"]
        if len(order) != FEATURE_COUNT or order != CANONICAL_FEATURE_COLUMNS:
            raise PredictorError("feature_order does not match CANONICAL_FEATURE_COLUMNS")
        self.feature_order = order
        self.model_name = f"{self.meta['model']} ({self.meta['variant']})"
        self.model_version = self.meta["phase"]

        inf = self.config["inference"]
        self.known_confidence_threshold = float(inf["known_confidence_threshold"])
        self.anomaly_threshold = float(inf["anomaly_threshold"])

        risk = self.config["risk"]
        self.risk_thresholds = RiskThresholds(
            medium_threshold=float(risk["medium_threshold"]),
            high_threshold=float(risk["high_threshold"]),
            critical_threshold=float(risk["critical_threshold"]),
            severity=dict(risk.get("severity", {})),
        )

    # ------------------------------------------------------------------ #
    # prediction
    # ------------------------------------------------------------------ #
    def _feature_array(self, features: dict) -> np.ndarray:
        """Validate + convert one feature dict to the canonical raw matrix row."""
        missing = set(self.feature_order) - set(features)
        extra = set(features) - set(self.feature_order)
        if missing:
            raise PredictorError(f"Missing {len(missing)} features, e.g. {sorted(missing)[:5]}")
        if extra:
            raise PredictorError(f"Unexpected extra features: {sorted(extra)[:5]}")

        row = {name: features[name] for name in self.feature_order}
        df = pd.DataFrame([row])[self.feature_order]
        return clean_numeric(df).to_numpy()

    def predict(self, features: dict, *, with_shap: bool = True) -> dict:
        """Run the full Phase-2 pipeline for one flow.

        Returns a dict with all Phase-2 contract fields:
          label, family, classification (hybrid), confidence, probabilities,
          anomaly_score, risk, top_features, base_value.
        """
        X = self._feature_array(features)
        X2 = X.reshape(1, -1)

        # --- supervised ---
        proba = self.supervised.predict_proba(X2)[0]
        idx = int(np.argmax(proba))
        label_code = int(self.supervised.classes_[idx])
        label = self._label_for(label_code)
        confidence = float(proba[idx])

        # --- anomaly ---
        anomaly_score = float(self.isolation_forest.decision_function(X2)[0])

        # --- hybrid (PRD §10) ---
        thresholds = HybridThresholds(
            known_confidence_threshold=self.known_confidence_threshold,
            anomaly_threshold=self.anomaly_threshold,
        )
        classification = hybrid_decision(
            confidence=confidence,
            label=label,
            anomaly_score=anomaly_score,
            thresholds=thresholds,
        )

        # --- risk (PRD §11) ---
        risk = risk_score(
            classification=classification,
            family=family_for(label),
            confidence=confidence,
            anomaly_score=anomaly_score,
            anomaly_threshold=self.anomaly_threshold,
            thresholds=self.risk_thresholds,
        )

        # --- SHAP local explanation (PRD §12) ---
        shap = {}
        if with_shap:
            shap = self._shap.explain(X2[0], top_k=5)

        return {
            "label": label,
            "family": family_for(label),
            "classification": classification,
            "confidence": confidence,
            "probabilities": {
                self._label_for(int(c)): float(p)
                for c, p in zip(self.supervised.classes_, proba)
            },
            "anomaly_score": round(anomaly_score, 6),
            "anomaly_threshold": self.anomaly_threshold,
            "risk_score": risk["score"],
            "risk_level": risk["level"],
            "top_features": shap.get("top_features", []),
            "shap_base_value": shap.get("base_value"),
        }

    def explain(self, features: dict, top_k: int = 5) -> dict:
        """SHAP local explanation for one flow WITHOUT re-running the pipeline.

        Phase-3.5 hardening (BUG-010): the replay engine scores every flow once
        and attaches SHAP only to suspicious flows. Calling ``predict`` again
        with ``with_shap=True`` would re-execute the supervised + anomaly +
        hybrid + risk stack for a result the caller already holds; this method
        recomputes only the explanation block on the canonical feature row.
        Deterministic: identical output to the ``with_shap=True`` path.
        """
        X = self._feature_array(features)
        return self._shap.explain(X[0], top_k=top_k)

    def _label_for(self, code: int) -> str:
        from ml.preprocessing.labels import INT_TO_LABEL

        return INT_TO_LABEL[code]
