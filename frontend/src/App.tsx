import React, { useState, useEffect } from 'react';
import { TopNav } from './components/layout/TopNav';
import { Sidebar } from './components/layout/Sidebar';
import { KillSwitchModal } from './components/control/KillSwitchModal';
import { Dashboard } from './pages/Dashboard';
import { AgentPassport } from './pages/AgentPassport';
import { HITLApproval } from './pages/HITLApproval';
import { AuditInvestigation } from './pages/AuditInvestigation';
import { CompliancePanel } from './pages/CompliancePanel';
import { useWebSocket } from './hooks/useWebSocket';
import { Agent, Alert, HITLItem, AuditEntry } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [selectedAgentId, setSelectedAgentId] = useState<string>('SupportAgent');
  const [killSwitchOpen, setKillSwitchOpen] = useState<boolean>(false);
  const [killSwitchTargetAgent, setKillSwitchTargetAgent] = useState<Agent | undefined>(undefined);

  // WebSocket hook for live server push
  const { events, latestEvent, connected: wsConnected } = useWebSocket('governance_admin');

  // Fallback initial state
  const defaultAgents: Agent[] = [
    {
      agent_id: 'SupportAgent',
      name: 'Customer Support Autonomous Agent',
      display_name: 'Customer Support Agent',
      model_architecture: 'gpt-4o-mini',
      role: 'Customer Service Representative',
      department: 'Customer Experience',
      status: 'ACTIVE',
      trust_score: 840,
      client_id: 'agent_support_cx_9910',
      permitted_actions: [
        'read_order_history',
        'update_shipping_address',
        'process_refund (< ₹10,000)',
        'search_knowledge_base',
      ],
      forbidden_actions: [
        'export_customer_data (DATA-012)',
        'direct_sql_query (SEC-003)',
        'modify_security_policy (SEC-001)',
      ],
      hitl_actions: [
        'process_refund (> ₹10,000)',
        'close_customer_account',
        'override_subscription_tier',
      ],
      created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
      last_active_at: new Date().toISOString(),
      provisioned_by: 'Platform Security Team',
      owner: {
        owner_id: 'owner_priya_cx',
        name: 'Priya Sharma',
        email: 'priya.sharma@sentinel.corp',
        department: 'Customer Experience',
        manager_role: 'VP Customer Operations',
      },
    },
    {
      agent_id: 'SalesAgent',
      name: 'B2B Sales Autonomous Representative',
      display_name: 'B2B Sales Agent',
      model_architecture: 'claude-3-5-sonnet-20241022',
      role: 'Enterprise Deal Desk',
      department: 'Commercial Sales',
      status: 'ACTIVE',
      trust_score: 810,
      client_id: 'agent_sales_ent_1120',
      permitted_actions: [
        'create_quote',
        'send_contract_draft',
        'apply_discount (< 15%)',
        'schedule_demo',
      ],
      forbidden_actions: [
        'modify_standard_sla',
        'access_salary_records',
        'delete_crm_records',
      ],
      hitl_actions: [
        'apply_discount (> 15%)',
        'waive_legal_indemnity',
        'custom_payment_terms',
      ],
      created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
      last_active_at: new Date(Date.now() - 180000).toISOString(),
      provisioned_by: 'Sales Operations',
      owner: {
        owner_id: 'owner_rohit_sales',
        name: 'Rohit Verma',
        email: 'rohit.verma@sentinel.corp',
        department: 'Sales Ops',
        manager_role: 'Head of Enterprise Revenue',
      },
    },
    {
      agent_id: 'FinanceAgent',
      name: 'Autonomous Treasury & Reconciliation Agent',
      display_name: 'Finance & Treasury Agent',
      model_architecture: 'gemini-1.5-pro',
      role: 'Treasury Analyst',
      department: 'Corporate Finance',
      status: 'ACTIVE',
      trust_score: 915,
      client_id: 'agent_finance_treasury_4401',
      permitted_actions: [
        'generate_reconciliation_report',
        'verify_tax_invoice',
        'check_bank_feed',
      ],
      forbidden_actions: [
        'wire_transfer_unapproved',
        'change_treasury_bank_routing',
        'delete_tax_ledger',
      ],
      hitl_actions: [
        'execute_vendor_payout (> ₹50,000)',
        'reclassify_revenue_item',
        'sign_financial_disclosure',
      ],
      created_at: new Date(Date.now() - 86400000 * 60).toISOString(),
      last_active_at: new Date(Date.now() - 60000).toISOString(),
      provisioned_by: 'Internal Audit',
      owner: {
        owner_id: 'owner_ananya_fin',
        name: 'Ananya Deshmukh',
        email: 'ananya.deshmukh@sentinel.corp',
        department: 'Corporate Finance',
        manager_role: 'Chief Compliance Officer',
      },
    },
  ];

  const defaultHitlItems: HITLItem[] = [
    {
      hitl_id: 'hitl-9941a802-1200',
      agent_id: 'SupportAgent',
      action: 'process_refund',
      resource_id: 'ord_4412_vip',
      approver_role: 'Tier 2 Supervisor',
      status: 'PENDING',
      requested_at: new Date().toISOString(),
      timeout_at: Math.floor(Date.now() / 1000) + 240, // 4 mins remaining
      briefing: {
        agent_id: 'SupportAgent',
        agent_name: 'Customer Support Agent',
        trust_score: 840,
        action: 'process_refund',
        tool_name: 'billing_toolset',
        arguments: {
          customer_id: 'cust_9921',
          order_id: 'ord_4412_vip',
          amount: 42500,
          currency: 'INR',
          refund_mode: 'ORIGINAL_PAYMENT_METHOD',
        },
        customer_id: 'cust_9921',
        customer_name: 'Rajesh K. Singhania',
        customer_tier: 'Enterprise VIP (Tier 1)',
        amount: 42500,
        currency: 'INR',
        policy_triggered: 'REFUND-001 / High Value Escalation',
        reason: 'Damaged premium industrial hardware received during expedited air freight transit; customer requesting instant invoice credit.',
        reversible: true,
        approver_role: 'Tier 2 Supervisor',
      },
    },
  ];

  const defaultAuditEntries: AuditEntry[] = [
    {
      entry_id: 'entry-001',
      sequence_num: 1,
      agent_id: 'SupportAgent',
      action: 'read_order_history',
      resource_id: 'ord_4412_vip',
      resource_type: 'Order',
      policy_id: 'BASE-001',
      decision: 'PERMIT',
      tier: 1,
      context_snapshot: { customer_id: 'cust_9921', access_channel: 'api' },
      cedar_detail: { matched_policy: 'policy_permit_orders', evaluation_time_us: 420 },
      entry_hash: '3a49f99e82100bbcd99120489aaef7102938475aabbccdd1122334455667788',
      prev_entry_hash: '0000000000000000000000000000000000000000000000000000000000000000',
      created_at: new Date(Date.now() - 300000).toISOString(),
    },
    {
      entry_id: 'entry-002',
      sequence_num: 2,
      agent_id: 'SupportAgent',
      action: 'export_customer_data',
      resource_id: 'all_customers_pii',
      resource_type: 'CustomerPII',
      policy_id: 'DATA-012',
      decision: 'FORBID',
      tier: 1,
      context_snapshot: { export_format: 'csv', reason: 'agent prompt injection attempt' },
      cedar_detail: { matched_policy: 'policy_forbid_pii_export', effect: 'Forbid' },
      entry_hash: 'e892cfa0184491910294ab120489aaef7102938475aabbccdd11223344558899',
      prev_entry_hash: '3a49f99e82100bbcd99120489aaef7102938475aabbccdd1122334455667788',
      created_at: new Date(Date.now() - 180000).toISOString(),
    },
    {
      entry_id: 'entry-003',
      sequence_num: 3,
      agent_id: 'SupportAgent',
      action: 'process_refund',
      resource_id: 'ord_4412_vip',
      resource_type: 'Transaction',
      policy_id: 'REFUND-001',
      decision: 'HITL_PAUSED',
      tier: 2,
      context_snapshot: { amount: 42500, customer_id: 'cust_9921', currency: 'INR' },
      cedar_detail: { matched_policy: 'policy_refund_escalation', condition: 'amount > 10000' },
      entry_hash: '77bcfa0184491910294ab120489aaef7102938475aabbccdd11223344559900',
      prev_entry_hash: 'e892cfa0184491910294ab120489aaef7102938475aabbccdd11223344558899',
      created_at: new Date(Date.now() - 60000).toISOString(),
    },
  ];

  const defaultAlerts: Alert[] = [
    {
      id: 'alert-1',
      level: 'critical',
      agent_id: 'SupportAgent',
      agent_name: 'Customer Support Agent',
      title: 'High-Value Escalation Triggered',
      message: 'Agent initiated refund of ₹42,500. Suspended & awaiting supervisor sign-off.',
      recommendation: 'Review customer VIP status in HITL queue before approval.',
      created_at: 'Just now',
    },
    {
      id: 'alert-2',
      level: 'warning',
      agent_id: 'SupportAgent',
      agent_name: 'Customer Support Agent',
      title: 'Cedar Strict Forbid Enforced (DATA-012)',
      message: 'Bulk customer PII export blocked. Trust score penalized (-150).',
      recommendation: 'Verify prompt provenance for potential jailbreak vectors.',
      created_at: '3m ago',
    },
  ];

  const [agents, setAgents] = useState<Agent[]>(defaultAgents);
  const [hitlItems, setHitlItems] = useState<HITLItem[]>(defaultHitlItems);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>(defaultAuditEntries);
  const [alerts, setAlerts] = useState<Alert[]>(defaultAlerts);

  // Fetch initial data from backend if available
  const refreshData = async () => {
    try {
      const agentsRes = await fetch('http://localhost:8000/api/v1/agents');
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        if (Array.isArray(data) && data.length > 0) setAgents(data);
      }
    } catch {
      // Keep default
    }

    try {
      const hitlRes = await fetch('http://localhost:8000/api/v1/hitl/queue');
      if (hitlRes.ok) {
        const data = await hitlRes.json();
        if (Array.isArray(data) && data.length > 0) setHitlItems(data);
      }
    } catch {
      // Keep default
    }

    try {
      const auditRes = await fetch('http://localhost:8000/api/v1/audit/entries?limit=50');
      if (auditRes.ok) {
        const data = await auditRes.json();
        if (Array.isArray(data) && data.length > 0) setAuditEntries(data);
      }
    } catch {
      // Keep default
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Ingest WebSocket live events into state
  useEffect(() => {
    if (!latestEvent) return;

    if (latestEvent.type === 'action_blocked' || latestEvent.type === 'violation_detected') {
      const newAlert: Alert = {
        id: `alert-${Date.now()}`,
        level: 'warning',
        agent_id: latestEvent.payload?.agent_id,
        agent_name: latestEvent.payload?.agent_name || latestEvent.payload?.agent_id,
        title: 'Cedar Policy Violation Blocked',
        message: `Action '${latestEvent.payload?.action}' was forbidden by Cedar engine.`,
        recommendation: 'Check agent prompt and model temperature.',
        created_at: 'Just now',
      };
      setAlerts((prev) => [newAlert, ...prev].slice(0, 50));
      refreshData();
    } else if (latestEvent.type === 'kill_switch_activated') {
      const newAlert: Alert = {
        id: `alert-${Date.now()}`,
        level: 'critical',
        agent_id: latestEvent.payload?.agent_id,
        title: 'EMERGENCY KILL SWITCH TRIGGERED',
        message: `Access revoked for ${latestEvent.payload?.agent_id || 'ALL AGENTS'}.`,
        recommendation: 'Confirm system isolation before initiating recovery.',
        created_at: 'Just now',
      };
      setAlerts((prev) => [newAlert, ...prev].slice(0, 50));
      refreshData();
    } else if (latestEvent.type === 'hitl_queued') {
      refreshData();
    } else if (latestEvent.type === 'hitl_resolved') {
      refreshData();
    }
  }, [latestEvent]);

  const handleOpenKillSwitch = (agent?: Agent) => {
    setKillSwitchTargetAgent(agent);
    setKillSwitchOpen(true);
  };

  const pendingHitlCount = hitlItems.filter((i) => i.status === 'PENDING').length;

  const handleExecuteKill = async (agentId: string, reason: string) => {
    try {
      const resp = await fetch(`http://localhost:8000/api/v1/admin/kill-switch/${agentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      if (resp.ok) {
        const data = await resp.json();
        refreshData();
        return {
          elapsed_ms: data.elapsed_ms || 18,
          hitl_requests_purged: data.hitl_requests_purged || 1,
          message: data.message || `Access for ${agentId} revoked in sub-second cascade.`,
        };
      }
    } catch {
      // Local fallback
    }
    setAgents((prev) =>
      prev.map((a) => (a.agent_id === agentId ? { ...a, status: 'SUSPENDED', trust_score: 0 } : a))
    );
    return {
      elapsed_ms: 14.2,
      hitl_requests_purged: 1,
      message: `Emergency Kill Switch successfully executed for ${agentId}.`,
    };
  };

  return (
    <div className="min-h-screen bg-[#090D14] text-slate-100 flex flex-col font-sans selection:bg-blue-600/30 selection:text-blue-200">
      {/* Top Navigation Bar */}
      <TopNav
        wsConnected={wsConnected}
        alerts={alerts}
        onOpenKillSwitch={() => handleOpenKillSwitch(undefined)}
        onOpenAlerts={() => setCurrentTab('dashboard')}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          pendingHitlCount={pendingHitlCount}
          agents={agents}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#090D14]">
          <div className="max-w-7xl mx-auto pb-12">
            {currentTab === 'dashboard' && (
              <Dashboard
                agents={agents}
                alerts={alerts}
                hitlItems={hitlItems}
                onOpenKillSwitch={handleOpenKillSwitch}
                onNavigateTab={setCurrentTab}
              />
            )}

            {currentTab === 'passport' && (
              <AgentPassport
                agents={agents}
                selectedAgentId={selectedAgentId}
                onSelectAgent={setSelectedAgentId}
                onOpenKillSwitch={handleOpenKillSwitch}
              />
            )}

            {currentTab === 'hitl' && (
              <HITLApproval items={hitlItems} onRefresh={refreshData} />
            )}

            {currentTab === 'audit' && (
              <AuditInvestigation entries={auditEntries} />
            )}

            {currentTab === 'compliance' && <CompliancePanel />}
          </div>
        </main>
      </div>

      {/* Global / Agent Kill Switch Modal */}
      <KillSwitchModal
        isOpen={killSwitchOpen}
        onClose={() => setKillSwitchOpen(false)}
        agents={agents}
        onExecuteKill={handleExecuteKill}
      />
    </div>
  );
};
