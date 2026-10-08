import React, { useState } from 'react';
import { AlertOctagon, X, ShieldAlert, CheckCircle2, Loader2 } from 'lucide-react';
import { Agent } from '../../types';

interface KillSwitchModalProps {
  isOpen: boolean;
  onClose: () => void;
  agents: Agent[];
  onExecuteKill: (agentId: string, reason: string) => Promise<{ elapsed_ms: number; hitl_requests_purged: number; message: string }>;
}

export const KillSwitchModal: React.FC<KillSwitchModalProps> = ({
  isOpen,
  onClose,
  agents,
  onExecuteKill,
}) => {
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0]?.agent_id || 'SupportAgent');
  const [reason, setReason] = useState<string>('indirect_prompt_injection_suspected');
  const [customReason, setCustomReason] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ elapsed_ms: number; hitl_requests_purged: number; message: string } | null>(null);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const finalReason = reason === 'custom' ? customReason : reason;
      const res = await onExecuteKill(selectedAgentId, finalReason);
      setResult(res);
    } catch (e: any) {
      alert(`Kill switch failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-[#0F1420] border border-[#2B364D] rounded-xl shadow-modal max-w-lg w-full p-6 text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#1E2638]">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">
                Emergency Kill Switch Cascade
              </h2>
              <p className="text-xs text-slate-400">Immediate Isolation &amp; Token Revocation</p>
            </div>
          </div>
          <button
            onClick={() => {
              setResult(null);
              onClose();
            }}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#1A2234]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        {result ? (
          <div className="py-6 space-y-4">
            <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-500/30 flex items-start space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-sm text-emerald-300">Kill Switch Successfully Executed</p>
                <p className="text-xs text-slate-300 mt-1">{result.message}</p>
                <div className="mt-3 flex items-center space-x-4 text-xs font-mono">
                  <span className="text-emerald-400 font-bold">Elapsed: {result.elapsed_ms}ms</span>
                  <span className="text-slate-400">HITL Purged: {result.hitl_requests_purged}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => {
                setResult(null);
                onClose();
              }}
              className="w-full py-2 rounded-lg bg-[#1E2638] hover:bg-[#2B364D] text-xs font-medium text-slate-200"
            >
              Close
            </button>
          </div>
        ) : (
          <div className="py-5 space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-800/40 text-rose-300/90 leading-relaxed font-sans">
              <strong>Caution:</strong> This operation immediately transitions the agent to SUSPENDED status, blacklists all active JWT bearer tokens in Redis O(1), and purges pending HITL queue items.
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Target AI Agent
              </label>
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#0B0F18] border border-[#2B364D] text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
              >
                {agents.map((a) => (
                  <option key={a.agent_id} value={a.agent_id}>
                    {a.name} ({a.agent_id}) - Status: {a.status}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Revocation Rationale
              </label>
              <div className="space-y-2">
                {[
                  { id: 'indirect_prompt_injection_suspected', label: 'Indirect Prompt Injection Suspected' },
                  { id: 'rapid_policy_violation_spike', label: 'Rapid Policy Violation Velocity Spike (>3/min)' },
                  { id: 'unauthorized_data_exfiltration_attempt', label: 'Unauthorized PII Exfiltration Attempt' },
                  { id: 'operator_manual_override', label: 'Operator Manual Intervention' },
                  { id: 'custom', label: 'Custom Rationale...' },
                ].map((opt) => (
                  <label
                    key={opt.id}
                    className="flex items-center space-x-2 text-slate-300 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name="reason"
                      value={opt.id}
                      checked={reason === opt.id}
                      onChange={() => setReason(opt.id)}
                      className="text-rose-600 focus:ring-rose-500"
                    />
                    <span>{opt.label}</span>
                  </label>
                ))}
              </div>

              {reason === 'custom' && (
                <textarea
                  value={customReason}
                  onChange={(e) => setCustomReason(e.target.value)}
                  placeholder="Provide precise details for the cryptographic audit ledger..."
                  className="mt-2 w-full p-2.5 rounded-lg bg-[#0B0F18] border border-[#2B364D] text-slate-200 text-xs focus:outline-none focus:border-rose-500"
                  rows={2}
                />
              )}
            </div>

            <div className="pt-3 border-t border-[#1E2638] flex items-center justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-[#182030] hover:bg-[#202B40] text-slate-300 font-medium text-xs border border-[#2A374F]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs flex items-center space-x-1.5 shadow-sm disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldAlert className="w-3.5 h-3.5" />}
                <span>Execute Emergency Revocation</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
