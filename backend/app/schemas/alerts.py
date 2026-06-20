import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.alert import AlertSeverity, AlertType


class AlertResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    user_id: uuid.UUID
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    latitude: float | None
    longitude: float | None
    is_resolved: bool
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertResolve(BaseModel):
    resolved: bool = True
