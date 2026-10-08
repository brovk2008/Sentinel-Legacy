from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.core.database import get_db
from sentinel.ledger.writer import AuditLedger
from sentinel.models.audit import AuditEntry
from sentinel.models.hitl import HITLRecord

router = APIRouter(prefix="/compliance", tags=["Regulatory Compliance (DPDPA / EU AI Act)"])


class ErasureRequest(BaseModel):
    subject_id: str
    reason: Optional[str] = "Data principal revocation of consent"


@router.get("/data-access")
async def dpdpa_data_access_report(
    subject_id: str = Query(..., description="Data Principal's customer ID"),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    DPDPA 2023 Section 11 Right to Information:
    Returns complete chronological log of all AI agents that accessed this customer's data.
    """
    ledger = AuditLedger(db)
    entries = await ledger.query_by_resource(subject_id, from_date, to_date)
    is_valid, _ = await ledger.verify_chain()

    return {
        "subject_id": subject_id,
        "regulation": "India DPDP Act 2023 & DPDP Rules 2025 (Section 11)",
        "report_generated_at": datetime.utcnow().isoformat(),
        "total_access_events": len(entries),
        "agents_that_accessed": list({e["agent_id"] for e in entries}),
        "data_access_log": entries,
        "chain_integrity_verified": is_valid,
    }


@router.post("/erasure-request")
async def process_erasure_request(
    body: ErasureRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    DPDPA Section 13 Right to Erasure / Correction:
    Withdraws consent for future agent access.
    """
    ledger = AuditLedger(db)
    await ledger.write_entry(
        agent_id="SYSTEM_COMPLIANCE",
        action="consent.withdraw",
        resource_id=body.subject_id,
        policy_id=None,
        decision="CONSENT_REVOKED",
        tier=1,
        context_snapshot={"reason": body.reason, "revoked_at": datetime.utcnow().isoformat()},
        cedar_detail={"compliance_event": "DPDPA_SECTION_13"},
    )

    return {
        "subject_id": body.subject_id,
        "status": "CONSENT_WITHDRAWN",
        "message": f"Consent withdrawn for {body.subject_id}. Cedar will immediately DENY future agent requests.",
        "processed_at": datetime.utcnow().isoformat(),
    }


@router.get("/agents/{agent_id}/human-accountability")
async def get_human_accountability_record(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    EU AI Act Article 14 Compliance:
    Returns human oversight audit log binding every high-stakes agent decision to a verified human reviewer.
    """
    stmt = select(HITLRecord).where(HITLRecord.agent_id == agent_id).order_by(desc(HITLRecord.created_at))
    res = await db.execute(stmt)
    records = res.scalars().all()

    return {
        "agent_id": agent_id,
        "eu_ai_act_compliance": "Article 14 Human Oversight",
        "total_human_decisions": len(records),
        "decisions": [
            {
                "hitl_id": r.hitl_id,
                "action": r.action,
                "resource_id": r.resource_id,
                "approver_name": r.approver_name,
                "approver_email": r.approver_email,
                "decision": r.decision,
                "rationale": r.rationale,
                "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                "response_time_seconds": r.response_time_seconds,
            }
            for r in records
        ],
    }


@router.get("/chain-snapshot")
async def get_chain_snapshot(
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditEntry).order_by(desc(AuditEntry.sequence_num)).limit(1)
    res = await db.execute(stmt)
    latest = res.scalar_one_or_none()

    return {
        "sequence_num": latest.sequence_num if latest else 0,
        "head_hash": latest.entry_hash if latest else AuditLedger.GENESIS_HASH,
        "snapshot_at": datetime.utcnow().isoformat(),
        "attestation_standard": "SHA-256 Monotonic Merkle-Chain",
    }
