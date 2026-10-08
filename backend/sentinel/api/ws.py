import asyncio
import json
import logging
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sentinel.ws.hub import WebSocketHub

router = APIRouter(tags=["WebSocket Real-Time Plane"])
log = logging.getLogger(__name__)


@router.websocket("/ws/dashboard")
async def dashboard_websocket_endpoint(
    websocket: WebSocket,
    role: str = Query("governance_admin"),
    last_seq_ts: float = Query(0.0),
):
    hub: WebSocketHub = websocket.app.state.ws_hub
    rooms = ["all", f"role:{role}"]
    conn_id = await hub.connect(websocket, rooms)

    # Replay events missed during disconnect if reconnecting
    if last_seq_ts > 0.0:
        await hub.replay_missed(websocket, "all", last_seq_ts)

    # 25-second heartbeat ping
    async def heartbeat():
        while True:
            try:
                await asyncio.sleep(25)
                await asyncio.wait_for(websocket.send_text('{"type":"ping"}'), timeout=5.0)
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "pong":
                    continue
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.debug("WebSocket exception: %s", e)
    finally:
        hb_task.cancel()
        await hub.disconnect(conn_id)
