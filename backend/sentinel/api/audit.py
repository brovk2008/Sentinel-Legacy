from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.core.database import get_db
from sentinel.ledger.writer import AuditLedger
from sentinel.models.audit import AuditEntry, AuditEntryOut
from sentinel.models.hitl import HITLRecord, HITLRecordOut

router = APIRouter(prefix="/audit", tags=["Audit Ledger & Hash Chain"])


@router.get("/entries", response_model=list[AuditEntryOut])
async def list_audit_entries(
    agent_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    decision: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    ledger = AuditLedger(db)
    entries = await ledger.query_entries(
        agent_id=agent_id,
        action=action,
        decision=decision,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )
    return entries


@router.get("/entries/{entry_id}")
async def get_audit_entry_detail(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditEntry).where(AuditEntry.entry_id == entry_id)
    res = await db.execute(stmt)
    entry = res.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")

    # Fetch associated HITL record if any
    hitl_stmt = select(HITLRecord).where(HITLRecord.entry_id == entry_id)
    hitl_res = await db.execute(hitl_stmt)
    hitl_rec = hitl_res.scalar_one_or_none()

    return {
        "entry": AuditEntryOut.model_validate(entry),
        "hitl_record": HITLRecordOut.model_validate(hitl_rec) if hitl_rec else None,
    }


@router.get("/agents/{agent_id}/timeline")
async def get_agent_timeline(
    agent_id: str,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Returns the full chronological activity timeline for forensic analysis."""
    stmt = select(AuditEntry).where(AuditEntry.agent_id == agent_id).order_by(desc(AuditEntry.sequence_num)).limit(limit)
    res = await db.execute(stmt)
    entries = res.scalars().all()
    return entries


@router.get("/verify")
async def verify_chain_integrity(
    db: AsyncSession = Depends(get_db),
):
    """
    Cryptographically walks the entire SHA-256 hash chain.
    Verifies that no entry has been altered, deleted, or inserted out of order.
    """
    ledger = AuditLedger(db)
    is_valid, bad_seq = await ledger.verify_chain()

    # Count total entries
    stmt = select(AuditEntry.sequence_num).order_by(desc(AuditEntry.sequence_num)).limit(1)
    res = await db.execute(stmt)
    total = res.scalar_one_or_none() or 0

    return {
        "is_valid": is_valid,
        "tampered_sequence": bad_seq,
        "total_entries": total,
        "verified_at": datetime.utcnow().isoformat(),
        "algorithm": "SHA-256",
        "message": "✅ Cryptographic hash chain integrity fully verified" if is_valid else f"❌ Hash chain broken at sequence #{bad_seq}",
    }
