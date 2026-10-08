import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure sdk is in sys.path
root_dir = Path(__file__).parent.parent.parent.resolve()
sdk_dir = root_dir / "sdk" / "python"
if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))

from sentinel_sdk import (
    SentinelClient,
    PolicyViolationError,
    KillSwitchActiveError,
    governed_tool,
)


@pytest.mark.asyncio
async def test_sdk_execute_tool_permit():
    client = SentinelClient(control_plane_url="http://test-server")
    client._ensure_token = AsyncMock(return_value="mock_jwt_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "decision": "PERMIT",
        "result": {"status": "success", "order_id": "ORD-123"},
        "cedar_latency_ms": 0.82,
        "ledger_hash": "sha256_mock_hash",
        "receipt_id": "rcpt_991",
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await client.execute_tool(
            action="read_order_history",
            resource_type="Order",
            resource_id="ord_123",
            tool_name="support_tools",
            parameters={"customer_id": "cust_1"},
        )

        assert res.decision == "PERMIT"
        assert res.status == "COMPLETED"
        assert res.result["order_id"] == "ORD-123"
        assert res.cedar_latency_ms == 0.82
        assert res.ledger_hash == "sha256_mock_hash"


@pytest.mark.asyncio
async def test_sdk_execute_tool_forbid_raises_exception():
    client = SentinelClient(control_plane_url="http://test-server")
    client._ensure_token = AsyncMock(return_value="mock_jwt_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.json.return_value = {
        "decision": "FORBID",
        "policy_id": "DATA-012",
        "reason": "Unconsented PII exfiltration forbidden",
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(PolicyViolationError) as exc_info:
            await client.execute_tool(
                action="export_customer_data",
                resource_type="CustomerPII",
                resource_id="all",
                tool_name="admin_tools",
                parameters={"format": "csv"},
            )

        assert exc_info.value.policy_id == "DATA-012"
        assert "Unconsented PII" in exc_info.value.reason


@pytest.mark.asyncio
async def test_sdk_execute_tool_kill_switch_active():
    client = SentinelClient(control_plane_url="http://test-server")
    client._ensure_token = AsyncMock(return_value="mock_jwt_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.json.return_value = {
        "decision": "KILL_SWITCH_ACTIVE",
        "detail": "Emergency kill switch active for agent",
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(KillSwitchActiveError):
            await client.execute_tool(
                action="read_order",
                resource_type="Order",
                resource_id="ord_1",
                tool_name="tool",
                parameters={},
            )


@pytest.mark.asyncio
async def test_sdk_governed_tool_decorator():
    client = SentinelClient(control_plane_url="http://test-server")
    client.execute_tool = AsyncMock(return_value=None)

    @governed_tool(client=client, action="process_refund", resource_type="Transaction")
    async def process_refund(amount: int, currency: str, customer_id: str):
        return {"refunded": True, "amount": amount}

    result = await process_refund(amount=500, currency="INR", customer_id="cust_88")
    assert result["refunded"] is True
    assert result["amount"] == 500
    assert client.execute_tool.called
