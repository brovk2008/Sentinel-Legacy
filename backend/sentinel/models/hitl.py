from datetime import datetime
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sentinel.core.database import Base


class HITLRecord(Base):
    __tablename__ = "audit_hitl_records"

    hitl_id = Column(String(64), primary_key=True, default=lambda: f"hitl_{uuid.uuid4().hex[:12]}")
    entry_id = Column(String(64), nullable=True)
    agent_id = Column(String(64), nullable=False)
    action = Column(String(255), nullable=False)
    resource_id = Column(String(255), nullable=False)
    approver_role = Column(String(100), nullable=False, default="finance_manager")
    approver_id = Column(String(64), nullable=True)
    approver_name = Column(String(255), nullable=True)
    approver_email = Column(String(255), nullable=True)
    decision = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected, timeout
    rationale = Column(Text, nullable=True)
    checkbox_ack = Column(Boolean, nullable=False, default=False)
    briefing = Column(JSON, nullable=False, default=dict)
    original_context = Column(JSON, nullable=False, default=dict)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    response_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class HITLDecisionSubmit(BaseModel):
    decision: str  # "approved" | "rejected"
    rationale: str
    checkbox_ack: bool = True
    approver_id: Optional[str] = "own_priya_sharma_01"
    approver_name: Optional[str] = "Priya Sharma"
    approver_email: Optional[str] = "priya@corp.com"


class HITLRecordOut(BaseModel):
    hitl_id: str
    entry_id: Optional[str]
    agent_id: str
    action: str
    resource_id: str
    approver_role: str
    approver_id: Optional[str]
    approver_name: Optional[str]
    approver_email: Optional[str]
    decision: str
    rationale: Optional[str]
    checkbox_ack: bool
    briefing: dict[str, Any]
    requested_at: datetime
    decided_at: Optional[datetime]
    response_time_seconds: Optional[float]

    class Config:
        from_attributes = True
