from datetime import datetime
import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.auth.token_manager import TokenManager
from sentinel.core.database import get_db
from sentinel.hitl.queue import HITLQueue
from sentinel.ledger.writer import AuditLedger
from sentinel.models.agent import Agent, AgentStatus
from sentinel.models.audit import Violation
from sentinel.ws.hub import WebSocketHub

router = APIRouter(prefix="/admin", tags=["Kill Switch & Incident Response"])
log = logging.getLogger(__name__)


class KillSwitchRequest(BaseModel):
    reason: str = "indirect_prompt_injection_suspected"
    triggered_by: Optional[str] = "admin:priya_sharma"


class RestoreAgentRequest(BaseModel):
    rationale: str = "Investigation completed. Compromised prompt vector patched."
    restored_by: Optional[str] = "admin:priya_sharma"
    new_trust_score: Optional[float] = 85.0


class KillSwitchResponse(BaseModel):
    agent_id: str
    status: str
    suspended_at: str
    hitl_requests_purged: int
    elapsed_ms: float
    message: str


@router.post("/agents/{agent_id}/kill", response_model=KillSwitchResponse)
async def activate_kill_switch(
    agent_id: str,
    body: KillSwitchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Kills and isolates an agent in < 1 second (typically < 40ms):
    1. Updates Agent Registry status to SUSPENDED.
    2. Revokes all current and future tokens in Redis O(1).
    3. Purges and rejects all pending HITL items for this agent.
    4. Broadcasts agent:suspended across WebSocket.
    5. Writes sealed KILL_SWITCH_ACTIVATED audit entry to hash chain.
    """
    start = time.perf_counter()
    app_state = request.app.state
    if not hasattr(app_state, "token_manager"):
        from main import ensure_app_state
        await ensure_app_state(request.app)
        app_state = request.app.state

    token_mgr: TokenManager = app_state.token_manager
    hitl_queue: HITLQueue = app_state.hitl_queue
    ws_hub: WebSocketHub = app_state.ws_hub
    ledger = AuditLedger(db)

    # 1. Update DB Status
    stmt = select(Agent).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = AgentStatus.SUSPENDED.value
    agent.trust_score = min(agent.trust_score, 35.0)
    await db.commit()

    # 2. Redis O(1) Blacklist
    await token_mgr.revoke_all_agent_tokens(agent.agent_id)

    # 3. Purge pending HITL queue
    purged_count = await hitl_queue.purge_agent(agent.agent_id)

    # 4. Broadcast via WebSocket
    await ws_hub.broadcast(
        "agent:suspended",
        {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "triggered_by": body.triggered_by,
            "reason": body.reason,
            "timestamp": datetime.utcnow().isoformat(),
        },
        room="all",
    )

    # 5. Write audit entry
    await ledger.write_entry(
        agent_id=agent.agent_id,
        action="KILL_SWITCH_ACTIVATED",
        resource_id=body.triggered_by or "SYSTEM",
        policy_id=None,
        decision="KILL_SWITCH_ACTIVATED",
        tier=4,
        context_snapshot={"reason": body.reason, "triggered_by": body.triggered_by},
        cedar_detail={"tokens_revoked": "all", "hitl_purged": purged_count},
    )

    elapsed = (time.perf_counter() - start) * 1000

    return KillSwitchResponse(
        agent_id=agent.agent_id,
        status="SUSPENDED",
        suspended_at=datetime.utcnow().isoformat(),
        hitl_requests_purged=purged_count,
        elapsed_ms=round(elapsed, 1),
        message=f"Agent {agent.name} fully isolated in {round(elapsed, 1)}ms. All tokens revoked.",
    )


@router.post("/agents/{agent_id}/restore")
async def restore_agent(
    agent_id: str,
    body: RestoreAgentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    app_state = request.app.state
    if not hasattr(app_state, "token_manager"):
        from main import ensure_app_state
        await ensure_app_state(request.app)
        app_state = request.app.state

    token_mgr: TokenManager = app_state.token_manager
    ws_hub: WebSocketHub = app_state.ws_hub
    ledger = AuditLedger(db)

    stmt = select(Agent).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = AgentStatus.ACTIVE.value
    agent.trust_score = body.new_trust_score or 85.0
    await db.commit()

    # Clear Redis blacklist
    await token_mgr.clear_agent_revocation(agent.agent_id)

    # Broadcast restore
    await ws_hub.broadcast(
        "agent:restored",
        {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "restored_by": body.restored_by,
            "rationale": body.rationale,
            "trust_score": agent.trust_score,
            "timestamp": datetime.utcnow().isoformat(),
        },
        room="all",
    )

    await ledger.write_entry(
        agent_id=agent.agent_id,
        action="AGENT_RESTORED",
        resource_id=body.restored_by or "SYSTEM",
        policy_id=None,
        decision="ALLOW",
        tier=1,
        context_snapshot={"rationale": body.rationale, "restored_by": body.restored_by},
        cedar_detail={"new_trust_score": agent.trust_score},
    )

    return {
        "agent_id": agent.agent_id,
        "status": "ACTIVE",
        "trust_score": agent.trust_score,
        "message": f"Agent {agent.name} restored to ACTIVE status.",
    }


@router.get("/violations")
async def list_violations(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Violation)
    if agent_id:
        stmt = stmt.where(Violation.agent_id == agent_id)
    stmt = stmt.order_by(desc(Violation.detected_at)).limit(limit)
    res = await db.execute(stmt)
    violations = res.scalars().all()
    return violations


@router.get("/alerts")
async def get_active_alerts(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Returns real-time computed alerts based on recent violations and agent statuses."""
    stmt = select(Agent).where(Agent.status == AgentStatus.SUSPENDED.value)
    res = await db.execute(stmt)
    suspended_agents = res.scalars().all()

    # Query recent violations
    stmt_v = select(Violation).order_by(desc(Violation.detected_at)).limit(10)
    res_v = await db.execute(stmt_v)
    recent_v = res_v.scalars().all()

    alerts = []
    for a in suspended_agents:
        alerts.append({
            "id": f"alert_sus_{a.agent_id}",
            "level": "critical",
            "agent_id": a.agent_id,
            "agent_name": a.name,
            "title": f"Agent {a.name} is SUSPENDED",
            "message": "Agent has been isolated by Kill Switch. Tokens revoked.",
            "recommendation": "Review audit log and verify chain integrity before restoring.",
            "created_at": a.last_active_at.isoformat(),
        })

    # Group violations
    if len(recent_v) >= 3:
        alerts.append({
            "id": "alert_viol_velocity",
            "level": "critical",
            "agent_id": recent_v[0].agent_id,
            "agent_name": "SupportAgent",
            "title": "High Violation Velocity Detected (ASI01 / ASI03)",
            "message": f"Multiple forbidden resource access attempts detected in tight window.",
            "recommendation": "PAUSE AGENT immediately to prevent data exfiltration.",
            "created_at": datetime.utcnow().isoformat(),
        })

    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    return {"alert_id": alert_id, "acknowledged": True, "ts": datetime.utcnow().isoformat()}
