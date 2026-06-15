"""WebSocket connection manager for real-time updates."""

from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "wincc": set(),
            "activity": set()
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[client_type].add(websocket)
        logger.info(f"New {client_type} client connected. Total: {len(self.active_connections[client_type])}")

    async def disconnect(self, websocket: WebSocket, client_type: str):
        """Disconnect a WebSocket client."""
        self.active_connections[client_type].discard(websocket)
        logger.info(f"{client_type} client disconnected. Total: {len(self.active_connections[client_type])}")

    async def broadcast_to_type(self, message: Dict, client_type: str):
        """Broadcast a message to all clients of a specific type."""
        for connection in self.active_connections[client_type].copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_type} client: {e}")
                await self.disconnect(connection, client_type)

    async def broadcast_dashboard_update(self, data: Dict):
        """Broadcast a dashboard update."""
        await self.broadcast_to_type({"type": "dashboard_update", "data": data}, "dashboard")

    async def broadcast_wincc_update(self, data: Dict):
        """Broadcast a WinCC status update."""
        await self.broadcast_to_type({"type": "wincc_update", "data": data}, "wincc")

    async def broadcast_activity_update(self, data: Dict):
        """Broadcast an activity log update."""
        await self.broadcast_to_type({"type": "activity_update", "data": data}, "activity")

# Global connection manager instance
manager = ConnectionManager()
