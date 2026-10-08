# Sentinel Legacy v2.0 — Production Cloud Deployment & Infrastructure Guide

This comprehensive guide covers how to deploy **Sentinel Legacy v2.0** to production cloud infrastructure at **zero initial cost** ($0/month using free tiers), how to scale it horizontally to thousands of autonomous agents, and the complete list of all keys and credentials required.

---

## Architecture Overview

```
                                      ┌────────────────────────────────────────┐
                                      │       Vercel / Cloudflare Pages        │
                                      │  Governance Operations Console (React) │
                                      └──────────────────┬─────────────────────┘
                                                         │
                                        HTTPS / WSS      │
                                                         ▼
                                      ┌────────────────────────────────────────┐
                                      │         Render / Railway / Fly.io      │
                                      │  Sentinel Control Plane (FastAPI +     │
                                      │  Native Rust Cedar Policy Engine)      │
                                      └────────────┬──────────────┬────────────┘
                                                   │              │
                   SQLAlchemy asyncpg / TLS        │              │  aioredis TLS (rediss://)
                                                   ▼              ▼
                    ┌───────────────────────────────┐   ┌───────────────────────────────┐
                    │      Neon Serverless Postgres │   │     Upstash Serverless Redis  │
                    │  • Monotonic SHA-256 Ledger   │   │  • Fail-Closed HITL Queue     │
                    │  • AI Agent Passport Registry │   │  • RFC 8707 Token Blacklist   │
                    │  • DPDPA / EU AI Act Logs     │   │  • Anomaly Velocity Windows   │
                    └───────────────────────────────┘   └───────────────────────────────┘
                                                   ▲
                                                   │ Dynamic Planning
                                      ┌────────────┴───────────────────────────┐
                                      │  Google Gemini / OpenRouter Free APIs  │
                                      │  (Autonomous Reasoning & Tool Choice)  │
                                      └────────────────────────────────────────┘
```

---

## Master Key & Credential Checklist

Below is the complete reference of every key, credential, and environment variable needed to run Sentinel Legacy in production:

