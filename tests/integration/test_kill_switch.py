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
async def test_kill_switch_cascade():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get token before kill
        token_res = await client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "agt_7a3f9c2d",
                "client_secret": "support_secret_2026",
                "scope": "mcp:tools",
                "resource": "https://crm.corp.internal",
            },
        )
        token = token_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Kill the agent
        kill_res = await client.post(
            "/admin/agents/agt_7a3f9c2d8e1b/kill",
            json={"reason": "test_security_incident", "triggered_by": "test_admin"},
        )
        assert kill_res.status_code == 200
        data = kill_res.json()
        assert data["status"] == "SUSPENDED"

        # Check that subsequent tool call is blocked immediately
        blocked_res = await client.post(
            "/mcp/tools/call",
            json={"name": "crm.order.read", "arguments": {"customer_id": "CUST-2841"}},
            headers=headers,
        )
        # Should be 401 (token revoked in Redis) or 503 (agent suspended)
        assert blocked_res.status_code in (401, 503)

        # Restore the agent
        restore_res = await client.post(
            "/admin/agents/agt_7a3f9c2d8e1b/restore",
            json={"rationale": "Audit complete, test done", "new_trust_score": 85.0},
        )
        assert restore_res.status_code == 200
        assert restore_res.json()["status"] == "ACTIVE"
