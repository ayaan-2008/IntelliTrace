import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.device import Device
from app.models.telemetry import Telemetry
from app.models.user import User
from app.schemas.telemetry import TelemetryBatchResponse, TelemetryIngest, TelemetryResponse

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/ingest", response_model=TelemetryBatchResponse)
async def ingest_telemetry(
    data: TelemetryIngest,
    db: AsyncSession = Depends(get_db),
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    result = await db.execute(select(Device).where(Device.api_key == x_api_key))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    now = datetime.now(timezone.utc)
    objects = []
    for reading in data.readings:
        objects.append(Telemetry(
            device_id=device.id,
            timestamp=reading.timestamp,
            latitude=reading.latitude,
            longitude=reading.longitude,
            altitude=reading.altitude,
            speed=reading.speed,
            heart_rate=reading.heart_rate,
            pulse_rate=reading.pulse_rate,
            sp_o2=reading.sp_o2,
            skin_temperature=reading.skin_temperature,
            steps=reading.steps,
            accel_x=reading.accel_x,
            accel_y=reading.accel_y,
            accel_z=reading.accel_z,
            gyro_x=reading.gyro_x,
            gyro_y=reading.gyro_y,
            gyro_z=reading.gyro_z,
            battery_level=reading.battery_level,
        ))

    db.add_all(objects)
    device.last_seen = now
    await db.flush()

    return TelemetryBatchResponse(
        accepted=len(objects),
        rejected=0,
        message=f"Processed {len(objects)} readings",
    )


@router.get("/{device_id}/latest", response_model=TelemetryResponse | None)
async def get_latest_telemetry(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).where(
            Device.id == uuid.UUID(device_id), Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    result = await db.execute(
        select(Telemetry)
        .where(Telemetry.device_id == device.id)
        .order_by(Telemetry.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/{device_id}/history", response_model=list[TelemetryResponse])
async def get_telemetry_history(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Device).where(
            Device.id == uuid.UUID(device_id), Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    result = await db.execute(
        select(Telemetry)
        .where(Telemetry.device_id == device.id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
