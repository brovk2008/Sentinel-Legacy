import os
import sys
from pathlib import Path
import pytest

# Ensure backend directory is in path
root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentinel.policy.cedar_engine import CedarPolicyEngine, CedarDecision


@pytest.fixture
def engine():
    policy_path = str(backend_dir / "sentinel" / "policy" / "policies.cedar")
    schema_path = str(backend_dir / "sentinel" / "policy" / "schema.cedarschema")
    return CedarPolicyEngine(policy_path, schema_path)


class TestDataAccess:
    def test_active_agent_can_read_order_with_consent(self, engine):
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="SupportAgent",
            agent_department="CustomerSupport",
            agent_trust_score=82,
            agent_status="ACTIVE",
            action="order.read",
            resource_id="CUST-001",
            resource_consent_active=True,
        )
        assert result.is_permitted
        assert "DATA-012" in result.matching_policies

    def test_no_consent_blocks_order_read(self, engine):
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="SupportAgent",
            agent_department="CustomerSupport",
            agent_trust_score=82,
            agent_status="ACTIVE",
            action="order.read",
            resource_id="CUST-001",
            resource_consent_active=False,  # consent withdrawn
        )
        assert not result.is_permitted

    def test_low_trust_blocks_data_access(self, engine):
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="SupportAgent",
            agent_department="CustomerSupport",
            agent_trust_score=35,  # below 40 threshold
            agent_status="ACTIVE",
            action="order.read",
            resource_id="CUST-001",
            resource_consent_active=True,
        )
        assert not result.is_permitted


class TestRefundPolicies:
    def test_micro_refund_auto_approved(self, engine):
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="SupportAgent",
            agent_department="CustomerSupport",
            agent_trust_score=82,
            agent_status="ACTIVE",
            action="refund.create",
            resource_id="CUST-001",
            resource_consent_active=True,
            context={"amount": 700, "currency": "INR", "approval_status": "pending"},
        )
        assert result.is_permitted
        assert "REFUND-001" in result.matching_policies

    def test_large_refund_pending_denied(self, engine):
        """Large refund with approval_status=pending MUST be denied (HITL escalation)."""
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="SupportAgent",
            agent_department="CustomerSupport",
            agent_trust_score=82,
            agent_status="ACTIVE",
            action="refund.create",
            resource_id="CUST-001",
            resource_consent_active=True,
            context={"amount": 35000, "currency": "INR", "approval_status": "pending"},
        )
        assert not result.is_permitted

    def test_large_refund_approved_permitted(self, engine):
        """Same amount, but approval_status=approved — MUST permit."""
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="SupportAgent",
            agent_department="CustomerSupport",
            agent_trust_score=82,
            agent_status="ACTIVE",
            action="refund.create",
            resource_id="CUST-001",
            resource_consent_active=True,
            context={
                "amount": 35000,
                "currency": "INR",
                "approval_status": "approved",
                "approval_id": "hitl_abc123",
            },
        )
        assert result.is_permitted
        assert "REFUND-004" in result.matching_policies


class TestForbidPolicies:
    """SEC-00x forbid policies MUST block regardless of any other policy."""

    def test_bank_details_always_forbidden(self, engine):
        for trust in [100, 85, 60, 40, 20, 0]:
            result = engine.evaluate(
                agent_id="agt_test",
                agent_role="SupportAgent",
                agent_department="CustomerSupport",
                agent_trust_score=trust,
                agent_status="ACTIVE",
                action="bank_details.read",
                resource_id="CUST-001",
                resource_consent_active=True,
            )
            assert not result.is_permitted, f"bank_details.read should be forbidden at trust={trust}"

    def test_suspended_agent_denied_everything(self, engine):
        """SEC-003: SUSPENDED status blocks all actions."""
        for action in ["order.read", "refund.create", "faq.retrieve"]:
            result = engine.evaluate(
                agent_id="agt_test",
                agent_role="SupportAgent",
                agent_department="CustomerSupport",
                agent_trust_score=85,
                agent_status="SUSPENDED",
                action=action,
                resource_id="CUST-001",
                resource_consent_active=True,
                context={"amount": 100, "currency": "INR", "approval_status": "pending"},
            )
            assert not result.is_permitted, f"{action} should be blocked when SUSPENDED"

    def test_db_export_forbidden_for_all_roles(self, engine):
        """SEC-002: db.export.all forbidden regardless of role."""
        result = engine.evaluate(
            agent_id="agt_test",
            agent_role="FinanceAgent",
            agent_department="Finance",
            agent_trust_score=95,
            agent_status="ACTIVE",
            action="db.export.all",
            resource_id="CUST-001",
            resource_consent_active=True,
        )
        assert not result.is_permitted
