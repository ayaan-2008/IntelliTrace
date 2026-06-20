"""Generate synthetic telemetry data for demos and testing."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone


def generate_normal_wearing_data(
    device_id: uuid.UUID | None = None,
    num_readings: int = 500,
    start_time: datetime | None = None,
) -> list[dict]:
    """Simulate normal wearable data from a person wearing the device."""
    if device_id is None:
        device_id = uuid.uuid4()
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)

    readings = []
    base_hr = random.gauss(72, 8)
    base_lat, base_lon = 40.7128, -74.0060
    steps_acc = 0

    for i in range(num_readings):
        t = start_time + timedelta(seconds=i * 5)
        movement = random.gauss(0, 0.3)

        readings.append({
            "device_id": str(device_id),
            "timestamp": t.isoformat(),
            "heart_rate": int(max(50, min(150, base_hr + random.gauss(0, 5)))),
            "sp_o2": int(max(90, min(100, 97 + random.gauss(0, 1)))),
            "skin_temperature": round(36.2 + random.gauss(0, 0.3), 1),
            "accel_x": round(movement + random.gauss(0, 0.1), 3),
            "accel_y": round(random.gauss(0, 0.1), 3),
            "accel_z": round(9.8 + random.gauss(0, 0.2), 3),
            "gyro_x": round(random.gauss(0, 0.05), 3),
            "gyro_y": round(random.gauss(0, 0.05), 3),
            "gyro_z": round(random.gauss(0, 0.05), 3),
            "speed": round(abs(random.gauss(1.2, 0.5)), 2),
            "steps": steps_acc,
            "latitude": base_lat + random.gauss(0, 0.0001),
            "longitude": base_lon + random.gauss(0, 0.0001),
            "battery_level": max(10, 100 - i // 10),
        })
        steps_acc += random.randint(0, 3)

    return readings


def generate_anomaly_data(
    device_id: uuid.UUID | None = None,
    num_readings: int = 100,
    start_time: datetime | None = None,
) -> list[dict]:
    """Simulate data when device is NOT worn (on table, in bag, etc.)."""
    if device_id is None:
        device_id = uuid.uuid4()
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    readings = []
    for i in range(num_readings):
        t = start_time + timedelta(seconds=i * 5)
        readings.append({
            "device_id": str(device_id),
            "timestamp": t.isoformat(),
            "heart_rate": None,
            "sp_o2": None,
            "skin_temperature": round(22.0 + random.gauss(0, 0.5), 1),
            "accel_x": round(random.gauss(0, 0.01), 3),
            "accel_y": round(random.gauss(0, 0.01), 3),
            "accel_z": round(9.8 + random.gauss(0, 0.01), 3),
            "gyro_x": round(random.gauss(0, 0.001), 3),
            "gyro_y": round(random.gauss(0, 0.001), 3),
            "gyro_z": round(random.gauss(0, 0.001), 3),
            "speed": 0.0,
            "steps": 0,
            "latitude": None,
            "longitude": None,
            "battery_level": max(10, 100 - i // 5),
        })
    return readings


def generate_different_person_data(
    device_id: uuid.UUID | None = None,
    num_readings: int = 200,
    start_time: datetime | None = None,
) -> list[dict]:
    """Simulate a different person wearing the device."""
    if device_id is None:
        device_id = uuid.uuid4()
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    readings = []
    base_hr = random.gauss(85, 10)
    base_lat, base_lon = 40.7128, -74.0060
    steps_acc = 0

    for i in range(num_readings):
        t = start_time + timedelta(seconds=i * 5)
        movement = random.gauss(0, 0.5)

        readings.append({
            "device_id": str(device_id),
            "timestamp": t.isoformat(),
            "heart_rate": int(max(50, min(160, base_hr + random.gauss(0, 8)))),
            "sp_o2": int(max(90, min(100, 96 + random.gauss(0, 1.5)))),
            "skin_temperature": round(36.5 + random.gauss(0, 0.4), 1),
            "accel_x": round(movement + random.gauss(0, 0.2), 3),
            "accel_y": round(random.gauss(0, 0.2), 3),
            "accel_z": round(9.8 + random.gauss(0, 0.4), 3),
            "gyro_x": round(random.gauss(0, 0.1), 3),
            "gyro_y": round(random.gauss(0, 0.1), 3),
            "gyro_z": round(random.gauss(0, 0.1), 3),
            "speed": round(abs(random.gauss(1.8, 0.8)), 2),
            "steps": steps_acc,
            "latitude": base_lat + random.gauss(0, 0.0002),
            "longitude": base_lon + random.gauss(0, 0.0002),
            "battery_level": max(10, 100 - i // 8),
        })
        steps_acc += random.randint(1, 4)

    return readings
