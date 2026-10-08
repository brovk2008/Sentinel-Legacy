from typing import Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.core.config import get_settings
from sentinel.core.database import get_db
from sentinel.core.redis import get_redis
from sentinel.hitl.queue import HITLQueue
from sentinel.monitor.anomaly import ViolationVelocityTracker
from sentinel.policy.cedar_engine import CedarPolicyEngine
from sentinel.proxy.circuit_breaker import ToolCircuitBreaker
from sentinel.proxy.mcp_proxy import MCPProxy
from sentinel.auth.token_manager import TokenManager
from sentinel.ws.hub import WebSocketHub

router = APIRouter(prefix="/mcp", tags=["MCP Proxy (Core Gateway)"])
settings = get_settings()

_circuit_breaker = ToolCircuitBreaker()


async def get_mcp_proxy(request: Request) -> MCPProxy:
    app_state = request.app.state
    if not hasattr(app_state, "cedar_engine"):
        from main import ensure_app_state
        await ensure_app_state(request.app)
        app_state = request.app.state

    cedar_engine: CedarPolicyEngine = app_state.cedar_engine
    token_manager: TokenManager = app_state.token_manager
    hitl_queue: HITLQueue = app_state.hitl_queue
    velocity_tracker: ViolationVelocityTracker = app_state.velocity_tracker
    ws_hub: WebSocketHub = app_state.ws_hub

    return MCPProxy(
        token_manager=token_manager,
        cedar_engine=cedar_engine,
        hitl_queue=hitl_queue,
        velocity_tracker=velocity_tracker,
        circuit_breaker=_circuit_breaker,
        ws_hub=ws_hub,
    )


@router.post("/tools/call")
async def call_tool(
    request: Request,
    authorization: Optional[str] = Header(None),
    mcp_proxy: MCPProxy = Depends(get_mcp_proxy),
    db: AsyncSession = Depends(get_db),
):
    """
    Core authorization proxy intercepting MCP tools/call.
    Enforces Bearer JWT audience checks, Cedar policies, HITL pause, and audit chaining.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="401 Unauthorized: Missing or invalid Bearer token",
            headers={"WWW-Authenticate": 'Bearer realm="sentinel-legacy"'},
        )

    raw_token = authorization[7:].strip()
    body = await request.json()

    # Parse JSON-RPC 2.0 or REST body
    rpc_id = None
    tool_name = ""
    arguments: dict[str, Any] = {}

    if "jsonrpc" in body and body.get("method") == "tools/call":
        rpc_id = body.get("id")
        params = body.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
    else:
        rpc_id = body.get("id")
        tool_name = body.get("name") or body.get("tool") or ""
        arguments = body.get("arguments") or body.get("args") or {}

    if not tool_name:
        raise HTTPException(status_code=400, detail="Tool name must be specified in request body")

    result = await mcp_proxy.execute_tool_call(
        raw_token=raw_token,
        tool_name=tool_name,
        arguments=arguments,
        db=db,
    )

    if rpc_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": result,
        }
    return result


@router.get("/tools/list")
async def list_tools(
    authorization: Optional[str] = Header(None),
    request: Request = None,
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={
                "WWW-Authenticate": 'Bearer realm="sentinel-legacy", resource_metadata_url="/.well-known/oauth-protected-resource"'
            },
        )

    # Return standard MCP tool definitions
    return {
        "tools": [
            {
                "name": "crm.order.read",
                "description": "Read order history for customer with active consent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer identifier (e.g. CUST-2841)"}
                    },
                    "required": ["customer_id"],
                },
            },
            {
                "name": "payments.refund.create",
                "description": "Create a refund for customer order. Auto-approved up to ₹10,000; HITL approval required above ₹10,000.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string", "default": "INR"},
                    },
                    "required": ["customer_id", "amount"],
                },
            },
            {
                "name": "faq.retrieve",
                "description": "Retrieve corporate FAQ and damage policies",
                "inputSchema": {
                    "type": "object",
                    "properties": {"topic": {"type": "string"}},
                },
            },
            {
                "name": "ticket.create",
                "description": "Create a support resolution ticket",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "issue": {"type": "string"},
                    },
                },
            },
        ]
    }


@router.post("/resources/read")
async def read_resource(
    request: Request,
    authorization: Optional[str] = Header(None),
    mcp_proxy: MCPProxy = Depends(get_mcp_proxy),
    db: AsyncSession = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    raw_token = authorization[7:].strip()
    body = await request.json()
    uri = body.get("uri", "")

    return await mcp_proxy.execute_tool_call(
        raw_token=raw_token,
        tool_name="order.read",
        arguments={"resource_uri": uri, "customer_id": "CUST-2841"},
        db=db,
    )
