"""
IntelliTrace Demo Data Seeder — Enhanced
Generates rich, realistic pseudo telemetry data for ALL advanced sensor fields.
Run: .venv\Scripts\python.exe seed_demo.py
"""
import asyncio
import math
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


def circadian_curve(hour, peak_hour, amplitude, base):
    """Generate a realistic circadian curve peaking at peak_hour."""
    angle = ((hour - peak_hour) / 24) * 2 * math.pi
    return base + amplitude * math.cos(angle)


def generate_telemetry(base_time: datetime, day_index: int, user_profile: dict):
    hour = base_time.hour + base_time.minute / 60.0
    is_night = hour < 6 or hour >= 22
    is_morning = 6 <= hour <= 10
    is_active = 8 <= hour <= 18
    is_afternoon = 12 <= hour <= 17

    profile = user_profile

    # =====================================================================
    # CORE VITALS
    # =====================================================================
    hr_base = circadian_curve(hour, peak_hour=8, amplitude=8, base=profile["hr_resting"])
    if is_active:
        hr_base += random.uniform(0, 20)
    if is_night:
        hr_base -= 5

    # Simulate occasional anomalies (every ~25th reading)
    anomaly = random.random() < 0.04
    if anomaly:
        hr_base += random.uniform(30, 60)

    heart_rate = max(45, min(180, int(hr_base + random.gauss(0, 3))))
    pulse_rate = heart_rate + random.randint(-2, 2)

    sp_o2 = int(max(93, min(100, random.gauss(97.5, 1.2))))
    if anomaly:
        sp_o2 = int(max(85, min(93, random.gauss(90, 2))))

    skin_temp = round(random.gauss(36.5, 0.3), 1)
    if is_night:
        skin_temp -= 0.3
    if anomaly:
        skin_temp = round(random.gauss(38.5, 0.5), 1)

    # =====================================================================
    # LOCATION & MOTION
    # =====================================================================
    base_lat = profile["base_lat"]
    base_lon = profile["base_lon"]

    if is_active and random.random() > 0.3:
        lat = base_lat + random.gauss(0, 0.01)
        lon = base_lon + random.gauss(0, 0.01)
        speed = round(abs(random.gauss(1.5, 1.0)), 2)
    elif is_night:
        lat = base_lat + random.gauss(0, 0.001)
        lon = base_lon + random.gauss(0, 0.001)
        speed = 0.0
    else:
        lat = base_lat + random.gauss(0, 0.003)
        lon = base_lon + random.gauss(0, 0.003)
        speed = round(abs(random.gauss(0.5, 0.3)), 2)

    altitude = round(random.uniform(200, 220), 1)

    steps_acc = profile.get("steps_acc", 0)
    if is_active:
        steps_acc += random.randint(1, 5)
    profile["steps_acc"] = steps_acc

    accel_noise = 0.3 if is_active else 0.05
    accel_x = round(random.gauss(0, accel_noise), 3)
    accel_y = round(random.gauss(0, accel_noise), 3)
    accel_z = round(random.gauss(9.8, 0.2), 3)

    gyro_x = round(random.gauss(0, 0.08), 3)
    gyro_y = round(random.gauss(0, 0.08), 3)
    gyro_z = round(random.gauss(0, 0.08), 3)

    battery = max(5, 100 - (day_index * 3 + random.randint(0, 10)))

    # =====================================================================
    # BIOCHEMICAL / SWEAT ANALYSIS
    # =====================================================================
    # Cortisol: peaks 6-8 AM, lowest midnight, influenced by stress
    cortisol = circadian_curve(hour, peak_hour=7, amplitude=200, base=profile["cortisol_base"])
    cortisol += random.gauss(0, 30)
    if anomaly:
        cortisol += random.uniform(100, 200)
    cortisol = round(max(20, min(700, cortisol)), 1)

    # Lactate: low at rest, rises during exercise
    if is_active and speed > 2.0:
        lactate = round(random.gauss(4.5, 1.5), 2)
    elif is_active:
        lactate = round(random.gauss(2.0, 0.8), 2)
    else:
        lactate = round(random.gauss(1.0, 0.3), 2)
    lactate = max(0.3, min(20.0, lactate))

    # Skin conductance (EDA/GSR): varies with stress, time of day
    eda_base = profile["eda_base"]
    if is_night:
        eda_base *= 0.4
    elif is_active:
        eda_base *= 1.2
    skin_conductance = round(max(0.5, min(60, random.gauss(eda_base, 4))), 2)
    if anomaly:
        skin_conductance += random.uniform(8, 20)

    # =====================================================================
    # ADVANCED PHYSIOLOGICAL
    # =====================================================================
    # ECG (simplified amplitude)
    ecg = round(random.gauss(1.2, 0.15), 3)
    ecg = max(0.5, min(2.5, ecg))

    # Respiration rate
    if is_night:
        resp_rate = random.randint(10, 14)
    elif is_active:
        resp_rate = random.randint(16, 24)
    else:
        resp_rate = random.randint(12, 18)

    # HRV RMSSD: higher = more relaxed / recovered
    hrv_base = profile["hrv_base"]
    if is_night:
        hrv_base += 20
    elif is_active:
        hrv_base -= 10
    hrv_rmssd = round(max(5, min(150, random.gauss(hrv_base, 8))), 1)
    if anomaly:
        hrv_rmssd = round(max(5, hrv_rmssd * 0.3), 1)

    # Blood pressure
    bp_sys_base = profile["bp_systolic"]
    bp_dia_base = profile["bp_diastolic"]
    if is_active:
        bp_sys_base += 10
        bp_dia_base += 5
    if anomaly:
        bp_sys_base += 30
        bp_dia_base += 15
    bp_sys = max(90, min(200, int(bp_sys_base + random.gauss(0, 8))))
    bp_dia = max(55, min(120, int(bp_dia_base + random.gauss(0, 5))))

    # =====================================================================
    # ENVIRONMENTAL
    # =====================================================================
    # UV index: follows sun pattern
    if is_night:
        uv = 0.0
    elif 10 <= hour <= 14:
        uv = round(random.gauss(7, 2), 1)
    elif 7 <= hour <= 17:
        uv = round(random.gauss(3, 1.5), 1)
    else:
        uv = round(random.uniform(0, 1), 1)
    uv = max(0, min(14, uv))

    # PM2.5: urban baseline with occasional spikes
    pm25 = round(random.gauss(profile["pm25_baseline"], 15), 1)
    if random.random() < 0.05:
        pm25 += random.uniform(40, 80)
    pm25 = max(5, min(300, pm25))

    # VOC: indoor/outdoor variation
    voc = round(random.gauss(profile["voc_baseline"], 80), 0)
    if random.random() < 0.03:
        voc += random.uniform(200, 400)
    voc = max(20, min(2000, voc))

    # Barometric pressure: slow drift over days
    baro_drift = 1013 + 5 * math.sin(day_index * 0.3)
    barometric_pressure = round(baro_drift + random.gauss(0, 2), 1)
    barometric_pressure = max(995, min(1035, barometric_pressure))

    # Ambient light
    if is_night:
        ambient_light = round(random.uniform(0, 30), 0)
    elif 10 <= hour <= 15:
        ambient_light = round(random.gauss(50000, 15000), 0)
    elif 7 <= hour <= 18:
        ambient_light = round(random.gauss(15000, 8000), 0)
    else:
        ambient_light = round(random.uniform(100, 2000), 0)
    ambient_light = max(0, min(100000, ambient_light))

    # Humidity
    humidity = round(random.gauss(profile["humidity_baseline"], 8), 1)
    if is_night:
        humidity += 5
    humidity = max(15, min(90, humidity))

    # Ambient temperature
    ambient_temp = round(random.gauss(profile["temp_baseline"], 3), 1)
    ambient_temp = max(-5, min(50, ambient_temp))

    # =====================================================================
    # BIOMECHANICAL
    # =====================================================================
    if is_night:
        orientation = "lying"
    elif is_active:
        if speed > 4:
            orientation = "running"
        elif speed > 1:
            orientation = "walking" if random.random() > 0.3 else "standing"
        else:
            orientation = random.choice(["standing", "sitting"])
    else:
        orientation = random.choice(["standing", "sitting"])

    # Gait symmetry: only meaningful when walking/running
    if orientation in ("running", "walking"):
        gait_sym = round(random.gauss(0.95, 0.03), 3)
        gait_sym = max(0.7, min(1.0, gait_sym))
    else:
        gait_sym = None

    fall = False
    if anomaly and random.random() < 0.3:
        fall = True

    # =====================================================================
    # BUILD RECORD
    # =====================================================================
    return {
        "id": str(uuid.uuid4()),
        "device_id": None,
        "timestamp": base_time.isoformat(),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "altitude": altitude,
        "speed": speed,
        "heart_rate": heart_rate,
        "pulse_rate": pulse_rate,
        "sp_o2": sp_o2,
        "skin_temperature": skin_temp,
        "steps": steps_acc,
        "accel_x": accel_x,
        "accel_y": accel_y,
        "accel_z": accel_z,
        "gyro_x": gyro_x,
        "gyro_y": gyro_y,
        "gyro_z": gyro_z,
        "battery_level": battery,
        # Biochemical
        "cortisol_level": cortisol,
        "lactate_level": lactate,
        "skin_conductance": skin_conductance,
        # Advanced Physiological
        "ecg_value": ecg,
        "respiration_rate": resp_rate,
        "hrv_rmssd": hrv_rmssd,
        "blood_pressure_systolic": bp_sys,
        "blood_pressure_diastolic": bp_dia,
        # Environmental
        "uv_index": uv,
        "pm25": pm25,
        "voc_level": voc,
        "barometric_pressure": barometric_pressure,
        "ambient_light": ambient_light,
        "humidity": humidity,
        "ambient_temperature": ambient_temp,
        # Biomechanical
        "body_orientation": orientation,
        "gait_symmetry": gait_sym,
        "fall_detected": fall,
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

        # =================================================================
        # USER PROFILES — Each device has a different "person"
        # =================================================================
        profile_1 = {
            "base_lat": 28.6139,
            "base_lon": 77.2090,
            "hr_resting": 65,
            "cortisol_base": 250,
            "eda_base": 12,
            "hrv_base": 45,
            "bp_systolic": 118,
            "bp_diastolic": 75,
            "pm25_baseline": 55,
            "voc_baseline": 300,
            "humidity_baseline": 45,
            "temp_baseline": 28,
            "steps_acc": 0,
        }

        profile_2 = {
            "base_lat": 28.6200,
            "base_lon": 77.2150,
            "hr_resting": 72,
            "cortisol_base": 280,
            "eda_base": 15,
            "hrv_base": 38,
            "bp_systolic": 125,
            "bp_diastolic": 80,
            "pm25_baseline": 70,
            "voc_baseline": 350,
            "humidity_baseline": 50,
            "temp_baseline": 26,
            "steps_acc": 0,
        }

        # =================================================================
        # GENERATE 5 DAYS OF DATA (one reading every 30 minutes)
        # =================================================================
        now_time = datetime.now(timezone.utc)
        start_time = now_time - timedelta(days=5)
        readings = []

        # Device 1: 5 days x 48 readings/day = 240 readings
        for i in range(240):
            ts = start_time + timedelta(minutes=i * 30)
            day_index = i // 48
            reading = generate_telemetry(ts, day_index, profile_1)
            reading["device_id"] = device1_id
            readings.append(reading)

        # Device 2: 3 days x 48 readings/day = 144 readings
        for i in range(144):
            ts = start_time + timedelta(minutes=i * 30)
            day_index = i // 48
            reading = generate_telemetry(ts, day_index, profile_2)
            reading["device_id"] = device2_id
            readings.append(reading)

        # =================================================================
        # INSERT ALL READINGS
        # =================================================================
        insert_sql = text("""
            INSERT INTO telemetry (id, device_id, timestamp, latitude, longitude, altitude, speed,
                heart_rate, pulse_rate, sp_o2, skin_temperature, steps,
                accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,
                battery_level,
                cortisol_level, lactate_level, skin_conductance,
                ecg_value, respiration_rate, hrv_rmssd,
                blood_pressure_systolic, blood_pressure_diastolic,
                uv_index, pm25, voc_level, barometric_pressure,
                ambient_light, humidity, ambient_temperature,
                body_orientation, gait_symmetry, fall_detected,
                created_at, updated_at)
            VALUES (:id, :device_id, :timestamp, :latitude, :longitude, :altitude, :speed,
                :heart_rate, :pulse_rate, :sp_o2, :skin_temperature, :steps,
                :accel_x, :accel_y, :accel_z, :gyro_x, :gyro_y, :gyro_z,
                :battery_level,
                :cortisol_level, :lactate_level, :skin_conductance,
                :ecg_value, :respiration_rate, :hrv_rmssd,
                :blood_pressure_systolic, :blood_pressure_diastolic,
                :uv_index, :pm25, :voc_level, :barometric_pressure,
                :ambient_light, :humidity, :ambient_temperature,
                :body_orientation, :gait_symmetry, :fall_detected,
                :created_at, :created_at)
        """)

        for r in readings:
            await db.execute(insert_sql, r)

        # =================================================================
        # ALERTS
        # =================================================================
        alert_templates = [
            ("HEALTH_ANOMALY", "HIGH", "Abnormally high heart rate detected: {val} bpm"),
            ("UNUSUAL_LOCATION", "MEDIUM", "Device detected outside usual geofence area"),
            ("BATTERY_CRITICAL", "CRITICAL", "Battery level critically low: {val}%"),
            ("DEVICE_NOT_WORN", "LOW", "Device appears to not be worn for extended period"),
            ("UNAUTHORIZED_WEARER", "HIGH", "Biometric verification failed - possible unauthorized wearer"),
            ("HEALTH_ANOMALY", "MEDIUM", "SpO2 level dropped below normal: {val}%"),
            ("HEALTH_ANOMALY", "CRITICAL", "Elevated skin temperature detected: {val} C"),
            ("BATTERY_CRITICAL", "LOW", "Battery below 30%: {val}%"),
            ("UNUSUAL_LOCATION", "HIGH", "Rapid movement detected outside known routes"),
            ("DEVICE_NOT_WORN", "MEDIUM", "No motion detected for 2+ hours during daytime"),
        ]

        for i, (atype, severity, msg) in enumerate(alert_templates):
            val = (
                random.randint(85, 93) if "SpO2" in msg
                else random.randint(120, 160) if "heart" in msg.lower() or "bpm" in msg
                else random.randint(8, 25) if "Battery" in atype
                else random.randint(38, 40)
            )
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

        print("=" * 60)
        print("  IntelliTrace Enhanced Demo Data Seeded Successfully!")
        print("=" * 60)
        print(f"  User:      demo@intellitrace.com")
        print(f"  Password:  Demo@1234")
        print(f"  Device 1:  IntelliWatch Pro #1 ({len(readings[:240])} readings)")
        print(f"  Device 2:  IntelliWatch Pro #2 ({len(readings[240:])} readings)")
        print(f"  Total:     {len(readings)} telemetry records (5 days)")
        print(f"  Alerts:    {len(alert_templates)} alerts")
        print()
        print("  Sensor fields populated:")
        print("    Core:     HR, Pulse, SpO2, Skin Temp, Steps, Accel, Gyro, Battery")
        print("    Bio:      Cortisol, Lactate, EDA/GSR")
        print("    Physio:   ECG, Respiration, HRV, Blood Pressure")
        print("    Environ:  UV, PM2.5, VOC, Barometric, Light, Humidity, Temp")
        print("    BioMech:  Body Orientation, Gait Symmetry, Fall Detection")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
