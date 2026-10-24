"""ParkFlow AI — Reservations API"""
import uuid
import string
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.reservation import Reservation
from app.models.parking_slot import ParkingSlot
from app.models.enums import SlotStatus, ReservationStatus, EventSource
from app.services.occupancy import occupancy_service
from app.websocket.manager import broadcast_reservation_created, broadcast_reservation_cancelled

router = APIRouter()

RESERVATION_DURATION_MINUTES = 30


def _make_reservation_code() -> str:
    """Generate a short human-readable reservation code."""
    chars = string.ascii_uppercase + string.digits
    return "PF-" + "".join(random.choices(chars, k=6))


def _res_to_dict(r: Reservation) -> dict:
    return {
        "id": r.id,
        "reservation_code": r.reservation_code,
        "parking_slot_id": r.parking_slot_id,
        "user_session_id": r.user_session_id,
        "status": r.status.value,
        "starts_at": r.starts_at.isoformat(),
        "expires_at": r.expires_at.isoformat(),
        "created_at": r.created_at.isoformat(),
    }


class CreateReservationRequest(BaseModel):
    slot_code: str = Field(..., description="Target slot code, e.g. F2-B08")
    user_session_id: str = Field(default="guest-user", description="User or session identifier")
    duration_minutes: int = Field(default=30, ge=5, le=120)


@router.post("")
async def create_reservation(
    body: CreateReservationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new slot reservation."""
    # Fetch and validate slot
    result = await db.execute(
        select(ParkingSlot).where(ParkingSlot.slot_code == body.slot_code)
    )
    slot = result.scalar_one_or_none()

    if not slot:
        raise HTTPException(404, f"Slot '{body.slot_code}' not found")

    if slot.status == SlotStatus.occupied:
        raise HTTPException(409, f"Slot '{body.slot_code}' is already occupied")

    if slot.status == SlotStatus.reserved:
        # Check if existing reservation is truly active
        existing = await db.execute(
            select(Reservation).where(
                Reservation.parking_slot_id == slot.id,
                Reservation.status == ReservationStatus.active,
            )
        )
        active_res = existing.scalar_one_or_none()
        if active_res and active_res.expires_at > datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(
                409,
                f"Slot '{body.slot_code}' is already reserved until {active_res.expires_at.isoformat()}"
            )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(minutes=body.duration_minutes)

    reservation = Reservation(
        reservation_code=_make_reservation_code(),
        parking_slot_id=slot.id,
        user_session_id=body.user_session_id,
        status=ReservationStatus.active,
        starts_at=now,
        expires_at=expires_at,
    )
    db.add(reservation)

    # Mark slot as reserved
    slot.status = SlotStatus.reserved
    await db.flush()

    await broadcast_reservation_created(
        reservation.reservation_code,
        body.slot_code,
        expires_at.isoformat(),
    )

    return {**_res_to_dict(reservation), "slot_code": body.slot_code}


@router.get("")
async def list_reservations(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List reservations with optional status filter."""
    q = select(Reservation, ParkingSlot.slot_code).join(
        ParkingSlot, Reservation.parking_slot_id == ParkingSlot.id
    ).order_by(Reservation.created_at.desc())

    if status:
        try:
            q = q.where(Reservation.status == ReservationStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    result = await db.execute(q)
    rows = result.all()

    return {
        "reservations": [
            {**_res_to_dict(row[0]), "slot_code": row[1]}
            for row in rows
        ],
        "total": len(rows),
    }


@router.get("/{reservation_id}")
async def get_reservation(reservation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a reservation by code or ID."""
    if reservation_id.startswith("PF-"):
        q = select(Reservation, ParkingSlot.slot_code).join(
            ParkingSlot, Reservation.parking_slot_id == ParkingSlot.id
        ).where(Reservation.reservation_code == reservation_id)
    else:
        try:
            rid = int(reservation_id)
        except ValueError:
            raise HTTPException(400, "Invalid reservation ID")
        q = select(Reservation, ParkingSlot.slot_code).join(
            ParkingSlot, Reservation.parking_slot_id == ParkingSlot.id
        ).where(Reservation.id == rid)

    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(404, f"Reservation '{reservation_id}' not found")

    return {**_res_to_dict(row[0]), "slot_code": row[1]}


@router.delete("/{reservation_id}")
async def cancel_reservation(reservation_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel an active reservation and free the slot."""
    if reservation_id.startswith("PF-"):
        result = await db.execute(
            select(Reservation, ParkingSlot).join(
                ParkingSlot, Reservation.parking_slot_id == ParkingSlot.id
            ).where(Reservation.reservation_code == reservation_id)
        )
    else:
        try:
            rid = int(reservation_id)
        except ValueError:
            raise HTTPException(400, "Invalid reservation ID")
        result = await db.execute(
            select(Reservation, ParkingSlot).join(
                ParkingSlot, Reservation.parking_slot_id == ParkingSlot.id
            ).where(Reservation.id == rid)
        )

    row = result.first()
    if not row:
        raise HTTPException(404, f"Reservation '{reservation_id}' not found")

    reservation, slot = row

    if reservation.status != ReservationStatus.active:
        raise HTTPException(409, f"Reservation is already {reservation.status.value}")

    reservation.status = ReservationStatus.cancelled

    # Free the slot if it was marked reserved
    if slot.status == SlotStatus.reserved:
        slot.status = SlotStatus.available

    await db.flush()

    await broadcast_reservation_cancelled(reservation.reservation_code, slot.slot_code)

    return {
        "reservation_code": reservation.reservation_code,
        "slot_code": slot.slot_code,
        "status": "cancelled",
    }
