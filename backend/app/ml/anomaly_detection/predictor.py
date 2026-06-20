"""Inference predictor for anomaly detection."""

from __future__ import annotations

import joblib
import numpy as np

from app.ml.anomaly_detection.model import AnomalyDetector
from app.ml.shared.model_manager import ModelManager
from app.ml.shared.preprocessing import extract_window_features


class AnomalyPredictor:
    """Runs anomaly detection inference on telemetry windows."""

    def __init__(self, model_manager: ModelManager | None = None):
        self.model_manager = model_manager or ModelManager()
        self.detector: AnomalyDetector | None = None
        self.feature_keys: list[str] = []
        self.norm_mean: np.ndarray | None = None
        self.norm_std: np.ndarray | None = None

    def load(self, model_name: str = "anomaly_detector") -> bool:
        """Load the trained anomaly detector. Returns True if successful."""
        try:
            meta = self.model_manager.load_metadata(model_name)
            if not meta:
                return False

            input_dim = meta["input_dim"]
            self.feature_keys = meta["feature_keys"]
            self.norm_mean = np.array(meta["norm_mean"], dtype=np.float32)
            self.norm_std = np.array(meta["norm_std"], dtype=np.float32)

            self.detector = AnomalyDetector(input_dim=input_dim)
            self.detector.threshold = meta["threshold"]
            self.model_manager.load_model(self.detector.autoencoder, model_name)

            # Load Isolation Forest
            version = self.model_manager.get_latest_version(model_name)
            if_path = self.model_manager.model_dir / model_name / version / "isolation_forest.pkl"
            if if_path.exists():
                self.detector.isolation_forest = joblib.load(if_path)

            self.detector.is_fitted = True
            return True
        except FileNotFoundError:
            return False

    def predict(self, readings: list[dict]) -> dict:
        """Predict if the device is being worn normally."""
        if self.detector is None:
            return {"is_anomaly": False, "confidence": 0.0, "reason": "model not loaded"}

        features = extract_window_features(readings)
        if features is None:
            return {"is_anomaly": False, "confidence": 0.0, "reason": "insufficient data"}

        vec = np.array([features.get(k, 0.0) for k in self.feature_keys], dtype=np.float32)
        vec = (vec - self.norm_mean) / (self.norm_std + 1e-8)
        vec = vec.reshape(1, -1)

        result = self.detector.predict(vec)

        is_anomaly = bool(result["combined_anomalies"][0])
        confidence = float(np.clip(result["confidence"][0], 0.0, 1.0))

        reason_parts = []
        if result["if_predictions"][0] == -1:
            reason_parts.append("isolation_forest")
        if result["ae_anomalies"][0]:
            reason_parts.append("autoencoder")

        return {
            "is_anomaly": is_anomaly,
            "confidence": round(confidence, 4),
            "ae_error": round(float(result["ae_errors"][0]), 6),
            "if_score": round(float(result["if_scores"][0]), 4),
            "reason": "+".join(reason_parts) if reason_parts else "normal",
        }
