import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List
from starlette.websockets import WebSocketState
from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code (e.g. datetime)."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    raise TypeError(f"Type {type(obj)} not serializable")


class ConnectionManager:
    """Manages real-time WebSocket connections per station.

    Supports:
    - Multiple connected clients per station or across stations
    - Target broadcasts by station_id (case-insensitive)
    - Global broadcasts across all clients
    - Clean disconnection and graceful error handling
    """

    def __init__(self) -> None:
        # Maps normalized station_id (lowercase string) to list of active WebSockets
        self.station_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, station_id: str) -> None:
        await websocket.accept()
        norm_station = str(station_id).strip().lower()
        if norm_station not in self.station_connections:
            self.station_connections[norm_station] = []
        self.station_connections[norm_station].append(websocket)
        logger.info(
            "WebSocket client connected for station '%s' (active in station: %d, total active: %d)",
            norm_station,
            len(self.station_connections[norm_station]),
            self.total_connections,
        )

    def disconnect(self, websocket: WebSocket, station_id: str = None) -> None:
        norm_station = str(station_id).strip().lower() if station_id else None
        if norm_station and norm_station in self.station_connections:
            if websocket in self.station_connections[norm_station]:
                self.station_connections[norm_station].remove(websocket)
            if not self.station_connections[norm_station]:
                del self.station_connections[norm_station]
        else:
            # Search and remove from all stations if station_id is not specified
            for sid in list(self.station_connections.keys()):
                if websocket in self.station_connections[sid]:
                    self.station_connections[sid].remove(websocket)
                if not self.station_connections[sid]:
                    del self.station_connections[sid]

        logger.info("WebSocket client disconnected. Total active: %d", self.total_connections)

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self.station_connections.values())

    async def broadcast_to_station(self, station_id: str, message: Dict[str, Any]) -> None:
        """Broadcast an event payload directly to all clients connected to station_id.
        Handles client disconnects or socket errors cleanly without raising or crashing.
        """
        norm_station = str(station_id).strip().lower()
        clients = self.station_connections.get(norm_station, [])
        if not clients:
            return

        json_text = json.dumps(message, default=_json_serial)
        disconnected: List[WebSocket] = []
        for ws in list(clients):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(json_text)
                else:
                    disconnected.append(ws)
            except Exception as exc:
                logger.warning(
                    "Error sending to WebSocket client on station '%s': %s",
                    norm_station,
                    exc,
                )
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, norm_station)

    async def broadcast_all(self, message: Dict[str, Any]) -> None:
        """Broadcast message to every connected client across all stations."""
        for sid in list(self.station_connections.keys()):
            await self.broadcast_to_station(sid, message)


# Global singleton
ws_manager = ConnectionManager()
