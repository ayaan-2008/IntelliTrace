import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_model import BaseModel, GUID


class BiometricProfile(BaseModel):
    __tablename__ = "biometric_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    baseline_heart_rate_pattern: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    baseline_gait_pattern: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="biometric_profile")
    device = relationship("Device", back_populates="biometric_profile")
