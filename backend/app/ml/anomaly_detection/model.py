"""Anomaly detection model architecture.

Uses Isolation Forest for anomaly detection on sensor patterns,
plus an Autoencoder to learn "normal human wearing" pattern.
High reconstruction error = device likely not worn.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from numpy.typing import NDArray
from sklearn.ensemble import IsolationForest
import joblib


class WearAutoencoder(nn.Module):
    """Autoencoder that learns normal wearing patterns."""

    def __init__(self, input_dim: int, encoding_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, encoding_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded, encoded

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Per-sample reconstruction error (MSE)."""
        decoded, _ = self.forward(x)
        return torch.mean((x - decoded) ** 2, dim=1)


class AnomalyDetector:
    """Combined Isolation Forest + Autoencoder anomaly detector."""

    def __init__(self, input_dim: int, contamination: float = 0.1):
        self.input_dim = input_dim
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        self.autoencoder = WearAutoencoder(input_dim=input_dim)
        self.threshold: float = 0.0
        self.is_fitted = False

    def fit(
        self,
        X_normal: NDArray[np.float32],
        epochs: int = 50,
        lr: float = 1e-3,
        batch_size: int = 64,
    ) -> dict[str, float]:
        """Train both models on normal wearing data."""
        self.isolation_forest.fit(X_normal)

        dataset = torch.utils.data.TensorDataset(
            torch.tensor(X_normal, dtype=torch.float32)
        )
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.autoencoder.train()
        for _ in range(epochs):
            for (batch,) in loader:
                decoded, _ = self.autoencoder(batch)
                loss = criterion(decoded, batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        self.autoencoder.eval()
        with torch.no_grad():
            errors = self.autoencoder.reconstruction_error(
                torch.tensor(X_normal, dtype=torch.float32)
            ).numpy()
        self.threshold = float(np.percentile(errors, 95))
        self.is_fitted = True

        return {
            "threshold": self.threshold,
            "mean_error": float(errors.mean()),
            "max_error": float(errors.max()),
        }

    def predict(self, X: NDArray[np.float32]) -> dict[str, NDArray]:
        """Predict anomalies."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if_scores = self.isolation_forest.score_samples(X)
        if_predictions = self.isolation_forest.predict(X)

        with torch.no_grad():
            errors = self.autoencoder.reconstruction_error(
                torch.tensor(X, dtype=torch.float32)
            ).numpy()

        ae_anomalies = errors > self.threshold
        combined = (if_predictions == -1) | ae_anomalies

        return {
            "if_scores": if_scores,
            "if_predictions": if_predictions,
            "ae_errors": errors,
            "ae_anomalies": ae_anomalies,
            "combined_anomalies": combined,
            "confidence": 1.0 - (errors / (self.threshold * 2 + 1e-8)),
        }
