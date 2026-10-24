"""ParkFlow AI — WebSocket Endpoint"""
import uuid
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates."""
    client_id = str(uuid.uuid4())[:8]
    await ws_manager.connect(websocket, client_id)

    try:
        while True:
            # Keep connection alive; handle ping/pong
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": "now"}))
            except (json.JSONDecodeError, Exception):
                pass  # Non-critical client messages ignored
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await ws_manager.disconnect(client_id)
