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
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0]?.agent_id || 'agt_7a3f9c2d8e1b');
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0B111D] border border-red-500/50 rounded-xl shadow-2xl max-w-lg w-full p-6 text-slate-100 cyber-border-red">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3 text-red-400">
            <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/30">
              <AlertOctagon className="w-6 h-6 text-red-500 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-bold uppercase tracking-wider text-red-400">
                EMERGENCY KILL SWITCH
              </h2>
              <p className="text-xs text-slate-400 font-mono">Immediate Isolation & Token Revocation</p>
            </div>
          </div>
          <button
            onClick={() => {
              setResult(null);
              onClose();
            }}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        {result ? (
          <div className="py-6 space-y-4">
            <div className="p-4 rounded-lg bg-emerald-950/40 border border-emerald-500/40 flex items-start space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-sm text-emerald-300">KILL SWITCH CASCADE EXECUTED</p>
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
              className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold uppercase tracking-wider text-slate-200"
            >
              CLOSE
            </button>
          </div>
        ) : (
          <div className="py-5 space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-red-950/30 border border-red-800/40 text-red-300/90 leading-relaxed font-mono">
              ⚠️ WARNING: This will immediately set the agent's status to SUSPENDED, revoke all past and future Bearer tokens in Redis O(1), and purge the pending HITL approval queue.
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5 font-mono">
                Target AI Agent
              </label>
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-xs font-mono focus:border-red-500 focus:outline-none"
              >
                {agents.map((a) => (
                  <option key={a.agent_id} value={a.agent_id}>
                    {a.name} ({a.role} · Status: {a.status})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5 font-mono">
                Security Rationale
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-xs font-mono focus:border-red-500 focus:outline-none"
              >
                <option value="indirect_prompt_injection_suspected">
                  Indirect Prompt Injection Suspected (ASI01)
                </option>
                <option value="privilege_escalation_attempt">
                  Multi-Agent Privilege Escalation (ASI07 / ASI08)
                </option>
                <option value="data_exfiltration_anomaly">
                  Rogue Agent & Data Exfiltration (ASI10)
                </option>
                <option value="threshold_velocity_breached">
                  Violation Velocity Threshold Breached (3 in 5 min)
                </option>
                <option value="custom">Other / Custom Rationale</option>
              </select>
            </div>

            {reason === 'custom' && (
              <div>
                <input
                  type="text"
                  placeholder="Enter specific incident rationale..."
                  value={customReason}
                  onChange={(e) => setCustomReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-xs font-mono focus:border-red-500 focus:outline-none"
                />
              </div>
            )}

            <div className="pt-2 flex items-center space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 font-semibold"
              >
                CANCEL
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={loading}
                className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold uppercase tracking-wider flex items-center justify-center space-x-2 shadow-glow-red"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>REVOKING...</span>
                  </>
                ) : (
                  <>
                    <AlertOctagon className="w-4 h-4" />
                    <span>CONFIRM KILL</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
