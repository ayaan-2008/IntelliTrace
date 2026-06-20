"""Inference predictor for person verification."""

from __future__ import annotations

import torch

from app.config import settings
from app.ml.person_verification.model import BiometricCNNLSTM, SiameseVerifier
from app.ml.shared.model_manager import ModelManager
from app.ml.shared.preprocessing import build_sequence


class PersonPredictor:
    """Verifies if current wearer matches the enrolled user."""

    def __init__(self, model_manager: ModelManager | None = None):
        self.model_manager = model_manager or ModelManager()
        self.model: SiameseVerifier | None = None
        self.n_features: int = 9
        self.seq_len: int = 50

    def load(self, model_name: str = "person_verifier") -> bool:
        """Load the trained verification model. Returns True if successful."""
        try:
            meta = self.model_manager.load_metadata(model_name)
            if not meta:
                return False

            self.n_features = meta["n_features"]
            self.seq_len = meta["seq_len"]

            backbone = BiometricCNNLSTM(
                n_features=self.n_features, seq_len=self.seq_len
            )
            self.model = SiameseVerifier(backbone)
            self.model_manager.load_model(self.model, model_name)
            self.model.eval()
            return True
        except FileNotFoundError:
            return False

    def verify(
        self,
        current_readings: list[dict],
        baseline_readings: list[dict] | None = None,
        baseline_tensor: torch.Tensor | None = None,
    ) -> dict:
        """Verify if current wearer matches the enrolled user."""
        if self.model is None:
            return {"matches": True, "score": 0.5, "reason": "model not loaded"}

        current_seq = build_sequence(current_readings, self.seq_len)
        if current_seq is None:
            return {"matches": True, "score": 0.5, "reason": "insufficient data"}

        current_tensor = torch.tensor(current_seq, dtype=torch.float32).unsqueeze(0)

        if baseline_tensor is None:
            if baseline_readings is not None:
                baseline_seq = build_sequence(baseline_readings, self.seq_len)
                if baseline_seq is None:
                    return {"matches": True, "score": 0.5, "reason": "no baseline data"}
                baseline_tensor = torch.tensor(baseline_seq, dtype=torch.float32).unsqueeze(0)
            else:
                return {"matches": True, "score": 0.5, "reason": "no baseline provided"}

        with torch.no_grad():
            score = self.model(current_tensor, baseline_tensor).item()

        threshold = settings.PERSON_VERIFICATION_THRESHOLD

        return {
            "matches": score >= threshold,
            "score": round(score, 4),
            "threshold": threshold,
            "reason": "match" if score >= threshold else "mismatch",
        }
