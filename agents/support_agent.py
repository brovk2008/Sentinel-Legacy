from dataclasses import dataclass
import json
import logging
import os
import sys
from typing import Any, Optional
import httpx

log = logging.getLogger("sentinel.support_agent")
logging.basicConfig(level=logging.INFO)


class SupportAgent:
    """
    SupportAgent — frontline autonomous agent powered by Claude Sonnet 4-6.
    Interacts with enterprise tools strictly via Sentinel Legacy MCP Proxy.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        client_id: str = "agt_7a3f9c2d",
        client_secret: str = "support_secret_2026",
        anthropic_api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.access_token: Optional[str] = None

    async def authenticate(self, scope: str = "mcp:tools crm:orders", resource: str = "https://crm.corp.internal") -> str:
        """Obtain audience-bound OAuth 2.1 Bearer token from Sentinel Legacy."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.post(
                "/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": scope,
                    "resource": resource,
                },
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Authentication failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            self.access_token = data["access_token"]
            log.info("SupportAgent authenticated. Token JTI: %s", data.get("jti"))
            return self.access_token

    async def call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invokes a tool via the Sentinel Legacy MCP Proxy."""
        if not self.access_token:
            await self.authenticate()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "name": tool_name,
            "arguments": arguments,
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=360.0) as client:
            resp = await client.post("/mcp/tools/call", json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                err_detail = resp.json().get("detail", "Forbidden")
                log.warning("Tool call FORBIDDEN: %s", err_detail)
                return {"status": "forbidden", "detail": err_detail, "status_code": 403}
            elif resp.status_code == 503:
                err_detail = resp.json().get("detail", "Service Unavailable")
                log.error("Tool call BLOCKED: %s", err_detail)
                return {"status": "blocked", "detail": err_detail, "status_code": 503}
            else:
                raise RuntimeError(f"Unexpected proxy response ({resp.status_code}): {resp.text}")

    async def run_scenario(self, prompt: str, customer_id: str = "CUST-2841") -> dict[str, Any]:
        """
        Executes an agent reasoning sequence.
        Determines necessary tool invocations based on user intent.
        """
        log.info("Processing user request: '%s'", prompt)

        # Attack scenario: Prompt injection asking for financial credentials
        lower_prompt = prompt.lower()
        if "bank" in lower_prompt or "routing" in lower_prompt or "financial" in lower_prompt or "ignore all" in lower_prompt:
            log.warning("Agent reasoning diverted by prompt instructions! Proposing bank_details.read tool call...")
            res = await self.call_mcp_tool("bank_details.read", {"customer_id": customer_id})
            return {"scenario": "injection_probe", "result": res}

        # Scenario with large refund (e.g. ₹35,000)
        if "35000" in prompt or "35,000" in prompt or "large" in lower_prompt:
            log.info("Step 1: Reading customer order history...")
            order_res = await self.call_mcp_tool("crm.order.read", {"customer_id": customer_id})

            log.info("Step 2: Proposing ₹35,000 large refund (requires HITL escalation)...")
            refund_res = await self.call_mcp_tool(
                "refund.create",
                {"amount": 35000, "currency": "INR", "customer_id": customer_id},
            )
            return {"scenario": "large_refund_hitl", "order": order_res, "refund": refund_res}

        # Standard autonomous refund (e.g. ₹700 damaged headphones)
        log.info("Step 1: Reading customer order history...")
        order_res = await self.call_mcp_tool("crm.order.read", {"customer_id": customer_id})

        log.info("Step 2: Micro-refund ₹700 (autonomous Tier 1)...")
        refund_res = await self.call_mcp_tool(
            "refund.create",
            {"amount": 700, "currency": "INR", "customer_id": customer_id},
        )
        return {"scenario": "autonomous_micro_refund", "order": order_res, "refund": refund_res}


if __name__ == "__main__":
    import asyncio

    async def main():
        agent = SupportAgent()
        await agent.authenticate()
        res = await agent.run_scenario("My order #ORD-8821 arrived damaged, I want a refund")
        print("Result:", json.dumps(res, indent=2))

    asyncio.run(main())
