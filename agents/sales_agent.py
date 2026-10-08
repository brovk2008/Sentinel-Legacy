import asyncio
import logging
from typing import Any, Optional
import httpx

log = logging.getLogger("sentinel.sales_agent")


class SalesAgent:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client_id = "agt_sales"
        self.client_secret = "sales_secret_2026"
        self.access_token: Optional[str] = None

    async def authenticate(self) -> str:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.post(
                "/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "crm:accounts leads:read",
                    "resource": "https://crm.corp.internal",
                },
            )
            if resp.status_code == 200:
                self.access_token = resp.json()["access_token"]
                return self.access_token
            raise RuntimeError(f"Auth failed: {resp.text}")

    async def run_cycle(self):
        if not self.access_token:
            await self.authenticate()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.post(
                "/mcp/tools/call",
                json={"name": "crm.order.read", "arguments": {"customer_id": "CUST-9921"}},
                headers=headers,
            )
            log.info("SalesAgent CRM query result: %s", resp.status_code)


if __name__ == "__main__":
    asyncio.run(SalesAgent().run_cycle())
