from datetime import datetime
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sentinel.core.database import Base


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    entry_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_num = Column(Integer, autoincrement=True, unique=True, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    resource_id = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, default="Customer")
    policy_id = Column(String(100), nullable=True, index=True)
    decision = Column(String(50), nullable=False, index=True)
    tier = Column(Integer, nullable=False, default=1)
    context_snapshot = Column(JSON, nullable=False, default=dict)
    cedar_detail = Column(JSON, nullable=False, default=dict)
    entry_hash = Column(String(128), nullable=False)
    prev_entry_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class Violation(Base):
    __tablename__ = "audit_violations"

    violation_id = Column(String(64), primary_key=True, default=lambda: f"viol_{uuid.uuid4().hex[:12]}")
    agent_id = Column(String(64), nullable=False, index=True)
    entry_id = Column(String(64), nullable=True)
    violation_type = Column(String(100), nullable=False)
    severity = Column(Integer, nullable=False, default=3)
    attempted_action = Column(String(255), nullable=False)
    policy_blocked = Column(String(100), nullable=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OTelSpan(Base):
    __tablename__ = "otel_spans"

    span_id = Column(String(64), primary_key=True, default=lambda: f"span_{uuid.uuid4().hex[:12]}")
    agent_id = Column(String(64), nullable=False, index=True)
    operation_name = Column(String(100), nullable=False, default="tool_call")
    model = Column(String(100), nullable=False, default="claude-sonnet-4-6")
    tool_name = Column(String(255), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    decision = Column(String(50), nullable=False, default="ALLOW")
    trace_id = Column(String(128), nullable=False, default=lambda: uuid.uuid4().hex)
    sentinel_decision = Column(String(50), nullable=False, default="ALLOW")
    trust_score_at_time = Column(Float, nullable=False, default=85.0)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=False, default=100)


class ChainSnapshot(Base):
    __tablename__ = "audit_chain_snapshots"

    snapshot_id = Column(String(64), primary_key=True, default=lambda: f"snap_{uuid.uuid4().hex[:12]}")
    sequence_num = Column(Integer, nullable=False)
    entry_hash = Column(String(128), nullable=False)
    snapshot_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Pydantic Models

class AuditEntryOut(BaseModel):
    entry_id: str
    sequence_num: Optional[int]
    agent_id: str
    action: str
    resource_id: str
    resource_type: str
    policy_id: Optional[str]
    decision: str
    tier: int
    context_snapshot: dict[str, Any]
    cedar_detail: dict[str, Any]
    entry_hash: str
    prev_entry_hash: str
    created_at: datetime
    hitl_record: Optional[Any] = None

    class Config:
        from_attributes = True


class ViolationOut(BaseModel):
    violation_id: str
    agent_id: str
    entry_id: Optional[str]
    violation_type: str
    severity: int
    attempted_action: str
    policy_blocked: Optional[str]
    detected_at: datetime

    class Config:
        from_attributes = True
