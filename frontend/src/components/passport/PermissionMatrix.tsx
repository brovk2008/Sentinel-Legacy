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
      <div className="rounded-xl border border-[#1E2638] bg-[#0E1320] p-4 flex flex-col">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2638] mb-3">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>Permitted Actions</span>
          </div>
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {permittedActions.length}
          </span>
        </div>

        <div className="space-y-2 flex-1">
          {permittedActions.map((action, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] hover:border-[#2D3A54] transition-colors flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-medium text-slate-200">
                  {action}
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/40">
                  {getPolicyTag(action)}
                </span>
              </div>
              <div className="flex items-center text-[10px] text-slate-400 justify-between pt-1 border-t border-[#1E2638]/60">
                <span className="flex items-center gap-1 text-slate-400">
                  <Shield className="w-3 h-3 text-emerald-500" />
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
      <div className="rounded-xl border border-[#1E2638] bg-[#0E1320] p-4 flex flex-col">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2638] mb-3">
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs uppercase tracking-wider">
            <XCircle className="w-4 h-4 text-rose-500" />
            <span>Forbidden Actions</span>
          </div>
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            {forbiddenActions.length}
          </span>
        </div>

        <div className="space-y-2 flex-1">
          {forbiddenActions.map((action, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] hover:border-[#2D3A54] transition-colors flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-medium text-slate-200">
                  {action}
                </span>
                <span className="text-[10px] font-mono text-rose-400 bg-rose-950/40 px-1.5 py-0.5 rounded border border-rose-800/40">
                  {getPolicyTag(action)}
                </span>
              </div>
              <div className="flex items-center text-[10px] text-slate-400 justify-between pt-1 border-t border-[#1E2638]/60">
                <span className="flex items-center gap-1 text-slate-400">
                  <Shield className="w-3 h-3 text-rose-500" />
                  Cedar: Forbid
                </span>
                <span className="text-rose-400 font-mono">Strict Block</span>
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
      <div className="rounded-xl border border-[#1E2638] bg-[#0E1320] p-4 flex flex-col">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2638] mb-3">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs uppercase tracking-wider">
            <AlertCircle className="w-4 h-4 text-amber-500" />
            <span>HITL Escalations</span>
          </div>
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            {hitlActions.length}
          </span>
        </div>

        <div className="space-y-2 flex-1">
          {hitlActions.map((action, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] hover:border-[#2D3A54] transition-colors flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-medium text-slate-200">
                  {action}
                </span>
                <span className="text-[10px] font-mono text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-800/40">
                  {getPolicyTag(action)}
                </span>
              </div>
              <div className="flex items-center text-[10px] text-slate-400 justify-between pt-1 border-t border-[#1E2638]/60">
                <span className="flex items-center gap-1 text-slate-400">
                  <ArrowUpRight className="w-3 h-3 text-amber-500" />
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
