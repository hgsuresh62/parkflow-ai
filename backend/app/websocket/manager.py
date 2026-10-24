"""ParkFlow AI — WebSocket Connection Manager"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events to all clients.
    Thread-safe for asyncio environments.
    """

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id} (total: {len(self._connections)})")

        # Send initial connection acknowledgment
        await self._send_to(websocket, {
            "type": "connection.established",
            "timestamp": _now(),
            "data": {
                "client_id": client_id,
                "message": "Connected to ParkFlow AI real-time updates",
            },
        })

    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.pop(client_id, None)
        logger.info(f"WebSocket disconnected: {client_id} (total: {len(self._connections)})")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        if not self._connections:
            return

        message = {
            "type": event_type,
            "timestamp": _now(),
            "data": data,
        }

        disconnected = []
        async with self._lock:
            clients = list(self._connections.items())

        for client_id, websocket in clients:
            try:
                await self._send_to(websocket, message)
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up dead connections
        for client_id in disconnected:
            await self.disconnect(client_id)

    async def send_to_client(self, client_id: str, event_type: str, data: Dict[str, Any]):
        """Send a message to a specific client."""
        async with self._lock:
            websocket = self._connections.get(client_id)

        if websocket:
            try:
                await self._send_to(websocket, {
                    "type": event_type,
                    "timestamp": _now(),
                    "data": data,
                })
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")
                await self.disconnect(client_id)

    async def _send_to(self, websocket: WebSocket, message: Dict[str, Any]):
        """Serialize and send a message to a single WebSocket."""
        await websocket.send_text(json.dumps(message, default=str))

    @property
    def client_count(self) -> int:
        return len(self._connections)

    @property
    def connected_clients(self) -> list:
        return list(self._connections.keys())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Singleton instance
ws_manager = ConnectionManager()


# ============================================================
# Event Broadcasting Helpers
# ============================================================

async def broadcast_slot_updated(
    slot_code: str,
    status: str,
    floor: int,
    source: str,
    extra: Optional[Dict] = None,
):
    data = {
        "slot_code": slot_code,
        "status": status,
        "floor": floor,
        "source": source,
    }
    if extra:
        data.update(extra)
    await ws_manager.broadcast("slot.updated", data)


async def broadcast_reservation_created(reservation_code: str, slot_code: str, expires_at: str):
    await ws_manager.broadcast("reservation.created", {
        "reservation_code": reservation_code,
        "slot_code": slot_code,
        "expires_at": expires_at,
    })


async def broadcast_reservation_cancelled(reservation_code: str, slot_code: str):
    await ws_manager.broadcast("reservation.cancelled", {
        "reservation_code": reservation_code,
        "slot_code": slot_code,
    })


async def broadcast_route_invalidated(route_id: str, slot_code: str, reason: str):
    await ws_manager.broadcast("route.invalidated", {
        "route_id": route_id,
        "slot_code": slot_code,
        "reason": reason,
    })


async def broadcast_sensor_status(sensor_uid: str, status: str, slot_code: Optional[str] = None):
    await ws_manager.broadcast("sensor.status_changed", {
        "sensor_uid": sensor_uid,
        "status": status,
        "slot_code": slot_code,
    })


async def broadcast_simulator_event(event: str, details: Optional[Dict] = None):
    await ws_manager.broadcast("simulator.event", {
        "event": event,
        "details": details or {},
    })
