import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.device import Device
from app.models.telemetry import Telemetry
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/{device_id}/health-summary")
async def get_health_summary(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=90),
):
    result = await db.execute(
        select(Device).where(
            Device.id == uuid.UUID(device_id), Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    from datetime import timedelta

    cutoff = func.now() - timedelta(days=days)

    result = await db.execute(
        select(
            func.avg(Telemetry.heart_rate).label("avg_heart_rate"),
            func.min(Telemetry.heart_rate).label("min_heart_rate"),
            func.max(Telemetry.heart_rate).label("max_heart_rate"),
            func.avg(Telemetry.sp_o2).label("avg_sp_o2"),
            func.avg(Telemetry.skin_temperature).label("avg_temperature"),
            func.sum(Telemetry.steps).label("total_steps"),
            func.count(Telemetry.id).label("total_readings"),
        ).where(
            Telemetry.device_id == device.id,
            Telemetry.created_at >= cutoff,
        )
    )
    row = result.one()
    return {
        "device_id": device.id,
        "period_days": days,
        "avg_heart_rate": float(row.avg_heart_rate) if row.avg_heart_rate else None,
        "min_heart_rate": row.min_heart_rate,
        "max_heart_rate": row.max_heart_rate,
        "avg_sp_o2": float(row.avg_sp_o2) if row.avg_sp_o2 else None,
        "avg_temperature": float(row.avg_temperature) if row.avg_temperature else None,
        "total_steps": row.total_steps or 0,
        "total_readings": row.total_readings or 0,
    }


@router.get("/{device_id}/location-history")
async def get_location_history(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
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
        select(Telemetry.latitude, Telemetry.longitude, Telemetry.timestamp, Telemetry.speed)
        .where(
            Telemetry.device_id == device.id,
            Telemetry.latitude.isnot(None),
            Telemetry.longitude.isnot(None),
        )
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
    )
    locations = [
        {"latitude": row.latitude, "longitude": row.longitude, "timestamp": row.timestamp, "speed": row.speed}
        for row in result.all()
    ]
    return {"device_id": device.id, "locations": locations}


@router.get("/{device_id}/activity")
async def get_activity_breakdown(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=90),
):
    result = await db.execute(
        select(Device).where(
            Device.id == uuid.UUID(device_id), Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    from datetime import timedelta

    cutoff = func.now() - timedelta(days=days)

    result = await db.execute(
        select(
            func.sum(Telemetry.steps).label("total_steps"),
            func.avg(Telemetry.speed).label("avg_speed"),
            func.max(Telemetry.speed).label("max_speed"),
            func.count(Telemetry.id).label("total_readings"),
        ).where(
            Telemetry.device_id == device.id,
            Telemetry.created_at >= cutoff,
        )
    )
    row = result.one()
    return {
        "device_id": device.id,
        "period_days": days,
        "total_steps": row.total_steps or 0,
        "avg_speed": float(row.avg_speed) if row.avg_speed else None,
        "max_speed": float(row.max_speed) if row.max_speed else None,
        "total_readings": row.total_readings or 0,
    }
