"""Training pipeline for anomaly detection model."""

from __future__ import annotations

import joblib
import numpy as np
from pathlib import Path

from app.ml.anomaly_detection.model import AnomalyDetector
from app.ml.shared.model_manager import ModelManager
from app.ml.shared.preprocessing import extract_window_features


class AnomalyTrainer:
    """Trains the anomaly detection model on telemetry data."""

    def __init__(self, model_manager: ModelManager | None = None):
        self.model_manager = model_manager or ModelManager()

    def prepare_features(
        self,
        readings_list: list[list[dict]],
        window_size: int = 50,
        step: int = 10,
    ) -> list[dict[str, float]]:
        """Extract feature vectors from multiple telemetry windows."""
        features_list = []
        for readings in readings_list:
            for i in range(0, len(readings) - window_size + 1, step):
                window = readings[i : i + window_size]
                feats = extract_window_features(window, window_size)
                if feats is not None:
                    features_list.append(feats)
        return features_list

    def train(
        self,
        features_list: list[dict[str, float]],
        model_name: str = "anomaly_detector",
    ) -> dict:
        """Train the anomaly detector and save it."""
        if len(features_list) < 10:
            raise ValueError("Need at least 10 feature windows for training")

        keys = list(features_list[0].keys())
        X = np.array([[f[k] for k in keys] for f in features_list], dtype=np.float32)

        mean = X.mean(axis=0)
        std = X.std(axis=0) + 1e-8
        X_norm = (X - mean) / std

        detector = AnomalyDetector(input_dim=X.shape[1])
        metrics = detector.fit(X_norm)

        version = self.model_manager.save_model(
            detector.autoencoder,
            model_name,
            metadata={
                "input_dim": X.shape[1],
                "feature_keys": keys,
                "threshold": detector.threshold,
                "norm_mean": mean.tolist(),
                "norm_std": std.tolist(),
                "training_samples": len(features_list),
                **metrics,
            },
        )

        # Save Isolation Forest separately
        if_path = self.model_manager.model_dir / model_name / version / "isolation_forest.pkl"
        joblib.dump(detector.isolation_forest, if_path)

        return {"features_used": keys, "samples": len(features_list), **metrics}
