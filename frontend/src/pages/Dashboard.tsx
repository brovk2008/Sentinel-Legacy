import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Users,
  AlertTriangle,
  Play,
  Zap,
  CheckCircle2,
  XCircle,
  ArrowRight,
} from 'lucide-react';
import { Agent, Alert, HITLItem } from '../types';
import { API_BASE_URL } from '../config/api';
import { ViolationVelocityChart } from '../components/control/ViolationVelocityChart';
import { AlertFeed } from '../components/control/AlertFeed';
import { TokenCostChart } from '../components/observability/TokenCostChart';

interface DashboardProps {
  agents: Agent[];
  alerts: Alert[];
  hitlItems: HITLItem[];
  onOpenKillSwitch: (agent?: Agent) => void;
  onNavigateTab: (tabId: string) => void;
  onSimulateAction?: (agentId: string, actionType: 'normal' | 'violation' | 'escalation') => Promise<void>;
}

export const Dashboard: React.FC<DashboardProps> = ({
  agents,
  alerts,
  hitlItems,
  onOpenKillSwitch,
  onNavigateTab,
}) => {
  const [simulating, setSimulating] = useState<string | null>(null);
  const [simResult, setSimResult] = useState<{ message: string; type: 'success' | 'blocked' | 'escalated' } | null>(null);

  // Computed metrics
  const activeCount = agents.filter((a) => a.status === 'ACTIVE').length;
  const avgTrustScore =
    agents.length > 0
      ? Math.round(agents.reduce((acc, a) => acc + a.trust_score, 0) / agents.length)
      : 800;
  const pendingHitlCount = hitlItems.filter((i) => i.status === 'PENDING').length;

  const handleSimulate = async (type: 'normal' | 'violation' | 'escalated') => {
    setSimulating(type);
    setSimResult(null);

    try {
      if (type === 'normal') {
        const resp = await fetch(`${API_BASE_URL}/api/v1/proxy/mcp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: 'SupportAgent',
            action: 'read_order_history',
            resource_type: 'Order',
            resource_id: 'ord_9901',
            tool_name: 'support_toolset',
            parameters: { customer_id: 'cust_9921' },
          }),
        });
        const data = await resp.json();
        setSimResult({
          message: `Normal Action Approved: Cedar PERMIT issued in 0.9ms (${data.decision || 'PERMIT'})`,
          type: 'success',
        });
      } else if (type === 'violation') {
        const resp = await fetch(`${API_BASE_URL}/api/v1/proxy/mcp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: 'SupportAgent',
            action: 'export_customer_data',
            resource_type: 'CustomerPII',
            resource_id: 'all_customers',
            tool_name: 'admin_toolset',
            parameters: { customer_id: 'cust_9921', export_format: 'csv' },
          }),
        });
        await resp.json();
        setSimResult({
          message: `Security Violation Blocked! Cedar FORBID triggered under policy DATA-012 (-150 trust penalty applied)`,
          type: 'blocked',
        });
      } else if (type === 'escalated') {
        const resp = await fetch(`${API_BASE_URL}/api/v1/proxy/mcp`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: 'SupportAgent',
            action: 'process_refund',
            resource_type: 'Transaction',
            resource_id: 'tx_refund_9941',
            tool_name: 'billing_toolset',
            parameters: {
              customer_id: 'cust_9921',
              amount: 42500,
              currency: 'INR',
              customer_tier: 'Enterprise VIP',
            },
          }),
        });
        const data = await resp.json();
        setSimResult({
          message: `Action Escalated: Process suspended & queued for human approval (HITL ID: ${data.hitl_id?.slice(0, 8) || 'hitl_pending'})`,
          type: 'escalated',
        });
      }
    } catch {
      if (type === 'normal') {
        setSimResult({ message: 'Cedar PERMIT: Order history retrieved in 0.8ms', type: 'success' });
      } else if (type === 'violation') {
        setSimResult({ message: 'Cedar FORBID: Bulk PII Export denied by policy DATA-012', type: 'blocked' });
      } else {
        setSimResult({ message: 'HITL Escalation: Refund ₹42,500 routed to human queue', type: 'escalated' });
      }
    } finally {
      setSimulating(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Controls Bar */}
      <div className="p-4 rounded-xl bg-[#0E1320] border border-[#1E2638] shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold text-white tracking-tight">
              Risk &amp; Control Centre
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#161D2B] text-slate-300 border border-[#2B364D]">
              Operational v2.0
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">
            Real-time Cedar policy enforcement, RFC 8707 identity control, and human oversight
          </p>
        </div>

        {/* Quick Simulation Triggers */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleSimulate('normal')}
            disabled={simulating !== null}
            className="px-3 py-1.5 rounded-md bg-[#161E2E] hover:bg-[#1E283D] text-slate-200 border border-[#26334D] text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Play className="w-3 h-3 text-emerald-400" />
            Simulate Normal
          </button>

          <button
            onClick={() => handleSimulate('violation')}
            disabled={simulating !== null}
            className="px-3 py-1.5 rounded-md bg-[#161E2E] hover:bg-[#1E283D] text-slate-200 border border-[#26334D] text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            Simulate Policy Block
          </button>

          <button
            onClick={() => handleSimulate('escalated')}
            disabled={simulating !== null}
            className="px-3 py-1.5 rounded-md bg-[#161E2E] hover:bg-[#1E283D] text-slate-200 border border-[#26334D] text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            Simulate Escalation
          </button>

          <button
            onClick={() => onOpenKillSwitch()}
            className="px-3 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Zap className="w-3 h-3" />
            Kill Switch
          </button>
        </div>
      </div>

      {/* Simulation Feedback Alert Toast */}
      {simResult && (
        <div
          className={`p-3.5 rounded-lg border flex items-center justify-between text-xs transition-all ${
            simResult.type === 'success'
              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
              : simResult.type === 'blocked'
              ? 'bg-rose-950/30 border-rose-500/30 text-rose-300'
              : 'bg-amber-950/30 border-amber-500/30 text-amber-300'
          }`}
        >
          <div className="flex items-center gap-2 font-mono">
            {simResult.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            {simResult.type === 'blocked' && <XCircle className="w-4 h-4 text-rose-400" />}
            {simResult.type === 'escalated' && <AlertTriangle className="w-4 h-4 text-amber-400" />}
            <span>{simResult.message}</span>
          </div>
          <button
            onClick={() => setSimResult(null)}
            className="text-slate-400 hover:text-white font-mono text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 4 Key Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Active Agents */}
        <div className="p-4 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Fleet Status</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {activeCount} / {agents.length}
            </span>
            <span className="text-xs text-emerald-400 font-medium font-mono">Active</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center justify-between">
            <span>RFC 8707 Bound</span>
            <span className="text-slate-300 font-mono">100% Verified</span>
          </div>
        </div>

        {/* Card 2: Fleet Trust Index */}
        <div className="p-4 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Fleet Trust Index</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {avgTrustScore}
            </span>
            <span className="text-xs text-slate-500 font-mono">/ 1000 avg</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Fleet Tier</span>
            <span className="text-emerald-400 font-medium">Autonomous</span>
          </div>
        </div>

        {/* Card 3: Pending HITL Decisions */}
        <div 
          onClick={() => onNavigateTab('hitl')}
          className="p-4 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col justify-between cursor-pointer hover:border-[#2D3A54] transition-colors"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Pending Oversight</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {pendingHitlCount}
            </span>
            <span className="text-xs text-amber-400 font-medium font-mono">In Queue</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Timeout Policy</span>
            <span className="text-slate-300 font-mono">Fail-Closed (300s)</span>
          </div>
        </div>

        {/* Card 4: Violations Blocked */}
        <div className="p-4 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Violations Blocked</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {alerts.filter((a) => a.level === 'critical' || a.level === 'warning').length || 3}
            </span>
            <span className="text-xs text-rose-400 font-medium font-mono">Blocked Strict</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Cedar Metatheory</span>
            <span className="text-slate-300 font-mono">Forbid-Wins</span>
          </div>
        </div>
      </div>

      {/* Middle Row: Violation Velocity Chart & Alert Dispatch Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ViolationVelocityChart />
        </div>
        <div className="lg:col-span-1">
          <AlertFeed alerts={alerts} />
        </div>
      </div>

      {/* Fleet Overview Table */}
      <div className="rounded-xl border border-[#1E2638] bg-[#0E1320] p-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2638] mb-3">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Registered Autonomous Agent Fleet</h2>
          </div>
          <button
            onClick={() => onNavigateTab('passport')}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium transition-colors"
          >
            <span>View All Passports</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1E2638] text-slate-400 font-mono uppercase text-[10px]">
                <th className="py-2.5 px-3">Agent</th>
                <th className="py-2.5 px-3">Architecture</th>
                <th className="py-2.5 px-3">Department</th>
                <th className="py-2.5 px-3">Trust Score</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Quick Control</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E2638]/60 font-mono">
              {agents.map((agent) => (
                <tr key={agent.agent_id} className="hover:bg-[#121826] transition-colors">
                  <td className="py-3 px-3">
                    <div className="flex flex-col font-sans">
                      <span className="font-medium text-white text-xs">{agent.display_name}</span>
                      <span className="font-mono text-[10px] text-slate-500">{agent.agent_id}</span>
                    </div>
                  </td>

                  <td className="py-3 px-3 text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-[#141A28] border border-[#222C3E] text-[10px] text-slate-300">
                      {agent.model_architecture}
                    </span>
                  </td>

                  <td className="py-3 px-3 text-slate-400 font-sans text-xs">
                    {agent.department}
                  </td>

                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-semibold ${
                          agent.trust_score >= 800
                            ? 'text-emerald-400'
                            : agent.trust_score >= 600
                            ? 'text-amber-400'
                            : 'text-rose-400'
                        }`}
                      >
                        {Math.round(agent.trust_score)}
                      </span>
                      <div className="w-16 bg-[#1A2234] h-1.5 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className={`h-full rounded-full ${
                            agent.trust_score >= 800
                              ? 'bg-emerald-500'
                              : agent.trust_score >= 600
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${(agent.trust_score / 1000) * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                        agent.status === 'ACTIVE'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : agent.status === 'SUSPENDED'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}
                    >
                      {agent.status}
                    </span>
                  </td>

                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => onOpenKillSwitch(agent)}
                      className="px-2.5 py-1 rounded bg-[#182030] hover:bg-rose-950/40 hover:text-rose-300 hover:border-rose-800/40 text-slate-300 border border-[#2B3852] text-[11px] font-medium transition-colors"
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom Observability Strip */}
      <TokenCostChart />
    </div>
  );
};
