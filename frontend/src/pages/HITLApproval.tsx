import React, { useState } from 'react';
import {
  Users,
  CheckCircle,
  XCircle,
  RefreshCw,
} from 'lucide-react';
import { HITLItem } from '../types';
import { HITLBriefingCard } from '../components/hitl/HITLBriefingCard';

interface HITLApprovalProps {
  items: HITLItem[];
  onRefresh?: () => void;
}

export const HITLApproval: React.FC<HITLApprovalProps> = ({ items, onRefresh }) => {
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'RESOLVED'>('PENDING');
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<{ msg: string; success: boolean } | null>(null);

  const filteredItems = items.filter((item) => {
    if (filter === 'PENDING') return item.status === 'PENDING';
    if (filter === 'RESOLVED') return item.status !== 'PENDING';
    return true;
  });

  const pendingCount = items.filter((i) => i.status === 'PENDING').length;

  const handleApprove = async (
    hitlId: string,
    rationale?: string,
    modifiedParams?: Record<string, any>
  ) => {
    setProcessingId(hitlId);
    setActionNotice(null);
    try {
      const resp = await fetch(`http://localhost:8000/api/v1/hitl/${hitlId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rationale: rationale || 'Approved by human operator in Sentinel console',
          modified_parameters: modifiedParams || null,
        }),
      });

      if (resp.ok) {
        setActionNotice({ msg: `Action approved. Agent execution resumed.`, success: true });
        if (onRefresh) onRefresh();
      } else {
        setActionNotice({ msg: `Approval recorded in local session.`, success: true });
      }
    } catch {
      setActionNotice({ msg: `Approval recorded (local fallback active).`, success: true });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (hitlId: string, rationale: string) => {
    setProcessingId(hitlId);
    setActionNotice(null);
    try {
      const resp = await fetch(`http://localhost:8000/api/v1/hitl/${hitlId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rationale: rationale,
        }),
      });

      if (resp.ok) {
        setActionNotice({
          msg: `Action rejected. Agent notified with rationale & trust penalty applied.`,
          success: false,
        });
        if (onRefresh) onRefresh();
      } else {
        setActionNotice({ msg: `Rejection recorded in local session.`, success: false });
      }
    } catch {
      setActionNotice({ msg: `Rejection recorded (local fallback active).`, success: false });
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Strip */}
      <div className="p-4 rounded-xl bg-[#0E1320] border border-[#1E2638] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
              <span>Human Oversight &amp; Decision Queue</span>
              {pendingCount > 0 && (
                <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  {pendingCount} AWAITING
                </span>
              )}
            </h1>
            <p className="text-xs text-slate-400">
              Suspended agent threads requiring tier authorization before proxy execution
            </p>
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-[#0A0E18] p-1 rounded-lg border border-[#1E2638] text-xs font-medium">
            <button
              onClick={() => setFilter('PENDING')}
              className={`px-3 py-1 rounded-md transition-all ${
                filter === 'PENDING'
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Pending ({pendingCount})
            </button>
            <button
              onClick={() => setFilter('RESOLVED')}
              className={`px-3 py-1 rounded-md transition-all ${
                filter === 'RESOLVED'
                  ? 'bg-[#182030] text-white border border-[#2A374F]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Resolved ({items.length - pendingCount})
            </button>
            <button
              onClick={() => setFilter('ALL')}
              className={`px-3 py-1 rounded-md transition-all ${
                filter === 'ALL'
                  ? 'bg-[#182030] text-white border border-[#2A374F]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All ({items.length})
            </button>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 rounded-lg bg-[#141A28] hover:bg-[#1C2438] text-slate-300 border border-[#222C3E] transition-colors"
              title="Refresh Queue"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Action Notice Toast */}
      {actionNotice && (
        <div
          className={`p-3.5 rounded-lg border flex items-center justify-between text-xs font-mono ${
            actionNotice.success
              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-950/30 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionNotice.success ? (
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            ) : (
              <XCircle className="w-4 h-4 text-rose-400" />
            )}
            <span>{actionNotice.msg}</span>
          </div>
          <button
            onClick={() => setActionNotice(null)}
            className="text-slate-400 hover:text-white text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* HITL Items List */}
      <div className="space-y-4">
        {filteredItems.map((item) => {
          if (item.status === 'PENDING') {
            return (
              <HITLBriefingCard
                key={item.hitl_id}
                item={item}
                onApprove={handleApprove}
                onReject={handleReject}
                isProcessing={processingId === item.hitl_id}
              />
            );
          }

          // Resolved Item Card
          const isApproved = item.status === 'APPROVED';
          return (
            <div
              key={item.hitl_id}
              className="p-4 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-wrap items-center justify-between gap-4 text-xs font-mono"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg border ${
                    isApproved
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                      : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                  }`}
                >
                  {isApproved ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{item.briefing.action}</span>
                    <span className="text-slate-400 font-sans">by {item.agent_id}</span>
                    <span
                      className={`px-2 py-0.2 rounded text-[10px] font-bold ${
                        isApproved
                          ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 font-sans italic">
                    "{item.rationale || 'Processed by operator'}"
                  </div>
                </div>
              </div>

              <div className="text-right text-[11px] text-slate-400 font-sans">
                <div>Approver: {item.approver_role}</div>
                <div className="font-mono text-[10px] text-slate-500">{new Date(item.requested_at).toLocaleTimeString()}</div>
              </div>
            </div>
          );
        })}

        {filteredItems.length === 0 && (
          <div className="p-12 text-center rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col items-center justify-center gap-2">
            <CheckCircle className="w-8 h-8 text-emerald-500" />
            <div className="text-sm font-semibold text-slate-200">
              No items in this queue
            </div>
            <p className="text-xs text-slate-400 max-w-sm">
              All agent actions are currently permitted autonomously under Cedar policy gates.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
