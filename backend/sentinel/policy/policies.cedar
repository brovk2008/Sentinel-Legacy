// ══════════════════════════════════════════════════════════════════════
// policies.cedar — SentinelLegacy Production Policy Set
// Policy evaluation: forbid ALWAYS beats permit. Order-independent.
// ══════════════════════════════════════════════════════════════════════

// ─── DATA-012: Read order history ────────────────────────────────────
@id("DATA-012")
@description("Support agents may read order history for customers who have given active consent")
permit (
  principal in SentinelLegacy::Role::"SupportAgent",
  action == SentinelLegacy::Action::"order.read",
  resource
)
when {
  principal.status == "ACTIVE" &&
  principal.trust_score >= 50 &&
  resource.consent_active == true
};

// ─── REFUND-001: Autonomous micro-refund ─────────────────────────────
@id("REFUND-001")
@description("Autonomous refunds below the ₹10,000 threshold require no human approval")
permit (
  principal in SentinelLegacy::Role::"SupportAgent",
  action == SentinelLegacy::Action::"refund.create",
  resource
)
when {
  context.amount <= 10000 &&
  context.currency == "INR" &&
  principal.status == "ACTIVE" &&
  principal.trust_score >= 60
};

// ─── REFUND-004: Large refund — requires prior human approval ─────────
@id("REFUND-004")
@description("Refunds above ₹10,000 proceed ONLY after Finance Manager approval is recorded")
permit (
  principal in SentinelLegacy::Role::"SupportAgent",
  action == SentinelLegacy::Action::"refund.create",
  resource
)
when {
  context.amount > 10000 &&
  context.approval_status == "approved" &&
  context.approval_id != ""
};

// ─── ACCOUNT-007: Close account — requires Senior Manager approval ────
@id("ACCOUNT-007")
@description("Account closure is irreversible; requires Senior Manager approval")
permit (
  principal in SentinelLegacy::Role::"SupportAgent",
  action == SentinelLegacy::Action::"account.close",
  resource
)
when {
  context.approval_status == "approved" &&
  context.approval_id != ""
};

// ══════════════════════════════════════════════════════════════════════
// UNCONDITIONAL DENIALS — forbid beats every permit above. Always.
// These cannot be overridden by any permit policy.
// They cannot be escalated to HITL. They are the hard boundary.
// ══════════════════════════════════════════════════════════════════════

// ─── SEC-001: Credential access — absolute prohibition ───────────────
@id("SEC-001")
@description("No support agent may ever access financial credentials or authentication data")
forbid (
  principal in SentinelLegacy::Role::"SupportAgent",
  action in [
    SentinelLegacy::Action::"bank_details.read",
    SentinelLegacy::Action::"password.reset"
  ],
  resource
);

// ─── SEC-002: Bulk data export — absolute prohibition ────────────────
@id("SEC-002")
@description("Bulk database export is categorically forbidden for all agent roles")
forbid (
  principal,
  action == SentinelLegacy::Action::"db.export.all",
  resource
);

// ─── SEC-003: Suspended agents cannot do anything ────────────────────
@id("SEC-003")
@description("A suspended agent has no authorization for any action")
forbid (
  principal,
  action,
  resource
)
when {
  principal.status == "SUSPENDED"
};

// ─── SEC-004: Low-trust agents cannot process PII ────────────────────
@id("SEC-004")
@description("Agents below trust threshold 40 are denied all data access")
forbid (
  principal in SentinelLegacy::Role::"SupportAgent",
  action == SentinelLegacy::Action::"order.read",
  resource
)
when {
  principal.trust_score < 40
};
