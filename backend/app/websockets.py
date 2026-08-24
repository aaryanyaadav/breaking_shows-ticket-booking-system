import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Map show_id -> List of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, show_id: str):
        await websocket.accept()
        if show_id not in self.active_connections:
            self.active_connections[show_id] = []
        self.active_connections[show_id].append(websocket)

    def disconnect(self, websocket: WebSocket, show_id: str):
        if show_id in self.active_connections:
            if websocket in self.active_connections[show_id]:
                self.active_connections[show_id].remove(websocket)
            if not self.active_connections[show_id]:
                del self.active_connections[show_id]

    async def broadcast_seat_update(self, show_id: str, payload: dict):
        """
        Payload structure e.g.:
        {
            "event": "SEAT_STATUS_CHANGED",
            "show_id": "...",
            "seat_ids": ["..."],
            "status": "HELD" | "AVAILABLE" | "BOOKED" | "OFFERED",
            "timestamp": "..."
        }
        """
        if show_id in self.active_connections:
            dead_connections = []
            message = json.dumps(payload)
            for connection in self.active_connections[show_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            
            for dead in dead_connections:
                self.disconnect(dead, show_id)

ws_manager = ConnectionManager()
