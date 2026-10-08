import React, { useState } from 'react';
import {
  Shield,
  User,
  Cpu,
  Calendar,
  Clock,
  Key,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';
import { Agent, TrustScoreBreakdown } from '../types';
import { TrustScoreGauge } from '../components/passport/TrustScoreGauge';
import { PermissionMatrix } from '../components/passport/PermissionMatrix';
import { TelemetrySummary } from '../components/passport/TelemetrySummary';
import { RecentActivity } from '../components/passport/RecentActivity';

interface AgentPassportProps {
  agents: Agent[];
  selectedAgentId?: string;
  onSelectAgent?: (agentId: string) => void;
  onOpenKillSwitch: (agent: Agent) => void;
}

export const AgentPassport: React.FC<AgentPassportProps> = ({
  agents,
  selectedAgentId,
  onSelectAgent,
  onOpenKillSwitch,
}) => {
  const [activeId, setActiveId] = useState<string>(
    selectedAgentId || (agents.length > 0 ? agents[0].agent_id : 'SupportAgent')
  );

  const currentAgent = agents.find((a) => a.agent_id === activeId) || agents[0];

  const handleSelect = (id: string) => {
    setActiveId(id);
    if (onSelectAgent) onSelectAgent(id);
  };

  // Realistic trust score breakdown for the active agent
  const breakdown: TrustScoreBreakdown = {
    base_score: 800,
    success_count: 84,
    success_contribution: 42.0,
    violation_count: currentAgent?.status === 'SUSPENDED' ? 3 : 0,
    violation_penalty: currentAgent?.status === 'SUSPENDED' ? 450.0 : 0,
    rejection_count: 0,
    rejection_penalty: 0,
    temporal_decay_adjustment: -2.0,
    total: currentAgent?.trust_score ?? 840,
  };

  if (!currentAgent) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono">
        No registered agents found. Initializing Sentinel database...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Agent Selector Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Select Agent Dossier:
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {agents.map((agent) => (
            <button
              key={agent.agent_id}
              onClick={() => handleSelect(agent.agent_id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                activeId === agent.agent_id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-md shadow-cyan-950/40'
                  : 'bg-slate-950/60 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  agent.status === 'ACTIVE'
                    ? 'bg-emerald-400'
                    : agent.status === 'SUSPENDED'
                    ? 'bg-rose-400'
                    : 'bg-amber-400'
                }`}
              />
              <span>{agent.display_name}</span>
              <span className="text-[10px] font-mono text-slate-500">
                ({Math.round(agent.trust_score)})
              </span>
            </button>
          ))}
        </div>

        <button
          onClick={() => onOpenKillSwitch(currentAgent)}
          className="px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-semibold transition-colors flex items-center gap-1.5"
        >
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          Revoke Agent Access
        </button>
      </div>

      {/* Main Passport Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-950 to-slate-900/90 border border-slate-800 shadow-2xl relative overflow-hidden">
        {/* Background Watermark */}
        <div className="absolute right-0 bottom-0 opacity-5 pointer-events-none transform translate-x-12 translate-y-12">
          <Shield className="w-96 h-96 text-cyan-400" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 relative z-10">
          {/* Left Column: Metadata & Human Owner */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header Title */}
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  EU AI ACT / DPDPA AUDIT PASSPORT
                </span>
                <span className="text-[10px] font-mono text-slate-500">
                  REF: {currentAgent.agent_id}
                </span>
              </div>
              <h2 className="text-2xl font-black text-white mt-1 tracking-tight">
                {currentAgent.display_name}
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Role: {currentAgent.role} • Department: {currentAgent.department}
              </p>
            </div>

            {/* Core Specs Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                  <Cpu className="w-3 h-3 text-cyan-400" />
                  Architecture
                </span>
                <span className="text-white font-semibold mt-1">
                  {currentAgent.model_architecture}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                  <Key className="w-3 h-3 text-indigo-400" />
                  RFC 8707 Client
                </span>
                <span className="text-indigo-300 font-semibold mt-1 truncate">
                  {currentAgent.client_id}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                  <Clock className="w-3 h-3 text-emerald-400" />
                  Last Active
                </span>
                <span className="text-slate-300 mt-1 truncate">
                  {new Date(currentAgent.last_active_at).toLocaleTimeString()}
                </span>
              </div>
            </div>

            {/* Human Owner Section */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Designated Human Supervisor (Owner)
                  </div>
                  <div className="text-sm font-bold text-white mt-0.5">
                    {currentAgent.owner?.name || 'Aarav Patel'}
                  </div>
                  <div className="text-xs text-slate-400 font-mono">
                    {currentAgent.owner?.email || 'aarav.patel@sentinel.corp'} •{' '}
                    {currentAgent.owner?.manager_role || 'VP of Autonomous Infrastructure'}
                  </div>
                </div>
              </div>

              <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                Verified Signer
              </span>
            </div>
          </div>

          {/* Right Column: Trust Score Radial Gauge */}
          <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Autonomous Trust Score
            </div>
            <TrustScoreGauge
              score={currentAgent.trust_score}
              status={currentAgent.status}
              breakdown={breakdown}
              size={190}
            />
          </div>
        </div>
      </div>

      {/* 30-Day Telemetry Strip */}
      <TelemetrySummary />

      {/* 3-Column Permission Matrix */}
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">
              Formal Cedar Policy Permission Matrix
            </h3>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Evaluated via cedar-python (Rust engine)
          </span>
        </div>

        <PermissionMatrix
          permittedActions={currentAgent.permitted_actions}
          forbiddenActions={currentAgent.forbidden_actions}
          hitlActions={currentAgent.hitl_actions}
        />
      </div>

      {/* Recent Activity Feed */}
      <RecentActivity />
    </div>
  );
};
