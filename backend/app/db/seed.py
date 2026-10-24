"""
ParkFlow AI — Database Seeder

Seeds the database with:
- 3 floors
- 100 parking slots (34 + 33 + 33)
- 100 virtual sensors (one per slot)
- Realistic mix of available and occupied slots
"""
import logging
import random
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.floor import Floor
from app.models.parking_slot import ParkingSlot
from app.models.sensor import Sensor
from app.models.enums import SlotStatus, SlotType, SensorStatus, EventSource
from app.routing.graph import get_graph, get_slot_node

logger = logging.getLogger(__name__)

# Seed random with fixed value for deterministic initial state
SEED_RANDOM = random.Random(42)

# Percentage of slots initially occupied (realistic starting state)
INITIAL_OCCUPANCY_RATE = 0.38  # ~38% occupied


def _slot_type_for(slot_code: str) -> SlotType:
    """Determine slot type based on slot number."""
    num_str = slot_code.split("-")[-1]
    num = int("".join(c for c in num_str if c.isdigit()))
    if num <= 2:
        return SlotType.accessible
    if num in (3, 4):
        return SlotType.ev_charging
    if num > 15:
        return SlotType.compact
    return SlotType.standard


def _initial_status(slot_code: str) -> SlotStatus:
    """Assign initial occupancy status with seeded randomness."""
    # Always keep accessible and EV slots available initially for demo
    slot_type = _slot_type_for(slot_code)
    if slot_type in (SlotType.accessible, SlotType.ev_charging):
        return SlotStatus.available
    return SlotStatus.occupied if SEED_RANDOM.random() < INITIAL_OCCUPANCY_RATE else SlotStatus.available


FLOOR_DEFINITIONS = [
    {
        "floor_number": 1,
        "name": "Floor 1 — Ground Level",
        "description": "Ground floor with main entrance, accessible and EV spaces.",
        "layout_config": {
            "rows": ["A", "B"],
            "entrance": "ENTRANCE",
            "ramp_up": "F1_RAMP_UP",
            "svg_height": 550,
            "svg_width": 700,
        },
    },
    {
        "floor_number": 2,
        "name": "Floor 2 — Mid Level",
        "description": "Mid-level floor accessible via ramp from Floor 1.",
        "layout_config": {
            "rows": ["B", "C"],
            "ramp_down": "F2_RAMP_DOWN",
            "ramp_up": "F2_RAMP_UP",
            "svg_height": 550,
            "svg_width": 700,
        },
    },
    {
        "floor_number": 3,
        "name": "Floor 3 — Top Level",
        "description": "Top floor with panoramic access via ramp from Floor 2.",
        "layout_config": {
            "rows": ["C", "D"],
            "ramp_down": "F3_RAMP_DOWN",
            "svg_height": 550,
            "svg_width": 700,
        },
    },
]


async def seed_database():
    """
    Idempotent seed function.
    Checks if data already exists before inserting.
    """
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(func.count(Floor.id)))
        floor_count = result.scalar()
        if floor_count >= 3:
            logger.info("Database already seeded — skipping")
            return

        logger.info("Seeding database...")
        await _seed_floors(session)
        await session.commit()

        await _seed_slots(session)
        await session.commit()

        await _seed_sensors(session)
        await session.commit()

        logger.info("✅ Seeding complete")


async def _seed_floors(session: AsyncSession):
    """Insert floor records."""
    for floor_def in FLOOR_DEFINITIONS:
        floor = Floor(
            floor_number=floor_def["floor_number"],
            name=floor_def["name"],
            description=floor_def["description"],
            layout_config=floor_def["layout_config"],
        )
        session.add(floor)
    await session.flush()
    logger.info("Floors seeded (3)")


async def _seed_slots(session: AsyncSession):
    """Insert all 100 parking slot records, consistent with graph nodes."""
    G = get_graph()

    # Get floor ID map
    result = await session.execute(select(Floor))
    floors = result.scalars().all()
    floor_map = {f.floor_number: f.id for f in floors}

    slot_nodes = [
        (n, data)
        for n, data in G.nodes(data=True)
        if data.get("node_type") == "slot"
    ]

    # Sort by slot code for deterministic ordering
    slot_nodes.sort(key=lambda x: x[1].get("slot_code", ""))

    slot_count = 0
    for node_id, data in slot_nodes:
        slot_code = data.get("slot_code", node_id)
        floor_num = data.get("floor", 1)
        floor_id = floor_map.get(floor_num)
        if not floor_id:
            continue

        row_label = slot_code[3] if len(slot_code) > 3 else "A"
        slot_type = _slot_type_for(slot_code)
        status = _initial_status(slot_code)

        slot = ParkingSlot(
            slot_code=slot_code,
            floor_id=floor_id,
            slot_type=slot_type,
            status=status,
            row_label=row_label,
            position_x=data.get("x"),
            position_y=data.get("y"),
            graph_node=node_id,
            is_accessible=(slot_type == SlotType.accessible),
        )
        session.add(slot)
        slot_count += 1

    await session.flush()
    logger.info(f"Parking slots seeded ({slot_count})")

    # Update floor total_slots counts
    for floor in floors:
        result = await session.execute(
            select(func.count(ParkingSlot.id)).where(ParkingSlot.floor_id == floor.id)
        )
        floor.total_slots = result.scalar() or 0

    await session.flush()


async def _seed_sensors(session: AsyncSession):
    """Create one virtual sensor per parking slot."""
    result = await session.execute(select(ParkingSlot))
    slots = result.scalars().all()

    for slot in slots:
        sensor = Sensor(
            sensor_uid=f"SIM-{slot.slot_code}",
            sensor_type="ultrasonic_hcsr04",
            parking_slot_id=slot.id,
            provider=EventSource.simulator,
            status=SensorStatus.online,
            last_distance_cm=15.0 if slot.status == SlotStatus.occupied else 120.0,
            last_seen_at=datetime.now(timezone.utc),
            meta_data={
                "model": "HC-SR04",
                "threshold_cm": 50.0,
                "update_interval_s": 5,
                "simulated": True,
            },
        )
        session.add(sensor)

    await session.flush()
    logger.info(f"Sensors seeded ({len(slots)})")
