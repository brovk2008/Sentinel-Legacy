import React, { useState } from 'react';
import { FileText, Shield, Filter, Search, Download, Layers } from 'lucide-react';
import { AuditEntry } from '../types';
import { AuditTimeline } from '../components/audit/AuditTimeline';
import { ChainVerifier } from '../components/audit/ChainVerifier';
import { DPDPAQueryPanel } from '../components/audit/DPDPAQueryPanel';

interface AuditInvestigationProps {
  entries: AuditEntry[];
}

export const AuditInvestigation: React.FC<AuditInvestigationProps> = ({ entries }) => {
  const [selectedAgent, setSelectedAgent] = useState<string>('ALL');
  const [selectedDecision, setSelectedDecision] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredEntries = entries.filter((entry) => {
    if (selectedAgent !== 'ALL' && entry.agent_id !== selectedAgent) return false;
    if (selectedDecision !== 'ALL' && entry.decision !== selectedDecision) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        entry.action.toLowerCase().includes(q) ||
        entry.resource_id.toLowerCase().includes(q) ||
        entry.entry_hash.toLowerCase().includes(q) ||
        entry.agent_id.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  const uniqueAgents = Array.from(new Set(entries.map((e) => e.agent_id)));

  const handleExportJson = () => {
    const jsonStr = JSON.stringify(entries, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sentinel_audit_ledger_full_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Top Header Strip */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span>Cryptographic Audit &amp; Forensic Ledger</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                SHA-256 TAMPER-EVIDENT
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Zero-knowledge verifiable decision chain satisfying RFC 6962 and EU AI Act Art. 12
            </p>
          </div>
        </div>

        <button
          onClick={handleExportJson}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center gap-1.5 border border-slate-700 transition-colors"
        >
          <Download className="w-3.5 h-3.5 text-cyan-400" />
          Export Ledger (.JSON)
        </button>
      </div>

      {/* Chain Verifier Component */}
      <ChainVerifier />

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          {/* Agent Filter */}
          <div className="flex items-center gap-1.5 text-slate-400">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Agent:</span>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Agents</option>
              {uniqueAgents.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>

          {/* Decision Filter */}
          <div className="flex items-center gap-1.5 text-slate-400">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <span>Decision:</span>
            <select
              value={selectedDecision}
              onChange={(e) => setSelectedDecision(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Decisions</option>
              <option value="PERMIT">PERMIT</option>
              <option value="FORBID">FORBID</option>
              <option value="HITL_PAUSED">HITL_PAUSED</option>
            </select>
          </div>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search action, resource, hash..."
            className="pl-8 pr-3 py-1 rounded-lg bg-slate-950 border border-slate-700 text-white font-mono text-xs w-64 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Main Timeline */}
      <AuditTimeline entries={filteredEntries} />

      {/* DPDPA 2023 Statutory Query Section */}
      <DPDPAQueryPanel />
    </div>
  );
};
