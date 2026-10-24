"""
ParkFlow AI — Occupancy Service

Single source of truth for updating slot occupancy.
All providers (simulator, ThingSpeak, MQTT, manual) must go through this service.
Ensures database consistency and WebSocket broadcast after each committed update.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.parking_slot import ParkingSlot
from app.models.sensor import Sensor
from app.models.sensor_event import SensorEvent
from app.models.enums import SlotStatus, SensorStatus, EventSource
from app.websocket.manager import broadcast_slot_updated

logger = logging.getLogger(__name__)


class OccupancyService:
    """
    Handles slot occupancy state transitions with full audit trail.
    """

    async def process_sensor_event(
        self,
        slot_code: str,
        distance_cm: Optional[float],
        new_status: SlotStatus,
        source: EventSource,
        sensor_uid: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ParkingSlot]:
        """
        Process an incoming sensor event and update slot status.

        Args:
            slot_code: Human-readable slot code (e.g., "F2-B08")
            distance_cm: Raw sensor distance reading
            new_status: Derived occupancy status
            source: Event source provider
            sensor_uid: Optional sensor identifier
            session: Optional external session (creates own if None)

        Returns:
            Updated ParkingSlot or None if slot not found
        """
        if session is not None:
            return await self._process(session, slot_code, distance_cm, new_status, source, sensor_uid)

        async with AsyncSessionLocal() as db:
            result = await self._process(db, slot_code, distance_cm, new_status, source, sensor_uid)
            await db.commit()
            return result

    async def _process(
        self,
        session: AsyncSession,
        slot_code: str,
        distance_cm: Optional[float],
        new_status: SlotStatus,
        source: EventSource,
        sensor_uid: Optional[str],
    ) -> Optional[ParkingSlot]:
        # Fetch the slot
        result = await session.execute(
            select(ParkingSlot).where(ParkingSlot.slot_code == slot_code)
        )
        slot = result.scalar_one_or_none()

        if not slot:
            logger.warning(f"Slot not found: {slot_code}")
            return None

        # Skip if status unchanged
        if slot.status == new_status:
            return slot

        old_status = slot.status

        # Guard against overwriting a reservation with a simulator 'available' signal
        if slot.status == SlotStatus.reserved and new_status == SlotStatus.available:
            if source in (EventSource.simulator,):
                logger.debug(f"Skipping sim 'available' for reserved slot {slot_code}")
                return slot

        # Update slot status
        slot.status = new_status
        slot.last_sensor_update = datetime.now(timezone.utc)

        # Update sensor if we have a UID
        if sensor_uid:
            sensor_result = await session.execute(
                select(Sensor).where(Sensor.sensor_uid == sensor_uid)
            )
            sensor = sensor_result.scalar_one_or_none()
            if sensor:
                sensor.last_distance_cm = distance_cm
                sensor.last_seen_at = datetime.now(timezone.utc)
                sensor.status = SensorStatus.online
                sensor_id = sensor.id
            else:
                sensor_id = None
        else:
            sensor_id = None

        # Record event
        event = SensorEvent(
            sensor_id=sensor_id,
            parking_slot_id=slot.id,
            raw_distance_cm=distance_cm,
            occupancy_state=new_status,
            source=source,
            processed=True,
            event_timestamp=datetime.now(timezone.utc),
        )
        session.add(event)

        await session.flush()

        logger.info(
            f"Slot {slot_code}: {old_status} → {new_status} (source: {source.value})"
        )

        # Broadcast WebSocket event after successful flush (commit is handled by caller)
        from app.models.floor import Floor
        floor_result = await session.execute(
            select(Floor.floor_number).where(Floor.id == slot.floor_id)
        )
        floor_num = floor_result.scalar_one_or_none() or 1

        # Schedule broadcast (non-blocking)
        import asyncio
        asyncio.create_task(
            broadcast_slot_updated(
                slot_code=slot_code,
                status=new_status.value,
                floor=floor_num,
                source=source.value,
                extra={"distance_cm": distance_cm, "previous_status": old_status.value},
            )
        )

        return slot

    async def get_available_slots(
        self,
        floor_number: Optional[int] = None,
        session: Optional[AsyncSession] = None,
    ) -> list:
        """Return all available slot codes, optionally filtered by floor."""
        async def _query(db: AsyncSession):
            from app.models.floor import Floor
            q = (
                select(ParkingSlot.slot_code, Floor.floor_number)
                .join(Floor, ParkingSlot.floor_id == Floor.id)
                .where(ParkingSlot.status == SlotStatus.available)
            )
            if floor_number is not None:
                q = q.where(Floor.floor_number == floor_number)
            result = await db.execute(q)
            return [row[0] for row in result.all()]

        if session:
            return await _query(session)
        async with AsyncSessionLocal() as db:
            return await _query(db)


# Singleton
occupancy_service = OccupancyService()
