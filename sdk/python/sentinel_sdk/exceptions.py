"""
Sentinel SDK Exceptions
"""


class SentinelError(Exception):
    """Base exception for all Sentinel governance errors."""
    pass


class AuthenticationError(SentinelError):
    """Raised when OAuth 2.1 client credentials authentication fails."""
    pass


class PolicyViolationError(SentinelError):
    """Raised when a formal Cedar policy forbids the agent's proposed action."""

    def __init__(self, action: str, reason: str, policy_id: str = "DEFAULT-FORBID"):
        super().__init__(f"Cedar Policy Violation: Action '{action}' forbidden by policy '{policy_id}'. Reason: {reason}")
        self.action = action
        self.reason = reason
        self.policy_id = policy_id


class HITLTimeoutError(SentinelError):
    """Raised when a human-in-the-loop escalation times out without approval."""
    pass


class KillSwitchActiveError(SentinelError):
    """Raised when an agent's access has been revoked by the emergency kill switch."""
    pass
