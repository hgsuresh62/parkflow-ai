"""ParkFlow AI — API v1 Router"""
from fastapi import APIRouter
from app.api.v1 import health, floors, slots, routes, reservations, sessions, iot, analytics

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(floors.router, prefix="/floors", tags=["Floors"])
api_router.include_router(slots.router, prefix="/slots", tags=["Slots"])
api_router.include_router(routes.router, prefix="/routes", tags=["Routing"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(iot.router, prefix="/iot", tags=["IoT"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
