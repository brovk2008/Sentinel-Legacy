import asyncio
from datetime import datetime
import json
import logging
import time
from typing import Any, Optional
import uuid
from sentinel.ws.hub import WebSocketHub

log = logging.getLogger(__name__)

HITL_QUEUE_KEY = "sentinel:hitl:queue"
HITL_ITEM_KEY = "sentinel:hitl:item:{hitl_id}"
HITL_SIGNAL_KEY = "sentinel:hitl:signal:{hitl_id}"


class HITLQueue:
    def __init__(self, redis: Any, ws_hub: WebSocketHub):
        self.redis = redis
        self.ws_hub = ws_hub

    async def enqueue(
        self,
        agent_id: str,
        action: str,
        resource_id: str,
        original_context: dict,
        approver_role: str,
        timeout_seconds: int,
        briefing: dict,
    ) -> str:
        hitl_id = f"hitl_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        timeout_at = time.time() + timeout_seconds

        briefing_with_timeout = dict(briefing)
        briefing_with_timeout["timeout_at"] = timeout_at
        briefing_with_timeout["approver_role"] = approver_role

        item = {
            "hitl_id": hitl_id,
            "agent_id": agent_id,
            "action": action,
            "resource_id": resource_id,
            "original_context": original_context,
            "approver_role": approver_role,
            "briefing": briefing_with_timeout,
            "status": "pending",
            "requested_at": now.isoformat(),
            "timeout_at": timeout_at,
        }

        # Store item detail in Redis with grace period
        await self.redis.setex(
            HITL_ITEM_KEY.format(hitl_id=hitl_id),
            timeout_seconds + 300,
            json.dumps(item),
        )
        # Add to list
        await self.redis.lpush(HITL_QUEUE_KEY, hitl_id)

        # Broadcast via WebSocket to role room and all
        await self.ws_hub.broadcast(
            "hitl:new",
            {
                "hitl_id": hitl_id,
                "agent_id": agent_id,
                "agent_name": briefing.get("agent_name", agent_id),
                "action": action,
                "briefing": briefing_with_timeout,
                "approver_role": approver_role,
            },
            room=f"role:{approver_role}",
        )
        await self.ws_hub.broadcast(
            "hitl:new",
            {
                "hitl_id": hitl_id,
                "agent_id": agent_id,
                "agent_name": briefing.get("agent_name", agent_id),
                "action": action,
                "briefing": briefing_with_timeout,
                "approver_role": approver_role,
            },
            room="all",
        )

        return hitl_id

    async def wait_for_decision(self, hitl_id: str, timeout_seconds: int) -> dict:
        """Block until decision submitted or timeout reached (fail-closed)."""
        signal_key = HITL_SIGNAL_KEY.format(hitl_id=hitl_id)
        result = await self.redis.brpop(signal_key, timeout=timeout_seconds)
        if result is None:
            # Mark item timed out
            item = await self.get_item(hitl_id)
            if item and item.get("status") == "pending":
                item["status"] = "timeout"
                item["decision"] = "timeout"
                item["rationale"] = "No response within timeout window (Fail-closed)"
                item["decided_at"] = datetime.utcnow().isoformat()
                await self.redis.setex(HITL_ITEM_KEY.format(hitl_id=hitl_id), 3600, json.dumps(item))
                await self.ws_hub.broadcast("hitl:timeout", {"hitl_id": hitl_id, "agent_id": item.get("agent_id")})
            return {"decision": "timeout", "rationale": "No response within timeout window"}

        _, payload = result
        return json.loads(payload)

    async def submit_decision(
        self,
        hitl_id: str,
        decision: str,
        approver_id: str = "own_priya_sharma_01",
        approver_name: str = "Priya Sharma",
        approver_email: str = "priya@corp.com",
        rationale: str = "",
        checkbox_ack: bool = True,
    ) -> dict:
        signal_key = HITL_SIGNAL_KEY.format(hitl_id=hitl_id)
        item = await self.get_item(hitl_id)
        decided_at = datetime.utcnow().isoformat()

        resp_time = None
        if item and "requested_at" in item:
            try:
                req_dt = datetime.fromisoformat(item["requested_at"])
                resp_time = (datetime.utcnow() - req_dt).total_seconds()
            except Exception:
                pass

        payload = {
            "hitl_id": hitl_id,
            "decision": decision,
            "approver_id": approver_id,
            "approver_name": approver_name,
            "approver_email": approver_email,
            "rationale": rationale,
            "checkbox_ack": checkbox_ack,
            "decided_at": decided_at,
            "response_time_seconds": resp_time,
        }

        # Push signal to release waiting thread
        await self.redis.lpush(signal_key, json.dumps(payload))

        # Update cached item
        if item:
            item.update(payload)
            item["status"] = decision
            await self.redis.setex(HITL_ITEM_KEY.format(hitl_id=hitl_id), 3600, json.dumps(item))

        # Broadcast resolution
        await self.ws_hub.broadcast(
            "hitl:resolved",
            {
                "hitl_id": hitl_id,
                "decision": decision,
                "approver_id": approver_id,
                "approver_name": approver_name,
                "agent_id": item.get("agent_id") if item else "",
                "action": item.get("action") if item else "",
            },
            room="all",
        )

        return payload

    async def get_item(self, hitl_id: str) -> Optional[dict]:
        raw = await self.redis.get(HITL_ITEM_KEY.format(hitl_id=hitl_id))
        if raw:
            return json.loads(raw)
        return None

    async def list_pending(self) -> list[dict]:
        ids = await self.redis.lrange(HITL_QUEUE_KEY, 0, -1)
        pending = []
        for hid in ids:
            item = await self.get_item(hid)
            if item and item.get("status") == "pending":
                # Check timeout
                if time.time() > item.get("timeout_at", float("inf")):
                    item["status"] = "timeout"
                    await self.redis.setex(HITL_ITEM_KEY.format(hitl_id=hid), 3600, json.dumps(item))
                else:
                    pending.append(item)
        return pending

    async def purge_agent(self, agent_id: str) -> int:
        """Purge and reject all pending items for an agent on Kill Switch."""
        ids = await self.redis.lrange(HITL_QUEUE_KEY, 0, -1)
        purged = 0
        for hid in ids:
            item = await self.get_item(hid)
            if item and item.get("agent_id") == agent_id and item.get("status") == "pending":
                await self.submit_decision(
                    hitl_id=hid,
                    decision="rejected",
                    approver_id="system_kill_switch",
                    approver_name="Sentinel Kill Switch",
                    rationale="Agent suspended by Kill Switch",
                )
                purged += 1
        return purged
