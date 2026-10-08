from collections import defaultdict
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)


class ToolCircuitBreaker:
    """
    Per-tool circuit breaker. Prevents cascading failures from
    flaky enterprise APIs from degrading agent trust scores unfairly.
    """

    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"            # Tool failing — reject fast
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

    def __init__(self, failure_threshold: int = 5, recovery_seconds: int = 60):
        self._state: dict[str, str] = defaultdict(lambda: self.CLOSED)
        self._failures: dict[str, int] = defaultdict(int)
        self._opened_at: dict[str, datetime] = {}
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds

    def is_open(self, tool_name: str) -> bool:
        state = self._state[tool_name]
        if state == self.OPEN:
            if datetime.utcnow() - self._opened_at.get(tool_name, datetime.min) > timedelta(seconds=self.recovery_seconds):
                self._state[tool_name] = self.HALF_OPEN
                return False
            return True
        return False

    def record_success(self, tool_name: str):
        self._state[tool_name] = self.CLOSED
        self._failures[tool_name] = 0

    def record_failure(self, tool_name: str):
        self._failures[tool_name] += 1
        if self._failures[tool_name] >= self.failure_threshold:
            self._state[tool_name] = self.OPEN
            self._opened_at[tool_name] = datetime.utcnow()
            log.warning("Circuit breaker OPEN for tool %s (%d failures)", tool_name, self._failures[tool_name])
