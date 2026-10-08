import asyncio
from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, Optional
import httpx

from .exceptions import (
    AuthenticationError,
    PolicyViolationError,
    HITLTimeoutError,
    KillSwitchActiveError,
    SentinelError,
)

log = logging.getLogger("sentinel_sdk")


@dataclass
class ToolExecutionResult:
    decision: str
    status: str
    result: Dict[str, Any] = field(default_factory=dict)
    cedar_latency_ms: float = 0.0
    ledger_hash: str = ""
    receipt_id: str = ""
    approver: Optional[str] = None
    rationale: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)


class SentinelClient:
    """
    SentinelClient — Production Python client for Sentinel Legacy Governance Control Plane.
    
    Usage:
        client = SentinelClient(
            control_plane_url="https://sentinel-backend.onrender.com",
            client_id="agt_7a3f9c2d",
            client_secret="support_secret_2026",
            agent_id="SupportAgent",
        )
        
        # Governed tool invocation
        result = await client.execute_tool(
            action="read_order_history",
            resource_type="Order",
            resource_id="ord_9901",
            tool_name="support_toolset",
            parameters={"customer_id": "cust_9921"},
        )
    """

    def __init__(
        self,
        control_plane_url: str = "http://localhost:8000",
        client_id: str = "agt_7a3f9c2d",
        client_secret: str = "support_secret_2026",
        agent_id: str = "SupportAgent",
        default_resource: str = "https://crm.corp.internal",
        timeout: float = 30.0,
    ):
        self.control_plane_url = control_plane_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.agent_id = agent_id
        self.default_resource = default_resource
        self.timeout = timeout
        self.access_token: Optional[str] = None
        self.token_expiry: float = 0.0

    async def authenticate(self, resource: Optional[str] = None) -> str:
        """Issues an RFC 8707 audience-bound OAuth 2.1 token from Sentinel."""
        target_resource = resource or self.default_resource
        url = f"{self.control_plane_url}/api/v1/auth/token"

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "resource": target_resource,
            "scope": "agent:tool:execute",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, json=payload)
                if resp.status_code != 200:
                    raise AuthenticationError(
                        f"Authentication failed ({resp.status_code}): {resp.text}"
                    )
                data = resp.json()
                self.access_token = data["access_token"]
                self.token_expiry = time.time() + data.get("expires_in", 3600) - 60
                return self.access_token
            except httpx.RequestError as e:
                raise AuthenticationError(f"Network error during authentication: {e}")

    async def _ensure_token(self) -> str:
        if not self.access_token or time.time() >= self.token_expiry:
            await self.authenticate()
        return self.access_token or ""

    async def execute_tool(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        poll_hitl: bool = True,
        hitl_timeout_seconds: float = 300.0,
    ) -> ToolExecutionResult:
        """
        Executes an agent tool call strictly through Sentinel Legacy's MCP Reverse Proxy.
        
        - Formally evaluated by Cedar in < 1ms
        - Enforces fail-closed human oversight if escalated
        - Sealed into monotonic SHA-256 cryptographic audit chain
        """
        token = await self._ensure_token()
        url = f"{self.control_plane_url}/api/v1/proxy/mcp"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "agent_id": self.agent_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "context": context or {},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, json=payload, headers=headers)
                raw_json = resp.json()
                data = await raw_json if asyncio.iscoroutine(raw_json) else raw_json
            except httpx.RequestError as e:
                raise SentinelError(f"Failed to communicate with Sentinel control plane: {e}")

        decision = data.get("decision", "UNKNOWN")

        # 1. Kill Switch Check
        if decision == "KILL_SWITCH_ACTIVE" or resp.status_code == 403 and "kill switch" in str(data).lower():
            raise KillSwitchActiveError(f"Agent '{self.agent_id}' has been quarantined by an Emergency Kill Switch.")

        # 2. Strict Forbid
        if decision == "FORBID" or resp.status_code == 403:
            policy_id = data.get("policy_id", "POLICY-FORBID")
            reason = data.get("reason", "Action strictly forbidden by security policy.")
            raise PolicyViolationError(action=action, reason=reason, policy_id=policy_id)

        # 3. Direct Permit
        if decision in ("PERMIT", "ALLOW") or resp.status_code == 200:
            return ToolExecutionResult(
                decision=decision,
                status="COMPLETED",
                result=data.get("result", {}),
                cedar_latency_ms=data.get("cedar_latency_ms", 0.0),
                ledger_hash=data.get("ledger_hash", ""),
                receipt_id=data.get("receipt_id", ""),
                raw_response=data,
            )

        # 4. Human-In-The-Loop Escalation
        if decision == "HITL_ESCALATED" or data.get("status") == "SUSPENDED":
            hitl_id = data.get("hitl_id")
            if not poll_hitl or not hitl_id:
                return ToolExecutionResult(
                    decision="HITL_ESCALATED",
                    status="SUSPENDED",
                    result={"hitl_id": hitl_id, "message": "Thread suspended waiting for human approval."},
                    raw_response=data,
                )

            # Poll for human approval
            return await self._poll_hitl_resolution(hitl_id, hitl_timeout_seconds)

        return ToolExecutionResult(
            decision=decision,
            status=data.get("status", "UNKNOWN"),
            result=data.get("result", {}),
            raw_response=data,
        )

    async def _poll_hitl_resolution(
        self, hitl_id: str, timeout_seconds: float, interval_seconds: float = 2.0
    ) -> ToolExecutionResult:
        """Polls HITL item until human approves, rejects, or times out."""
        start_time = time.time()
        url = f"{self.control_plane_url}/api/v1/hitl/{hitl_id}"

        async with httpx.AsyncClient(timeout=10.0) as http:
            while time.time() - start_time < timeout_seconds:
                try:
                    resp = await http.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = data.get("status")
                        if status == "APPROVED":
                            return ToolExecutionResult(
                                decision="HITL_APPROVED",
                                status="COMPLETED",
                                result=data.get("result", {}),
                                approver=data.get("approver_name"),
                                rationale=data.get("rationale"),
                                ledger_hash=data.get("ledger_hash", ""),
                                raw_response=data,
                            )
                        elif status == "REJECTED":
                            raise PolicyViolationError(
                                action="hitl_action",
                                reason=f"Rejected by human operator: {data.get('rationale', 'No rationale provided')}",
                                policy_id="HITL-HUMAN-REJECT",
                            )
                except httpx.RequestError:
                    pass
                await asyncio.sleep(interval_seconds)

        raise HITLTimeoutError(f"Human oversight request {hitl_id} timed out after {timeout_seconds}s (Fail-Closed).")
