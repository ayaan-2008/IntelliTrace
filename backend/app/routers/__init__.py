from app.routers.auth import auth_router
from app.routers.users import users_router
from app.routers.devices import devices_router
from app.routers.telemetry import telemetry_router
from app.routers.analytics import analytics_router
from app.routers.alerts import alerts_router

__all__ = [
    "auth_router",
    "users_router",
    "devices_router",
    "telemetry_router",
    "analytics_router",
    "alerts_router",
]
