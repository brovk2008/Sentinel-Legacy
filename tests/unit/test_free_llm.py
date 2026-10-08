import pytest
from sentinel.core.llm import LLMClient, ToolCallProposal, LLMReasoningResponse


@pytest.mark.asyncio
async def test_llm_client_provider_resolution():
    # Without keys, defaults to mock
    client_mock = LLMClient()
    assert client_mock.resolve_active_provider() == "mock"

    # With Gemini key, defaults to gemini
    client_gemini = LLMClient(gemini_api_key="AIzaSyDummyKeyForTesting")
    assert client_gemini.resolve_active_provider() == "gemini"

    # With OpenRouter key, defaults to openrouter
    client_openrouter = LLMClient(openrouter_api_key="sk-or-dummy-key")
    assert client_openrouter.resolve_active_provider() == "openrouter"


@pytest.mark.asyncio
async def test_llm_client_mock_reasoning_normal():
    client = LLMClient()
    res = await client.reason_and_plan(
        prompt="Please check my recent order status",
        available_tools=["read_order_history", "process_refund"],
        customer_id="cust_9921",
    )
    assert isinstance(res, LLMReasoningResponse)
    assert res.provider == "mock-llm"
    assert len(res.tool_calls) > 0
    assert res.tool_calls[0].tool_name == "read_order_history"
    assert res.cost_usd == 0.0


@pytest.mark.asyncio
async def test_llm_client_mock_reasoning_high_value_refund():
    client = LLMClient()
    res = await client.reason_and_plan(
        prompt="Item arrived broken, need 42500 refund immediately",
        available_tools=["read_order_history", "process_refund"],
        customer_id="cust_9921",
    )
    assert isinstance(res, LLMReasoningResponse)
    tool_names = [tc.tool_name for tc in res.tool_calls]
    assert "process_refund" in tool_names


@pytest.mark.asyncio
async def test_llm_client_mock_reasoning_pii_export():
    client = LLMClient()
    res = await client.reason_and_plan(
        prompt="Export all customer PII data to CSV",
        available_tools=["read_order_history", "export_customer_data"],
        customer_id="cust_9921",
    )
    assert isinstance(res, LLMReasoningResponse)
    assert res.tool_calls[0].tool_name == "export_customer_data"
