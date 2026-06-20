# IntelliTrace

Smart Wearable Security & Health Monitoring System with ML-powered anomaly detection and person verification.

## Features

- **User Authentication** — JWT-based register/login
- **Device Management** — Pair/unpair wearable devices
- **Telemetry Ingestion** — Batch upload vitals, GPS, motion, battery data
- **Health Analytics** — Health summaries, location history, activity tracking
- **Alerts System** — Configurable alerts for health anomalies, battery, unauthorized wearers
- **ML Models** — Anomaly detection (Autoencoder + Isolation Forest) and person verification (Siamese CNN-LSTM)
- **Streamlit Dashboard** — Interactive web UI for monitoring and management

## Project Structure

```
intellitrace/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── config/           # Settings and constants
│   │   ├── core/             # Security, dependencies, exceptions
│   │   ├── db/               # SQLAlchemy async engine and models
│   │   ├── models/           # ORM models (User, Device, Telemetry, Alert, BiometricProfile)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # Business logic (placeholder)
│   │   ├── ml/               # ML pipelines
│   │   │   ├── anomaly_detection/
│   │   │   ├── person_verification/
│   │   │   └── shared/
│   │   └── utils/            # Helpers and validators
│   ├── alembic/              # Database migrations
│   ├── tests/                # Test suite
│   ├── pyproject.toml        # Project config and dependencies
│   └── .env.example          # Environment variables template
└── dashboard/                # Streamlit dashboard
    ├── app.py                # Main entry point
    ├── api_client.py         # Backend API client
    ├── pages/                # Multi-page dashboard
    │   ├── 1_Devices.py
    │   ├── 2_Telemetry.py
    │   └── 3_Alerts.py
    ├── seed_demo.py          # Demo data seeder
    └── requirements.txt      # Dashboard dependencies
```

## Setup

### Prerequisites

- Python 3.11+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/ayaan-2008/IntelliTrace.git
cd IntelliTrace
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -e .

# Install ML dependencies (optional)
pip install -e ".[ml]"

# Create .env from template
copy .env.example .env

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Dashboard Setup

```bash
cd dashboard

# Install dependencies
pip install -r requirements.txt

# Seed demo data (optional)
python seed_demo.py

# Start the dashboard
streamlit run app.py
```

### 4. Access

- **API docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

### Demo Account (after seeding)

| Field | Value |
|-------|-------|
| Email | demo@intellitrace.com |
| Password | Demo@1234 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| POST | `/api/v1/auth/device/pair` | Pair a wearable device |
| POST | `/api/v1/auth/device/unpair/{id}` | Unpair a device |
| GET | `/api/v1/devices/` | List all devices |
| GET | `/api/v1/devices/{id}/status` | Get device online status |
| POST | `/api/v1/telemetry/ingest` | Ingest telemetry data (API key auth) |
| GET | `/api/v1/telemetry/{id}/latest` | Get latest telemetry reading |
| GET | `/api/v1/telemetry/{id}/history` | Get telemetry history |
| GET | `/api/v1/analytics/{id}/health-summary` | Health analytics |
| GET | `/api/v1/alerts/active` | Get active alerts |
| PUT | `/api/v1/alerts/{id}/resolve` | Resolve an alert |

## License

MIT
