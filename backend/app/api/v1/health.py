"""ParkFlow AI — Health Endpoints"""
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.websocket.manager import ws_manager

router = APIRouter()


@router.get("")
@router.get("/")
async def health_check():
    """Application health check."""
    return {
        "status": "ok",
        "service": "ParkFlow AI Backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.APP_ENV,
        "websocket_clients": ws_manager.client_count,
    }


@router.get("/config")
async def get_config():
    """Return non-sensitive application configuration."""
    return {
        "iot_mode": settings.IOT_MODE,
        "simulation_interval_s": settings.SIMULATION_INTERVAL_SECONDS,
        "occupancy_threshold_cm": settings.OCCUPANCY_THRESHOLD_CM,
        "thingspeak_enabled": settings.thingspeak_enabled,
        "mqtt_enabled": settings.mqtt_enabled,
        "debug": settings.DEBUG,
    }
