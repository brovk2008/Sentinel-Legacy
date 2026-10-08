import React, { useState } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  XCircle, 
  ArrowUpRight, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronRight,
  Shield, 
  Link as LinkIcon
} from 'lucide-react';
import { AuditEntry } from '../../types';

interface AuditTimelineProps {
  entries: AuditEntry[];
  onSelectEntry?: (entry: AuditEntry) => void;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ entries, onSelectEntry }) => {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const copyToClipboard = (text: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const toggleExpand = (entryId: string) => {
    setExpandedId(expandedId === entryId ? null : entryId);
  };

  return (
    <div className="rounded-xl border border-[#1E2638] bg-[#0E1320] p-4">
      <div className="flex items-center justify-between pb-3 border-b border-[#1E2638] mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-white">Audit Ledger</span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Monotonic SHA-256 Hash Chain
        </span>
      </div>

      <div className="space-y-2.5">
        {entries.map((entry) => {
          const isExpanded = expandedId === entry.entry_id;
          let badgeStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
          let DecisionIcon = CheckCircle2;

          if (entry.decision === 'FORBID') {
            badgeStyle = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
            DecisionIcon = XCircle;
          } else if (entry.decision === 'HITL_PAUSED') {
            badgeStyle = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
            DecisionIcon = ArrowUpRight;
          }

          return (
            <div
              key={entry.entry_id}
              className={`rounded-xl border transition-all ${
                isExpanded 
                  ? 'border-blue-500/40 bg-[#121826]' 
                  : 'border-[#1E2638] bg-[#101522] hover:border-[#2D3A54]'
              }`}
            >
              <div 
                className="p-3 cursor-pointer flex flex-wrap items-center justify-between gap-3 text-xs"
                onClick={() => toggleExpand(entry.entry_id)}
              >
                {/* Left side: Seq #, Decision Badge, Action */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 font-mono text-slate-400 text-xs w-16">
                    <span className="text-slate-600">#</span>
                    <span className="text-white font-semibold">{entry.sequence_num}</span>
                  </div>

                  <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold flex items-center gap-1 ${badgeStyle}`}>
                    <DecisionIcon className="w-3 h-3" />
                    {entry.decision}
                  </span>

                  <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-medium text-slate-200">
                        {entry.action}
                      </span>
                      <span className="text-[10px] font-mono text-slate-300 bg-[#1A2234] px-1.5 py-0.2 rounded border border-[#2B364D]">
                        {entry.agent_id}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400 truncate max-w-sm">
                      {entry.resource_type}: {entry.resource_id}
                    </span>
                  </div>
                </div>

                {/* Right side: Hash snippet, Policy ID, Timestamp */}
                <div className="flex items-center gap-4">
                  {entry.policy_id && (
                    <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-amber-300/90 bg-amber-950/30 px-1.5 py-0.5 rounded border border-amber-800/40">
                      <Shield className="w-2.5 h-2.5" />
                      {entry.policy_id}
                    </span>
                  )}

                  <div 
                    className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400 bg-[#0B0F18] px-2 py-1 rounded border border-[#1E2638] hover:border-slate-600"
                    onClick={(e) => copyToClipboard(entry.entry_hash, e)}
                    title="Copy SHA-256 hash"
                  >
                    <LinkIcon className="w-3 h-3 text-blue-400" />
                    <span>{entry.entry_hash.slice(0, 8)}...{entry.entry_hash.slice(-6)}</span>
                    {copiedHash === entry.entry_hash ? (
                      <Check className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Copy className="w-3 h-3 text-slate-500 hover:text-slate-300" />
                    )}
                  </div>

                  <span className="text-[10px] text-slate-500 min-w-[70px] text-right font-mono">
                    {new Date(entry.created_at).toLocaleTimeString()}
                  </span>

                  <div className="text-slate-500">
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </div>
                </div>
              </div>

              {/* Expanded Detail Inspector */}
              {isExpanded && (
                <div className="p-4 border-t border-[#1E2638] bg-[#0E1320] text-xs space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Cryptographic Hash Chain
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#0A0E18] border border-[#1E2638] font-mono text-[10px] space-y-1.5">
                        <div className="flex flex-col">
                          <span className="text-slate-500">Parent Hash (H_{entry.sequence_num - 1}):</span>
                          <span className="text-slate-300 break-all select-all">{entry.prev_entry_hash}</span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-slate-500">Block Hash (H_{entry.sequence_num}):</span>
                          <span className="text-blue-400 font-semibold break-all select-all">{entry.entry_hash}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Cedar Evaluation Detail
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#0A0E18] border border-[#1E2638] font-mono text-[10px] text-slate-300 overflow-x-auto max-h-28">
                        <pre>{JSON.stringify(entry.cedar_detail || {}, null, 2)}</pre>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Context Snapshot (Audit Trail)
                    </div>
                    <pre className="p-2.5 rounded-lg bg-[#0A0E18] border border-[#1E2638] font-mono text-[10px] text-slate-300 overflow-x-auto max-h-36">
                      {JSON.stringify(entry.context_snapshot || {}, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {entries.length === 0 && (
          <div className="text-xs text-slate-500 italic py-12 text-center">
            Zero entries in audit ledger yet
          </div>
        )}
      </div>
    </div>
  );
};
