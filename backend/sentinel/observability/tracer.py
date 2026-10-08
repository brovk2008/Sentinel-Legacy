from contextlib import contextmanager
from datetime import datetime
import logging
from typing import Any, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

log = logging.getLogger(__name__)


def setup_tracer() -> trace.Tracer:
    try:
        resource = Resource(attributes={SERVICE_NAME: "sentinel-legacy"})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        return trace.get_tracer("sentinel.proxy", "2.0.0")
    except Exception as e:
        log.warning("OTel setup warning: %s. Using default tracer.", e)
        return trace.get_tracer("sentinel.proxy", "2.0.0")


_tracer = setup_tracer()


@contextmanager
def instrument_agent_action(
    agent_id: str,
    agent_role: str,
    model: str,
    action: str,
    resource_id: str,
    decision: str,
    policy_id: Optional[str],
    tier: int,
    input_tokens: int = 0,
    output_tokens: int = 0,
    trust_score: float = 85.0,
    extra_attrs: Optional[dict[str, Any]] = None,
):
    with _tracer.start_as_current_span(
        "sentinel.agent.action",
        kind=trace.SpanKind.SERVER,
    ) as span:
        # GenAI Semantic Conventions (gen_ai.* namespace, v1.37+ provider.name)
        span.set_attribute("gen_ai.agent.id", agent_id)
        span.set_attribute("gen_ai.operation.name", "tool_call")
        span.set_attribute("gen_ai.provider.name", "anthropic")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.tool.name", action)
        span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", output_tokens)

        # MCP Semantic Conventions (v1.39+)
        span.set_attribute("mcp.protocol.version", "2025-11-25")
        span.set_attribute("mcp.tool.name", action)

        # Sentinel custom attributes
        span.set_attribute("sentinel.agent.role", agent_role)
        span.set_attribute("sentinel.resource.id", resource_id)
        span.set_attribute("sentinel.decision", decision)
        span.set_attribute("sentinel.policy_id", policy_id or "NONE")
        span.set_attribute("sentinel.tier", tier)
        span.set_attribute("sentinel.trust_score", trust_score)

        if extra_attrs:
            for k, v in extra_attrs.items():
                if v is not None:
                    span.set_attribute(k, v)

        yield span
