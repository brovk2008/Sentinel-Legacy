import React from 'react';
import { AlertCircle, AlertTriangle, Info, ShieldAlert, ArrowRight } from 'lucide-react';
import { Alert } from '../../types';

interface AlertFeedProps {
  alerts: Alert[];
  onSelectAlert?: (alert: Alert) => void;
}

export const AlertFeed: React.FC<AlertFeedProps> = ({ alerts, onSelectAlert }) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur-sm flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span className="text-sm font-semibold text-white">Live Alert Dispatch</span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
          {alerts.length} Events
        </span>
      </div>

      <div className="space-y-2.5 overflow-y-auto max-h-[380px] pr-1">
        {alerts.map((alert) => {
          let border = 'border-slate-800';
          let bg = 'bg-slate-950/60';
          let text = 'text-cyan-400';
          let Icon = Info;

          if (alert.level === 'critical') {
            border = 'border-rose-500/40';
            bg = 'bg-rose-950/20';
            text = 'text-rose-400';
            Icon = AlertCircle;
          } else if (alert.level === 'warning') {
            border = 'border-amber-500/30';
            bg = 'bg-amber-950/15';
            text = 'text-amber-400';
            Icon = AlertTriangle;
          }

          return (
            <div
              key={alert.id}
              onClick={() => onSelectAlert && onSelectAlert(alert)}
              className={`p-3 rounded-lg border ${border} ${bg} hover:border-slate-600 transition-all cursor-pointer flex flex-col gap-1.5`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className={`w-3.5 h-3.5 ${text}`} />
                  <span className={`text-xs font-bold font-mono uppercase tracking-wide ${text}`}>
                    {alert.level}
                  </span>
                  {alert.agent_name && (
                    <span className="text-[11px] font-semibold text-slate-300">
                      • {alert.agent_name}
                    </span>
                  )}
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  {alert.created_at}
                </span>
              </div>

              <div className="text-xs font-semibold text-slate-200">
                {alert.title}
              </div>

              <div className="text-[11px] text-slate-400 leading-relaxed">
                {alert.message}
              </div>

              {alert.recommendation && (
                <div className="mt-1 pt-1.5 border-t border-slate-800/60 flex items-center gap-1.5 text-[11px] font-medium text-amber-300/90">
                  <ArrowRight className="w-3 h-3 text-amber-400" />
                  <span>Recommendation: {alert.recommendation}</span>
                </div>
              )}
            </div>
          );
        })}

        {alerts.length === 0 && (
          <div className="text-xs text-slate-500 italic py-8 text-center flex flex-col items-center justify-center gap-2">
            <Info className="w-5 h-5 text-slate-600" />
            <span>Zero critical anomaly alerts in sliding buffer</span>
          </div>
        )}
      </div>
    </div>
  );
};
