import React from 'react';
import { Shield, Radio, AlertOctagon, Bell, UserCheck, Activity } from 'lucide-react';
import { Alert } from '../../types';

interface TopNavProps {
  wsConnected: boolean;
  alerts: Alert[];
  onOpenKillSwitch: () => void;
  onOpenAlerts?: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  wsConnected,
  alerts,
  onOpenKillSwitch,
  onOpenAlerts,
}) => {
  const criticalCount = alerts.filter(a => a.level === 'critical').length;

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#0B111D]/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & System Status */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-cyan-400 p-0.5 flex items-center justify-center shadow-glow">
            <div className="w-full h-full bg-[#0B111D] rounded-[7px] flex items-center justify-center">
              <Shield className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-wider text-slate-100">
                SENTINEL <span className="text-cyan-400">LEGACY</span>
              </span>
              <span className="px-1.5 py-0.5 text-[10px] uppercase font-mono font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono tracking-tight">
              Agentic Enterprise Governance Infrastructure
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center space-x-2 pl-4 border-l border-slate-800">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-mono text-emerald-400 font-medium">
            CEDAR ENGINE: ACTIVE (SMT-VERIFIED)
          </span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* WebSocket Heartbeat */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
          <Radio className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
          <span className={wsConnected ? 'text-slate-300' : 'text-amber-400'}>
            {wsConnected ? 'LIVE FEED (WS)' : 'CONNECTING...'}
          </span>
        </div>

        {/* Alert Notification Pill */}
        {criticalCount > 0 && (
          <button
            onClick={onOpenAlerts}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-red-500/15 border border-red-500/40 text-red-400 text-xs font-semibold animate-pulse hover:bg-red-500/25 transition-all"
          >
            <Bell className="w-3.5 h-3.5 text-red-400" />
            <span>{criticalCount} CRITICAL ALERT{criticalCount > 1 ? 'S' : ''}</span>
          </button>
        )}

        {/* Global Emergency Kill Switch Button */}
        <button
          onClick={onOpenKillSwitch}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white text-xs font-bold uppercase tracking-wider shadow-glow-red border border-red-500/50 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
        >
          <AlertOctagon className="w-4 h-4 text-white" />
          <span>KILL SWITCH</span>
        </button>

        {/* Operator Profile */}
        <div className="hidden sm:flex items-center space-x-3 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400 font-semibold text-xs">
            PS
          </div>
          <div className="text-left">
            <p className="text-xs font-semibold text-slate-200 leading-tight">Priya Sharma</p>
            <p className="text-[10px] text-slate-400 font-mono">Gov Admin & Finance Mgr</p>
          </div>
        </div>
      </div>
    </header>
  );
};
