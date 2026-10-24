"""ParkFlow AI — Routing API"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.parking_slot import ParkingSlot
from app.models.route_record import RouteRecord
from app.models.enums import SlotStatus
from app.routing.pathfinder import get_pathfinding_engine
from app.services.occupancy import occupancy_service

router = APIRouter()


class RouteRequest(BaseModel):
    source_node: str = Field(default="ENTRANCE", description="Starting graph node")
    destination_slot: str = Field(..., description="Target slot code, e.g. F2-B08")
    floor_preference: Optional[int] = Field(None, description="Preferred floor for alternatives")


class RecalculateRequest(BaseModel):
    route_id: str
    source_node: str = "ENTRANCE"
    new_destination_slot: Optional[str] = None


@router.post("")
async def calculate_route(
    body: RouteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate optimal route from source_node to destination_slot.
    Validates slot availability before computing the path.
    """
    # Validate slot exists and is available
    result = await db.execute(
        select(ParkingSlot).where(ParkingSlot.slot_code == body.destination_slot)
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(404, f"Slot '{body.destination_slot}' not found")

    if slot.status == SlotStatus.occupied:
        # Find alternatives
        available = await occupancy_service.get_available_slots(session=db)
        engine = get_pathfinding_engine()
        alternatives = engine.find_alternative_slots(
            body.source_node,
            preferred_floor=body.floor_preference,
            count=5,
            available_slot_codes=available[:20],
        )
        raise HTTPException(
            409,
            detail={
                "error": f"Slot '{body.destination_slot}' is occupied",
                "suggestion": "Please select an available slot",
                "alternatives": alternatives,
            },
        )

    # Calculate route
    engine = get_pathfinding_engine()
    route_result = engine.find_route(body.source_node, body.destination_slot)

    if not route_result.is_feasible:
        raise HTTPException(422, detail={"error": route_result.error})

    # Persist route record
    route_uid = str(uuid.uuid4())
    record = RouteRecord(
        route_uid=route_uid,
        source_node=route_result.source_node,
        destination_node=route_result.destination_node,
        destination_slot_code=body.destination_slot,
        path_nodes=route_result.path,
        instructions=route_result.instructions,
        distance_m=route_result.distance_m,
        estimated_time_seconds=route_result.estimated_time_seconds,
        route_cost=route_result.route_cost,
        is_valid=True,
    )
    db.add(record)
    await db.flush()

    return {
        "route_id": route_uid,
        "destination_slot": route_result.destination_slot,
        "source_node": route_result.source_node,
        "path": route_result.path,
        "instructions": route_result.instructions,
        "distance_m": route_result.distance_m,
        "estimated_time_seconds": route_result.estimated_time_seconds,
        "route_cost": route_result.route_cost,
        "floor_changes": route_result.floor_changes,
        "is_valid": True,
    }


@router.get("/{route_id}")
async def get_route(route_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a previously calculated route by ID."""
    result = await db.execute(
        select(RouteRecord).where(RouteRecord.route_uid == route_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, f"Route '{route_id}' not found")

    return {
        "route_id": record.route_uid,
        "destination_slot": record.destination_slot_code,
        "source_node": record.source_node,
        "path": record.path_nodes,
        "instructions": record.instructions,
        "distance_m": record.distance_m,
        "estimated_time_seconds": record.estimated_time_seconds,
        "route_cost": record.route_cost,
        "is_valid": record.is_valid,
        "invalidated_reason": record.invalidated_reason,
        "created_at": record.created_at.isoformat(),
    }


@router.post("/recalculate")
async def recalculate_route(
    body: RecalculateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Recalculate a route, optionally to a new destination.
    Used when the original destination becomes unavailable.
    """
    # If new destination provided, validate it
    destination = body.new_destination_slot

    if destination:
        result = await db.execute(
            select(ParkingSlot).where(ParkingSlot.slot_code == destination)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            raise HTTPException(404, f"Slot '{destination}' not found")
        if slot.status == SlotStatus.occupied:
            raise HTTPException(409, f"Slot '{destination}' is occupied")
    else:
        # Find nearest available slot
        available = await occupancy_service.get_available_slots(session=db)
        engine = get_pathfinding_engine()
        alts = engine.find_alternative_slots(body.source_node, count=1, available_slot_codes=available[:10])
        if not alts:
            raise HTTPException(404, "No available slots found for rerouting")
        destination = alts[0]["slot_code"]

    engine = get_pathfinding_engine()
    route_result = engine.find_route(body.source_node, destination)

    if not route_result.is_feasible:
        raise HTTPException(422, {"error": route_result.error})

    route_uid = str(uuid.uuid4())
    record = RouteRecord(
        route_uid=route_uid,
        source_node=route_result.source_node,
        destination_node=route_result.destination_node,
        destination_slot_code=destination,
        path_nodes=route_result.path,
        instructions=route_result.instructions,
        distance_m=route_result.distance_m,
        estimated_time_seconds=route_result.estimated_time_seconds,
        route_cost=route_result.route_cost,
        is_valid=True,
    )
    db.add(record)
    await db.flush()

    return {
        "route_id": route_uid,
        "recalculated": True,
        "previous_route_id": body.route_id,
        "destination_slot": destination,
        "path": route_result.path,
        "instructions": route_result.instructions,
        "distance_m": route_result.distance_m,
        "estimated_time_seconds": route_result.estimated_time_seconds,
        "floor_changes": route_result.floor_changes,
        "is_valid": True,
    }


@router.get("/{route_id}/alternatives")
async def get_route_alternatives(
    route_id: str,
    source_node: str = "ENTRANCE",
    floor_preference: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Return 5 alternative available slots with route costs."""
    available = await occupancy_service.get_available_slots(session=db)
    engine = get_pathfinding_engine()
    alternatives = engine.find_alternative_slots(
        source_node,
        preferred_floor=floor_preference,
        count=5,
        available_slot_codes=available[:30],
    )
    return {"alternatives": alternatives, "source_node": source_node}
