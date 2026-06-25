import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_model import BaseModel, GUID


class Telemetry(BaseModel):
    __tablename__ = "telemetry"

    device_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Vitals
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pulse_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sp_o2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skin_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Activity
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Motion
    accel_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    accel_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    accel_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_z: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Device status
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Biochemical / Sweat Analysis
    cortisol_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    lactate_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    skin_conductance: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Advanced Physiological
    ecg_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    respiration_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hrv_rmssd: Mapped[float | None] = mapped_column(Float, nullable=True)
    blood_pressure_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Environmental
    uv_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    voc_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    barometric_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_light: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Biomechanical
    body_orientation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gait_symmetry: Mapped[float | None] = mapped_column(Float, nullable=True)
    fall_detected: Mapped[bool | None] = mapped_column(nullable=True)

    # Relationships
    device = relationship("Device", back_populates="telemetry")
