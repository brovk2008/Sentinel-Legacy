import asyncio
from datetime import datetime
import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentinel.core.redis import InMemoryRedis
from sentinel.monitor.anomaly import AlertLevel, ViolationVelocityTracker


@pytest.mark.asyncio
async def test_violation_velocity_thresholds():
    redis = InMemoryRedis()
    tracker = ViolationVelocityTracker(
        redis=redis,
        window_seconds=300,
        warning_threshold=2,
        critical_threshold=3,
    )

    now = datetime.utcnow()

    # Violation 1 -> INFO
    level1, count1 = await tracker.record_and_evaluate("agt_test", "bank_details.read", "SEC-001", now)
    assert count1 == 1
    assert level1 == AlertLevel.INFO

    # Violation 2 -> WARNING
    level2, count2 = await tracker.record_and_evaluate("agt_test", "bank_details.read", "SEC-001", now)
    assert count2 == 2
    assert level2 == AlertLevel.WARNING

    # Violation 3 -> CRITICAL
    level3, count3 = await tracker.record_and_evaluate("agt_test", "bank_details.read", "SEC-001", now)
    assert count3 == 3
    assert level3 == AlertLevel.CRITICAL
