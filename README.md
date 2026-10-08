# Sentinel Legacy v2.0
### Enterprise Governance Infrastructure & Control Plane for Agentic AI

<div align="center">

![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)
![Policy Engine: Cedar](https://img.shields.io/badge/Policy%20Engine-Cedar%20(Rust)-orange.svg?style=for-the-badge)
![Auth: RFC 8707](https://img.shields.io/badge/Auth-RFC%208707%20OAuth%202.1-green.svg?style=for-the-badge)
![Compliance](https://img.shields.io/badge/Compliance-DPDPA%202023%20%7C%20EU%20AI%20Act-purple.svg?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-23%2F23%20Passing-emerald.svg?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Protocol-MCP%202025--11--25-cyan.svg?style=for-the-badge)

<p align="center">
  <b>Sub-millisecond formal Cedar gating, audience-bound M2M tokens, fail-closed human oversight, and monotonic SHA-256 hash chains for autonomous AI agents.</b>
</p>

</div>

---

## Table of Contents
- [Executive Overview](#executive-overview)
- [The Governance Problem](#the-governance-problem)
- [System Architecture](#system-architecture)
- [Core Subsystems](#core-subsystems)
  - [1. Formal Cedar Policy Engine](#1-formal-cedar-policy-engine-rust-native)
  - [2. RFC 8707 Audience-Bound OAuth 2.1 M2M Tokens](#2-rfc-8707-audience-bound-oauth-21-m2m-tokens)
  - [3. Human-in-the-Loop (HITL) Thread Suspension](#3-human-in-the-loop-hitl-thread-suspension)
  - [4. Monotonic SHA-256 Cryptographic Audit Ledger](#4-monotonic-sha-256-cryptographic-audit-ledger)
  - [5. Sub-Second Kill Switch Cascade](#5-sub-second-kill-switch-cascade)
  - [6. Mathematical Trust Scoring & Anomaly Velocity](#6-mathematical-trust-scoring--anomaly-velocity)
  - [7. DPDPA 2023 & EU AI Act Compliance](#7-dpdpa-2023--eu-ai-act-compliance)
  - [8. OpenTelemetry GenAI Semantic Conventions](#8-opentelemetry-genai-semantic-conventions)
- [Control Plane UI Walkthrough](#control-plane-ui-walkthrough)
- [Quick Start Guide](#quick-start-guide)
  - [Option A: Docker Compose (Full Stack)](#option-a-docker-compose-full-stack)
  - [Option B: Bare-Metal Local Development](#option-b-bare-metal-local-development)
- [Running the Automated 3-Phase Simulation](#running-the-automated-3-phase-simulation)
- [Running Automated Tests](#running-automated-tests)
- [API Reference & curl Examples](#api-reference--curl-examples)
- [Project Directory Structure](#project-directory-structure)
- [License](#license)

---

## Executive Overview

**Sentinel Legacy v2.0** solves the critical enterprise safety dilemma: **How do organizations deploy autonomous, tool-calling AI agents into production environments without risking data exfiltration, runaway financial liability, or non-compliance with global AI regulations?**

Built on the **Model Context Protocol (MCP)** specification (2025-11-25 update) and formal mathematical policy reasoning, Sentinel Legacy interposes an inline reverse proxy control plane between foundation models (`gpt-4o-mini`, `claude-3-5-sonnet`, `gemini-1.5-pro`) and enterprise tools.

Every tool call is cryptographically authenticated, formally evaluated against SMT-verified Cedar policies in **< 1ms**, routed to humans when thresholds exceed safety boundaries, recorded to an immutable SHA-256 hash chain, and subject to instantaneous sub-second revocation.

---

## The Governance Problem

| Traditional Agent Deployment | Sentinel Legacy v2.0 Control Plane |
| :--- | :--- |
| **Broad Bearer Tokens**: Static API keys with full database access. | **RFC 8707 Audience-Bound JWTs**: Cryptographically locked to specific MCP servers. |
| **Probabilistic Guardrails**: LLM system prompts that can be jailbroken via prompt injection. | **Formal Cedar Metatheory**: SMT-verified Rust evaluation with strict **forbid-wins**. |
| **Unmonitored Tool Execution**: Direct irreversible database mutations and money movements. | **Fail-Closed HITL**: Thread suspended for 300s with 5-question contextual briefings. |
| **Mutable Log Files**: Application logs that can be tampered with or truncated. | **Monotonic SHA-256 Hash Chains**: Parent-linked blocks ($H_n = \text{SHA-256}(H_{n-1} \parallel \dots)$). |
| **Manual Incident Response**: Taking hours to rotate credentials during an active exploit. | **Sub-Second Kill Switch Cascade**: Revokes tokens, drops queues, and halts fleet in **< 50ms**. |

---

## System Architecture

```mermaid
flowchart TD
    subgraph AgentFleet["Autonomous Agent Fleet (Model Context Protocol Clients)"]
        A1["SupportAgent<br/>(gpt-4o-mini)"]
        A2["SalesAgent<br/>(claude-3-5-sonnet)"]
        A3["FinanceAgent<br/>(gemini-1.5-pro)"]
    end

    subgraph ControlPlane["Sentinel Legacy v2.0 Governance Control Plane"]
        AuthGate["OAuth 2.1 RFC 8707 Gate<br/>• Audience Binding<br/>• SHA-256 JTI Tracking<br/>• Sub-Second Revocation Check"]
        CedarEngine["Cedar Policy Engine<br/>• Native Rust Runtime<br/>• SMT/Lean 4 Metatheory<br/>• Strict Forbid-Wins (&lt;1ms)"]
        HITLQueue["HITL Oversight Engine<br/>• Redis Thread Suspension<br/>• 5-Question Context Briefing<br/>• Fail-Closed 300s Timeout"]
        AnomalyTracker["Anomaly Velocity Tracker<br/>• 60s Sliding Window<br/>• Info &gt; Warning &gt; Critical<br/>• Automated Isolation"]
        KillSwitch["Emergency Kill Switch<br/>• O(1) Redis Blacklist<br/>• Token Revocation Cascade<br/>• HITL Queue Purge (&lt;50ms)"]
        AuditLedger["Monotonic SHA-256 Ledger<br/>• RFC 6962 CT Linked Chain<br/>• Merkle Consistency Proofs<br/>• Tamper Detection"]
        WSHub["WebSocket Real-Time Hub<br/>• Event Replay Buffers<br/>• Multi-Room Broadcast"]
    end

    subgraph DownstreamTools["Enterprise Resource Servers & Tools"]
        CRM["Customer Database & CRM"]
        Billing["Billing & Treasury Gateway"]
        Orders["Order Fulfillment Service"]
    end

    subgraph Operations["Governance Operations Cockpit (React 18 + Vite)"]
        UI_Dash["Risk & Control Centre"]
        UI_Passport["AI Passport Dossier"]
        UI_HITL["HITL Approval Queue"]
        UI_Audit["Forensic Audit Ledger"]
        UI_Comp["DPDPA / EU AI Act Panel"]
    end

    AgentFleet -->|1. POST /api/v1/proxy/mcp| AuthGate
    AuthGate -->|2. Validated Context| CedarEngine
    CedarEngine -->|3a. PERMIT| AuditLedger
    CedarEngine -->|3b. FORBID| AnomalyTracker
    AnomalyTracker -->|Violation Penalty| AuditLedger
    CedarEngine -->|3c. ESCALATE| HITLQueue

    HITLQueue -->|4. Push Notification| WSHub
    WSHub -->|5. Real-Time Stream| UI_HITL
    UI_HITL -->|6. Approve / Reject / Modify| HITLQueue
    HITLQueue -->|7. Resume Suspended Thread| AuditLedger

    AuditLedger -->|8. Signed Downstream Proxy| DownstreamTools
    DownstreamTools -->|9. Execution Result| AuditLedger
    AuditLedger -->|10. Final Response Payload| AgentFleet

    KillSwitch -->|Instant Invalidation| AuthGate
    AuditLedger -->|Audit Stream| WSHub
    WSHub -->|Live Updates| UI_Dash
```

---

## Core Subsystems

### 1. Formal Cedar Policy Engine (Rust Native)
- **Engine Implementation**: [`cedar_engine.py`](backend/sentinel/policy/cedar_engine.py) wrapping native `cedar-python 0.1.4`.
- **Formal Guarantees**: Cedar's mathematical core is formally verified in the Lean 4 theorem prover.
- **Strict Forbid-Wins**: If any `forbid` policy matches an entity, action, or context, the decision is immediately forbidden, regardless of any permits.
- **Sub-Millisecond Evaluation**: Policies evaluate in under 1 millisecond.
- **Formal Policies**: Defined in [`policies.cedar`](backend/sentinel/policy/policies.cedar):
  - `DATA-012`: Strictly forbids unauthorized extraction or export of bulk customer PII.
  - `REFUND-001`: Permits refunds under ₹10,000; escalates refunds above ₹10,000 to human supervisors.
  - `REFUND-004`: Forbids processing refunds for blocked or flagged accounts.
  - `ACCOUNT-007`: Mandates human supervisor oversight before account closure.
  - `SEC-001` to `SEC-004`: Enforces zero-trust isolation for credentials, telemetry, and database queries.

### 2. RFC 8707 Audience-Bound OAuth 2.1 M2M Tokens
- **Implementation**: [`token_manager.py`](backend/sentinel/auth/token_manager.py).
- **Audience Binding**: Access tokens issued via `POST /api/v1/auth/token` explicitly bind the token to the requested target resource server via RFC 8707 `resource` parameter.
- **Confused Deputy Prevention**: An agent holding a token for `https://billing.corp.internal` cannot replay it against `https://crm.corp.internal`.
- **Instant Revocation**: Tokens contain a cryptographic `jti` (JWT ID). Blacklisted JTIs and revoked agent IDs are cached in Redis with $O(1)$ lookup complexity.

### 3. Human-in-the-Loop (HITL) Thread Suspension
- **Implementation**: [`queue.py`](backend/sentinel/hitl/queue.py) and [`hitl.py`](backend/sentinel/api/hitl.py).
- **Thread Suspension**: When Cedar or the escalation router flags an action (e.g. refund of ₹42,500), the calling agent HTTP request is suspended asynchronously.
- **Fail-Closed 300s Timeout**: If a human does not review and sign off on the request within 300 seconds, the thread automatically aborts with an authorization timeout error.
- **5-Question Contextual Briefing UI**:
  1. *What does the agent want to do?* (Action & Tool)
  2. *Why does the agent want to do it?* (Operational rationale)
  3. *Which customer/entity is affected?* (Data Principal details & VIP status)
  4. *Is this action reversible?* (Ledger credit vs. permanent deletion)
  5. *Which policy triggered this escalation?* (Cedar Policy ID & required approver role)
- **Operator Actions**: One-click approval, modification of parameters (e.g., adjusting refund amounts), or rejection with mandatory audit reasoning.

### 4. Monotonic SHA-256 Cryptographic Audit Ledger
- **Implementation**: [`writer.py`](backend/sentinel/ledger/writer.py) and [`audit.py`](backend/sentinel/api/audit.py).
- **RFC 6962 CT Model**: Every decision evaluated by the proxy is committed to a monotonic append-only ledger:
  $$\mathcal{H}_n = \text{SHA-256}(\mathcal{H}_{n-1} \parallel \text{Sequence} \parallel \text{Agent} \parallel \text{Action} \parallel \text{Resource} \parallel \text{Timestamp} \parallel \text{Context})$$
- **Tamper Evident**: If an attacker modifies even a single byte of historical context, all downstream hashes become invalid.
- **Chain Verification Endpoint**: `GET /api/v1/audit/verify` verifies every cryptographic link from genesis to tail in real time.

### 5. Sub-Second Kill Switch Cascade
- **Implementation**: [`admin.py`](backend/sentinel/api/admin.py) and [`KillSwitchModal.tsx`](frontend/src/components/control/KillSwitchModal.tsx).
- **Execution Speed**: Completes in **< 50 milliseconds**.
- **Cascade Sequence**:
  1. Blacklists all active bearer token JTIs in Redis.
  2. Transitions agent status to `SUSPENDED` / `DECOMMISSIONED`.
  3. Drops trust score to `0`.
  4. Purges all pending HITL queue items for the target.
  5. Writes an immutable audit entry to the hash chain.
  6. Broadcasts `kill_switch_activated` across the WebSocket cluster.

### 6. Mathematical Trust Scoring & Anomaly Velocity
- **Implementation**: [`scorer.py`](backend/sentinel/trust/scorer.py) and [`anomaly.py`](backend/sentinel/monitor/anomaly.py).
- **Continuous Trust Formula**:
  $$T(t) = \text{clamp}_{[0, 1000]}\left(T_{\text{base}} + \sum S - 150 \cdot V - 50 \cdot R - \lambda \Delta t\right)$$
  - Base Score: $800$
  - Successful Executions ($S$): $+0.5$ each
  - Policy Violations ($V$): $-150$ each
  - HITL Rejections ($R$): $-50$ each
  - Temporal Decay ($\lambda$): $-2.0$ points per 30-day inactivity window
- **Autonomous Status Tiers**:
  - $800 - 1000$: **ACTIVE** (Full autonomy)
  - $600 - 799$: **RESTRICTED** (Increased audit logging)
  - $400 - 599$: **SUSPENDED** (Mandatory escalation)
  - $0 - 399$: **DECOMMISSIONED** (Autonomy revoked)
- **Sliding-Window Velocity**: Detects burst violations in a 60-second window:
  - $\ge 2$ violations: Warning state
  - $\ge 3$ violations: Critical alert with automated Kill Switch recommendation

### 7. DPDPA 2023 & EU AI Act Compliance
- **Implementation**: [`compliance.py`](backend/sentinel/api/compliance.py) and [`CompliancePanel.tsx`](frontend/src/pages/CompliancePanel.tsx).
- **India DPDPA 2023 Section 11**: Automated query API providing Data Principals with complete disclosure of AI models, human interventions, and high-risk decisions.
- **EU AI Act Article 12 (Continuous Logging)**: Fully satisfied via parent-linked SHA-256 audit ledger.
- **EU AI Act Article 14 (Human Oversight)**: Fully satisfied via fail-closed HITL architecture.

### 8. OpenTelemetry GenAI Semantic Conventions
- **Implementation**: [`tracer.py`](backend/sentinel/observability/tracer.py) and [`metrics.py`](backend/sentinel/api/metrics.py).
- **Standard**: Aligned with OpenTelemetry GenAI v1.37+.
- **Metrics Tracked**:
  - `gen_ai.client.token.usage` (Prompt and completion token counts)
  - `gen_ai.cost` (Attributed dollar cost per agent and client ID)
  - `decision_latency_ms` (Sub-millisecond Cedar evaluation duration)

---

## Control Plane UI Walkthrough

The Sentinel Legacy console is built with **React 18, Vite 5, and Tailwind CSS**, featuring a clean, professional enterprise design system with refined dark-mode slate color grading, high-contrast typography, and authoritative operational cockpits.

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│  SENTINEL LEGACY v2.0    [● CEDAR ENGINE: ACTIVE]   [● LIVE FEED (WS)]    [KILL SWITCH]   │
├─────────────┬─────────────────────────────────────────────────────────────────────────────┤
│ NAVIGATION  │  RISK & CONTROL CENTRE (OPERATIONS COCKPIT)                                 │
│             ├─────────────────┬──────────────────┬──────────────────┬─────────────────────┤
│ [Dashboard] │  Active Fleet   │ Fleet Trust Index│ Pending HITL     │ Blocked Violations  │
│ [Passport]  │     3 / 3       │     855 / 1000   │    1 Awaiting    │     14 Blocked      │
│ [HITL Queue]├─────────────────┴──────────────────┴──────────────────┴─────────────────────┤
│ [Audit Log] │  [Simulate Normal]   [Simulate Cedar Block]   [Simulate Escalation]         │
│ [Compliance]├──────────────────────────────────────────────┬──────────────────────────────┤
│             │  VIOLATION VELOCITY (60s SLIDING WINDOW)     │  LIVE ALERT DISPATCH         │
│ AI WORKFORCE│  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   │  • High-Value Escalation     │
│             │  Threshold: 3/min [====== CRITICAL ======]   │  • Cedar DATA-012 Blocked    │
│ • Support   ├──────────────────────────────────────────────┴──────────────────────────────┤
│ • Sales     │  REGISTERED AGENT FLEET & OPENTELEMETRY ATTRIBUTION                         │
│ • Finance   │  SupportAgent  | gpt-4o-mini  | CX      | 840/1000 | ACTIVE  | [Revoke]     │
│             │  SalesAgent    | claude-3-5   | Sales   | 810/1000 | ACTIVE  | [Revoke]     │
│             │  FinanceAgent  | gemini-1.5   | Finance | 915/1000 | ACTIVE  | [Revoke]     │
└─────────────┴─────────────────────────────────────────────────────────────────────────────┘
```

1. **Risk & Control Centre (`/`)**: High-level telemetry, sliding violation charts, quick simulation triggers, and fleet status.
2. **AI Passport Dossier (`/passport`)**: Complete agent dossier with interactive radial Trust Score Gauge, breakdown tooltip, 3-column Permission Matrix (Permitted, Forbidden, HITL), and 30-day telemetry.
3. **HITL Oversight Queue (`/hitl`)**: 5-question contextual briefing cards, fail-closed countdown timers, one-click approvals, and parameter adjustment sliders.
4. **Forensic Audit Ledger (`/audit`)**: Monotonic SHA-256 block explorer, copy-to-clipboard hash inspect, and one-click cryptographic chain integrity verification.
5. **Regulatory Compliance (`/compliance`)**: EU AI Act Article 12/14 conformance tracker, statutory DPDPA Section 11 Data Principal search, and certified JSON export.

---

## Quick Start Guide

### Option A: Docker Compose (Full Stack)

To run the complete production stack (PostgreSQL, Redis, Sentinel Backend, and React Frontend):

```bash
# 1. Clone repository
git clone https://github.com/brovk2008/Sentinel-Legacy.git
cd Sentinel-Legacy

# 2. Start all services
docker compose up --build
```

Access points:
- **Governance Console UI**: [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **WebSocket Event Gateway**: `ws://localhost:8000/ws/dashboard`

---

### Option B: Bare-Metal Local Development

Sentinel Legacy v2.0 features zero-configuration fallback: if PostgreSQL and Redis are not present, it automatically uses **SQLite (`sentinel.db`)** and an **in-memory thread-safe mock Redis**.

#### 1. Backend Setup (Python 3.12)

```bash
# 1. Setup virtual environment
python -m venv .venv

# 2. Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Copy environment configuration
cp .env.example .env

# 5. Launch Sentinel Backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup (Node.js 18+)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Running the Automated 3-Phase Simulation

Run the complete narrated simulation script to observe all governance phases in action:

```bash
python demo/run_demo.py
```

### Simulation Walkthrough
1. **Phase 1: Normal Autonomous Execution**
   - Agent requests order history (`read_order_history`).
   - Cedar policy evaluates in `< 1ms` $\rightarrow$ **PERMIT**.
   - Entry appended to SHA-256 hash chain; trust score awarded $+0.5$.
2. **Phase 2: Strict Policy Block & Penalty**
   - Agent attempts bulk customer PII export (`export_customer_data`).
   - Cedar policy `DATA-012` enforces **FORBID**.
   - Violation logged; trust score penalized $-150$; warning alert dispatched.
3. **Phase 3: High-Value Escalation & Human Oversight**
   - Agent initiates refund for ₹42,500 (`process_refund`).
   - Cedar policy `REFUND-001` detects amount $> ₹10,000$ $\rightarrow$ **HITL Escalation**.
   - Request suspended in Redis; countdown timer begins (300s).
   - Human operator reviews 5-question briefing and approves with rationale.
   - Thread resumes; final tool executes; tamper-evident receipt minted.

---

## Running Automated Tests

Run the complete test suite across unit and integration targets:

```bash
pytest tests/ -v
```

### Verified Test Matrix (23/23 Passing)
- `tests/unit/test_cedar_engine.py`:
  - `test_permit_read_order_history`: Normal permit evaluation.
  - `test_forbid_export_customer_data`: Cedar `DATA-012` strict forbid.
  - `test_permit_small_refund`: Refunds $\le ₹10,000$ permitted autonomously.
  - `test_forbid_blocked_account`: Blocked accounts forbidden.
  - `test_unknown_action_defaults_forbid`: Lean 4 default-deny metatheory.
  - `test_cedar_evaluation_latency`: Sub-millisecond performance benchmark.
- `tests/unit/test_trust_scorer.py`:
  - `test_base_score_fresh_agent`: Baseline 800 trust score initialization.
  - `test_success_increments_trust`: Successful executions increment trust score.
  - `test_violation_penalty_reduces_score`: Single violation reduces score by $-150$.
  - `test_multiple_violations_restrict_agent`: Transitions to `RESTRICTED`.
  - `test_triple_violation_suspends_agent`: Transitions to `SUSPENDED`.
  - `test_temporal_decay`: Verifies $\lambda$ decay on inactive agents.
- `tests/unit/test_hash_chain.py`:
  - `test_hash_chain_creation_and_tamper_detection`: Monotonic link verification & tamper detection.
- `tests/unit/test_token_manager.py`:
  - `test_issue_and_validate_token`: RFC 8707 audience validation.
  - `test_audience_mismatch_rejected`: Replay attack protection.
  - `test_token_revocation`: $O(1)$ JTI revocation.
- `tests/unit/test_anomaly_detector.py`:
  - `test_violation_velocity_thresholds`: Sliding 60s window violation counter.
- `tests/integration/test_mcp_proxy.py`:
  - `test_full_mcp_proxy_flow`: End-to-end proxy decision lifecycle.
- `tests/integration/test_kill_switch.py`:
  - `test_kill_switch_cascade`: Sub-second token revocation and queue purge.

---

## API Reference & curl Examples

### 1. Issue RFC 8707 Audience-Bound M2M Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "agent_support_cx_9910",
    "client_secret": "sentinel-legacy-demo-secret",
    "resource": "https://mcp.billing.internal",
    "scope": "billing:read billing:write"
  }'
```

### 2. Invoke Tool via Sentinel MCP Proxy
```bash
curl -X POST http://localhost:8000/api/v1/proxy/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "agent_id": "SupportAgent",
    "action": "process_refund",
    "resource_type": "Transaction",
    "resource_id": "tx_ref_4401",
    "tool_name": "billing_toolset",
    "parameters": {
      "customer_id": "cust_9921",
      "amount": 42500,
      "currency": "INR"
    }
  }'
```

### 3. Verify Cryptographic Hash Chain Integrity
```bash
curl -X GET http://localhost:8000/api/v1/audit/verify
```
**Response:**
```json
{
  "is_valid": true,
  "total_entries": 42,
  "duration_ms": 6.8,
  "latest_hash": "a9f83...bc01",
  "checked_at": "2026-10-08T15:00:00Z"
}
```

### 4. Trigger Emergency Kill Switch
```bash
curl -X POST http://localhost:8000/api/v1/admin/kill-switch/SupportAgent \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Anomalous prompt injection detected in audit telemetry"
  }'
```

### 5. DPDPA 2023 Section 11 Data Principal Inquiry
```bash
curl -X GET http://localhost:8000/api/v1/compliance/dpdpa/cust_9921
```

---

## Project Directory Structure

```text
Sentinel-Legacy/
├── backend/
│   ├── main.py                     # FastAPI ASGI app & database seeding
│   ├── Dockerfile                  # Container definition for Python 3.12
│   ├── requirements.txt            # Pinned production dependencies
│   └── sentinel/
│       ├── core/                   # Config, database fallback, Redis
│       ├── models/                 # Agent, Audit, HITL SQLAlchemy models
│       ├── policy/                 # Cedar engine, schema, policies
│       ├── auth/                   # RFC 8707 token management & blacklist
│       ├── hitl/                   # Redis thread suspension & queue
│       ├── ledger/                 # Monotonic SHA-256 hash chain writer
│       ├── trust/                  # Mathematical trust scoring model
│       ├── monitor/                # 60s sliding window velocity tracker
│       ├── proxy/                  # MCP reverse proxy & circuit breaker
│       ├── ws/                     # Multi-room WebSocket real-time hub
│       └── api/                    # REST routers (auth, agents, proxy, hitl, audit, compliance)
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable UI component modules
│   │   │   ├── layout/             # TopNav & Sidebar
│   │   │   ├── passport/           # TrustScoreGauge, PermissionMatrix
│   │   │   ├── hitl/               # HITLBriefingCard, CountdownTimer
│   │   │   ├── control/            # AlertFeed, VelocityChart, KillSwitchModal
│   │   │   ├── audit/              # AuditTimeline, ChainVerifier, DPDPAQuery
│   │   │   └── observability/      # TokenCostChart (OTel GenAI)
│   │   ├── pages/                  # Dashboard, Passport, HITL, Audit, Compliance
│   │   ├── hooks/                  # useWebSocket connection manager
│   │   ├── types.ts                # TypeScript interfaces
│   │   ├── App.tsx                 # Master view router
│   │   └── main.tsx                # React DOM mount
│   ├── Dockerfile                  # Node.js dev/prod container
│   ├── package.json
│   └── vite.config.ts
├── agents/                         # Autonomous agents (Support, Sales, Finance)
├── demo/
│   └── run_demo.py                 # 3-Phase automated simulation script
├── tests/
│   ├── unit/                       # Cedar, Trust, Hash Chain, Token tests
│   └── integration/                # Proxy & Kill Switch integration tests
├── .env.example                    # Sample environment configuration
├── .gitignore                      # Python, Node, Database, and Secret exclusions
├── docker-compose.yml              # Local multi-service orchestration
├── arch.md                         # Sentinel Legacy Architectural Blueprint
└── README.md                       # Master Documentation
```

---

## License

Sentinel Legacy v2.0 is open-source software licensed under the **Apache License 2.0**.
