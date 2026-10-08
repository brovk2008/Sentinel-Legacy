from datetime import datetime, timedelta
import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentinel.trust.scorer import (
    BASE_SCORE,
    TrustEvent,
    TrustEventType,
    compute_trust_score,
    get_trust_score_breakdown,
    status_from_score,
)


def test_base_score_fresh_agent():
    score = compute_trust_score([])
    assert score == 85.0
    assert status_from_score(score) == "ACTIVE"


def test_success_increments_trust():
    events = [TrustEvent(TrustEventType.SUCCESS, datetime.utcnow()) for _ in range(10)]
    score = compute_trust_score(events)
    assert score == pytest.approx(85.5, rel=1e-2)


def test_violation_penalty_reduces_score():
    events = [TrustEvent(TrustEventType.VIOLATION, datetime.utcnow())]
    score = compute_trust_score(events)
    assert score == pytest.approx(70.0, rel=1e-2)
    assert status_from_score(score) == "ACTIVE"


def test_multiple_violations_restrict_agent():
    events = [
        TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()),
        TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()),
    ]
    score = compute_trust_score(events)
    assert score == pytest.approx(55.0, rel=1e-2)
    assert status_from_score(score) == "RESTRICTED"


def test_triple_violation_suspends_agent():
    events = [
        TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()),
        TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()),
        TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()),
    ]
    score = compute_trust_score(events)
    assert score == pytest.approx(40.0, rel=1e-2)
    # At 40 it's borderline, another violation drops to suspend
    events.append(TrustEvent(TrustEventType.VIOLATION, datetime.utcnow()))
    score4 = compute_trust_score(events)
    assert score4 < 40.0
    assert status_from_score(score4) == "SUSPENDED"


def test_temporal_decay():
    old_time = datetime.utcnow() - timedelta(days=30)
    old_events = [TrustEvent(TrustEventType.VIOLATION, old_time)]
    recent_events = [TrustEvent(TrustEventType.VIOLATION, datetime.utcnow())]

    score_old = compute_trust_score(old_events)
    score_recent = compute_trust_score(recent_events)

    # Older infraction decays more and thus causes less penalty
    assert score_old > score_recent
