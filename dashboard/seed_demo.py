"""
IntelliTrace Demo Data Seeder
Generates realistic demo data directly in the database.
Run: .venv\Scripts\python.exe seed_demo.py
"""
import asyncio
import random
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///../backend/intellitrace.db"
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def hash_password_demo():
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash("Demo@1234")


def generate_telemetry(base_time: datetime, is_anomaly: bool = False):
    hour = base_time.hour
    if 6 <= hour <= 10:
        hr_base = random.randint(70, 90)
    elif 10 < hour <= 18:
        hr_base = random.randint(65, 85)
    elif 18 < hour <= 22:
        hr_base = random.randint(60, 80)
    else:
        hr_base = random.randint(55, 70)

    if is_anomaly:
        hr_base = random.randint(110, 160)

    return {
        "id": str(uuid.uuid4()),
        "device_id": None,
        "timestamp": base_time.isoformat(),
        "latitude": 28.6139 + random.uniform(-0.05, 0.05),
        "longitude": 77.2090 + random.uniform(-0.05, 0.05),
        "altitude": random.uniform(200, 220),
        "speed": random.uniform(0, 15),
        "heart_rate": hr_base + random.randint(-5, 5),
        "pulse_rate": hr_base + random.randint(-3, 3),
        "sp_o2": random.randint(94, 99) if not is_anomaly else random.randint(85, 93),
        "skin_temperature": round(random.uniform(36.1, 37.2), 1) if not is_anomaly else round(random.uniform(37.8, 39.5), 1),
        "steps": random.randint(0, 200),
        "accel_x": round(random.uniform(-1.5, 1.5), 3),
        "accel_y": round(random.uniform(-1.5, 1.5), 3),
        "accel_z": round(random.uniform(8.5, 10.5), 3),
        "gyro_x": round(random.uniform(-1, 1), 3),
        "gyro_y": round(random.uniform(-1, 1), 3),
        "gyro_z": round(random.uniform(-1, 1), 3),
        "battery_level": random.randint(20, 100),
        "created_at": base_time.isoformat(),
    }


