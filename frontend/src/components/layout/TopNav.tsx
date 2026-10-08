import React from 'react';
import { Shield, Radio, AlertOctagon, Bell, CheckCircle2 } from 'lucide-react';
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
  const criticalCount = alerts.filter((a) => a.level === 'critical').length;

  return (
    <header className="h-16 border-b border-[#1E2638] bg-[#0D121D] px-6 flex items-center justify-between sticky top-0 z-40 shadow-sm">
      {/* Brand & System Status */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-base text-slate-100 tracking-tight">
                Sentinel Legacy
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold rounded bg-slate-800 text-slate-300 border border-slate-700">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Enterprise AI Governance &amp; Control Plane
            </p>
          </div>
        </div>

        {/* Engine Status Tag */}
        <div className="hidden lg:flex items-center space-x-2 pl-4 border-l border-[#1E2638]">
          <span className="flex h-2 w-2 relative">
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-mono text-emerald-400 font-medium">
            Cedar Policy Engine: Active
          </span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* WebSocket Connection State */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-[#141A28] border border-[#212B3E] text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              wsConnected ? 'bg-emerald-500' : 'bg-amber-500'
            }`}
          />
          <span className={wsConnected ? 'text-slate-300' : 'text-amber-400'}>
            {wsConnected ? 'Live Feed (WS)' : 'Reconnecting...'}
          </span>
        </div>

        {/* Alert Notification Pill */}
        {criticalCount > 0 && (
          <button
            onClick={onOpenAlerts}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-rose-950/60 border border-rose-800/60 text-rose-300 text-xs font-semibold hover:bg-rose-900/60 transition-colors"
          >
            <Bell className="w-3.5 h-3.5 text-rose-400" />
            <span>{criticalCount} Critical Alert{criticalCount > 1 ? 's' : ''}</span>
          </button>
        )}

        {/* Authoritative Kill Switch Button */}
        <button
          onClick={onOpenKillSwitch}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold border border-rose-500/80 shadow-sm transition-colors"
        >
          <AlertOctagon className="w-3.5 h-3.5" />
          <span>Emergency Kill Switch</span>
        </button>

        {/* Operator Profile */}
        <div className="hidden sm:flex items-center space-x-3 pl-3 border-l border-[#1E2638]">
          <div className="w-8 h-8 rounded-full bg-[#1A2234] border border-[#2B364D] flex items-center justify-center text-blue-400 font-semibold text-xs">
            PS
          </div>
          <div className="text-left">
            <p className="text-xs font-semibold text-slate-200 leading-tight">Priya Sharma</p>
            <p className="text-[10px] text-slate-400">Governance Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
};
