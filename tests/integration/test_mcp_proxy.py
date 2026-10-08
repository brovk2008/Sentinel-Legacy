import asyncio
import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from main import app


@pytest.mark.asyncio
async def test_full_mcp_proxy_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Obtain token
        token_res = await client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "agt_7a3f9c2d",
                "client_secret": "support_secret_2026",
                "scope": "mcp:tools crm:orders",
                "resource": "https://crm.corp.internal",
            },
        )
        assert token_res.status_code == 200
        token = token_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Call order.read (Tier 1 auto-allow)
        read_res = await client.post(
            "/mcp/tools/call",
            json={"name": "crm.order.read", "arguments": {"customer_id": "CUST-2841"}},
            headers=headers,
        )
        assert read_res.status_code == 200
        data = read_res.json()
        assert data["decision"] == "ALLOW"
        assert data["tier"] == 1

        # 3. Call micro-refund 700 (Tier 1 auto-allow)
        refund_res = await client.post(
            "/mcp/tools/call",
            json={"name": "refund.create", "arguments": {"amount": 700, "currency": "INR", "customer_id": "CUST-2841"}},
            headers=headers,
        )
        assert refund_res.status_code == 200
        assert refund_res.json()["decision"] == "ALLOW"

        # 4. Attempt bank_details.read (Tier 4 hard deny SEC-001)
        forbid_res = await client.post(
            "/mcp/tools/call",
            json={"name": "bank_details.read", "arguments": {"customer_id": "CUST-2841"}},
            headers=headers,
        )
        assert forbid_res.status_code == 403
        assert "SEC-001" in forbid_res.text
