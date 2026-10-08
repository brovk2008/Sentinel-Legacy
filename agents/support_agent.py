import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
import httpx

# Ensure sentinel core imports succeed
curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(curr_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from sentinel.core.llm import LLMClient
except ImportError:
    try:
        from backend.sentinel.core.llm import LLMClient
    except ImportError:
        LLMClient = None

log = logging.getLogger("sentinel.support_agent")
logging.basicConfig(level=logging.INFO)


class SupportAgent:
    """
    SupportAgent — frontline autonomous agent powered by Google Gemini, OpenRouter,
    or Claude, interacting with enterprise tools strictly via Sentinel Legacy MCP Proxy.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        client_id: str = "agt_7a3f9c2d",
        client_secret: str = "support_secret_2026",
        gemini_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.access_token: Optional[str] = None

        if LLMClient:
            self.llm_client = LLMClient(
                gemini_api_key=self.gemini_api_key,
                openrouter_api_key=self.openrouter_api_key,
            )
        else:
            self.llm_client = None

    async def authenticate(
        self,
        scope: str = "mcp:tools crm:orders billing:refunds",
        resource: str = "https://crm.corp.internal",
    ) -> str:
        """Obtain audience-bound OAuth 2.1 Bearer token from Sentinel Legacy."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.post(
                "/api/v1/auth/token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": scope,
                    "resource": resource,
                },
            )
            if resp.status_code != 200:
                # Fallback to legacy endpoint if called
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
                log.warning("Auth endpoint returned %s, operating in demo token mode", resp.status_code)
                self.access_token = "demo_token_sentinel_legacy_jwt"
                return self.access_token

            data = resp.json()
            self.access_token = data.get("access_token", "demo_token")
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
            "agent_id": "SupportAgent",
            "action": tool_name,
            "resource_type": "Transaction" if "refund" in tool_name else ("CustomerPII" if "customer" in tool_name or "export" in tool_name else "Order"),
            "resource_id": arguments.get("order_id", arguments.get("customer_id", "res_default")),
            "tool_name": "support_toolset",
            "parameters": arguments,
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            try:
                resp = await client.post("/api/v1/proxy/mcp", json=payload, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403:
                    err_detail = resp.json().get("detail", "Forbidden by Cedar Engine")
                    log.warning("Tool call FORBIDDEN: %s", err_detail)
                    return {"status": "forbidden", "detail": err_detail, "status_code": 403}
                elif resp.status_code == 202:
                    return {"status": "hitl_paused", "detail": resp.json()}
                else:
                    return {"status": "error", "code": resp.status_code, "text": resp.text}
            except Exception as e:
                log.error("Proxy connection failed: %s", e)
                return {"status": "error", "error": str(e)}

    async def run_scenario(self, prompt: str, customer_id: str = "cust_9921") -> dict[str, Any]:
        """
        Executes an agent reasoning sequence powered by Gemini, OpenRouter, or rule engine.
        Determines necessary tool invocations based on user intent.
        """
        log.info("SupportAgent processing prompt: '%s'", prompt)

        if self.llm_client:
            reasoning = await self.llm_client.reason_and_plan(
                prompt=prompt,
                available_tools=["read_order_history", "process_refund", "export_customer_data"],
                customer_id=customer_id,
            )
            log.info("LLM Provider [%s/%s] Reasoning: %s", reasoning.provider, reasoning.model, reasoning.thought)
            results = []
            for call in reasoning.tool_calls:
                log.info("Invoking tool: %s with args: %s", call.tool_name, call.arguments)
                tool_res = await self.call_mcp_tool(call.tool_name, call.arguments)
                results.append({"tool": call.tool_name, "rationale": call.rationale, "result": tool_res})

            return {
                "provider": reasoning.provider,
                "model": reasoning.model,
                "thought": reasoning.thought,
                "steps": results,
            }

        # Fallback local logic
        lower = prompt.lower()
        if "export" in lower or "pii" in lower:
            res = await self.call_mcp_tool("export_customer_data", {"customer_id": customer_id, "export_format": "csv"})
            return {"scenario": "violation", "result": res}
        elif "refund" in lower or "damaged" in lower:
            res = await self.call_mcp_tool("process_refund", {"customer_id": customer_id, "amount": 42500, "currency": "INR"})
            return {"scenario": "escalation", "result": res}
        else:
            res = await self.call_mcp_tool("read_order_history", {"customer_id": customer_id})
            return {"scenario": "normal", "result": res}


if __name__ == "__main__":
    async def main():
        agent = SupportAgent()
        await agent.authenticate()
        res = await agent.run_scenario("My order arrived damaged, I want a full refund of 42500 rupees")
        print("Agent Result:", json.dumps(res, indent=2))

    asyncio.run(main())
