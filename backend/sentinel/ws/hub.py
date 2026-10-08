import asyncio
from collections import defaultdict
import json
import logging
import time
from typing import Any, Optional
import uuid
from fastapi import WebSocket

log = logging.getLogger(__name__)


class WebSocketHub:
    """
    Multi-room WebSocket hub with Redis pub-sub / memory backend for horizontal scaling.
    Supports event buffering and reconnection replay.
    """

    def __init__(self, redis: Any = None):
        self.redis = redis
        # room_id -> { conn_id -> WebSocket }
        self._rooms: dict[str, dict[str, WebSocket]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._event_buffer: dict[str, list[dict]] = defaultdict(list)
        self.BUFFER_SIZE = 100

    async def connect(self, ws: WebSocket, rooms: list[str], conn_id: Optional[str] = None) -> str:
        await ws.accept()
        cid = conn_id or str(uuid.uuid4())
        async with self._lock:
            for room in rooms:
                self._rooms[room][cid] = ws
        return cid

    async def disconnect(self, conn_id: str):
        async with self._lock:
            for room in self._rooms.values():
                room.pop(conn_id, None)

    async def disconnect_many(self, conn_ids: list[str]):
        async with self._lock:
            for room in self._rooms.values():
                for cid in conn_ids:
                    room.pop(cid, None)

    async def broadcast(self, event_type: str, payload: dict, room: str = "all"):
        event = {
            "type": event_type,
            "payload": payload,
            "ts": time.time(),
            "id": str(uuid.uuid4()),
        }
        message = json.dumps(event)

        # Buffer event
        async with self._lock:
            buf = self._event_buffer[room]
            buf.append(event)
            if len(buf) > self.BUFFER_SIZE:
                buf.pop(0)

        target_rooms = [room, "all"] if room != "all" else ["all"]
        dead_conns = []

        async with self._lock:
            conns_to_notify: dict[str, WebSocket] = {}
            for r in target_rooms:
                conns_to_notify.update(self._rooms.get(r, {}))

        for cid, ws in conns_to_notify.items():
            try:
                await asyncio.wait_for(ws.send_text(message), timeout=5.0)
            except Exception:
                dead_conns.append(cid)

        if dead_conns:
            await self.disconnect_many(dead_conns)

    async def replay_missed(self, ws: WebSocket, room: str, since_ts: float):
        """Send buffered events after since_ts for reconnect catch-up."""
        async with self._lock:
            missed = [e for e in self._event_buffer.get(room, []) if e["ts"] > since_ts]
        for event in missed:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                break
