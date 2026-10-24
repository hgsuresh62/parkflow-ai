"""ParkFlow AI — Slots API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.parking_slot import ParkingSlot
from app.models.floor import Floor
from app.models.enums import SlotStatus, SlotType, EventSource
from app.services.occupancy import occupancy_service

router = APIRouter()


def _slot_to_dict(slot: ParkingSlot, floor_number: Optional[int] = None) -> dict:
    return {
        "id": slot.id,
        "slot_code": slot.slot_code,
        "floor_id": slot.floor_id,
        "floor_number": floor_number,
        "slot_type": slot.slot_type.value,
        "status": slot.status.value,
        "row_label": slot.row_label,
        "position_x": slot.position_x,
        "position_y": slot.position_y,
        "graph_node": slot.graph_node,
        "is_accessible": slot.is_accessible,
        "last_sensor_update": slot.last_sensor_update.isoformat() if slot.last_sensor_update else None,
        "created_at": slot.created_at.isoformat(),
    }


@router.get("")
async def list_slots(
    floor_number: Optional[int] = Query(None, description="Filter by floor (1, 2, or 3)"),
    status: Optional[str] = Query(None, description="Filter by status (available/occupied/reserved)"),
    slot_type: Optional[str] = Query(None, description="Filter by type"),
    db: AsyncSession = Depends(get_db),
):
    """List all parking slots with optional filtering."""
    q = (
        select(ParkingSlot, Floor.floor_number)
        .join(Floor, ParkingSlot.floor_id == Floor.id)
        .order_by(Floor.floor_number, ParkingSlot.slot_code)
    )

    if floor_number is not None:
        q = q.where(Floor.floor_number == floor_number)
    if status:
        try:
            q = q.where(ParkingSlot.status == SlotStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    if slot_type:
        try:
            q = q.where(ParkingSlot.slot_type == SlotType(slot_type))
        except ValueError:
            raise HTTPException(400, f"Invalid slot_type: {slot_type}")

    result = await db.execute(q)
    rows = result.all()

    slots = [_slot_to_dict(row[0], row[1]) for row in rows]

    return {
        "slots": slots,
        "total": len(slots),
        "filters": {"floor_number": floor_number, "status": status, "slot_type": slot_type},
    }


@router.get("/availability")
async def get_availability(db: AsyncSession = Depends(get_db)):
    """Get a compact availability summary across all floors."""
    result = await db.execute(
        select(Floor.floor_number, ParkingSlot.status, func.count(ParkingSlot.id))
        .join(Floor, ParkingSlot.floor_id == Floor.id)
        .group_by(Floor.floor_number, ParkingSlot.status)
    )
    rows = result.all()

    summary: dict = {}
    total_available = 0
    total_occupied = 0
    total_reserved = 0
    total_all = 0

    for floor_num, status, count in rows:
        if floor_num not in summary:
            summary[floor_num] = {"available": 0, "occupied": 0, "reserved": 0, "total": 0}
        key = status.value if hasattr(status, "value") else status
        summary[floor_num][key] = count
        summary[floor_num]["total"] += count
        if key == "available":
            total_available += count
        elif key == "occupied":
            total_occupied += count
        elif key == "reserved":
            total_reserved += count
        total_all += count

    occupancy_pct = round((total_occupied + total_reserved) / total_all * 100, 1) if total_all else 0

    return {
        "total_slots": total_all,
        "available": total_available,
        "occupied": total_occupied,
        "reserved": total_reserved,
        "occupancy_percentage": occupancy_pct,
        "floors": [
            {
                "floor_number": fn,
                **data,
                "occupancy_percentage": round(
                    (data.get("occupied", 0) + data.get("reserved", 0)) / data["total"] * 100, 1
                ) if data.get("total") else 0,
            }
            for fn, data in sorted(summary.items())
        ],
    }


@router.get("/{slot_id}")
async def get_slot(slot_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific slot by slot_code or ID."""
    # Try by slot_code first (e.g., "F2-B08")
    if slot_id.startswith("F"):
        result = await db.execute(
            select(ParkingSlot, Floor.floor_number)
            .join(Floor, ParkingSlot.floor_id == Floor.id)
            .where(ParkingSlot.slot_code == slot_id)
        )
    else:
        try:
            sid = int(slot_id)
        except ValueError:
            raise HTTPException(400, "slot_id must be a slot code (e.g. F2-B08) or numeric ID")
        result = await db.execute(
            select(ParkingSlot, Floor.floor_number)
            .join(Floor, ParkingSlot.floor_id == Floor.id)
            .where(ParkingSlot.id == sid)
        )

    row = result.first()
    if not row:
        raise HTTPException(404, f"Slot '{slot_id}' not found")

    return _slot_to_dict(row[0], row[1])


class SlotStatusUpdate(BaseModel):
    status: str
    source: str = "manual"


@router.patch("/{slot_id}/status")
async def update_slot_status(
    slot_id: str,
    body: SlotStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Manually update a slot's occupancy status."""
    try:
        new_status = SlotStatus(body.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {body.status}")

    try:
        source = EventSource(body.source)
    except ValueError:
        source = EventSource.manual

    slot = await occupancy_service.process_sensor_event(
        slot_code=slot_id,
        distance_cm=None,
        new_status=new_status,
        source=source,
        session=db,
    )

    if not slot:
        raise HTTPException(404, f"Slot '{slot_id}' not found")

    return {"slot_code": slot_id, "status": new_status.value, "updated": True}
