from datetime import datetime
from enum import Enum
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sentinel.core.database import Base


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    DECOMMISSIONED = "DECOMMISSIONED"


class ModelArchitecture(str, Enum):
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    GPT_4O = "gpt-4o"
    LLAMA_3_70B = "llama-3-70b"
    GEMINI_2_PRO = "gemini-2-pro"
    MOCK_SIMULATION = "mock-simulation"


class HumanOwner(Base):
    __tablename__ = "human_owners"

    owner_id = Column(String(64), primary_key=True, default=lambda: f"own_{uuid.uuid4().hex[:12]}")
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    manager_role = Column(String(100), nullable=False, default="finance_manager")
    slack_user_id = Column(String(100), nullable=True)
    slack_webhook_url = Column(String(500), nullable=True)
    teams_webhook_url = Column(String(500), nullable=True)

    agents = relationship("Agent", back_populates="owner")


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String(64), primary_key=True, default=lambda: f"agt_{uuid.uuid4().hex[:12]}")
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    model_architecture = Column(String(100), nullable=False, default=ModelArchitecture.CLAUDE_SONNET_4_6.value)
    role = Column(String(100), nullable=False, default="SupportAgent")
    department = Column(String(100), nullable=False, default="CustomerSupport")
    status = Column(String(50), nullable=False, default=AgentStatus.ACTIVE.value)
    trust_score = Column(Float, nullable=False, default=85.0)
    human_owner_id = Column(String(64), ForeignKey("human_owners.owner_id"), nullable=True)
    client_id = Column(String(100), nullable=False, unique=True)
    client_secret_hash = Column(String(255), nullable=False)
    permitted_actions = Column(JSON, nullable=False, default=list)
    forbidden_actions = Column(JSON, nullable=False, default=list)
    hitl_actions = Column(JSON, nullable=False, default=list)
    escalation_config = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    provisioned_by = Column(String(255), nullable=False, default="Governance Admin")

    owner = relationship("HumanOwner", back_populates="agents")


class CedarPolicy(Base):
    __tablename__ = "cedar_policies"

    policy_id = Column(String(64), primary_key=True)
    policy_name = Column(String(255), nullable=False)
    cedar_definition = Column(Text, nullable=False)
    tier = Column(Integer, nullable=False, default=1)
    escalation_tier = Column(String(50), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False, default="admin")
    version = Column(String(50), nullable=False, default="1.0.0")


# Pydantic Schemas

class HumanOwnerOut(BaseModel):
    owner_id: str
    name: str
    email: str
    department: str
    manager_role: str

    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    name: str
    display_name: str
    model_architecture: Optional[str] = "claude-sonnet-4-6"
    role: Optional[str] = "SupportAgent"
    department: Optional[str] = "CustomerSupport"
    human_owner_id: Optional[str] = None
    permitted_actions: Optional[list[str]] = None
    forbidden_actions: Optional[list[str]] = None
    hitl_actions: Optional[list[str]] = None


class AgentStatusUpdate(BaseModel):
    status: AgentStatus
    reason: Optional[str] = "Administrative update"


class AgentOut(BaseModel):
    agent_id: str
    name: str
    display_name: str
    model_architecture: str
    role: str
    department: str
    status: str
    trust_score: float
    human_owner_id: Optional[str]
    client_id: str
    permitted_actions: list[Any]
    forbidden_actions: list[Any]
    hitl_actions: list[Any]
    created_at: datetime
    last_active_at: datetime
    provisioned_by: str
    owner: Optional[HumanOwnerOut] = None

    class Config:
        from_attributes = True


class AgentTelemetry30d(BaseModel):
    agent_id: str
    total_actions: int = 1247
    auto_allowed: int = 1198
    notify_proceed: int = 15
    hitl_approved: int = 11
    hitl_rejected: int = 0
    hitl_timed_out: int = 0
    blocked_tier4: int = 23
    input_tokens_total: int = 4200000
    output_tokens_total: int = 1100000
    cost_usd_total: float = 4.32
    avg_response_ms: float = 142.5
    computed_at: datetime = Field(default_factory=datetime.utcnow)