async def seed():
    async with Session() as db:
        await db.execute(text("DELETE FROM telemetry"))
        await db.execute(text("DELETE FROM alerts"))
        await db.execute(text("DELETE FROM biometric_profiles"))
        await db.execute(text("DELETE FROM devices"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()

        user_id = str(uuid.uuid4())
        device1_id = str(uuid.uuid4())
        device2_id = str(uuid.uuid4())

        hashed = hash_password_demo()

        await db.execute(text("""
            INSERT INTO users (id, email, full_name, hashed_password, phone, emergency_contact, is_active, created_at, updated_at)
            VALUES (:id, :email, :name, :pw, :phone, :emergency, 1, :now, :now)
        """), {
            "id": user_id,
            "email": "demo@intellitrace.com",
            "name": "Demo User",
            "pw": hashed,
            "phone": "+91-9876543210",
            "emergency": "emergency@contact.com",
            "now": datetime.now(timezone.utc).isoformat(),
        })

        api_key1 = secrets.token_hex(32)
        api_key2 = secrets.token_hex(32)
        now = datetime.now(timezone.utc)

        await db.execute(text("""
            INSERT INTO devices (id, user_id, device_serial, device_name, firmware_version, paired_at, last_seen, api_key, created_at, updated_at)
            VALUES (:id, :uid, :serial, :name, :fw, :paired, :last, :key, :now, :now)
        """), {
            "id": device1_id, "uid": user_id,
            "serial": "IW-2024-DEMO-001",
            "name": "IntelliWatch Pro #1",
            "fw": "v2.4.1",
            "paired": (now - timedelta(days=30)).isoformat(),
            "last": now.isoformat(),
            "key": api_key1,
            "now": now.isoformat(),
        })

        await db.execute(text("""
            INSERT INTO devices (id, user_id, device_serial, device_name, firmware_version, paired_at, last_seen, api_key, created_at, updated_at)
            VALUES (:id, :uid, :serial, :name, :fw, :paired, :last, :key, :now, :now)
        """), {
            "id": device2_id, "uid": user_id,
            "serial": "IW-2024-DEMO-002",
            "name": "IntelliWatch Pro #2",
            "fw": "v2.3.8",
            "paired": (now - timedelta(days=15)).isoformat(),
            "last": (now - timedelta(hours=3)).isoformat(),
            "key": api_key2,
            "now": now.isoformat(),
        })

        now_time = datetime.now(timezone.utc)
        readings = []
        for i in range(150):
            ts = now_time - timedelta(hours=i * 0.5)
            is_anomaly = (i % 25 == 0)
            reading = generate_telemetry(ts, is_anomaly)
            reading["device_id"] = device1_id
            readings.append(reading)

        for i in range(80):
            ts = now_time - timedelta(hours=i * 0.5)
            reading = generate_telemetry(ts, is_anomaly=False)
            reading["device_id"] = device2_id
            readings.append(reading)

        for r in readings:
            await db.execute(text("""
                INSERT INTO telemetry (id, device_id, timestamp, latitude, longitude, altitude, speed,
                    heart_rate, pulse_rate, sp_o2, skin_temperature, steps,
                    accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,
                    battery_level, created_at, updated_at)
                VALUES (:id, :device_id, :timestamp, :latitude, :longitude, :altitude, :speed,
                    :heart_rate, :pulse_rate, :sp_o2, :skin_temperature, :steps,
                    :accel_x, :accel_y, :accel_z, :gyro_x, :gyro_y, :gyro_z,
                    :battery_level, :created_at, :created_at)
            """), r)

        alert_templates = [
            ("HEALTH_ANOMALY", "HIGH", "Abnormally high heart rate detected: {val} bpm"),
            ("UNUSUAL_LOCATION", "MEDIUM", "Device detected outside usual geofence area"),
            ("BATTERY_CRITICAL", "CRITICAL", "Battery level critically low: {val}%"),
            ("DEVICE_NOT_WORN", "LOW", "Device appears to not be worn for extended period"),
            ("UNAUTHORIZED_WEARER", "HIGH", "Biometric verification failed - possible unauthorized wearer"),
            ("HEALTH_ANOMALY", "MEDIUM", "SpO2 level dropped below normal: {val}%"),
            ("HEALTH_ANOMALY", "CRITICAL", "Elevated skin temperature detected: {val}°C"),
            ("BATTERY_CRITICAL", "LOW", "Battery below 30%: {val}%"),
            ("UNUSUAL_LOCATION", "HIGH", "Rapid movement detected outside known routes"),
            ("DEVICE_NOT_WORN", "MEDIUM", "No motion detected for 2+ hours during daytime"),
        ]

        for i, (atype, severity, msg) in enumerate(alert_templates):
            val = random.randint(85, 99) if "SpO2" in msg else random.randint(110, 160) if "heart" in msg.lower() or "bpm" in msg else random.randint(10, 25) if "Battery" in atype else random.randint(37, 39)
            alert_msg = msg.format(val=val)
            created = now_time - timedelta(hours=random.randint(1, 72))
            is_resolved = i > 5

            await db.execute(text("""
                INSERT INTO alerts (id, device_id, user_id, alert_type, severity, message,
                    latitude, longitude, is_resolved, resolved_at, created_at, updated_at)
                VALUES (:id, :did, :uid, :atype, :sev, :msg, :lat, :lng, :resolved, :rtime, :cat, :cat)
            """), {
                "id": str(uuid.uuid4()),
                "did": device1_id if i < 7 else device2_id,
                "uid": user_id,
                "atype": atype,
                "sev": severity,
                "msg": alert_msg,
                "lat": 28.6139 + random.uniform(-0.05, 0.05),
                "lng": 77.2090 + random.uniform(-0.05, 0.05),
                "resolved": 1 if is_resolved else 0,
                "rtime": created.isoformat() if is_resolved else None,
                "cat": created.isoformat(),
            })

        await db.commit()

        print("=" * 50)
        print("  IntelliTrace Demo Data Seeded Successfully!")
        print("=" * 50)
        print(f"  User:     demo@intellitrace.com")
        print(f"  Password: Demo@1234")
        print(f"  Devices:  2 (IntelliWatch Pro #1 & #2)")
        print(f"  Telemetry: {len(readings)} readings")
        print(f"  Alerts:   {len(alert_templates)} alerts")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
