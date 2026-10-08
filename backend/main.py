from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import hashlib
import logging
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentinel.api import admin, agents, audit, auth, compliance, metrics, proxy, hitl, ws
from sentinel.auth.token_manager import TokenManager
from sentinel.core.config import get_settings
from sentinel.core.database import AsyncSessionLocal, Base, engine
from sentinel.core.redis import get_redis
from sentinel.hitl.queue import HITLQueue
from sentinel.ledger.writer import AuditLedger
from sentinel.models.agent import Agent, AgentStatus, HumanOwner, ModelArchitecture
from sentinel.monitor.anomaly import ViolationVelocityTracker
from sentinel.policy.cedar_engine import CedarPolicyEngine
from sentinel.ws.hub import WebSocketHub

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sentinel.main")
settings = get_settings()


async def seed_database():
    """Seeds default agents, human owner, and sample forensic entries if DB is fresh."""
    async with AsyncSessionLocal() as session:
        # Check if human owner exists
        stmt = select(HumanOwner).where(HumanOwner.owner_id == "own_priya_sharma_01")
        res = await session.execute(stmt)
        owner = res.scalar_one_or_none()
        if not owner:
            owner = HumanOwner(
                owner_id="own_priya_sharma_01",
                name="Priya Sharma",
                email="priya@corp.com",
                department="Customer Support",
                manager_role="finance_manager",
            )
            session.add(owner)
            await session.commit()

        # Seed SupportAgent
        stmt_sa = select(Agent).where(Agent.name == "SupportAgent")
        res_sa = await session.execute(stmt_sa)
        support_agent = res_sa.scalar_one_or_none()
        if not support_agent:
            support_agent = Agent(
                agent_id="agt_7a3f9c2d8e1b",
                name="SupportAgent",
                display_name="SupportAgent (Frontline Ops)",
                model_architecture=ModelArchitecture.CLAUDE_SONNET_4_6.value,
                role="SupportAgent",
                department="CustomerSupport",
                status=AgentStatus.ACTIVE.value,
                trust_score=82.0,
                human_owner_id=owner.owner_id,
                client_id="agt_7a3f9c2d",
                client_secret_hash=hashlib.sha256(b"support_secret_2026").hexdigest(),
                permitted_actions=[
                    "order.read",
                    "ticket.create",
                    "faq.retrieve",
                    "refund.create",
                    "email.send",
                ],
                forbidden_actions=[
                    "bank_details.read",
                    "db.export.all",
                    "password.reset",
                    "cred.access.any",
                    "agent.elevate",
                    "infra.modify",
                ],
                hitl_actions=[
                    "refund.create (> ₹10,000)",
                    "account.close",
                    "customer.data.bulk_delete",
                    "contract.amend",
                    "pii.export",
                ],
                escalation_config={"refund.create": {"threshold": 10000, "approver": "finance_manager"}},
                created_at=datetime.utcnow() - timedelta(days=37),
                last_active_at=datetime.utcnow() - timedelta(minutes=2),
                provisioned_by="Priya Sharma (Finance Manager)",
            )
            session.add(support_agent)

        # Seed SalesAgent
        stmt_sales = select(Agent).where(Agent.name == "SalesAgent")
        res_sales = await session.execute(stmt_sales)
        if not res_sales.scalar_one_or_none():
            sales_agent = Agent(
                agent_id="agt_sales_99a81",
                name="SalesAgent",
                display_name="SalesAgent (Enterprise CRM)",
                model_architecture=ModelArchitecture.GPT_4O.value,
                role="SalesAgent",
                department="Sales & Accounts",
                status=AgentStatus.ACTIVE.value,
                trust_score=91.0,
                human_owner_id=owner.owner_id,
                client_id="agt_sales",
                client_secret_hash=hashlib.sha256(b"sales_secret_2026").hexdigest(),
                permitted_actions=["lead.enrich", "crm.account.read", "meeting.schedule"],
                forbidden_actions=["db.export.all", "payment.initiate"],
                hitl_actions=["contract.amend", "discount.apply (> 20%)"],
                created_at=datetime.utcnow() - timedelta(days=20),
                last_active_at=datetime.utcnow() - timedelta(minutes=15),
                provisioned_by="Governance Admin",
            )
            session.add(sales_agent)

        # Seed FinanceAgent
        stmt_fin = select(Agent).where(Agent.name == "FinanceAgent")
        res_fin = await session.execute(stmt_fin)
        if not res_fin.scalar_one_or_none():
            fin_agent = Agent(
                agent_id="agt_fin_88c42",
                name="FinanceAgent",
                display_name="FinanceAgent (Settlements)",
                model_architecture=ModelArchitecture.LLAMA_3_70B.value,
                role="FinanceAgent",
                department="Finance Operations",
                status=AgentStatus.ACTIVE.value,
                trust_score=95.0,
                human_owner_id=owner.owner_id,
                client_id="agt_finance",
                client_secret_hash=hashlib.sha256(b"finance_secret_2026").hexdigest(),
                permitted_actions=["invoice.verify", "ledger.read", "reconciliation.run"],
                forbidden_actions=["db.export.all", "bank.wire.transfer"],
                hitl_actions=["payout.approve (> ₹1,00,000)"],
                created_at=datetime.utcnow() - timedelta(days=15),
                last_active_at=datetime.utcnow() - timedelta(hours=1),
                provisioned_by="Governance Admin",
            )
            session.add(fin_agent)

        await session.commit()

        # Seed sample initial ledger entries if empty
        ledger = AuditLedger(session)
        is_valid, _ = await ledger.verify_chain()
        from sentinel.models.audit import AuditEntry
        res_count = await session.execute(select(AuditEntry.entry_id).limit(1))
        if not res_count.scalar_one_or_none():
            log.info("Seeding initial sealed audit entries into hash chain...")
            await ledger.write_entry(
                agent_id="agt_7a3f9c2d8e1b",
                action="faq.retrieve",
                resource_id="ITEM-CARE",
                policy_id="DATA-003",
                decision="ALLOW",
                tier=1,
                context_snapshot={"topic": "return_policy"},
                cedar_detail={"matching_policies": ["DATA-003"]},
            )
            await ledger.write_entry(
                agent_id="agt_7a3f9c2d8e1b",
                action="order.read",
                resource_id="CUST-2841",
                policy_id="DATA-012",
                decision="ALLOW",
                tier=1,
                context_snapshot={"customer_id": "CUST-2841", "consent_active": True},
                cedar_detail={"matching_policies": ["DATA-012"]},
            )
            await ledger.write_entry(
                agent_id="agt_7a3f9c2d8e1b",
                action="refund.create",
                resource_id="CUST-2841",
                policy_id="REFUND-001",
                decision="ALLOW",
                tier=1,
                context_snapshot={"amount": 700, "currency": "INR"},
                cedar_detail={"matching_policies": ["REFUND-001"]},
            )


