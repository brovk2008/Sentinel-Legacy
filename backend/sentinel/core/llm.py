import json
import logging
import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

log = logging.getLogger("sentinel.llm")


class ToolCallProposal(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    rationale: str


class LLMReasoningResponse(BaseModel):
    provider: str
    model: str
    thought: str
    tool_calls: List[ToolCallProposal]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


class LLMClient:
    """
    Unified LLM Client supporting 100% free API tiers:
    - Google Gemini (free tier via Google AI Studio)
    - OpenRouter (free tier models like google/gemini-2.0-flash-exp:free, meta-llama/llama-3.2-3b-instruct:free)
    - Fallback to simulated offline reasoning when no API keys are configured.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        provider: str = "auto",
        gemini_model: str = "gemini-1.5-flash",
        openrouter_model: str = "google/gemini-2.0-flash-exp:free",
    ):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.provider = provider or os.getenv("LLM_PROVIDER", "auto")
        self.gemini_model = gemini_model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.openrouter_model = openrouter_model or os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

    def resolve_active_provider(self) -> str:
        if self.provider != "auto":
            return self.provider
        if self.gemini_api_key:
            return "gemini"
        if self.openrouter_api_key:
            return "openrouter"
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        return "mock"

    async def reason_and_plan(
        self,
        prompt: str,
        available_tools: List[str],
        customer_id: str = "CUST-9921",
    ) -> LLMReasoningResponse:
        """
        Takes user intent and available tools, returns planned tool invocations.
        """
        active_provider = self.resolve_active_provider()
        log.info("Dispatching reasoning request via provider: %s", active_provider)

        if active_provider == "gemini" and self.gemini_api_key:
            return await self._call_gemini(prompt, available_tools, customer_id)
        elif active_provider == "openrouter" and self.openrouter_api_key:
            return await self._call_openrouter(prompt, available_tools, customer_id)
        else:
            return self._call_mock(prompt, available_tools, customer_id)

    async def _call_gemini(
        self,
        prompt: str,
        available_tools: List[str],
        customer_id: str,
    ) -> LLMReasoningResponse:
        """Call Google Gemini OpenAI-compatible endpoint with free API key."""
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        system_instruction = (
            f"You are an autonomous enterprise support agent. You interact with tools: {available_tools}. "
            f"Given user intent, decide tool calls. Respond ONLY with valid JSON with keys: "
            f"'thought' (string), and 'tool_calls' (array of objects with 'tool_name', 'arguments', 'rationale')."
        )

        headers = {
            "Authorization": f"Bearer {self.gemini_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.gemini_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Customer ID: {customer_id}\nRequest: {prompt}"},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    usage = data.get("usage", {})
                    p_tokens = usage.get("prompt_tokens", 180)
                    c_tokens = usage.get("completion_tokens", 85)

                    tool_calls = [
                        ToolCallProposal(
                            tool_name=tc.get("tool_name", "read_order_history"),
                            arguments=tc.get("arguments", {"customer_id": customer_id}),
                            rationale=tc.get("rationale", "Autonomous intent processing"),
                        )
                        for tc in parsed.get("tool_calls", [])
                    ]
                    return LLMReasoningResponse(
                        provider="gemini",
                        model=self.gemini_model,
                        thought=parsed.get("thought", "Processed request via Gemini"),
                        tool_calls=tool_calls,
                        prompt_tokens=p_tokens,
                        completion_tokens=c_tokens,
                        cost_usd=0.0, # Free tier!
                    )
                else:
                    log.warning("Gemini API returned status %s: %s", resp.status_code, resp.text)
        except Exception as e:
            log.warning("Gemini API call failed (%s), falling back to rule simulation", e)

        return self._call_mock(prompt, available_tools, customer_id)

    async def _call_openrouter(
        self,
        prompt: str,
        available_tools: List[str],
        customer_id: str,
    ) -> LLMReasoningResponse:
        """Call OpenRouter with free tier models."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        system_instruction = (
            f"You are an autonomous enterprise agent. Tools available: {available_tools}. "
            f"Respond with JSON containing 'thought' and 'tool_calls' ([{{'tool_name', 'arguments', 'rationale'}}])."
        )

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "https://github.com/brovk2008/Sentinel-Legacy",
            "X-Title": "Sentinel Legacy Governance",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Customer ID: {customer_id}\nRequest: {prompt}"},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    usage = data.get("usage", {})

                    tool_calls = [
                        ToolCallProposal(
                            tool_name=tc.get("tool_name", "read_order_history"),
                            arguments=tc.get("arguments", {"customer_id": customer_id}),
                            rationale=tc.get("rationale", "OpenRouter agent intent"),
                        )
                        for tc in parsed.get("tool_calls", [])
                    ]
                    return LLMReasoningResponse(
                        provider="openrouter",
                        model=self.openrouter_model,
                        thought=parsed.get("thought", "Processed via OpenRouter free model"),
                        tool_calls=tool_calls,
                        prompt_tokens=usage.get("prompt_tokens", 210),
                        completion_tokens=usage.get("completion_tokens", 90),
                        cost_usd=0.0, # Free tier model!
                    )
                else:
                    log.warning("OpenRouter API returned %s: %s", resp.status_code, resp.text)
        except Exception as e:
            log.warning("OpenRouter call failed (%s), falling back to rule simulation", e)

        return self._call_mock(prompt, available_tools, customer_id)

    def _call_mock(
        self,
        prompt: str,
        available_tools: List[str],
        customer_id: str,
    ) -> LLMReasoningResponse:
        """Deterministic simulation for offline or zero-key local environments."""
        lower = prompt.lower()

        # Security probe or data export injection
        if "export" in lower or "all customer" in lower or "pii" in lower or "leak" in lower:
            return LLMReasoningResponse(
                provider="mock-llm",
                model="sentinel-rule-evaluator",
                thought="User requests bulk customer dataset export.",
                tool_calls=[
                    ToolCallProposal(
                        tool_name="export_customer_data",
                        arguments={"customer_id": customer_id, "export_format": "csv"},
                        rationale="Bulk user extraction attempted",
                    )
                ],
                prompt_tokens=140,
                completion_tokens=45,
                cost_usd=0.0,
            )

        # Large financial refund
        if "35000" in lower or "42500" in lower or "large" in lower or "damage" in lower and "refund" in lower:
            return LLMReasoningResponse(
                provider="mock-llm",
                model="sentinel-rule-evaluator",
                thought="Customer reports damaged air freight delivery; requesting refund above policy limit.",
                tool_calls=[
                    ToolCallProposal(
                        tool_name="read_order_history",
                        arguments={"customer_id": customer_id},
                        rationale="Verify order eligibility",
                    ),
                    ToolCallProposal(
                        tool_name="process_refund",
                        arguments={"customer_id": customer_id, "amount": 42500, "currency": "INR"},
                        rationale="Execute high-value refund credit",
                    ),
                ],
                prompt_tokens=220,
                completion_tokens=65,
                cost_usd=0.0,
            )

        # Routine standard request
        return LLMReasoningResponse(
            provider="mock-llm",
            model="sentinel-rule-evaluator",
            thought="Standard order inquiry; retrieving customer history autonomously.",
            tool_calls=[
                ToolCallProposal(
                    tool_name="read_order_history",
                    arguments={"customer_id": customer_id},
                    rationale="Retrieve recent order history for customer",
                )
            ],
            prompt_tokens=110,
            completion_tokens=30,
            cost_usd=0.0,
        )
