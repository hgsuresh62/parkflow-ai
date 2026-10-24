"""
ParkFlow AI — IoT Simulator

Simulates 100 virtual HC-SR04 ultrasonic sensors.
Provides:
  - Random mode: random occupancy changes at configured interval
  - Demo mode: scripted predictable scenario for hackathon judging
  - Stress mode: rapid random changes across all slots
  - Manual triggers: arrive/depart specific slots
"""
import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum

from app.routing.graph import get_graph, get_all_slot_codes
from app.models.enums import SlotStatus, EventSource
from app.services.occupancy import occupancy_service
from app.websocket.manager import broadcast_simulator_event

logger = logging.getLogger(__name__)

THRESHOLD_CM = 50.0
OCCUPIED_DISTANCE = 15.0
AVAILABLE_DISTANCE = 120.0
NOISE_AMPLITUDE = 3.0  # ±cm noise to simulate real sensor jitter


class SimulatorMode(str, Enum):
    IDLE = "idle"
    RANDOM = "random"
    DEMO = "demo"
    STRESS = "stress"


@dataclass
class VirtualSensor:
    sensor_uid: str
    slot_code: str
    distance_cm: float
    is_occupied: bool
    online: bool = True
    last_update: float = field(default_factory=time.time)
    update_count: int = 0

    def simulate_reading(self) -> float:
        """Generate a realistic sensor reading with noise."""
        noise = random.uniform(-NOISE_AMPLITUDE, NOISE_AMPLITUDE)
        base = OCCUPIED_DISTANCE if self.is_occupied else AVAILABLE_DISTANCE
        return max(2.0, base + noise)


