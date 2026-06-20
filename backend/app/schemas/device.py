import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    device_serial: str = Field(..., min_length=1, max_length=100)
    device_name: str = Field(..., min_length=1, max_length=100)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_name: str | None = None
    firmware_version: str | None = None


class DeviceResponse(DeviceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    firmware_version: str | None
    paired_at: datetime | None
    last_seen: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DevicePairRequest(BaseModel):
    device_serial: str
    pairing_token: str


class DeviceStatusResponse(BaseModel):
    device_id: uuid.UUID
    is_online: bool
    last_seen: datetime | None
    battery_level: int | None
