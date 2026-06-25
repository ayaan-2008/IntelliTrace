import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryBase(BaseModel):
    timestamp: datetime
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    speed: float | None = None
    heart_rate: int | None = Field(None, ge=0, le=300)
    pulse_rate: int | None = Field(None, ge=0, le=300)
    sp_o2: int | None = Field(None, ge=0, le=100)
    skin_temperature: float | None = Field(None, ge=30.0, le=45.0)
    steps: int | None = Field(None, ge=0)
    accel_x: float | None = None
    accel_y: float | None = None
    accel_z: float | None = None
    gyro_x: float | None = None
    gyro_y: float | None = None
    gyro_z: float | None = None
    battery_level: int | None = Field(None, ge=0, le=100)

    # Biochemical / Sweat Analysis
    cortisol_level: float | None = Field(None, ge=0.0, le=1000.0, description="nmol/L")
    lactate_level: float | None = Field(None, ge=0.0, le=30.0, description="mmol/L")
    skin_conductance: float | None = Field(None, ge=0.0, le=100.0, description="microsiemens")

    # Advanced Physiological
    ecg_value: float | None = Field(None, description="mV")
    respiration_rate: int | None = Field(None, ge=0, le=60, description="breaths/min")
    hrv_rmssd: float | None = Field(None, ge=0.0, le=500.0, description="ms")
    blood_pressure_systolic: int | None = Field(None, ge=60, le=250, description="mmHg")
    blood_pressure_diastolic: int | None = Field(None, ge=30, le=150, description="mmHg")

    # Environmental
    uv_index: float | None = Field(None, ge=0.0, le=20.0)
    pm25: float | None = Field(None, ge=0.0, le=500.0, description="ug/m3")
    voc_level: float | None = Field(None, ge=0.0, le=5000.0, description="ppb")
    barometric_pressure: float | None = Field(None, ge=800.0, le=1100.0, description="hPa")
    ambient_light: float | None = Field(None, ge=0.0, le=100000.0, description="lux")
    humidity: float | None = Field(None, ge=0.0, le=100.0, description="percent")
    ambient_temperature: float | None = Field(None, ge=-40.0, le=60.0, description="celsius")

    # Biomechanical
    body_orientation: str | None = Field(None, description="standing/sitting/lying/running")
    gait_symmetry: float | None = Field(None, ge=0.0, le=1.0, description="ratio 0-1")
    fall_detected: bool | None = None


class TelemetryIngest(BaseModel):
    readings: list[TelemetryBase] = Field(..., min_length=1, max_length=100)


class TelemetryResponse(TelemetryBase):
    id: uuid.UUID
    device_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TelemetryBatchResponse(BaseModel):
    accepted: int
    rejected: int
    message: str
