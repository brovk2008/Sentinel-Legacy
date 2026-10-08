from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math
from typing import Optional


class TrustEventType(str, Enum):
    SUCCESS = "success"
    VIOLATION = "violation"
    REJECTION = "rejection"
    TIMEOUT = "timeout"


WEIGHTS = {
    TrustEventType.SUCCESS: +0.05,
    TrustEventType.VIOLATION: -15.0,
    TrustEventType.REJECTION: -5.0,
    TrustEventType.TIMEOUT: -3.0,
}

LAMBDA_DECAY = 0.001  # per hour
BASE_SCORE = 85.0


@dataclass(frozen=True)
class TrustEvent:
    event_type: TrustEventType
    occurred_at: datetime


@dataclass
class TrustScoreBreakdown:
    current_score: float
    base_score: float
    success_count: int
    success_contribution: float
    violation_count: int
    violation_penalty: float
    rejection_count: int
    rejection_penalty: float
    timeout_count: int
    timeout_penalty: float
    temporal_decay_adjustment: float
    status: str


def compute_trust_score(events: list[TrustEvent], now: Optional[datetime] = None) -> float:
    now = now or datetime.utcnow()
    score = BASE_SCORE
    for event in events:
        weight = WEIGHTS[event.event_type]
        if event.event_type == TrustEventType.SUCCESS:
            score += weight  # successes do not decay
        else:
            hours_ago = max(0.0, (now - event.occurred_at).total_seconds() / 3600.0)
            decay = math.exp(-LAMBDA_DECAY * hours_ago)
            score += weight * decay
    return round(max(0.0, min(100.0, score)), 2)


def get_trust_score_breakdown(
    events: list[TrustEvent], current_score: Optional[float] = None, now: Optional[datetime] = None
) -> TrustScoreBreakdown:
    now = now or datetime.utcnow()
    success_cnt = 0
    viol_cnt = 0
    rej_cnt = 0
    to_cnt = 0

    succ_contrib = 0.0
    viol_pen = 0.0
    rej_pen = 0.0
    to_pen = 0.0
    raw_viol_pen = 0.0
    raw_rej_pen = 0.0

    for ev in events:
        if ev.event_type == TrustEventType.SUCCESS:
            success_cnt += 1
            succ_contrib += WEIGHTS[TrustEventType.SUCCESS]
        elif ev.event_type == TrustEventType.VIOLATION:
            viol_cnt += 1
            raw_viol_pen += WEIGHTS[TrustEventType.VIOLATION]
            hours_ago = max(0.0, (now - ev.occurred_at).total_seconds() / 3600.0)
            viol_pen += WEIGHTS[TrustEventType.VIOLATION] * math.exp(-LAMBDA_DECAY * hours_ago)
        elif ev.event_type == TrustEventType.REJECTION:
            rej_cnt += 1
            raw_rej_pen += WEIGHTS[TrustEventType.REJECTION]
            hours_ago = max(0.0, (now - ev.occurred_at).total_seconds() / 3600.0)
            rej_pen += WEIGHTS[TrustEventType.REJECTION] * math.exp(-LAMBDA_DECAY * hours_ago)
        elif ev.event_type == TrustEventType.TIMEOUT:
            to_cnt += 1
            hours_ago = max(0.0, (now - ev.occurred_at).total_seconds() / 3600.0)
            to_pen += WEIGHTS[TrustEventType.TIMEOUT] * math.exp(-LAMBDA_DECAY * hours_ago)

    computed = max(0.0, min(100.0, BASE_SCORE + succ_contrib + viol_pen + rej_pen + to_pen))
    final_score = current_score if current_score is not None else computed

    # Temporal decay adjustment is difference between raw penalty and decayed penalty
    decay_adj = round((raw_viol_pen + raw_rej_pen) - (viol_pen + rej_pen), 2)
    decay_adj = max(0.0, decay_adj)

    return TrustScoreBreakdown(
        current_score=round(final_score, 2),
        base_score=BASE_SCORE,
        success_count=success_cnt,
        success_contribution=round(succ_contrib, 2),
        violation_count=viol_cnt,
        violation_penalty=round(viol_pen, 2),
        rejection_count=rej_cnt,
        rejection_penalty=round(rej_pen, 2),
        timeout_count=to_cnt,
        timeout_penalty=round(to_pen, 2),
        temporal_decay_adjustment=decay_adj,
        status=status_from_score(final_score),
    )


def status_from_score(score: float) -> str:
    if score >= 70.0:
        return "ACTIVE"
    elif score >= 40.0:
        return "RESTRICTED"
    return "SUSPENDED"
