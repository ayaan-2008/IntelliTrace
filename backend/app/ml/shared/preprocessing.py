"""Data preprocessing utilities for ML pipelines."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def extract_window_features(
    readings: list[dict] | pd.DataFrame,
    window_seconds: int = 300,
) -> dict[str, float] | None:
    """Extract statistical features from a telemetry window."""
    if isinstance(readings, pd.DataFrame):
        df = readings
    else:
        if not readings:
            return None
        df = pd.DataFrame(readings)

    if len(df) < 5:
        return None

    features: dict[str, float] = {}

    # Heart rate features
    hr = df["heart_rate"].dropna() if "heart_rate" in df.columns else pd.Series(dtype=float)
    if len(hr) > 0:
        features["hr_mean"] = float(hr.mean())
        features["hr_std"] = float(hr.std()) if len(hr) > 1 else 0.0
        features["hr_min"] = float(hr.min())
        features["hr_max"] = float(hr.max())
        features["hr_range"] = features["hr_max"] - features["hr_min"]
    else:
        features["hr_mean"] = 0.0
        features["hr_std"] = 0.0
        features["hr_min"] = 0.0
        features["hr_max"] = 0.0
        features["hr_range"] = 0.0

    # Motion magnitude features
    for axis in ["x", "y", "z"]:
        col = f"accel_{axis}"
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                features[f"accel_{axis}_mean"] = float(vals.mean())
                features[f"accel_{axis}_std"] = float(vals.std()) if len(vals) > 1 else 0.0
            else:
                features[f"accel_{axis}_mean"] = 0.0
                features[f"accel_{axis}_std"] = 0.0

    # Magnitude of acceleration
    accel_cols = [c for c in ["accel_x", "accel_y", "accel_z"] if c in df.columns]
    if accel_cols:
        mag = np.sqrt((df[accel_cols] ** 2).sum(axis=1))
        features["accel_mag_mean"] = float(mag.mean())
        features["accel_mag_std"] = float(mag.std()) if len(mag) > 1 else 0.0
    else:
        features["accel_mag_mean"] = 0.0
        features["accel_mag_std"] = 0.0

    # Gyroscope features
    for axis in ["x", "y", "z"]:
        col = f"gyro_{axis}"
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                features[f"gyro_{axis}_mean"] = float(vals.mean())
                features[f"gyro_{axis}_std"] = float(vals.std()) if len(vals) > 1 else 0.0
            else:
                features[f"gyro_{axis}_mean"] = 0.0
                features[f"gyro_{axis}_std"] = 0.0

    # Step rate
    if "steps" in df.columns:
        steps = df["steps"].dropna()
        if len(steps) > 1:
            features["step_rate"] = float((steps.iloc[-1] - steps.iloc[0]) / window_seconds)
        else:
            features["step_rate"] = 0.0
    else:
        features["step_rate"] = 0.0

    # Speed features
    if "speed" in df.columns:
        spd = df["speed"].dropna()
        if len(spd) > 0:
            features["speed_mean"] = float(spd.mean())
            features["speed_std"] = float(spd.std()) if len(spd) > 1 else 0.0
        else:
            features["speed_mean"] = 0.0
            features["speed_std"] = 0.0
    else:
        features["speed_mean"] = 0.0
        features["speed_std"] = 0.0

    # SpO2
    if "sp_o2" in df.columns:
        spo2 = df["sp_o2"].dropna()
        features["sp_o2_mean"] = float(spo2.mean()) if len(spo2) > 0 else 98.0
    else:
        features["sp_o2_mean"] = 98.0

    # Skin temperature
    if "skin_temperature" in df.columns:
        temp = df["skin_temperature"].dropna()
        features["temp_mean"] = float(temp.mean()) if len(temp) > 0 else 36.5
    else:
        features["temp_mean"] = 36.5

    return features


def normalize_features(
    features: dict[str, float],
    mean_std: dict[str, tuple[float, float]] | None = None,
) -> NDArray[np.float32]:
    """Normalize features to zero mean, unit variance."""
    arr = np.array(list(features.values()), dtype=np.float32)

    if mean_std is None:
        return (arr - arr.mean()) / (arr.std() + 1e-8)

    keys = list(features.keys())
    means = np.array([mean_std.get(k, (0.0, 1.0))[0] for k in keys], dtype=np.float32)
    stds = np.array([mean_std.get(k, (0.0, 1.0))[1] for k in keys], dtype=np.float32)
    return (arr - means) / (stds + 1e-8)


def build_sequence(
    readings: list[dict] | pd.DataFrame,
    seq_len: int = 50,
    feature_keys: list[str] | None = None,
) -> NDArray[np.float32] | None:
    """Build a fixed-length sequence from raw readings for CNN+LSTM input."""
    if isinstance(readings, pd.DataFrame):
        df = readings
    else:
        if len(readings) < seq_len:
            return None
        df = pd.DataFrame(readings)

    if feature_keys is None:
        feature_keys = [
            "heart_rate", "accel_x", "accel_y", "accel_z",
            "gyro_x", "gyro_y", "gyro_z", "speed", "sp_o2",
        ]

    available = [k for k in feature_keys if k in df.columns]
    if not available:
        return None

    step = len(df) // seq_len
    indices = list(range(0, len(df), step))[:seq_len]

    sequence = df[available].iloc[indices].fillna(0.0).values.astype(np.float32)

    if len(sequence) < seq_len:
        pad_len = seq_len - len(sequence)
        sequence = np.vstack([sequence, np.zeros((pad_len, len(available)), dtype=np.float32)])

    return sequence
