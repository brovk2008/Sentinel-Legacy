from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.core.database import get_db
from sentinel.hitl.queue import HITLQueue
from sentinel.models.hitl import HITLDecisionSubmit, HITLRecord, HITLRecordOut

router = APIRouter(prefix="/hitl", tags=["Human-in-the-Loop (HITL)"])


async def get_hitl_queue(request: Request) -> HITLQueue:
    if not hasattr(request.app.state, "hitl_queue"):
        from main import ensure_app_state
        await ensure_app_state(request.app)
    return request.app.state.hitl_queue


@router.get("/pending")
async def list_pending_approvals(
    hitl_queue: HITLQueue = Depends(get_hitl_queue),
):
    """Returns all currently queued HITL decisions awaiting human judgment."""
    pending_items = await hitl_queue.list_pending()
    return pending_items


@router.get("/history", response_model=list[HITLRecordOut])
async def list_resolved_history(
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Returns resolved HITL requests for forensic and audit review."""
    stmt = select(HITLRecord).where(HITLRecord.decision != "pending").order_by(desc(HITLRecord.created_at)).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return records


@router.get("/{hitl_id}", response_model=HITLRecordOut)
async def get_hitl_detail(
    hitl_id: str,
    hitl_queue: HITLQueue = Depends(get_hitl_queue),
    db: AsyncSession = Depends(get_db),
):
    # Check cache first
    cached = await hitl_queue.get_item(hitl_id)
    if cached:
        return cached

    stmt = select(HITLRecord).where(HITLRecord.hitl_id == hitl_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="HITL request not found")
    return rec


@router.post("/{hitl_id}/decision")
async def submit_human_decision(
    hitl_id: str,
    body: HITLDecisionSubmit,
    hitl_queue: HITLQueue = Depends(get_hitl_queue),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a human approval or rejection with mandatory two-factor judgment:
    1. Checkbox acknowledgment
    2. Written rationale
    Releases the waiting agent thread via Redis signal.
    """
    if body.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    if not body.checkbox_ack and body.decision == "approved":
        raise HTTPException(status_code=400, detail="Must acknowledge parameter review checkbox")

    if not body.rationale or len(body.rationale.strip()) < 5:
        raise HTTPException(status_code=400, detail="A rationale is required for human judgment")

    result = await hitl_queue.submit_decision(
        hitl_id=hitl_id,
        decision=body.decision,
        approver_id=body.approver_id or "own_priya_sharma_01",
        approver_name=body.approver_name or "Priya Sharma",
        approver_email=body.approver_email or "priya@corp.com",
        rationale=body.rationale,
        checkbox_ack=body.checkbox_ack,
    )

    # Sync DB record
    stmt = select(HITLRecord).where(HITLRecord.hitl_id == hitl_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if rec:
        rec.decision = body.decision
        rec.rationale = body.rationale
        rec.approver_id = body.approver_id or "own_priya_sharma_01"
        rec.approver_name = body.approver_name or "Priya Sharma"
        rec.approver_email = body.approver_email or "priya@corp.com"
        rec.checkbox_ack = body.checkbox_ack
        rec.decided_at = datetime.utcnow()
        await db.commit()

    return {
        "hitl_id": hitl_id,
        "decision": body.decision,
        "status": "resolved",
        "rationale": body.rationale,
        "resolved_at": datetime.utcnow().isoformat(),
    }
