from datetime import datetime
import hashlib
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sentinel.core.database import get_db
from sentinel.models.agent import (
    Agent,
    AgentCreate,
    AgentOut,
    AgentStatus,
    AgentStatusUpdate,
    AgentTelemetry30d,
    HumanOwner,
    HumanOwnerOut,
)
from sentinel.trust.scorer import (
    TrustEvent,
    TrustEventType,
    get_trust_score_breakdown,
)

router = APIRouter(prefix="/agents", tags=["Agent Registry & AI Passport"])


@router.get("", response_model=list[AgentOut])
async def list_agents(
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).options(selectinload(Agent.owner))
    if status:
        stmt = stmt.where(Agent.status == status)
    if department:
        stmt = stmt.where(Agent.department == department)
    res = await db.execute(stmt)
    agents = res.scalars().all()
    return agents


@router.post("", response_model=AgentOut)
async def register_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    agent_id = f"agt_{uuid.uuid4().hex[:12]}"
    client_id = f"client_{body.name.lower()}_{uuid.uuid4().hex[:6]}"
    default_secret = f"sec_{uuid.uuid4().hex}"
    secret_hash = hashlib.sha256(default_secret.encode()).hexdigest()

    permitted = body.permitted_actions or [
        "order.read",
        "ticket.create",
        "faq.retrieve",
        "refund.create",
        "email.send",
    ]
    forbidden = body.forbidden_actions or [
        "bank_details.read",
        "db.export.all",
        "password.reset",
        "cred.access.any",
        "agent.elevate",
        "infra.modify",
    ]
    hitl = body.hitl_actions or [
        "refund.create (> ₹10,000)",
        "account.close",
        "customer.data.bulk_delete",
        "contract.amend",
        "pii.export",
    ]

    agent = Agent(
        agent_id=agent_id,
        name=body.name,
        display_name=body.display_name,
        model_architecture=body.model_architecture or "claude-sonnet-4-6",
        role=body.role or "SupportAgent",
        department=body.department or "CustomerSupport",
        status=AgentStatus.ACTIVE.value,
        trust_score=85.0,
        human_owner_id=body.human_owner_id,
        client_id=client_id,
        client_secret_hash=secret_hash,
        permitted_actions=permitted,
        forbidden_actions=forbidden,
        hitl_actions=hitl,
        escalation_config={"refund.create": {"threshold": 10000, "approver": "finance_manager"}},
        created_at=datetime.utcnow(),
        last_active_at=datetime.utcnow(),
        provisioned_by="Governance Admin",
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent_passport(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).options(selectinload(Agent.owner)).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}/status", response_model=AgentOut)
async def update_agent_status(
    agent_id: str,
    body: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).options(selectinload(Agent.owner)).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = body.status.value
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}/telemetry", response_model=AgentTelemetry30d)
async def get_agent_telemetry(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentTelemetry30d(
        agent_id=agent.agent_id,
        total_actions=1247,
        auto_allowed=1198,
        notify_proceed=15,
        hitl_approved=11,
        hitl_rejected=0,
        hitl_timed_out=0,
        blocked_tier4=23,
        input_tokens_total=4200000,
        output_tokens_total=1100000,
        cost_usd_total=4.32,
        avg_response_ms=142.5,
        computed_at=datetime.utcnow(),
    )


@router.get("/{agent_id}/trust-score")
async def get_agent_trust_score(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Generate synthetic telemetry breakdown consistent with current score
    events = [
        TrustEvent(TrustEventType.SUCCESS, datetime.utcnow()) for _ in range(1198)
    ]
    if agent.trust_score < 85.0:
        pen = int((85.0 - agent.trust_score) / 15.0) or 1
        events.extend([TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()) for _ in range(pen)])

    breakdown = get_trust_score_breakdown(events, current_score=agent.trust_score)

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "trust_score": agent.trust_score,
        "status": agent.status,
        "breakdown": {
            "base_score": breakdown.base_score,
            "success_contribution": breakdown.success_contribution,
            "success_count": breakdown.success_count,
            "violation_penalty": breakdown.violation_penalty,
            "violation_count": breakdown.violation_count,
            "rejection_penalty": breakdown.rejection_penalty,
            "rejection_count": breakdown.rejection_count,
            "temporal_decay_adjustment": breakdown.temporal_decay_adjustment,
            "total": agent.trust_score,
        },
    }


@router.post("/{agent_id}/reset-score")
async def reset_agent_trust_score(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).where((Agent.agent_id == agent_id) | (Agent.name == agent_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.trust_score = 85.0
    agent.status = AgentStatus.ACTIVE.value
    await db.commit()
    return {"agent_id": agent.agent_id, "trust_score": 85.0, "status": "ACTIVE"}
