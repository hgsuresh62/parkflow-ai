"""ParkFlow AI — Floors API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.floor import Floor
from app.models.parking_slot import ParkingSlot
from app.models.enums import SlotStatus

router = APIRouter()


@router.get("")
async def list_floors(db: AsyncSession = Depends(get_db)):
    """List all parking floors with occupancy statistics."""
    result = await db.execute(select(Floor).order_by(Floor.floor_number))
    floors = result.scalars().all()

    response = []
    for floor in floors:
        # Get slot counts
        total = await db.execute(
            select(func.count(ParkingSlot.id)).where(ParkingSlot.floor_id == floor.id)
        )
        available = await db.execute(
            select(func.count(ParkingSlot.id)).where(
                ParkingSlot.floor_id == floor.id,
                ParkingSlot.status == SlotStatus.available
            )
        )
        occupied = await db.execute(
            select(func.count(ParkingSlot.id)).where(
                ParkingSlot.floor_id == floor.id,
                ParkingSlot.status == SlotStatus.occupied
            )
        )
        reserved = await db.execute(
            select(func.count(ParkingSlot.id)).where(
                ParkingSlot.floor_id == floor.id,
                ParkingSlot.status == SlotStatus.reserved
            )
        )

        total_count = total.scalar() or 0
        available_count = available.scalar() or 0
        occupied_count = occupied.scalar() or 0
        reserved_count = reserved.scalar() or 0
        occupancy_pct = round((occupied_count + reserved_count) / total_count * 100, 1) if total_count else 0

        response.append({
            "id": floor.id,
            "floor_number": floor.floor_number,
            "name": floor.name,
            "description": floor.description,
            "layout_config": floor.layout_config,
            "total_slots": total_count,
            "available_slots": available_count,
            "occupied_slots": occupied_count,
            "reserved_slots": reserved_count,
            "occupancy_percentage": occupancy_pct,
        })

    return {"floors": response, "total": len(response)}


@router.get("/{floor_number}")
async def get_floor(floor_number: int, db: AsyncSession = Depends(get_db)):
    """Get a specific floor by number."""
    result = await db.execute(
        select(Floor).where(Floor.floor_number == floor_number)
    )
    floor = result.scalar_one_or_none()
    if not floor:
        raise HTTPException(status_code=404, detail=f"Floor {floor_number} not found")

    # Get all slots for this floor
    slots_result = await db.execute(
        select(ParkingSlot).where(ParkingSlot.floor_id == floor.id).order_by(ParkingSlot.slot_code)
    )
    slots = slots_result.scalars().all()

    return {
        "id": floor.id,
        "floor_number": floor.floor_number,
        "name": floor.name,
        "description": floor.description,
        "layout_config": floor.layout_config,
        "slots": [
            {
                "id": s.id,
                "slot_code": s.slot_code,
                "slot_type": s.slot_type.value,
                "status": s.status.value,
                "row_label": s.row_label,
                "position_x": s.position_x,
                "position_y": s.position_y,
                "graph_node": s.graph_node,
                "is_accessible": s.is_accessible,
                "last_sensor_update": s.last_sensor_update.isoformat() if s.last_sensor_update else None,
            }
            for s in slots
        ],
    }
