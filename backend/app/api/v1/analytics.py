"""ParkFlow AI — Analytics API"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.parking_slot import ParkingSlot
from app.models.sensor_event import SensorEvent
from app.models.floor import Floor
from app.models.enums import SlotStatus

router = APIRouter()


@router.get("/overview")
async def analytics_overview(db: AsyncSession = Depends(get_db)):
    """High-level parking analytics overview."""
    # Overall slot counts
    total = await db.execute(select(func.count(ParkingSlot.id)))
    available = await db.execute(
        select(func.count(ParkingSlot.id)).where(ParkingSlot.status == SlotStatus.available)
    )
    occupied = await db.execute(
        select(func.count(ParkingSlot.id)).where(ParkingSlot.status == SlotStatus.occupied)
    )
    reserved = await db.execute(
        select(func.count(ParkingSlot.id)).where(ParkingSlot.status == SlotStatus.reserved)
    )

    total_count = total.scalar() or 0
    available_count = available.scalar() or 0
    occupied_count = occupied.scalar() or 0
    reserved_count = reserved.scalar() or 0
    in_use = occupied_count + reserved_count
    occupancy_pct = round(in_use / total_count * 100, 1) if total_count else 0

    # Recent events count (last hour)
    one_hour_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    recent_events = await db.execute(
        select(func.count(SensorEvent.id)).where(SensorEvent.event_timestamp >= one_hour_ago)
    )
    recent_count = recent_events.scalar() or 0

    return {
        "total_slots": total_count,
        "available": available_count,
        "occupied": occupied_count,
        "reserved": reserved_count,
        "occupancy_percentage": occupancy_pct,
        "recent_events_1h": recent_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/floors")
async def analytics_by_floor(db: AsyncSession = Depends(get_db)):
    """Occupancy breakdown per floor for charts."""
    result = await db.execute(
        select(Floor.floor_number, Floor.name, ParkingSlot.status, func.count(ParkingSlot.id))
        .join(ParkingSlot, Floor.id == ParkingSlot.floor_id)
        .group_by(Floor.floor_number, Floor.name, ParkingSlot.status)
        .order_by(Floor.floor_number)
    )
    rows = result.all()

    floors_data: dict = {}
    for floor_num, floor_name, status, count in rows:
        if floor_num not in floors_data:
            floors_data[floor_num] = {
                "floor_number": floor_num,
                "name": floor_name,
                "available": 0,
                "occupied": 0,
                "reserved": 0,
                "total": 0,
            }
        key = status.value if hasattr(status, "value") else status
        floors_data[floor_num][key] = count
        floors_data[floor_num]["total"] += count

    chart_data = []
    for fn, data in sorted(floors_data.items()):
        total = data["total"]
        chart_data.append({
            **data,
            "occupancy_percentage": round(
                (data.get("occupied", 0) + data.get("reserved", 0)) / total * 100, 1
            ) if total else 0,
        })

    return {"floors": chart_data}


@router.get("/activity")
async def analytics_activity(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve"),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Recent sensor event activity for the activity timeline."""
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    result = await db.execute(
        select(SensorEvent, ParkingSlot.slot_code, Floor.floor_number)
        .join(ParkingSlot, SensorEvent.parking_slot_id == ParkingSlot.id)
        .join(Floor, ParkingSlot.floor_id == Floor.id)
        .where(SensorEvent.event_timestamp >= since)
        .order_by(desc(SensorEvent.event_timestamp))
        .limit(limit)
    )
    rows = result.all()

    return {
        "activity": [
            {
                "id": e.id,
                "slot_code": slot_code,
                "floor_number": floor_num,
                "occupancy_state": e.occupancy_state.value,
                "source": e.source.value,
                "event_timestamp": e.event_timestamp.isoformat(),
            }
            for e, slot_code, floor_num in rows
        ],
        "count": len(rows),
        "hours": hours,
    }


@router.get("/hourly")
async def analytics_hourly(
    hours: int = Query(default=12, ge=1, le=48),
    db: AsyncSession = Depends(get_db),
):
    """Hourly occupancy event counts for time-series chart."""
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    result = await db.execute(
        select(SensorEvent.event_timestamp, SensorEvent.occupancy_state)
        .where(SensorEvent.event_timestamp >= since)
        .order_by(SensorEvent.event_timestamp)
    )
    events = result.all()

    # Bucket by hour
    buckets: dict = {}
    for ts, state in events:
        hour_key = ts.strftime("%Y-%m-%dT%H:00:00")
        if hour_key not in buckets:
            buckets[hour_key] = {"hour": hour_key, "occupied": 0, "available": 0, "total": 0}
        sval = state.value if hasattr(state, "value") else state
        if sval in ("occupied", "reserved"):
            buckets[hour_key]["occupied"] += 1
        else:
            buckets[hour_key]["available"] += 1
        buckets[hour_key]["total"] += 1

    return {
        "hourly": list(buckets.values()),
        "hours": hours,
    }
