"""websockets/routes.py

WebSocket endpoint: /ws/{station_id}
Handles:
- Validation of station (ensuring station exists or reporting error)
- Connection registration
- Continuous keep-alive / client communication loop
- Graceful handling of disconnects and exceptions without crashing server
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.websockets.manager import ws_manager
from app.core.database import SessionLocal
from app.models.station import Station

logger = logging.getLogger(__name__)

ws_router = APIRouter(tags=["WebSocket"])


def _station_exists(station_id: str) -> bool:
    """Validate whether the station exists by ID or code (case-insensitive)."""
    db = SessionLocal()
    try:
        norm = station_id.strip()
        if norm.isdigit():
            st = db.query(Station).filter(Station.id == int(norm)).first()
            if st:
                return True
        st = db.query(Station).filter(Station.code.ilike(norm)).first()
        return st is not None
    except Exception as exc:
        logger.error("Error checking station existence for '%s': %s", station_id, exc)
        return True  # Fallback to allow connection in case DB is transiently unreachable
    finally:
        db.close()


@ws_router.websocket("/ws/{station_id}")
async def websocket_station_endpoint(websocket: WebSocket, station_id: str):
    norm_station = station_id.strip().lower()

    # Validate station existence
    if not _station_exists(norm_station):
        logger.warning("Rejected WebSocket connection: Station '%s' not found", station_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid station_id")
        return

    await ws_manager.connect(websocket, norm_station)
    try:
        while True:
            # Receive text or keepalive ping/pong from client
            data = await websocket.receive_text()
            logger.debug("Received WebSocket message from client on station '%s': %s", norm_station, data)
    except WebSocketDisconnect:
        logger.info("Client cleanly disconnected from /ws/%s", norm_station)
        ws_manager.disconnect(websocket, norm_station)
    except Exception as exc:
        logger.error("Unexpected WebSocket error on station '%s': %s", norm_station, exc, exc_info=True)
        ws_manager.disconnect(websocket, norm_station)
