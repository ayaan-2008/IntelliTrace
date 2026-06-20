"""Feature extraction for person verification.

Extracts multi-modal biometric signatures from raw sensor data:
- Heart rate pattern: Resting HR, HR variability over time
- Gait analysis: Accelerometer + gyroscope patterns
- Movement signature: Activity intensity patterns
- Location pattern: Movement between known locations
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def extract_heart_rate_signature(readings: list[dict] | pd.DataFrame) -> NDArray[np.float32]:
    """Extract heart rate temporal signature."""
    df = readings if isinstance(readings, pd.DataFrame) else pd.DataFrame(readings)
    hr = df["heart_rate"].dropna().values if "heart_rate" in df.columns else np.array([])

    if len(hr) < 5:
        return np.zeros(12, dtype=np.float32)

    features = np.array([
        np.mean(hr),
        np.std(hr),
        np.min(hr),
        np.max(hr),
        np.percentile(hr, 25),
        np.percentile(hr, 75),
        np.mean(np.abs(np.diff(hr))),
        np.std(np.diff(hr)) if len(hr) > 1 else 0.0,
        np.mean(hr < 60),
        np.mean((hr >= 60) & (hr < 100)),
        np.mean((hr >= 100) & (hr < 140)),
        np.mean(hr >= 140),
    ], dtype=np.float32)

    return features


def extract_gait_signature(readings: list[dict] | pd.DataFrame) -> NDArray[np.float32]:
    """Extract gait pattern from accelerometer and gyroscope."""
    df = readings if isinstance(readings, pd.DataFrame) else pd.DataFrame(readings)

    accel_cols = [c for c in ["accel_x", "accel_y", "accel_z"] if c in df.columns]
    gyro_cols = [c for c in ["gyro_x", "gyro_y", "gyro_z"] if c in df.columns]

    features = []

    if accel_cols:
        accel = df[accel_cols].dropna().values
        if len(accel) > 5:
            mag = np.sqrt((accel ** 2).sum(axis=1))
            features.extend([
                np.mean(mag),
                np.std(mag),
                np.sum(np.diff(np.sign(mag - np.mean(mag))) != 0) / (len(mag) / 30),
                np.percentile(mag, 95) - np.percentile(mag, 5),
            ])
        else:
            features.extend([0.0] * 4)
    else:
        features.extend([0.0] * 4)

    if gyro_cols:
        gyro = df[gyro_cols].dropna().values
        if len(gyro) > 5:
            gyro_mag = np.sqrt((gyro ** 2).sum(axis=1))
            features.extend([
                np.mean(gyro_mag),
                np.std(gyro_mag),
                np.mean(np.abs(gyro[:, 0])),
                np.mean(np.abs(gyro[:, 1])),
                np.mean(np.abs(gyro[:, 2])),
            ])
        else:
            features.extend([0.0] * 5)
    else:
        features.extend([0.0] * 5)

    return np.array(features, dtype=np.float32)


def extract_movement_signature(readings: list[dict] | pd.DataFrame) -> NDArray[np.float32]:
    """Extract general movement intensity patterns."""
    df = readings if isinstance(readings, pd.DataFrame) else pd.DataFrame(readings)

    features = []

    if "speed" in df.columns:
        spd = df["speed"].dropna().values
        if len(spd) > 0:
            features.extend([np.mean(spd), np.std(spd), np.max(spd)])
        else:
            features.extend([0.0] * 3)
    else:
        features.extend([0.0] * 3)

    if "steps" in df.columns:
        steps = df["steps"].dropna().values
        if len(steps) > 1:
            total = steps[-1] - steps[0]
            features.append(float(total))
        else:
            features.append(0.0)
    else:
        features.append(0.0)

    for col in ["sp_o2", "skin_temperature"]:
        if col in df.columns:
            vals = df[col].dropna().values
            if len(vals) > 0:
                features.extend([np.mean(vals), np.std(vals)])
            else:
                features.extend([98.0 if col == "sp_o2" else 36.5, 0.0])
        else:
            features.extend([98.0 if col == "sp_o2" else 36.5, 0.0])

    return np.array(features, dtype=np.float32)


def extract_full_signature(readings: list[dict]) -> NDArray[np.float32]:
    """Combine all biometric features into a single signature vector."""
    df = pd.DataFrame(readings)
    hr_sig = extract_heart_rate_signature(df)
    gait_sig = extract_gait_signature(df)
    move_sig = extract_movement_signature(df)
    return np.concatenate([hr_sig, gait_sig, move_sig])
