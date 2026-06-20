"""Person verification model architecture.

1D-CNN + LSTM hybrid for biometric signature matching.
- CNN extracts local patterns (heart rate spikes, movement bursts)
- LSTM captures temporal dependencies (patterns over time)
- Output: probability score [0-1] that current wearer matches enrolled user
"""

from __future__ import annotations

import torch
import torch.nn as nn


class BiometricCNNLSTM(nn.Module):
    """CNN + LSTM for person verification from sensor sequences."""

    def __init__(
        self,
        n_features: int = 9,
        seq_len: int = 50,
        cnn_out: int = 64,
        lstm_hidden: int = 128,
        lstm_layers: int = 2,
    ):
        super().__init__()
        self.seq_len = seq_len

        self.cnn = nn.Sequential(
            nn.Conv1d(n_features, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, cnn_out, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )

        self.lstm = nn.LSTM(
            input_size=cnn_out,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=0.3,
        )

        self.head = nn.Sequential(
            nn.Linear(lstm_hidden, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, n_features)
        Returns:
            probability (batch,) that input matches enrolled user
        """
        cnn_in = x.permute(0, 2, 1)
        cnn_out = self.cnn(cnn_in)

        lstm_in = cnn_out.permute(0, 2, 1)
        lstm_out, (h_n, _) = self.lstm(lstm_in)

        last_hidden = h_n[-1]
        return self.head(last_hidden).squeeze(-1)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Get embedding vector (for comparing two inputs)."""
        cnn_in = x.permute(0, 2, 1)
        cnn_out = self.cnn(cnn_in)
        lstm_in = cnn_out.permute(0, 2, 1)
        _, (h_n, _) = self.lstm(lstm_in)
        return h_n[-1]


class SiameseVerifier(nn.Module):
    """Siamese network for comparing two biometric sequences."""

    def __init__(self, backbone: BiometricCNNLSTM):
        super().__init__()
        self.backbone = backbone

    def forward(
        self,
        x1: torch.Tensor,
        x2: torch.Tensor,
    ) -> torch.Tensor:
        """Returns similarity score [0-1] between two inputs."""
        emb1 = self.backbone.encode(x1)
        emb2 = self.backbone.encode(x2)

        sim = nn.functional.cosine_similarity(emb1, emb2, dim=1)
        return (sim + 1) / 2
