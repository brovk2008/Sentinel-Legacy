from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
import time
from typing import Any, Optional


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ViolationVelocityTracker:
    """
    Sliding window violation counter per agent.
    Tracks velocity of forbidden/denied access attempts.
    """

    def __init__(
        self,
        redis: Any,
        window_seconds: int = 300,
        warning_threshold: int = 2,
        critical_threshold: int = 3,
    ):
        self.redis = redis
        self.window = window_seconds
        self.warning = warning_threshold
        self.critical = critical_threshold
        # In-memory backup
        self._mem_windows: dict[str, deque[float]] = defaultdict(deque)

    async def record_and_evaluate(
        self, agent_id: str, action: str, policy_id: str, ts: Optional[datetime] = None
    ) -> tuple[AlertLevel, int]:
        ts = ts or datetime.utcnow()
        ts_score = ts.timestamp()
        key = f"sentinel:violations:{agent_id}"

        count = 0
        try:
            import uuid
            member = f"{ts_score}:{uuid.uuid4().hex[:8]}:{action}:{policy_id}"
            await self.redis.zadd(key, {member: ts_score})
            cutoff = ts_score - self.window
            await self.redis.zremrangebyscore(key, "-inf", cutoff)
            await self.redis.expire(key, self.window + 60)
            count = await self.redis.zcard(key)
        except Exception:
            # Fallback to in-memory sliding window
            q = self._mem_windows[agent_id]
            q.append(ts_score)
            cutoff = ts_score - self.window
            while q and q[0] < cutoff:
                q.popleft()
            count = len(q)

        if count >= self.critical:
            return AlertLevel.CRITICAL, count
        elif count >= self.warning:
            return AlertLevel.WARNING, count
        return AlertLevel.INFO, count

    async def get_recent_count(self, agent_id: str) -> int:
        key = f"sentinel:violations:{agent_id}"
        try:
            cutoff = time.time() - self.window
            await self.redis.zremrangebyscore(key, "-inf", cutoff)
            return await self.redis.zcard(key)
        except Exception:
            q = self._mem_windows[agent_id]
            cutoff = time.time() - self.window
            while q and q[0] < cutoff:
                q.popleft()
            return len(q)
