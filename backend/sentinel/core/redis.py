import asyncio
import logging
import time
from typing import Any, Optional
import redis.asyncio as aioredis
from sentinel.core.config import get_settings

log = logging.getLogger(__name__)


class InMemoryRedis:
    """
    High-performance in-memory fallback mimicking redis.asyncio.Redis.
    Ensures Sentinel Legacy runs seamlessly even without a standalone Redis instance.
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expiries: dict[str, float] = {}
        self._lists: dict[str, list[str]] = {}
        self._zsets: dict[str, dict[str, float]] = {}
        self._waiting_queues: dict[str, list[asyncio.Event]] = {}
        self._lock = asyncio.Lock()

    def _purge_if_expired(self, key: str):
        if key in self._expiries:
            if time.time() > self._expiries[key]:
                self._data.pop(key, None)
                self._lists.pop(key, None)
                self._zsets.pop(key, None)
                self._expiries.pop(key, None)

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            self._purge_if_expired(key)
            return self._data.get(key)

    async def set(self, key: str, value: Any) -> bool:
        async with self._lock:
            self._data[key] = str(value) if not isinstance(value, str) else value
            self._expiries.pop(key, None)
            return True

    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        async with self._lock:
            self._data[key] = str(value) if not isinstance(value, str) else value
            self._expiries[key] = time.time() + seconds
            return True

    async def exists(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                self._purge_if_expired(k)
                if k in self._data or k in self._lists or k in self._zsets:
                    count += 1
            return count

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            deleted = 0
            for k in keys:
                if k in self._data or k in self._lists or k in self._zsets:
                    deleted += 1
                self._data.pop(k, None)
                self._lists.pop(k, None)
                self._zsets.pop(k, None)
                self._expiries.pop(k, None)
            return deleted

    async def lpush(self, key: str, *values: Any) -> int:
        async with self._lock:
            if key not in self._lists:
                self._lists[key] = []
            for v in values:
                self._lists[key].insert(0, str(v))
            if key in self._waiting_queues:
                for ev in self._waiting_queues[key]:
                    ev.set()
            return len(self._lists[key])

    async def rpush(self, key: str, *values: Any) -> int:
        async with self._lock:
            if key not in self._lists:
                self._lists[key] = []
            for v in values:
                self._lists[key].append(str(v))
            if key in self._waiting_queues:
                for ev in self._waiting_queues[key]:
                    ev.set()
            return len(self._lists[key])

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        async with self._lock:
            self._purge_if_expired(key)
            lst = self._lists.get(key, [])
            if stop == -1:
                return lst[start:]
            return lst[start : stop + 1]

    async def brpop(self, key: str, timeout: int = 0) -> Optional[tuple[str, str]]:
        deadline = time.time() + timeout if timeout > 0 else float("inf")
        while time.time() <= deadline:
            async with self._lock:
                self._purge_if_expired(key)
                lst = self._lists.get(key, [])
                if lst:
                    val = lst.pop()
                    return (key, val)
                ev = asyncio.Event()
                if key not in self._waiting_queues:
                    self._waiting_queues[key] = []
                self._waiting_queues[key].append(ev)

            wait_duration = min(0.2, max(0.01, deadline - time.time()))
            try:
                await asyncio.wait_for(ev.wait(), timeout=wait_duration)
            except asyncio.TimeoutError:
                pass
            finally:
                async with self._lock:
                    if key in self._waiting_queues and ev in self._waiting_queues[key]:
                        self._waiting_queues[key].remove(ev)
            if timeout > 0 and time.time() >= deadline:
                break
        return None

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        async with self._lock:
            if key not in self._zsets:
                self._zsets[key] = {}
            for member, score in mapping.items():
                self._zsets[key][member] = float(score)
            return len(mapping)

    async def zremrangebyscore(self, key: str, min_score: Any, max_score: Any) -> int:
        async with self._lock:
            zset = self._zsets.get(key, {})
            min_val = -float("inf") if min_score in ("-inf", float("-inf")) else float(min_score)
            max_val = float("inf") if max_score in ("+inf", float("inf")) else float(max_score)
            to_remove = [m for m, s in zset.items() if min_val <= s <= max_val]
            for m in to_remove:
                del zset[m]
            return len(to_remove)

    async def zcard(self, key: str) -> int:
        async with self._lock:
            self._purge_if_expired(key)
            return len(self._zsets.get(key, {}))

    async def expire(self, key: str, seconds: int) -> bool:
        async with self._lock:
            if key in self._data or key in self._lists or key in self._zsets:
                self._expiries[key] = time.time() + seconds
                return True
            return False

    async def ping(self) -> bool:
        return True


_redis_instance: Optional[Any] = None


async def get_redis() -> Any:
    global _redis_instance
    if _redis_instance is not None:
        return _redis_instance

    settings = get_settings()
    timeout = getattr(settings, "redis_connect_timeout", 3.0)
    try:
        kwargs: dict[str, Any] = {"decode_responses": True}
        if settings.redis_url.startswith("rediss://"):
            kwargs["ssl_cert_reqs"] = None

        client = aioredis.from_url(settings.redis_url, **kwargs)
        # Verify connection with configurable timeout
        await asyncio.wait_for(client.ping(), timeout=timeout)
        log.info("Connected to Redis server at %s", settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url)
        _redis_instance = client
        return _redis_instance
    except Exception as e:
        log.warning("Could not connect to external Redis (%s). Using InMemoryRedis fallback.", e)
        _redis_instance = InMemoryRedis()
        return _redis_instance
