from datetime import datetime, date
import hashlib
import json
import logging
from typing import Any, Optional
import uuid
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sentinel.models.audit import AuditEntry, ChainSnapshot
from sentinel.models.hitl import HITLRecord

log = logging.getLogger(__name__)


class AuditLedger:
    GENESIS_HASH = "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _canonical_json(data: dict) -> str:
        """Deterministic JSON — sorted keys, no extra whitespace."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _compute_hash(content: dict, prev_hash: str) -> str:
        canonical = AuditLedger._canonical_json(content)
        payload = f"{canonical}:{prev_hash}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    async def _get_last_hash(self) -> str:
        stmt = select(AuditEntry.entry_hash).order_by(desc(AuditEntry.sequence_num)).limit(1)
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        return row if row else self.GENESIS_HASH

    async def write_entry(
        self,
        agent_id: str,
        action: str,
        resource_id: str,
        policy_id: Optional[str],
        decision: str,
        tier: int,
        context_snapshot: dict,
        cedar_detail: dict,
        resource_type: str = "Customer",
    ) -> AuditEntry:
        prev_hash = await self._get_last_hash()

        content = {
            "agent_id": str(agent_id),
            "action": str(action),
            "resource_id": str(resource_id),
            "policy_id": policy_id or "",
            "decision": str(decision),
            "tier": int(tier),
            "context_snapshot": context_snapshot or {},
            "cedar_detail": cedar_detail or {},
        }
        entry_hash = self._compute_hash(content, prev_hash)
        entry_id = str(uuid.uuid4())

        entry = AuditEntry(
            entry_id=entry_id,
            agent_id=agent_id,
            action=action,
            resource_id=resource_id,
            resource_type=resource_type,
            policy_id=policy_id,
            decision=decision,
            tier=tier,
            context_snapshot=context_snapshot or {},
            cedar_detail=cedar_detail or {},
            entry_hash=entry_hash,
            prev_entry_hash=prev_hash,
            created_at=datetime.utcnow(),
        )

        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def verify_chain(self) -> tuple[bool, Optional[int]]:
        """
        Walks the entire chain in sequence_num order.
        Verifies both hash computation and prev_hash continuity.
        Returns (is_valid, first_invalid_sequence_num).
        """
        stmt = select(AuditEntry).order_by(asc(AuditEntry.sequence_num))
        res = await self.session.execute(stmt)
        entries = res.scalars().all()

        expected_prev = self.GENESIS_HASH
        for entry in entries:
            content = {
                "agent_id": str(entry.agent_id),
                "action": str(entry.action),
                "resource_id": str(entry.resource_id),
                "policy_id": entry.policy_id or "",
                "decision": str(entry.decision),
                "tier": int(entry.tier),
                "context_snapshot": dict(entry.context_snapshot or {}),
                "cedar_detail": dict(entry.cedar_detail or {}),
            }
            computed_hash = self._compute_hash(content, expected_prev)
            if computed_hash != entry.entry_hash:
                log.warning("Hash mismatch at sequence %s: expected %s, got %s", entry.sequence_num, computed_hash, entry.entry_hash)
                return False, entry.sequence_num
            if entry.prev_entry_hash != expected_prev:
                log.warning("Chain link broken at sequence %s: expected prev %s, got %s", entry.sequence_num, expected_prev, entry.prev_entry_hash)
                return False, entry.sequence_num
            expected_prev = entry.entry_hash

        return True, None

    async def query_entries(
        self,
        agent_id: Optional[str] = None,
        action: Optional[str] = None,
        decision: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        conditions = []
        if agent_id:
            conditions.append(AuditEntry.agent_id == agent_id)
        if action:
            conditions.append(AuditEntry.action == action)
        if decision:
            conditions.append(AuditEntry.decision == decision)
        if resource_id:
            conditions.append(AuditEntry.resource_id == resource_id)

        stmt = select(AuditEntry)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(desc(AuditEntry.sequence_num)).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def query_by_resource(
        self,
        resource_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[dict]:
        stmt = select(AuditEntry).where(AuditEntry.resource_id == resource_id)
        if from_date:
            stmt = stmt.where(AuditEntry.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            stmt = stmt.where(AuditEntry.created_at <= datetime.combine(to_date, datetime.max.time()))
        stmt = stmt.order_by(asc(AuditEntry.created_at))
        res = await self.session.execute(stmt)
        entries = res.scalars().all()

        results = []
        for e in entries:
            # Check if there is an associated HITL record
            hitl_stmt = select(HITLRecord).where(HITLRecord.entry_id == e.entry_id)
            hitl_res = await self.session.execute(hitl_stmt)
            hitl_rec = hitl_res.scalar_one_or_none()

            results.append({
                "entry_id": e.entry_id,
                "sequence_num": e.sequence_num,
                "created_at": e.created_at.isoformat(),
                "agent_id": e.agent_id,
                "action": e.action,
                "decision": e.decision,
                "policy_id": e.policy_id,
                "tier": e.tier,
                "context_snapshot": e.context_snapshot,
                "hitl_approver_name": hitl_rec.approver_name if hitl_rec else None,
            })
        return results
