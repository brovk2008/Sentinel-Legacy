import base64
from datetime import datetime
import hashlib
from typing import Optional
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.auth.token_manager import TokenManager
from sentinel.core.config import get_settings
from sentinel.core.database import get_db
from sentinel.core.redis import get_redis
from sentinel.models.agent import Agent, AgentStatus

router = APIRouter(tags=["OAuth 2.1 / Auth"])
settings = get_settings()


async def get_token_mgr() -> TokenManager:
    redis = await get_redis()
    return TokenManager(redis, settings.jwt_secret_key, settings.jwt_algorithm, settings.jwt_expiry_seconds)


class ClientRegisterRequest(BaseModel):
    client_name: str
    grant_types: list[str] = ["client_credentials"]
    client_metadata_url: Optional[str] = None
    scope: str = "mcp:tools crm:orders mcp:read"
    token_endpoint_auth_method: str = "client_secret_basic"


class TokenRevokeRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = "access_token"


# ─── Metadata Endpoints (RFC 9728 & RFC 8414) ───

@router.get("/.well-known/oauth-protected-resource")
async def get_protected_resource_metadata():
    return {
        "resource": "https://sentinel.corp",
        "authorization_servers": ["https://sentinel.corp/oauth"],
        "bearer_methods_supported": ["header"],
        "scopes_supported": [
            "mcp:tools",
            "mcp:read",
            "mcp:write",
            "crm:orders",
            "payments:refund",
            "support:read",
        ],
    }


@router.get("/.well-known/oauth-authorization-server")
async def get_authorization_server_metadata(
    mcp_protocol_version: Optional[str] = Header(None, alias="Mcp-Protocol-Version")
):
    return {
        "issuer": "https://sentinel.corp",
        "token_endpoint": "/oauth/token",
        "grant_types_supported": ["client_credentials"],
        "registration_endpoint": "/oauth/register",
        "revocation_endpoint": "/oauth/revoke",
        "token_endpoint_auth_methods": ["client_secret_basic", "client_secret_post"],
        "mcp_spec_target": "2025-11-25",
    }


# ─── Dynamic Client Registration (CIMD fallback) ───

@router.post("/oauth/register")
async def register_client(
    body: ClientRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).where(Agent.name == body.client_name)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=400, detail=f"Agent {body.client_name} must first be registered in Agent Registry")

    secret = f"sec_{hashlib.sha256(f'{agent.agent_id}{datetime.utcnow()}'.encode()).hexdigest()[:24]}"
    agent.client_secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    await db.commit()

    return {
        "client_id": agent.client_id,
        "client_secret": secret,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "grant_types": body.grant_types,
        "scope": body.scope,
    }


# ─── Token Issuance ───

@router.post("/oauth/token")
async def issue_token(
    request: Request,
    grant_type: str = Form("client_credentials"),
    scope: str = Form("mcp:tools crm:orders"),
    resource: str = Form("https://crm.corp.internal"),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    token_mgr: TokenManager = Depends(get_token_mgr),
    db: AsyncSession = Depends(get_db),
):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Only grant_type=client_credentials is supported (Spec 2025-11-25)")

    cid = client_id
    csec = client_secret

    # Check Basic Auth header
    if authorization and authorization.startswith("Basic "):
        try:
            b64_val = authorization[6:].strip()
            decoded = base64.b64decode(b64_val).decode("utf-8")
            if ":" in decoded:
                cid, csec = decoded.split(":", 1)
        except Exception:
            pass

    # Look up agent by client_id, agent_id, or default SupportAgent
    agent = None
    if cid:
        stmt = select(Agent).where((Agent.client_id == cid) | (Agent.agent_id == cid) | (Agent.name == cid))
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()

    if not agent:
        # Default to SupportAgent
        stmt = select(Agent).where(Agent.role == "SupportAgent").limit(1)
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    if agent.status == AgentStatus.SUSPENDED.value:
        raise HTTPException(status_code=403, detail="Agent is SUSPENDED. Token issuance blocked.")

    token_data = await token_mgr.issue_token(
        agent_id=agent.agent_id,
        agent_role=agent.role,
        scope=scope,
        resource=resource,
        trust_score=agent.trust_score,
        owner_id=agent.human_owner_id or "own_priya_sharma_01",
    )

    return token_data


# ─── Token Revocation ───

@router.post("/oauth/revoke")
async def revoke_token(
    body: TokenRevokeRequest,
    token_mgr: TokenManager = Depends(get_token_mgr),
):
    try:
        # decode unverified to extract jti
        from jose import jwt
        unverified = jwt.get_unverified_claims(body.token)
        jti = unverified.get("jti")
        if jti:
            await token_mgr.revoke_token(jti)
    except Exception:
        pass
    return {"status": "revoked"}


@router.get("/oauth/clients/{client_id}")
async def get_client_metadata(
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).where((Agent.client_id == client_id) | (Agent.agent_id == client_id))
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "client_id": agent.client_id,
        "client_name": agent.name,
        "status": agent.status,
        "trust_score": agent.trust_score,
        "department": agent.department,
        "permitted_actions": agent.permitted_actions,
    }
