"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.core.websocket import manager
from app.core.security import verify_ws_token
from app.services.wincc_service import wincc_monitor
import logging
import asyncio

router = APIRouter(tags=["websocket"], prefix="/ws")
logger = logging.getLogger(__name__)


async def _authorize(websocket: WebSocket) -> bool:
    """Validate the ?token= query param before accepting the connection.
    Closes with policy-violation (1008) if the token is missing/invalid."""
    claims = verify_ws_token(websocket.query_params.get("token"))
    if claims is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False
    return True

@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard updates."""
    if not await _authorize(websocket):
        return
    await manager.connect(websocket, "dashboard")
    try:
        while True:
            # Wait for any incoming messages (heartbeat)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        manager.disconnect(websocket, "dashboard")

@router.websocket("/wincc")
async def websocket_wincc(websocket: WebSocket):
    """WebSocket endpoint for WinCC updates."""
    if not await _authorize(websocket):
        return
    await manager.connect(websocket, "wincc")
    try:
        while True:
            # Send current WinCC status
            await manager.broadcast_wincc_update(wincc_monitor.get_status())
            await asyncio.sleep(1)  # Update every second
    except WebSocketDisconnect:
        manager.disconnect(websocket, "wincc")
    except Exception as e:
        logger.error(f"WinCC WebSocket error: {e}")
        manager.disconnect(websocket, "wincc")

@router.websocket("/activity")
async def websocket_activity(websocket: WebSocket):
    """WebSocket endpoint for activity log updates."""
    if not await _authorize(websocket):
        return
    await manager.connect(websocket, "activity")
    try:
        while True:
            # Wait for any incoming messages (heartbeat)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "activity")
    except Exception as e:
        logger.error(f"Activity WebSocket error: {e}")
        manager.disconnect(websocket, "activity")
