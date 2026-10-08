import React from 'react';
import {
  LayoutDashboard,
  IdCard,
  UserCheck,
  FileSearch,
  Scale,
  Bot,
  Circle,
  Cpu,
} from 'lucide-react';
import { Agent } from '../../types';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  pendingHitlCount: number;
  agents: Agent[];
  selectedAgentId?: string;
  onSelectAgent?: (agentId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  pendingHitlCount,
  agents,
  selectedAgentId,
  onSelectAgent,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Risk & Control Centre', icon: LayoutDashboard },
    { id: 'passport', label: 'AI Passport Dossier', icon: IdCard },
    {
      id: 'hitl',
      label: 'HITL Human Oversight',
      icon: UserCheck,
      badge: pendingHitlCount > 0 ? pendingHitlCount : null,
      badgeColor: 'bg-amber-500/20 text-amber-300 border border-amber-500/40',
    },
    { id: 'audit', label: 'Audit & Hash Chain', icon: FileSearch },
    { id: 'compliance', label: 'DPDPA & EU AI Act', icon: Scale },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'text-emerald-500 fill-emerald-500';
      case 'RESTRICTED':
        return 'text-amber-500 fill-amber-500';
      case 'SUSPENDED':
        return 'text-rose-500 fill-rose-500';
      default:
        return 'text-slate-500 fill-slate-500';
    }
  };

  return (
    <aside className="w-64 border-r border-[#1E2638] bg-[#0B0F19] flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-6">
        {/* Navigation Section */}
        <div className="space-y-1">
          <p className="px-3 text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2">
            Governance Console
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-colors ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#141A28] border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* AI Workforce Registry Section */}
        <div className="space-y-2 pt-4 border-t border-[#1E2638]">
          <div className="flex items-center justify-between px-3 mb-2">
            <p className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
              AI Workforce
            </p>
            <span className="text-[10px] font-mono text-slate-300 bg-[#161D2C] px-1.5 py-0.5 rounded border border-[#263147]">
              {agents.length} AGENTS
            </span>
          </div>

          <div className="space-y-1.5">
            {agents.map((agent) => {
              const isSelected = selectedAgentId === agent.agent_id;
              return (
                <div
                  key={agent.agent_id}
                  onClick={() => {
                    onSelectAgent?.(agent.agent_id);
                    onSelectTab('passport');
                  }}
                  className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#161E2E] border-blue-500/50 shadow-sm'
                      : 'bg-[#101522] border-[#1C2436] hover:border-[#2C3852] hover:bg-[#141B2B]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Bot className="w-3.5 h-3.5 text-slate-400" />
                      <span className="text-xs font-semibold text-slate-200">{agent.name}</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <Circle className={`w-2 h-2 ${getStatusColor(agent.status)}`} />
                      <span className="text-[10px] font-mono text-slate-400">{agent.status}</span>
                    </div>
                  </div>
                  <div className="mt-1.5 flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span className="truncate max-w-[110px]">{agent.department}</span>
                    <span className="text-blue-400 font-medium">{Math.round(agent.trust_score)} / 1000</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* System Footer Info */}
      <div className="p-4 border-t border-[#1E2638] bg-[#090D15]">
        <div className="flex items-center space-x-2 text-slate-400 text-[11px] font-mono">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span>MCP PROTOCOL: 2025-11-25</span>
        </div>
        <p className="text-[10px] text-slate-500 font-mono mt-1">
          FAIL-CLOSED · RFC 8707 AUDIENCE BINDING
        </p>
      </div>
    </aside>
  );
};
