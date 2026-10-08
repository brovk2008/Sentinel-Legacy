"""
Sentinel Legacy Governance SDK
===============================
Production Python client library for integrating autonomous AI agents (LangChain, CrewAI,
LlamaIndex, AutoGen, and raw LLM tool callers) with the Sentinel Legacy Governance Control Plane.
"""

from .client import SentinelClient, ToolExecutionResult
from .exceptions import (
    SentinelError,
    AuthenticationError,
    PolicyViolationError,
    HITLTimeoutError,
    KillSwitchActiveError,
)
from .decorators import governed_tool

__version__ = "2.0.0"
__all__ = [
    "SentinelClient",
    "ToolExecutionResult",
    "SentinelError",
    "AuthenticationError",
    "PolicyViolationError",
    "HITLTimeoutError",
    "KillSwitchActiveError",
    "governed_tool",
]
