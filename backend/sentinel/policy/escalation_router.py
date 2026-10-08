from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EscalationConfig:
    escalatable: bool
    approver_role: str
    timeout_seconds: int
    reversible: bool
    risk_level: str
    reason_template: str
    require_rationale: bool = True
    require_checkbox_ack: bool = True


ESCALATION_ROUTING: dict[str, EscalationConfig] = {
    "refund.create": EscalationConfig(
        escalatable=True,
        approver_role="finance_manager",
        timeout_seconds=300,
        reversible=False,
        risk_level="high",
        reason_template="Refund ₹{amount} {currency} exceeds the ₹10,000 autonomous threshold (REFUND-004)",
    ),
    "account.close": EscalationConfig(
        escalatable=True,
        approver_role="senior_manager",
        timeout_seconds=600,
        reversible=False,
        risk_level="critical",
        reason_template="Account closure for {resource_id} is permanent and irreversible (ACCOUNT-007)",
    ),
    "pii.export": EscalationConfig(
        escalatable=True,
        approver_role="compliance_officer",
        timeout_seconds=900,
        reversible=False,
        risk_level="critical",
        reason_template="PII export for {num_records} records requires compliance officer authorization",
    ),
    "bank_details.read": EscalationConfig(
        escalatable=False,
        approver_role="",
        timeout_seconds=0,
        reversible=False,
        risk_level="forbidden",
        reason_template="",
    ),
    "db.export.all": EscalationConfig(
        escalatable=False,
        approver_role="",
        timeout_seconds=0,
        reversible=False,
        risk_level="forbidden",
        reason_template="",
    ),
}


def should_escalate(action: str, cedar_denied: bool, context: Optional[dict] = None) -> bool:
    config = ESCALATION_ROUTING.get(action)
    if not config or not config.escalatable or not cedar_denied:
        return False
    # If action is refund.create, only escalate if amount > 10000
    if action == "refund.create" and context:
        amount = context.get("amount", 0)
        if amount <= 10000:
            return False
    return True