async def ensure_app_state(app: FastAPI):
    if not hasattr(app.state, "cedar_engine"):
        # 1. Initialize DB schema
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 2. Seed database
        await seed_database()

        # 3. Redis singleton
        redis_client = await get_redis()
        app.state.redis = redis_client

        # 4. TokenManager
        app.state.token_manager = TokenManager(
            redis=redis_client,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expiry_seconds=settings.jwt_expiry_seconds,
        )

        # 5. CedarPolicyEngine
        app.state.cedar_engine = CedarPolicyEngine(
            policy_path=settings.resolved_cedar_policy_path(),
            schema_path=settings.resolved_cedar_schema_path(),
        )

        # 6. WebSocketHub
        ws_hub = WebSocketHub(redis=redis_client)
        app.state.ws_hub = ws_hub

        # 7. HITLQueue
        app.state.hitl_queue = HITLQueue(redis=redis_client, ws_hub=ws_hub)

        # 8. ViolationVelocityTracker
        app.state.velocity_tracker = ViolationVelocityTracker(
            redis=redis_client,
            window_seconds=settings.violation_window_seconds,
            warning_threshold=settings.violation_warning_count,
            critical_threshold=settings.violation_critical_count,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting Sentinel Legacy governance control plane...")
    await ensure_app_state(app)
    log.info("All Sentinel Legacy control plane subsystems ready.")
    yield
    log.info("Shutting down Sentinel Legacy...")


app = FastAPI(
    title="Sentinel Legacy",
    description="Governance Infrastructure for the Agentic Enterprise",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
cors_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(proxy.router)
app.include_router(hitl.router)
app.include_router(admin.router)
app.include_router(audit.router)
app.include_router(compliance.router)
app.include_router(metrics.router)
app.include_router(ws.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "sentinel-legacy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "cedar_engine": "active",
        "policy_spec": "MCP-2025-11-25",
    }


@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Liveness probe: verifies process is responsive."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Readiness probe: validates database and Cedar engine operational readiness."""
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
            db_ok = True
    except Exception as e:
        log.warning("Readiness probe DB check failed: %s", e)

    cedar_ok = hasattr(app.state, "cedar_engine") and app.state.cedar_engine is not None

    status_code = 200 if (db_ok and cedar_ok) else 503
    return {
        "status": "ready" if (db_ok and cedar_ok) else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "cedar_engine": "loaded" if cedar_ok else "uninitialized",
        "timestamp": datetime.utcnow().isoformat(),
    }
