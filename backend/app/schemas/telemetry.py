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