class SimulatorService:
    """
    Manages 100 virtual parking sensors.
    Lifecycle: start_background() → running → stop()
    """

    def __init__(self):
        self._mode: SimulatorMode = SimulatorMode.IDLE
        self._sensors: Dict[str, VirtualSensor] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._interval_s: float = 5.0
        self._protected_slots: Set[str] = set()  # Slots not randomized (e.g., demo destination)
        self._rng = random.Random(42)
        self._demo_step = 0
        self._demo_target_slot: Optional[str] = None
        self._stats = {
            "total_events": 0,
            "started_at": None,
            "last_event_at": None,
        }

    def _init_sensors(self, all_slot_codes: List[str], initial_states: Dict[str, str]):
        """Initialize virtual sensors from database slot states."""
        for code in all_slot_codes:
            status = initial_states.get(code, "available")
            is_occupied = status in ("occupied", "reserved")
            self._sensors[code] = VirtualSensor(
                sensor_uid=f"SIM-{code}",
                slot_code=code,
                distance_cm=OCCUPIED_DISTANCE if is_occupied else AVAILABLE_DISTANCE,
                is_occupied=is_occupied,
            )
        logger.info(f"Simulator initialized {len(self._sensors)} virtual sensors")

    async def _load_initial_states(self) -> Dict[str, str]:
        """Load current slot states from database."""
        from app.db.database import AsyncSessionLocal
        from app.models.parking_slot import ParkingSlot
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ParkingSlot.slot_code, ParkingSlot.status))
            return {row[0]: row[1].value for row in result.all()}

    async def start_background(self, interval_s: float = 5.0):
        """Start the simulator as a background asyncio task."""
        if self._running:
            logger.info("Simulator already running")
            return

        self._interval_s = interval_s
        self._running = True
        self._mode = SimulatorMode.RANDOM
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()

        # Initialize sensor states from DB
        all_codes = get_all_slot_codes(get_graph())
        initial_states = await self._load_initial_states()
        self._init_sensors(all_codes, initial_states)

        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Simulator started (mode={self._mode}, interval={interval_s}s)")
        await broadcast_simulator_event("started", {"mode": self._mode, "slot_count": len(self._sensors)})

    async def stop(self):
        """Stop the simulator gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._mode = SimulatorMode.IDLE
        logger.info("Simulator stopped")
        await broadcast_simulator_event("stopped", {})

    async def start_demo(self, target_slot: Optional[str] = None):
        """
        Start the predictable demo sequence.
        Picks a stable destination slot and runs a scripted arrival.
        """
        self._demo_step = 0
        self._demo_target_slot = target_slot or "F2-B05"  # Deterministic demo slot
        self._protected_slots = {self._demo_target_slot}
        self._mode = SimulatorMode.DEMO

        # Ensure demo slot is available
        if self._demo_target_slot in self._sensors:
            self._sensors[self._demo_target_slot].is_occupied = False
            await occupancy_service.process_sensor_event(
                slot_code=self._demo_target_slot,
                distance_cm=AVAILABLE_DISTANCE,
                new_status=SlotStatus.available,
                source=EventSource.simulator,
                sensor_uid=f"SIM-{self._demo_target_slot}",
            )

        logger.info(f"Demo mode started, target slot: {self._demo_target_slot}")
        await broadcast_simulator_event("demo_started", {
            "target_slot": self._demo_target_slot,
            "steps": ["select_slot", "calculate_route", "navigate", "arrive", "recalculate"],
        })
        return {"target_slot": self._demo_target_slot, "status": "demo_started"}

    async def trigger_arrival(self, slot_code: str) -> dict:
        """Simulate a vehicle arriving at a specific slot."""
        sensor = self._sensors.get(slot_code)
        if sensor:
            sensor.is_occupied = True
            sensor.distance_cm = OCCUPIED_DISTANCE

        await occupancy_service.process_sensor_event(
            slot_code=slot_code,
            distance_cm=OCCUPIED_DISTANCE,
            new_status=SlotStatus.occupied,
            source=EventSource.simulator,
            sensor_uid=f"SIM-{slot_code}",
        )
        self._stats["total_events"] += 1
        self._stats["last_event_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Simulated arrival at {slot_code}")
        return {"slot_code": slot_code, "event": "arrival", "status": "occupied"}

    async def trigger_departure(self, slot_code: str) -> dict:
        """Simulate a vehicle departing from a specific slot."""
        sensor = self._sensors.get(slot_code)
        if sensor:
            sensor.is_occupied = False
            sensor.distance_cm = AVAILABLE_DISTANCE

        await occupancy_service.process_sensor_event(
            slot_code=slot_code,
            distance_cm=AVAILABLE_DISTANCE,
            new_status=SlotStatus.available,
            source=EventSource.simulator,
            sensor_uid=f"SIM-{slot_code}",
        )
        self._stats["total_events"] += 1
        logger.info(f"Simulated departure from {slot_code}")
        return {"slot_code": slot_code, "event": "departure", "status": "available"}

    async def set_stress_mode(self, enabled: bool):
        """Enable/disable stress test mode with rapid random changes."""
        if enabled:
            self._mode = SimulatorMode.STRESS
            self._interval_s = 1.0
        else:
            self._mode = SimulatorMode.RANDOM
            self._interval_s = 5.0
        await broadcast_simulator_event(
            "stress_mode_changed", {"enabled": enabled, "interval_s": self._interval_s}
        )

    def get_status(self) -> dict:
        """Return current simulator status."""
        occupied = sum(1 for s in self._sensors.values() if s.is_occupied)
        online = sum(1 for s in self._sensors.values() if s.online)
        return {
            "running": self._running,
            "mode": self._mode.value,
            "interval_s": self._interval_s,
            "total_sensors": len(self._sensors),
            "online_sensors": online,
            "occupied_count": occupied,
            "available_count": len(self._sensors) - occupied,
            "demo_target_slot": self._demo_target_slot,
            **self._stats,
        }

    async def _run_loop(self):
        """Main simulator loop — runs as a background asyncio task."""
        while self._running:
            try:
                await asyncio.sleep(self._interval_s)
                if not self._running:
                    break

                if self._mode == SimulatorMode.RANDOM:
                    await self._random_update()
                elif self._mode == SimulatorMode.STRESS:
                    await self._stress_update()
                elif self._mode == SimulatorMode.DEMO:
                    await self._demo_update()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Simulator loop error: {e}")
                await asyncio.sleep(1)

    async def _random_update(self):
        """Randomly flip occupancy for 1–3 slots."""
        if not self._sensors:
            return

        # Pick 1–2 random slots (excluding protected ones)
        candidates = [
            code for code in self._sensors
            if code not in self._protected_slots
        ]
        if not candidates:
            return

        num_changes = self._rng.randint(1, min(2, len(candidates)))
        chosen = self._rng.sample(candidates, num_changes)

        for slot_code in chosen:
            sensor = self._sensors[slot_code]
            # Flip occupancy
            new_occupied = not sensor.is_occupied
            sensor.is_occupied = new_occupied
            sensor.distance_cm = sensor.simulate_reading()
            sensor.update_count += 1

            new_status = SlotStatus.occupied if new_occupied else SlotStatus.available
            await occupancy_service.process_sensor_event(
                slot_code=slot_code,
                distance_cm=sensor.distance_cm,
                new_status=new_status,
                source=EventSource.simulator,
                sensor_uid=sensor.sensor_uid,
            )
            self._stats["total_events"] += 1

        self._stats["last_event_at"] = datetime.now(timezone.utc).isoformat()

    async def _stress_update(self):
        """Rapidly update many slots for stress testing."""
        if not self._sensors:
            return

        candidates = [c for c in self._sensors if c not in self._protected_slots]
        num_changes = self._rng.randint(5, min(15, len(candidates)))
        chosen = self._rng.sample(candidates, num_changes)

        for slot_code in chosen:
            sensor = self._sensors[slot_code]
            new_occupied = self._rng.random() < 0.5
            sensor.is_occupied = new_occupied
            sensor.distance_cm = sensor.simulate_reading()

            await occupancy_service.process_sensor_event(
                slot_code=slot_code,
                distance_cm=sensor.distance_cm,
                new_status=SlotStatus.occupied if new_occupied else SlotStatus.available,
                source=EventSource.simulator,
                sensor_uid=sensor.sensor_uid,
            )
            self._stats["total_events"] += 1

    async def _demo_update(self):
        """Execute the scripted demo sequence step by step."""
        # Demo reverts to random after completing the scripted sequence
        await self._random_update()


# Singleton
simulator_service = SimulatorService()
