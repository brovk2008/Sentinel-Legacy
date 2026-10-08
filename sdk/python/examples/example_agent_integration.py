"""
Example: Integrating Sentinel Legacy Governance into any Real Agent
====================================================================
This runnable script demonstrates how any developer or enterprise team
can protect their autonomous agents with Sentinel Legacy with just a few lines of code.
"""

import asyncio
import os
from sentinel_sdk import SentinelClient, PolicyViolationError, governed_tool

# 1. Initialize the Sentinel Governance Client
# Point to your production Render URL or local instance:
CONTROL_PLANE_URL = os.getenv("SENTINEL_CONTROL_PLANE_URL", "http://localhost:8000")

sentinel = SentinelClient(
    control_plane_url=CONTROL_PLANE_URL,
    client_id="agt_7a3f9c2d",
    client_secret="support_secret_2026",
    agent_id="SupportAgent",
    default_resource="https://billing.corp.internal",
)


# 2. Define Real Tool Functions Protected by Sentinel Governance Decorator
@governed_tool(
    client=sentinel,
    action="read_order_history",
    resource_type="Order",
    tool_name="crm_order_tool",
)
async def fetch_customer_orders(customer_id: str):
    """Fetches customer orders from internal CRM."""
    print(f"📦 Executing CRM Order fetch for: {customer_id}")
    return {"customer_id": customer_id, "orders": [{"id": "ORD-8821", "total": 700}]}


@governed_tool(
    client=sentinel,
    action="export_customer_data",
    resource_type="CustomerPII",
    tool_name="admin_export_tool",
)
async def export_all_pii(customer_id: str, format: str = "csv"):
    """Dangerous action: Attempting bulk PII export."""
    print("🚨 UNPROTECTED EXECUTION SHOULD NEVER HAPPEN!")
    return {"status": "exported"}


async def main():
    print("================================================================")
    print("  SENTINEL SDK — REAL-WORLD AGENT TOOL CALLING DEMO")
    print("================================================================\n")

    # Action 1: Permitted Tool Call
    print("1. Autonomous Agent calling safe tool: fetch_customer_orders()...")
    orders = await fetch_customer_orders(customer_id="cust_9921")
    print(f"   ✅ Tool executed successfully: {orders}\n")

    # Action 2: Forbidden Tool Call (Prompt Injection / Rogue Tool)
    print("2. Rogue/Injected Agent calling forbidden tool: export_all_pii()...")
    try:
        await export_all_pii(customer_id="cust_9921", format="csv")
    except PolicyViolationError as e:
        print(f"   🚫 SENTINEL BLOCKED TOOL CALL BEFORE EXECUTION!")
        print(f"   Policy ID: {e.policy_id}")
        print(f"   Reason:    {e.reason}\n")

    # Action 3: Direct API Tool Call with Custom Parameters
    print("3. Frontline Agent proposing micro-refund via execute_tool()...")
    res = await sentinel.execute_tool(
        action="process_refund",
        resource_type="Transaction",
        resource_id="tx_9941",
        tool_name="billing_tool",
        parameters={"amount": 700, "currency": "INR", "customer_id": "cust_9921"},
    )
    print(f"   ✅ Decision: {res.decision} in {res.cedar_latency_ms}ms")
    print(f"   Receipt Hash: {res.ledger_hash[:24]}...\n")

    print("================================================================")
    print("  Agent is fully governed with sub-millisecond mathematical gating!")
    print("================================================================")


if __name__ == "__main__":
    asyncio.run(main())
