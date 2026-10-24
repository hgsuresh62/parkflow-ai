"""ParkFlow AI — Sessions API"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.session import ParkingSession
from app.models.parking_slot import ParkingSlot
from app.models.enums import SessionStatus, SlotStatus, EventSource
from app.services.occupancy import occupancy_service

router = APIRouter()


class CreateSessionRequest(BaseModel):
    destination_slot: str = Field(..., description="Target slot code")
    user_session_id: Optional[str] = "guest"
    vehicle_id: Optional[str] = None


@router.post("")
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    """Create a new parking navigation session."""
    result = await db.execute(
        select(ParkingSlot).where(ParkingSlot.slot_code == body.destination_slot)
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(404, f"Slot '{body.destination_slot}' not found")

    session = ParkingSession(
        session_uid=str(uuid.uuid4()),
        selected_slot_id=slot.id,
        status=SessionStatus.navigating,
        user_session_id=body.user_session_id,
        vehicle_id=body.vehicle_id,
        navigation_state={"destination": body.destination_slot, "phase": "navigating"},
    )
    db.add(session)
    await db.flush()

    return {
        "session_id": session.session_uid,
        "destination_slot": body.destination_slot,
        "status": session.status.value,
        "started_at": session.started_at.isoformat() if session.started_at else None,
    }


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get session by UID."""
    result = await db.execute(
        select(ParkingSession).where(ParkingSession.session_uid == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    return {
        "session_id": session.session_uid,
        "status": session.status.value,
        "navigation_state": session.navigation_state,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "arrived_at": session.arrived_at.isoformat() if session.arrived_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }


@router.post("/{session_id}/arrive")
async def session_arrive(session_id: str, db: AsyncSession = Depends(get_db)):
    """Mark a vehicle as arrived at the destination slot."""
    result = await db.execute(
        select(ParkingSession).where(ParkingSession.session_uid == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    if session.status != SessionStatus.navigating:
        raise HTTPException(409, f"Session is {session.status.value}, not navigating")

    session.status = SessionStatus.arrived
    session.arrived_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.navigation_state = {**session.navigation_state, "phase": "arrived"}

    # Mark slot as occupied
    if session.selected_slot_id:
        slot_result = await db.execute(
            select(ParkingSlot).where(ParkingSlot.id == session.selected_slot_id)
        )
        slot = slot_result.scalar_one_or_none()
        if slot:
            await occupancy_service.process_sensor_event(
                slot_code=slot.slot_code,
                distance_cm=15.0,
                new_status=SlotStatus.occupied,
                source=EventSource.manual,
                session=db,
            )

    await db.flush()
    return {"session_id": session_id, "status": "arrived"}


@router.post("/{session_id}/cancel")
async def cancel_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel an active navigation session."""
    result = await db.execute(
        select(ParkingSession).where(ParkingSession.session_uid == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    session.status = SessionStatus.cancelled
    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()
    return {"session_id": session_id, "status": "cancelled"}