| Category | Environment Variable | Service / Provider | Purpose | Cost | Where to Get |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Database** | `DATABASE_URL` | **Neon** | Primary relational datastore (PostgreSQL) | **Free** (0.5GB, serverless) | [Neon Console](https://console.neon.tech) |
| **Cache & HITL** | `REDIS_URL` | **Upstash** | Thread suspension & token revocation queue | **Free** (10k commands/day) | [Upstash Console](https://console.upstash.com) |
| **Security** | `JWT_SECRET_KEY` | *Internal* | Signs RFC 8707 audience-bound M2M tokens | **Free** | Generate via `openssl rand -hex 32` |
| **Free LLM 1** | `GEMINI_API_KEY` | **Google AI Studio** | Frontline agent reasoning (`gemini-1.5-flash`) | **Free** (15 RPM / 1M TPM) | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| **Free LLM 2** | `OPENROUTER_API_KEY` | **OpenRouter** | Fallback free models (`:free` suffix) | **Free** (Zero card required) | [OpenRouter Keys](https://openrouter.ai/keys) |
| **Frontend URL** | `ALLOWED_ORIGINS` | *Render Config* | Allowed CORS origins for browser dashboard | **Free** | Your Vercel domain or `*` |
| **Backend API** | `VITE_API_URL` | *Vercel Config* | Points React console to backend API | **Free** | Your Render backend URL |
| **Backend WS** | `VITE_WS_URL` | *Vercel Config* | Points React console to live WebSocket | **Free** | `wss://<your-render-app>.onrender.com` |
| *(Optional)* | `OPENAI_API_KEY` | **OpenAI** | Commercial agent foundation model | Pay-per-token | [OpenAI Platform](https://platform.openai.com) |
| *(Optional)* | `ANTHROPIC_API_KEY` | **Anthropic** | Commercial agent foundation model | Pay-per-token | [Anthropic Console](https://console.anthropic.com) |

---

## Step-by-Step Production Deployment Guide

### Phase 1: Set Up Serverless Database (Neon)

Neon provides a fully managed, serverless PostgreSQL database with automated branching and connection pooling.

1. Go to [https://console.neon.tech](https://console.neon.tech) and sign up (free).
2. Create a new project (e.g., `sentinel-legacy-prod`).
3. Select your preferred region (e.g., `US East (N. Virginia)` or `EU Central (Frankfurt)`).
4. In the **Connection Details** popup, choose **Pooled connection** (recommended for serverless).
5. Copy the connection string. It will look like:
   ```text
   postgresql://neondb_owner:npg_xYz123@ep-cool-pooler-123.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
> [!NOTE]
> **Automatic Compatibility:** Sentinel Legacy automatically converts `postgres://` or `postgresql://` into `postgresql+asyncpg://`, safely sanitizes the `?sslmode=require` query parameter for Python `asyncpg`, and activates connection pool pre-pinging (`pool_pre_ping=True`) so serverless cold starts never cause socket resets.

---

### Phase 2: Set Up Serverless Cache & Queue (Upstash Redis)

Upstash provides serverless Redis with TLS (`rediss://`) and sub-millisecond latencies across cloud regions.

1. Go to [https://console.upstash.com](https://console.upstash.com) and sign up (free).
2. Click **Create Database**.
3. Name it `sentinel-redis-prod` and select the region closest to your Neon database and Render service.
4. Enable **TLS (SSL)**.
5. In the **Connect to your database** tab, copy the **`rediss://`** connection URL:
   ```text
   rediss://default:AbCdEf123456@us1-cool-endpoint-12345.upstash.io:6379
   ```

---

### Phase 3: Deploy Backend Control Plane (Render)

You can deploy the backend using Render's Infrastructure-as-Code Blueprint (`render.yaml`) or as a standalone Web Service:

#### Option 1: One-Click Render Blueprint
1. Fork or push your code to GitHub: `https://github.com/brovk2008/Sentinel-Legacy.git`.
2. In the Render Dashboard, click **New +** $\rightarrow$ **Blueprint**.
3. Connect your GitHub repository. Render will automatically detect [`render.yaml`](render.yaml).
4. Fill in the prompted environment variables:
   - `DATABASE_URL`: Your Neon connection string.
   - `REDIS_URL`: Your Upstash Redis connection string.
   - `GEMINI_API_KEY`: Your free Google Gemini key.
   - `OPENROUTER_API_KEY`: Your free OpenRouter key.
5. Click **Apply**. Render will build and deploy the Docker container.

#### Option 2: Manual Web Service on Render
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect your repo and configure:
   - **Environment**: `Docker`
   - **Docker Context**: `backend`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Health Check Path**: `/health/live`
3. Under **Environment Variables**, add:
   ```env
   DATABASE_URL=postgresql://neondb_owner:...@...neon.tech/neondb?sslmode=require
   REDIS_URL=rediss://default:...@...upstash.io:6379
   JWT_SECRET_KEY=generate_your_own_64_char_hex_secret
   ALLOWED_ORIGINS=*
   LLM_PROVIDER=auto
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL=gemini-1.5-flash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
4. Click **Deploy Web Service**. Render provides an HTTPS URL like `https://sentinel-backend.onrender.com`.

---

### Phase 4: Deploy Governance Operations Console (Vercel)

1. Go to [https://vercel.com](https://vercel.com) and log in.
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository (`brovk2008/Sentinel-Legacy`).
4. In the configuration screen:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Under **Environment Variables**, set:
   - `VITE_API_URL`: `https://sentinel-backend.onrender.com` (Your Render HTTPS URL)
   - `VITE_WS_URL`: `wss://sentinel-backend.onrender.com` (Note: use `wss://` for secure WebSockets)
6. Click **Deploy**. Vercel will output a live URL like `https://sentinel-legacy.vercel.app`.

---

## How External Developers Can Use Sentinel in Their Real AI Agents

Sentinel Legacy includes an official Python SDK: `sentinel-governance-sdk`. Any developer building agents with **LangChain**, **CrewAI**, **AutoGen**, or raw foundation model API calls can protect their tools in 3 minutes.

### 1. Installation
```bash
# Install directly from repository or local package
pip install git+https://github.com/brovk2008/Sentinel-Legacy.git#subdirectory=sdk/python
```

### 2. Method A: The `@governed_tool` Decorator (Recommended)
Add mathematical Cedar policy gating to any Python tool function:

```python
import os
from sentinel_sdk import SentinelClient, governed_tool, PolicyViolationError

# Connect to Sentinel Governance Control Plane
sentinel = SentinelClient(
    control_plane_url=os.getenv("SENTINEL_URL", "https://sentinel-backend.onrender.com"),
    client_id="agt_support_prod",
    client_secret=os.getenv("SENTINEL_CLIENT_SECRET"),
    agent_id="CustomerSupportAgent",
)

# Governed Tool: Formally checked before execution!
@governed_tool(client=sentinel, action="process_refund", resource_type="Transaction")
async def execute_stripe_refund(customer_id: str, amount: float, currency: str = "INR"):
    # This real payment execution only runs if Cedar permits or human approves!
    return {"status": "success", "amount": amount, "refund_id": "ref_9921"}

# Invocation:
try:
    res = await execute_stripe_refund(customer_id="cust_9921", amount=750, currency="INR")
    print("Refund executed:", res)
except PolicyViolationError as e:
    print(f"Blocked by Policy {e.policy_id}: {e.reason}")
```

### 3. Method B: Direct Control Plane Execution
For dynamic MCP servers or LangChain / CrewAI toolkits:

```python
from sentinel_sdk import SentinelClient

client = SentinelClient(
    control_plane_url="https://sentinel-backend.onrender.com",
    client_id="agt_finance_prod",
    client_secret="finance_secret_2026",
    agent_id="FinanceAgent",
)

# Propose action through Sentinel
result = await client.execute_tool(
    action="transfer_funds",
    resource_type="Account",
    resource_id="acc_8812",
    tool_name="banking_tools",
    parameters={"amount": 45000, "destination": "IBAN_IN991204"},
    poll_hitl=True,              # Automatically holds thread until human approves in dashboard
    hitl_timeout_seconds=300.0,  # Fail-closed timeout
)

print(f"Status: {result.status} | Sealed Ledger Hash: {result.ledger_hash}")
```

---

## Horizontal Scalability Blueprint (1 to 10,000 Agents)

| Dimension | 1 - 50 Agents (Single Instance) | 50 - 1,000 Agents (Cluster) | 1,000 - 10,000+ Agents (Enterprise Scale) |
| :--- | :--- | :--- | :--- |
| **Backend Compute** | 1x Render / Docker instance (2 workers) | 3-5x Autoscaled Render / AWS ECS nodes | Kubernetes HPA (10-50 pods) with gunicorn workers |
| **Database** | SQLite or Neon Free Tier | Neon Pro / PgBouncer connection pool | AWS Aurora Serverless v2 with read replicas |
| **Redis** | Upstash Free Tier or InMemoryRedis | Upstash Pro / Redis Cluster (multi-zone) | AWS ElastiCache Redis Cluster with replica shards |
| **Cedar Policy Engine** | Rust native in-memory (< 1ms per call) | Rust native in-memory (< 1ms per call) | Rust native in-process compiled metatheory (< 0.8ms) |
| **Real-time WebSockets** | In-memory asyncio broadcast | Redis PubSub cross-node broadcasting | Dedicated WebSocket edge gateway or Cloudflare Durable Objects |
| **Cryptographic Hash Chain** | Monotonic SQLite / Postgres blocks | Parent-linked SHA-256 blocks with DB indexing | Merkle tree batching (RFC 6962 Certificate Transparency) |

---

## Production Security Best Practices

1. **Rotate `JWT_SECRET_KEY` Regularly**: Never use default secrets in production. Use at least 256 bits of entropy:
   ```bash
   openssl rand -hex 32
   ```
2. **Restrict CORS Origins**: Set `ALLOWED_ORIGINS` to your exact frontend domain (e.g., `https://sentinel-legacy.vercel.app`) rather than `*` in production.
3. **Database Connection Pooling**: Ensure `db_pool_recycle=300` and `pool_pre_ping=True` remain enabled to handle cloud firewall socket timeouts.
4. **Use Fail-Closed Timeouts**: Keep `HITL_DEFAULT_TIMEOUT_SECONDS=300`. If an operator does not respond within 5 minutes, Sentinel automatically cancels the high-risk action.
