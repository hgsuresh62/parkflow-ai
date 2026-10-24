"""ParkFlow AI — IoT API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.sensor import Sensor
from app.models.sensor_event import SensorEvent
from app.models.parking_slot import ParkingSlot
from app.models.enums import SlotStatus, EventSource
from app.services.occupancy import occupancy_service
from app.iot.simulator import simulator_service
from app.core.config import settings

router = APIRouter()


class SensorEventRequest(BaseModel):
    slot_code: str
    distance_cm: Optional[float] = None
    occupancy_state: str = Field(..., description="'occupied' or 'available'")
    source: str = "manual"
    sensor_uid: Optional[str] = None


class SimulationTriggerRequest(BaseModel):
    slot_code: str
    event_type: str = Field(..., description="'arrive' or 'depart'")


@router.post("/events")
async def ingest_sensor_event(body: SensorEventRequest, db: AsyncSession = Depends(get_db)):
    """Ingest a sensor event from any provider."""
    try:
        status = SlotStatus(body.occupancy_state)
    except ValueError:
        raise HTTPException(400, f"Invalid occupancy_state: {body.occupancy_state}")

    try:
        source = EventSource(body.source)
    except ValueError:
        source = EventSource.manual

    slot = await occupancy_service.process_sensor_event(
        slot_code=body.slot_code,
        distance_cm=body.distance_cm,
        new_status=status,
        source=source,
        sensor_uid=body.sensor_uid,
        session=db,
    )

    if not slot:
        raise HTTPException(404, f"Slot '{body.slot_code}' not found")

    return {
        "accepted": True,
        "slot_code": body.slot_code,
        "new_status": status.value,
        "source": source.value,
    }


@router.get("/sensors")
async def list_sensors(db: AsyncSession = Depends(get_db)):
    """List all sensors with their current status."""
    result = await db.execute(
        select(Sensor, ParkingSlot.slot_code)
        .join(ParkingSlot, Sensor.parking_slot_id == ParkingSlot.id, isouter=True)
        .order_by(Sensor.sensor_uid)
    )
    rows = result.all()

    return {
        "sensors": [
            {
                "id": s.id,
                "sensor_uid": s.sensor_uid,
                "sensor_type": s.sensor_type,
                "slot_code": slot_code,
                "provider": s.provider.value,
                "status": s.status.value,
                "last_distance_cm": s.last_distance_cm,
                "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
                "meta_data": s.meta_data,
            }
            for s, slot_code in rows
        ],
        "total": len(rows),
        "online": sum(1 for s, _ in rows if s.status.value == "online"),
    }


@router.get("/events")
async def list_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get recent sensor events."""
    result = await db.execute(
        select(SensorEvent, ParkingSlot.slot_code)
        .join(ParkingSlot, SensorEvent.parking_slot_id == ParkingSlot.id)
        .order_by(desc(SensorEvent.event_timestamp))
        .limit(min(limit, 200))
    )
    rows = result.all()

    return {
        "events": [
            {
                "id": e.id,
                "slot_code": slot_code,
                "occupancy_state": e.occupancy_state.value,
                "raw_distance_cm": e.raw_distance_cm,
                "source": e.source.value,
                "event_timestamp": e.event_timestamp.isoformat(),
            }
            for e, slot_code in rows
        ],
        "total": len(rows),
    }


@router.post("/simulation/start")
async def start_simulation(interval_s: float = 5.0):
    """Start the IoT simulator."""
    if simulator_service._running:
        return {"status": "already_running", **simulator_service.get_status()}

    import asyncio
    asyncio.create_task(simulator_service.start_background(interval_s))
    return {"status": "starting", "interval_s": interval_s}


@router.post("/simulation/stop")
async def stop_simulation():
    """Stop the IoT simulator."""
    await simulator_service.stop()
    return {"status": "stopped"}


@router.get("/simulation/status")
async def simulation_status():
    """Get the current simulator status."""
    return simulator_service.get_status()


@router.post("/simulation/trigger")
async def trigger_simulation_event(body: SimulationTriggerRequest):
    """Manually trigger a specific slot event."""
    if body.event_type == "arrive":
        result = await simulator_service.trigger_arrival(body.slot_code)
    elif body.event_type == "depart":
        result = await simulator_service.trigger_departure(body.slot_code)
    else:
        raise HTTPException(400, f"Invalid event_type: {body.event_type}. Use 'arrive' or 'depart'")

    return result


@router.post("/simulation/demo")
async def start_demo(target_slot: Optional[str] = None):
    """Start the predictable hackathon demo sequence."""
    result = await simulator_service.start_demo(target_slot)
    return result


@router.post("/simulation/stress")
async def toggle_stress(enabled: bool = True):
    """Toggle stress test mode."""
    await simulator_service.set_stress_mode(enabled)
    return {"stress_mode": enabled, "interval_s": simulator_service._interval_s}
