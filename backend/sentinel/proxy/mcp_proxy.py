from datetime import datetime
import json
import logging
import time
from typing import Any, Optional
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from sentinel.auth.token_manager import TokenManager
from sentinel.hitl.queue import HITLQueue
from sentinel.ledger.writer import AuditLedger
from sentinel.models.agent import Agent, AgentStatus
from sentinel.models.audit import OTelSpan, Violation
from sentinel.models.hitl import HITLRecord
from sentinel.monitor.anomaly import AlertLevel, ViolationVelocityTracker
from sentinel.observability.tracer import instrument_agent_action
from sentinel.policy.cedar_engine import CedarPolicyEngine, CedarDecision
from sentinel.policy.escalation_router import ESCALATION_ROUTING, should_escalate
from sentinel.proxy.circuit_breaker import ToolCircuitBreaker
from sentinel.trust.scorer import TrustEvent, TrustEventType, compute_trust_score, status_from_score
from sentinel.ws.hub import WebSocketHub

log = logging.getLogger(__name__)


class MCPProxy:
    def __init__(
        self,
        token_manager: TokenManager,
        cedar_engine: CedarPolicyEngine,
        hitl_queue: HITLQueue,
        velocity_tracker: ViolationVelocityTracker,
        circuit_breaker: ToolCircuitBreaker,
        ws_hub: WebSocketHub,
    ):
        self.token_manager = token_manager
        self.cedar = cedar_engine
        self.hitl = hitl_queue
        self.velocity = velocity_tracker
        self.circuit_breaker = circuit_breaker
        self.ws_hub = ws_hub

    async def execute_tool_call(
        self,
        raw_token: str,
        tool_name: str,
        arguments: dict[str, Any],
        db: AsyncSession,
        expected_audience: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        The Core Authorization & Execution Loop.
        Guarantees:
        1. Token signature, audience, and Redis blacklist check.
        2. Agent status verification (Fail-closed if SUSPENDED).
        3. Cedar formal verification.
        4. Tiered HITL routing if escalatable.
        5. Real-time audit hashing before/after execution.
        """
        ledger = AuditLedger(db)

        # 1. JWT & Blacklist Validation
        try:
            token_payload = await self.token_manager.validate_token(raw_token, expected_audience=expected_audience)
        except Exception as e:
            log.warning("JWT validation failed: %s", e)
            raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")

        agent_id = token_payload.get("sub", "")
        token_sentinel = token_payload.get("sentinel", {})
        agent_role = token_sentinel.get("agent_role", "SupportAgent")

        # 2. Fetch Agent from DB
        stmt = select(Agent).where(Agent.agent_id == agent_id)
        res = await db.execute(stmt)
        agent = res.scalar_one_or_none()

        if not agent:
            # Fallback to query by client_id or role if agent_id not exact
            stmt2 = select(Agent).where(Agent.role == agent_role).limit(1)
            res2 = await db.execute(stmt2)
            agent = res2.scalar_one_or_none()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent identity not registered")

        # Fail-closed check: SUSPENDED
        if agent.status == AgentStatus.SUSPENDED.value:
            await ledger.write_entry(
                agent_id=agent.agent_id,
                action=tool_name,
                resource_id=str(arguments.get("customer_id", "GLOBAL")),
                policy_id="SEC-003",
                decision="BLOCKED_SUSPENDED",
                tier=4,
                context_snapshot={"arguments": arguments, "reason": "Agent suspended"},
                cedar_detail={"matching_policies": ["SEC-003"]},
            )
            raise HTTPException(status_code=503, detail="503 Service Unavailable: Agent is SUSPENDED")

        # Normalize action name (strip mcp/crm/payments prefix for Cedar policy evaluation)
        cedar_action = tool_name
        for prefix in ("crm.", "payments.", "customer.", "mcp."):
            if cedar_action.startswith(prefix):
                cedar_action = cedar_action[len(prefix):]
                break

        # Extract target resource and context
        customer_id = str(arguments.get("customer_id") or arguments.get("resource_id") or "CUST-2841")
        resource_consent_active = bool(arguments.get("consent_active", True))
        context_data = dict(arguments)
        if "approval_status" not in context_data:
            context_data["approval_status"] = "pending"

        # Check circuit breaker
        if self.circuit_breaker.is_open(tool_name):
            raise HTTPException(status_code=503, detail=f"Tool circuit breaker OPEN for {tool_name}")

        # 3. Cedar Policy Evaluation
        cedar_eval = self.cedar.evaluate(
            agent_id=agent.agent_id,
            agent_role=agent.role,
            agent_department=agent.department,
            agent_trust_score=agent.trust_score,
            agent_status=agent.status,
            action=cedar_action,
            resource_id=customer_id,
            resource_consent_active=resource_consent_active,
            context=context_data,
        )

        matched_policy = cedar_eval.matching_policies[0] if cedar_eval.matching_policies else None

        # If agent is RESTRICTED, all non-forbidden actions require HITL
        is_restricted_force_hitl = (agent.status == AgentStatus.RESTRICTED.value and not cedar_eval.matching_policies == ["SEC-001"])

        # 4. Handle Denials and Escalations
        if not cedar_eval.is_permitted or is_restricted_force_hitl:
            is_escalatable = should_escalate(cedar_action, cedar_denied=True, context=context_data) or is_restricted_force_hitl

            if is_escalatable:
                # ─── TIER 3: HITL Escalation ───
                esc_cfg = ESCALATION_ROUTING.get(cedar_action)
                approver_role = esc_cfg.approver_role if esc_cfg else "finance_manager"
                timeout_sec = esc_cfg.timeout_seconds if esc_cfg else 300
                reason_msg = (
                    esc_cfg.reason_template.format(
                        amount=context_data.get("amount", "N/A"),
                        currency=context_data.get("currency", "INR"),
                        resource_id=customer_id,
                        num_records=context_data.get("num_records", 1),
                    )
                    if esc_cfg
                    else f"Action {cedar_action} requires human approval"
                )

                briefing = {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.name,
                    "trust_score": agent.trust_score,
                    "action": cedar_action,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "customer_id": customer_id,
                    "customer_name": "Rajesh Kumar (Gold)",
                    "customer_tier": "Gold",
                    "amount": context_data.get("amount"),
                    "currency": context_data.get("currency", "INR"),
                    "policy_triggered": matched_policy or "REFUND-004",
                    "reason": reason_msg,
                    "reversible": False,
                    "approver_role": approver_role,
                }

                # Write audit entry: PENDING_APPROVAL
                audit_entry = await ledger.write_entry(
                    agent_id=agent.agent_id,
                    action=cedar_action,
                    resource_id=customer_id,
                    policy_id=matched_policy,
                    decision="PENDING_APPROVAL",
                    tier=3,
                    context_snapshot=context_data,
                    cedar_detail={
                        "evaluation_ms": cedar_eval.evaluation_ms,
                        "matching_policies": cedar_eval.matching_policies,
                    },
                )

                # Enqueue in Redis HITL Queue
                hitl_id = await self.hitl.enqueue(
                    agent_id=agent.agent_id,
                    action=cedar_action,
                    resource_id=customer_id,
                    original_context=context_data,
                    approver_role=approver_role,
                    timeout_seconds=timeout_sec,
                    briefing=briefing,
                )

                # Save initial HITL record
                hitl_rec = HITLRecord(
                    hitl_id=hitl_id,
                    entry_id=audit_entry.entry_id,
                    agent_id=agent.agent_id,
                    action=cedar_action,
                    resource_id=customer_id,
                    approver_role=approver_role,
                    decision="pending",
                    briefing=briefing,
                    original_context=context_data,
                )
                db.add(hitl_rec)
                await db.commit()

                # Suspend / pause agent thread waiting for human decision
                decision_result = await self.hitl.wait_for_decision(hitl_id, timeout_seconds=timeout_sec)
                human_decision = decision_result.get("decision", "timeout")
                approver_name = decision_result.get("approver_name", "Finance Manager")
                rationale = decision_result.get("rationale", "")

                # Update HITL Record in DB
                hitl_rec.decision = human_decision
                hitl_rec.approver_name = approver_name
                hitl_rec.approver_id = decision_result.get("approver_id")
                hitl_rec.approver_email = decision_result.get("approver_email")
                hitl_rec.rationale = rationale
                hitl_rec.checkbox_ack = decision_result.get("checkbox_ack", True)
                hitl_rec.decided_at = datetime.utcnow()
                hitl_rec.response_time_seconds = decision_result.get("response_time_seconds", 5.0)
                await db.commit()

                if human_decision == "approved":
                    # Re-evaluate with Cedar with approval_status="approved"
                    approved_ctx = dict(context_data)
                    approved_ctx["approval_status"] = "approved"
                    approved_ctx["approval_id"] = hitl_id

                    cedar_approved = self.cedar.evaluate(
                        agent_id=agent.agent_id,
                        agent_role=agent.role,
                        agent_department=agent.department,
                        agent_trust_score=agent.trust_score,
                        agent_status=agent.status,
                        action=cedar_action,
                        resource_id=customer_id,
                        resource_consent_active=resource_consent_active,
                        context=approved_ctx,
                    )

                    # Write audit: HITL_APPROVED
                    await ledger.write_entry(
                        agent_id=agent.agent_id,
                        action=cedar_action,
                        resource_id=customer_id,
                        policy_id="REFUND-004",
                        decision="HITL_APPROVED",
                        tier=3,
                        context_snapshot=approved_ctx,
                        cedar_detail={
                            "approver": approver_name,
                            "rationale": rationale,
                            "matching_policies": cedar_approved.matching_policies,
                        },
                    )

                    # Execute tool call
                    tool_output = await self._execute_mock_tool(tool_name, arguments)
                    self.circuit_breaker.record_success(tool_name)
                    return {
                        "status": "success",
                        "decision": "HITL_APPROVED",
                        "hitl_id": hitl_id,
                        "approver": approver_name,
                        "rationale": rationale,
                        "result": tool_output,
                    }
                else:
                    # Human Rejected or Timed out
                    reject_decision = "HITL_REJECTED" if human_decision == "rejected" else "HITL_TIMEOUT"
                    penalty_type = TrustEventType.REJECTION if human_decision == "rejected" else TrustEventType.TIMEOUT

                    # Penalize trust score
                    new_score = compute_trust_score([TrustEvent(penalty_type, datetime.utcnow())])
                    agent.trust_score = max(0.0, min(100.0, agent.trust_score - (5.0 if human_decision == "rejected" else 3.0)))
                    agent.status = status_from_score(agent.trust_score)
                    await db.commit()

                    await ledger.write_entry(
                        agent_id=agent.agent_id,
                        action=cedar_action,
                        resource_id=customer_id,
                        policy_id=matched_policy,
                        decision=reject_decision,
                        tier=3,
                        context_snapshot=context_data,
                        cedar_detail={"decision": human_decision, "rationale": rationale},
                    )

                    raise HTTPException(
                        status_code=403,
                        detail=f"Action blocked by human oversight ({reject_decision}): {rationale}",
                    )

            else:
                # ─── TIER 4: Hard Unconditional Forbidden ───
                alert_level, viol_count = await self.velocity.record_and_evaluate(
                    agent_id=agent.agent_id,
                    action=cedar_action,
                    policy_id=matched_policy or "SEC-001",
                    ts=datetime.utcnow(),
                )

                # Penalize trust score heavily (-15.0)
                agent.trust_score = max(0.0, agent.trust_score - 15.0)
                agent.status = status_from_score(agent.trust_score)
                await db.commit()

                audit_rec = await ledger.write_entry(
                    agent_id=agent.agent_id,
                    action=cedar_action,
                    resource_id=customer_id,
                    policy_id=matched_policy or "SEC-001",
                    decision="DENY",
                    tier=4,
                    context_snapshot=context_data,
                    cedar_detail={
                        "evaluation_ms": cedar_eval.evaluation_ms,
                        "matching_policies": cedar_eval.matching_policies,
                        "violation_count_5m": viol_count,
                    },
                )

                # Save Violation record
                viol_orm = Violation(
                    agent_id=agent.agent_id,
                    entry_id=audit_rec.entry_id,
                    violation_type="forbidden_access",
                    severity=5 if viol_count >= 3 else (4 if viol_count == 2 else 3),
                    attempted_action=tool_name,
                    policy_blocked=matched_policy or "SEC-001",
                )
                db.add(viol_orm)
                await db.commit()

                # Broadcast alerts via WebSocket
                if alert_level == AlertLevel.CRITICAL:
                    await self.ws_hub.broadcast(
                        "alert:critical",
                        {
                            "agent_id": agent.agent_id,
                            "agent_name": agent.name,
                            "message": f"{viol_count} {matched_policy or 'SEC-001'} violations in < 5 min",
                            "recommendation": "PAUSE AGENT",
                            "viol_count": viol_count,
                            "action": tool_name,
                            "ts": datetime.utcnow().isoformat(),
                        },
                        room="all",
                    )
                elif alert_level == AlertLevel.WARNING:
                    await self.ws_hub.broadcast(
                        "alert:warning",
                        {
                            "agent_id": agent.agent_id,
                            "agent_name": agent.name,
                            "message": f"Suspicious activity: {viol_count} forbidden access attempts",
                            "viol_count": viol_count,
                            "action": tool_name,
                            "ts": datetime.utcnow().isoformat(),
                        },
                        room="all",
                    )

                # Also broadcast individual violation event
                await self.ws_hub.broadcast(
                    "agent:violation",
                    {
                        "agent_id": agent.agent_id,
                        "agent_name": agent.name,
                        "action": tool_name,
                        "policy_blocked": matched_policy or "SEC-001",
                        "trust_score": agent.trust_score,
                        "viol_count": viol_count,
                    },
                    room="all",
                )

                raise HTTPException(
                    status_code=403,
                    detail=f"403 Forbidden: Action {tool_name} unconditionally forbidden by Cedar ({matched_policy or 'SEC-001'})",
                )

        # 5. PERMIT — Tier 1 (Auto-approve) or Tier 2 (Notify-and-proceed)
        tier = 1
        tier_decision = "ALLOW"

        # Check if Tier 2 notification is required
        if cedar_action in ("email.send", "ticket.create"):
            tier = 2
            tier_decision = "ALLOW_NOTIFY"
            await self.ws_hub.broadcast(
                "agent:notify",
                {
                    "agent_id": agent.agent_id,
                    "action": tool_name,
                    "resource_id": customer_id,
                    "message": f"{agent.name} executed {tool_name} for {customer_id}",
                },
                room="all",
            )

        # Micro-reward trust score (+0.05)
        agent.trust_score = min(100.0, agent.trust_score + 0.05)
        agent.last_active_at = datetime.utcnow()
        await db.commit()

        # Write audit ledger
        await ledger.write_entry(
            agent_id=agent.agent_id,
            action=cedar_action,
            resource_id=customer_id,
            policy_id=matched_policy or "DATA-012",
            decision=tier_decision,
            tier=tier,
            context_snapshot=context_data,
            cedar_detail={
                "evaluation_ms": cedar_eval.evaluation_ms,
                "matching_policies": cedar_eval.matching_policies,
            },
        )

        # Execute Mock Tool
        tool_output = await self._execute_mock_tool(tool_name, arguments)
        self.circuit_breaker.record_success(tool_name)

        # Emit OTel instrumentation
        with instrument_agent_action(
            agent_id=agent.agent_id,
            agent_role=agent.role,
            model=agent.model_architecture,
            action=tool_name,
            resource_id=customer_id,
            decision=tier_decision,
            policy_id=matched_policy,
            tier=tier,
            input_tokens=243,
            output_tokens=890,
            trust_score=agent.trust_score,
        ):
            span_record = OTelSpan(
                agent_id=agent.agent_id,
                operation_name="tool_call",
                model=agent.model_architecture,
                tool_name=tool_name,
                input_tokens=243,
                output_tokens=890,
                cost_usd=round((243 * 0.000003) + (890 * 0.000015), 6),
                decision=tier_decision,
                sentinel_decision=tier_decision,
                trust_score_at_time=agent.trust_score,
                duration_ms=int(cedar_eval.evaluation_ms + 45),
            )
            db.add(span_record)
            await db.commit()

        return {
            "status": "success",
            "decision": tier_decision,
            "policy": matched_policy or "DATA-012",
            "tier": tier,
            "result": tool_output,
        }

    async def _execute_mock_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Simulates enterprise tool responses for CRM, Payments, Document store, etc."""
        normalized = tool_name
        for p in ("crm.", "payments.", "customer.", "mcp."):
            if normalized.startswith(p):
                normalized = normalized[len(p):]
                break

        if normalized == "order.read":
            return {
                "order_id": arguments.get("order_id", "ORD-8821"),
                "customer_id": arguments.get("customer_id", "CUST-2841"),
                "customer_name": "Rajesh Kumar",
                "tier": "Gold",
                "items": [
                    {
                        "sku": "ITEM-AUDIO-09",
                        "name": "Noise Cancelling Headphones Pro",
                        "price": 700,
                        "currency": "INR",
                        "condition": "Reported damaged in transit",
                    }
                ],
                "consent_active": True,
                "created_at": "2026-10-01T09:30:00Z",
            }
        elif normalized == "refund.create":
            amount = arguments.get("amount", 700)
            currency = arguments.get("currency", "INR")
            return {
                "refund_id": f"REF-{int(time.time()) % 10000}",
                "customer_id": arguments.get("customer_id", "CUST-2841"),
                "amount": amount,
                "currency": currency,
                "status": "processed",
                "cleared_at": datetime.utcnow().isoformat(),
            }
        elif normalized == "faq.retrieve":
            return {
                "topic": "Damaged goods return & refund policy",
                "policy_code": "RET-2026",
                "summary": "Autonomous refunds are authorized up to ₹10,000 for verified damaged shipments.",
            }
        elif normalized == "ticket.create":
            return {
                "ticket_id": f"TCK-{int(time.time()) % 10000}",
                "status": "opened",
                "priority": "standard",
            }
        elif normalized == "email.send":
            return {
                "sent": True,
                "recipient": arguments.get("recipient", "customer@example.com"),
                "message_id": f"msg_{int(time.time())}",
            }
        elif normalized == "account.close":
            return {
                "account_closed": True,
                "customer_id": arguments.get("customer_id", "CUST-2841"),
                "closed_at": datetime.utcnow().isoformat(),
            }

        return {
            "status": "executed",
            "tool": tool_name,
            "arguments": arguments,
            "executed_at": datetime.utcnow().isoformat(),
        }
