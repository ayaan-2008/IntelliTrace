"""Training pipeline for person verification model."""

from __future__ import annotations

import random

import numpy as np
import torch
import torch.nn as nn

from app.ml.person_verification.model import BiometricCNNLSTM, SiameseVerifier
from app.ml.shared.model_manager import ModelManager
from app.ml.shared.preprocessing import build_sequence


class PersonVerificationTrainer:
    """Trains the person verification model."""

    def __init__(self, model_manager: ModelManager | None = None):
        self.model_manager = model_manager or ModelManager()

    def prepare_pairs(
        self,
        user_readings: list[list[dict]],
        other_readings: list[list[dict]] | None = None,
        seq_len: int = 50,
    ) -> tuple[list[tuple[torch.Tensor, torch.Tensor]], list[tuple[torch.Tensor, torch.Tensor]]]:
        """Prepare positive and negative pairs for Siamese training."""
        # Build sequences from user data
        sequences = []
        for readings in user_readings:
            step = max(1, seq_len // 2)
            for i in range(0, len(readings) - seq_len + 1, step):
                seq = build_sequence(readings[i : i + seq_len], seq_len)
                if seq is not None:
                    sequences.append(torch.tensor(seq, dtype=torch.float32))

        if len(sequences) < 4:
            raise ValueError("Not enough valid sequences for training")

        # Positive pairs
        pos_pairs = []
        for i in range(len(sequences)):
            for j in range(i + 1, min(i + 3, len(sequences))):
                pos_pairs.append((sequences[i], sequences[j]))

        # Negative pairs
        neg_pairs = []
        if other_readings:
            other_seqs = []
            for readings in other_readings:
                for i in range(0, len(readings) - seq_len + 1, seq_len):
                    seq = build_sequence(readings[i : i + seq_len], seq_len)
                    if seq is not None:
                        other_seqs.append(torch.tensor(seq, dtype=torch.float32))

            for seq in sequences:
                if other_seqs:
                    neg_seq = random.choice(other_seqs)
                    neg_pairs.append((seq, neg_seq))
        else:
            # Self-negative: pair distant sequences
            for i in range(len(sequences)):
                candidates = [k for k in range(len(sequences)) if abs(k - i) > 5]
                if candidates:
                    neg_idx = random.choice(candidates)
                    neg_pairs.append((sequences[i], sequences[neg_idx]))

        return pos_pairs, neg_pairs

    def train(
        self,
        pos_pairs: list[tuple[torch.Tensor, torch.Tensor]],
        neg_pairs: list[tuple[torch.Tensor, torch.Tensor]],
        model_name: str = "person_verifier",
        epochs: int = 30,
        lr: float = 1e-3,
    ) -> dict:
        """Train the Siamese verification model."""
        n_features = pos_pairs[0][0].shape[1]
        seq_len = pos_pairs[0][0].shape[0]

        backbone = BiometricCNNLSTM(n_features=n_features, seq_len=seq_len)
        model = SiameseVerifier(backbone)

        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        criterion = nn.BCELoss()

        all_pairs = [(a, b, 1.0) for a, b in pos_pairs] + [(a, b, 0.0) for a, b in neg_pairs]
        random.shuffle(all_pairs)

        model.train()
        for _ in range(epochs):
            for x1, x2, label in all_pairs:
                x1 = x1.unsqueeze(0)
                x2 = x2.unsqueeze(0)
                target = torch.tensor([label])

                pred = model(x1, x2)
                loss = criterion(pred, target)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        metrics = {
            "n_features": n_features,
            "seq_len": seq_len,
            "pos_pairs": len(pos_pairs),
            "neg_pairs": len(neg_pairs),
        }
        self.model_manager.save_model(model, model_name, metadata=metrics)

        return metrics
