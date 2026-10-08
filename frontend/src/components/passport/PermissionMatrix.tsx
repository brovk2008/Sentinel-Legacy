import React from 'react';
import { CheckCircle2, XCircle, AlertCircle, Shield, ArrowUpRight } from 'lucide-react';

interface PermissionMatrixProps {
  permittedActions: string[];
  forbiddenActions: string[];
  hitlActions: string[];
}

export const PermissionMatrix: React.FC<PermissionMatrixProps> = ({
  permittedActions,
  forbiddenActions,
  hitlActions,
}) => {
  const getPolicyTag = (action: string) => {
    if (action.includes('refund')) return 'REFUND-001';
    if (action.includes('export') || action.includes('pii')) return 'DATA-012';
    if (action.includes('close')) return 'ACCOUNT-007';
    if (action.includes('credential') || action.includes('modify')) return 'SEC-001';
    if (action.includes('query')) return 'SEC-003';
    return 'BASE-POL';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Column 1: Permitted Actions */}
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-4 backdrop-blur-sm flex flex-col">
        <div className="flex items-center justify-between pb-3 border-b border-emerald-500/20 mb-3">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Permitted Actions</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            {permittedActions.length}
          </span>
        </div>

        <div className="space-y-2.5 flex-1">
          {permittedActions.map((action, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-slate-200">
                  {action}
                </span>
                <span className="text-[10px] font-mono text-emerald-400/90 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                  {getPolicyTag(action)}
                </span>
              </div>
              <div className="flex items-center text-[10px] text-slate-400 justify-between pt-1 border-t border-slate-800/40">
                <span className="flex items-center gap-1">
                  <Shield className="w-3 h-3 text-emerald-400" />
                  Cedar: Permit
                </span>
                <span className="text-slate-500 font-mono">Autonomous</span>
              </div>
            </div>
          ))}
          {permittedActions.length === 0 && (
            <div className="text-xs text-slate-500 italic py-4 text-center">
              No autonomous permissions active
            </div>
          )}
        </div>
      </div>

      {/* Column 2: Forbidden Actions */}
      <div className="rounded-xl border border-rose-500/20 bg-rose-950/10 p-4 backdrop-blur-sm flex flex-col">
        <div className="flex items-center justify-between pb-3 border-b border-rose-500/20 mb-3">
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
            <XCircle className="w-4 h-4 text-rose-400" />
            <span>Forbidden Actions</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            {forbiddenActions.length}
          </span>
        </div>

        <div className="space-y-2.5 flex-1">
          {forbiddenActions.map((action, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-rose-500/40 transition-colors flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-slate-200">
                  {action}
                </span>
                <span className="text-[10px] font-mono text-rose-400/90 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                  {getPolicyTag(action)}
                </span>
              </div>
              <div className="flex items-center text-[10px] text-slate-400 justify-between pt-1 border-t border-slate-800/40">
                <span className="flex items-center gap-1">
                  <Shield className="w-3 h-3 text-rose-400" />
                  Cedar: Forbid (Strict)
                </span>
                <span className="text-rose-400 font-mono">Blocks & Pen.</span>
              </div>
            </div>
          ))}
          {forbiddenActions.length === 0 && (
            <div className="text-xs text-slate-500 italic py-4 text-center">
              No forbidden actions declared
            </div>
          )}
        </div>
      </div>

      {/* Column 3: HITL Escalation */}
      <div className="rounded-xl border border-amber-500/20 bg-amber-950/10 p-4 backdrop-blur-sm flex flex-col">
        <div className="flex items-center justify-between pb-3 border-b border-amber-500/20 mb-3">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>HITL Escalations</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            {hitlActions.length}
          </span>
        </div>

        <div className="space-y-2.5 flex-1">
          {hitlActions.map((action, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-amber-500/40 transition-colors flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-slate-200">
                  {action}
                </span>
                <span className="text-[10px] font-mono text-amber-400/90 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                  {getPolicyTag(action)}
                </span>
              </div>
              <div className="flex items-center text-[10px] text-slate-400 justify-between pt-1 border-t border-slate-800/40">
                <span className="flex items-center gap-1">
                  <ArrowUpRight className="w-3 h-3 text-amber-400" />
                  Escalate to Human
                </span>
                <span className="text-amber-400 font-mono">Suspends 300s</span>
              </div>
            </div>
          ))}
          {hitlActions.length === 0 && (
            <div className="text-xs text-slate-500 italic py-4 text-center">
              No actions mapped for HITL escalation
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
