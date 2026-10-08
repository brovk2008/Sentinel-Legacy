import React, { useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Edit3, 
  AlertTriangle, 
  ShieldCheck, 
  User, 
  RotateCcw, 
  Ban, 
  IndianRupee,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { HITLItem } from '../../types';
import { HITLCountdownTimer } from './HITLCountdownTimer';

interface HITLBriefingCardProps {
  item: HITLItem;
  onApprove: (hitlId: string, rationale?: string, modifiedParams?: Record<string, any>) => Promise<void>;
  onReject: (hitlId: string, rationale: string) => Promise<void>;
  isProcessing?: boolean;
}

export const HITLBriefingCard: React.FC<HITLBriefingCardProps> = ({
  item,
  onApprove,
  onReject,
  isProcessing = false,
}) => {
  const [rejectMode, setRejectMode] = useState(false);
  const [modifyMode, setModifyMode] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [modifiedAmount, setModifiedAmount] = useState(item.briefing.amount?.toString() || '');
  const [showArgs, setShowArgs] = useState(false);

  const { briefing } = item;
  const isExpired = Date.now() > (item.timeout_at > 1e11 ? item.timeout_at : item.timeout_at * 1000);

  const handleApprove = () => {
    if (modifyMode && modifiedAmount) {
      const updatedArgs = {
        ...(briefing.arguments || {}),
        amount: parseFloat(modifiedAmount),
      };
      onApprove(item.hitl_id, 'Approved with adjusted financial parameters', updatedArgs);
    } else {
      onApprove(item.hitl_id, 'Approved by human oversight operator');
    }
  };

  const handleReject = () => {
    if (!rejectReason.trim()) {
      alert('Please provide a specific rejection rationale for the audit record.');
      return;
    }
    onReject(item.hitl_id, rejectReason);
  };

  return (
    <div className="rounded-xl border border-[#222C3E] bg-[#0E1320] shadow-card overflow-hidden transition-all">
      {/* Top Header Bar */}
      <div className="p-4 bg-[#121826] border-b border-[#1E2638] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white text-sm">
                {briefing.agent_name || item.agent_id}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#1A2234] text-slate-300 border border-[#2B364D]">
                {item.agent_id}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                PENDING APPROVAL
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
              Reference ID: {item.hitl_id}
            </div>
          </div>
        </div>

        {/* Countdown Timer */}
        <HITLCountdownTimer timeoutAt={item.timeout_at} />
      </div>

      {/* Prominent Financial Value Banner */}
      {briefing.amount !== undefined && (
        <div className="px-6 py-3 bg-[#131926] border-b border-[#1E2638] flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-300 text-xs font-medium">
            <IndianRupee className="w-4 h-4 text-amber-400" />
            <span>Escalation Threshold Exceeded (&gt; ₹10,000)</span>
          </div>
          <div className="text-xl font-bold font-mono text-white tracking-tight flex items-baseline gap-1">
            <span className="text-amber-400 text-sm">₹</span>
            {briefing.amount.toLocaleString('en-IN')}
            <span className="text-xs text-slate-400 font-mono font-normal">INR</span>
          </div>
        </div>
      )}

      {/* 5-Question Contextual Briefing Body */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-5 text-sm">
        {/* Q1: What does agent want to do? */}
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            1. Requested Action
          </span>
          <div className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] font-mono text-blue-300 font-medium text-xs flex items-center justify-between">
            <span>{briefing.action}</span>
            <span className="text-[10px] text-slate-500 font-normal">
              Resource: {item.resource_id}
            </span>
          </div>
        </div>

        {/* Q2: Why does agent want to do it? */}
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            2. Operational Rationale
          </span>
          <div className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] text-slate-300 text-xs italic">
            "{briefing.reason || 'Agent initiated higher-tier workflow requiring human oversight.'}"
          </div>
        </div>

        {/* Q3: Which customer/entity is affected? */}
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            3. Target Beneficiary / Customer
          </span>
          <div className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] text-xs flex items-center justify-between text-slate-200">
            <div className="flex items-center gap-2">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium">{briefing.customer_name || 'N/A'}</span>
              <span className="text-[10px] font-mono text-slate-500">
                ({briefing.customer_id || 'ID Unknown'})
              </span>
            </div>
            {briefing.customer_tier && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#1F273B] text-slate-300 border border-[#2D3A54]">
                {briefing.customer_tier}
              </span>
            )}
          </div>
        </div>

        {/* Q4: Reversibility & Impact */}
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            4. Impact Reversibility
          </span>
          <div className="p-2.5 rounded-lg bg-[#121826] border border-[#1E2638] text-xs flex items-center justify-between">
            {briefing.reversible ? (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <RotateCcw className="w-3.5 h-3.5" />
                Reversible (Financial ledger credit roll-back supported)
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                <Ban className="w-3.5 h-3.5" />
                Irreversible (Action permanently affects database state)
              </span>
            )}
          </div>
        </div>

        {/* Q5: Policy triggered & Approver Role */}
        <div className="space-y-1 md:col-span-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            5. Governance Policy &amp; Required Authority
          </span>
          <div className="p-3 rounded-lg bg-[#121826] border border-[#1E2638] text-xs flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span className="text-slate-300">Policy Mandate:</span>
              <span className="font-mono font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                {briefing.policy_triggered}
              </span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <span>Required Role:</span>
              <span className="font-medium text-white bg-[#1A2234] px-2 py-0.5 rounded border border-[#2B364D]">
                {briefing.approver_role || item.approver_role}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Expandable Arguments */}
      <div className="px-6 pb-2">
        <button
          onClick={() => setShowArgs(!showArgs)}
          className="text-[11px] font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
        >
          {showArgs ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          {showArgs ? 'Hide MCP Payload Arguments' : 'Inspect MCP Payload Arguments'}
        </button>
        {showArgs && (
          <pre className="mt-2 p-3 rounded-lg bg-[#0B0F18] border border-[#1E2638] text-[11px] font-mono text-slate-300 overflow-x-auto max-h-40">
            {JSON.stringify(briefing.arguments || {}, null, 2)}
          </pre>
        )}
      </div>

      {/* Modify Parameters Panel */}
      {modifyMode && (
        <div className="mx-6 mb-4 p-4 rounded-xl bg-[#121826] border border-blue-500/30 text-xs space-y-3">
          <div className="flex items-center justify-between text-blue-400 font-semibold">
            <span className="flex items-center gap-1.5">
              <Edit3 className="w-4 h-4" />
              Adjust Action Parameters Before Approval
            </span>
            <button
              onClick={() => setModifyMode(false)}
              className="text-slate-400 hover:text-white"
            >
              Cancel
            </button>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-slate-300 font-mono text-xs">Revised Amount (INR):</label>
            <input
              type="number"
              value={modifiedAmount}
              onChange={(e) => setModifiedAmount(e.target.value)}
              className="px-3 py-1.5 rounded-md bg-[#0B0F18] border border-[#2B364D] text-white font-mono text-sm w-44 focus:outline-none focus:border-blue-500"
            />
            <span className="text-slate-500 text-[11px]">
              Original: ₹{briefing.amount?.toLocaleString('en-IN')}
            </span>
          </div>
        </div>
      )}

      {/* Reject Reason Panel */}
      {rejectMode && (
        <div className="mx-6 mb-4 p-4 rounded-xl bg-[#121826] border border-rose-500/30 text-xs space-y-3">
          <div className="flex items-center justify-between text-rose-400 font-semibold">
            <span className="flex items-center gap-1.5">
              <XCircle className="w-4 h-4" />
              Provide Mandatory Rejection Rationale
            </span>
            <button
              onClick={() => setRejectMode(false)}
              className="text-slate-400 hover:text-white"
            >
              Cancel
            </button>
          </div>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="E.g., Customer refund exceeds allowed policy window; requires manual supervisor interview."
            rows={2}
            className="w-full p-2.5 rounded-md bg-[#0B0F18] border border-[#2B364D] text-white text-xs focus:outline-none focus:border-rose-500 resize-none"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="px-3.5 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs flex items-center gap-1.5 transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" />
              Confirm Rejection &amp; Penalize Trust
            </button>
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="p-4 bg-[#121826] border-t border-[#1E2638] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setModifyMode(!modifyMode);
              setRejectMode(false);
            }}
            disabled={isExpired || isProcessing}
            className="px-3 py-1.5 rounded-md bg-[#182030] hover:bg-[#202B40] text-slate-300 font-medium text-xs flex items-center gap-1.5 border border-[#2A374F] transition-colors disabled:opacity-50"
          >
            <Edit3 className="w-3.5 h-3.5 text-blue-400" />
            {modifyMode ? 'Cancel Edit' : 'Modify Parameters'}
          </button>

          <button
            onClick={() => {
              setRejectMode(!rejectMode);
              setModifyMode(false);
            }}
            disabled={isExpired || isProcessing}
            className="px-3 py-1.5 rounded-md bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 font-medium text-xs flex items-center gap-1.5 border border-rose-800/40 transition-colors disabled:opacity-50"
          >
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            Reject Action
          </button>
        </div>

        <button
          onClick={handleApprove}
          disabled={isExpired || isProcessing}
          className="px-4 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs flex items-center gap-1.5 shadow-sm transition-colors disabled:opacity-50"
        >
          <CheckCircle className="w-4 h-4" />
          {modifyMode ? 'Approve with Modifications' : 'Approve & Resume Agent'}
        </button>
      </div>
    </div>
  );
};
