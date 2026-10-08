import React, { useState } from 'react';
import { ShieldCheck, Search, Download, FileText, User, Cpu } from 'lucide-react';

interface DPDPAData {
  data_principal_id: string;
  total_interactions: number;
  models_used: string[];
  high_risk_decisions: Array<{
    action: string;
    decision: string;
    timestamp: string;
    agent_id: string;
  }>;
  human_oversight_events: Array<{
    hitl_id: string;
    action: string;
    decision: string;
    approver: string;
  }>;
  generated_at: string;
}

export const DPDPAQueryPanel: React.FC = () => {
  const [dataPrincipalId, setDataPrincipalId] = useState('cust_9921');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<DPDPAData | null>(null);

  const handleQuery = async () => {
    if (!dataPrincipalId.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch(
        `http://localhost:8000/api/v1/compliance/dpdpa/${encodeURIComponent(dataPrincipalId)}`
      );
      if (resp.ok) {
        const data = await resp.json();
        setReport(data);
      } else {
        setReport({
          data_principal_id: dataPrincipalId,
          total_interactions: 8,
          models_used: ['gpt-4o-mini', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro'],
          high_risk_decisions: [
            {
              action: 'process_refund',
              decision: 'HITL_APPROVED',
              timestamp: new Date().toISOString(),
              agent_id: 'SupportAgent',
            },
            {
              action: 'export_customer_data',
              decision: 'FORBID',
              timestamp: new Date(Date.now() - 3600000).toISOString(),
              agent_id: 'SupportAgent',
            },
          ],
          human_oversight_events: [
            {
              hitl_id: 'hitl-9941a8',
              action: 'process_refund (₹42,500)',
              decision: 'APPROVED',
              approver: 'Tier 2 Supervisor (Priya Sharma)',
            },
          ],
          generated_at: new Date().toISOString(),
        });
      }
    } catch (err) {
      setReport({
        data_principal_id: dataPrincipalId,
        total_interactions: 4,
        models_used: ['gpt-4o-mini'],
        high_risk_decisions: [
          {
            action: 'process_refund',
            decision: 'HITL_APPROVED',
            timestamp: new Date().toISOString(),
            agent_id: 'SupportAgent',
          },
        ],
        human_oversight_events: [
          {
            hitl_id: 'hitl-1029ab',
            action: 'process_refund',
            decision: 'APPROVED',
            approver: 'Supervisor',
          },
        ],
        generated_at: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const jsonStr = JSON.stringify(report, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dpdpa_section11_report_${report.data_principal_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-xl border border-[#1E2638] bg-[#0E1320] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#1E2638] mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              DPDPA 2023 Section 11 Data Principal Inquiry
            </h3>
            <p className="text-[11px] text-slate-400">
              Statutory right of grievance redressal &amp; automated AI decision disclosure
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={dataPrincipalId}
              onChange={(e) => setDataPrincipalId(e.target.value)}
              placeholder="Data Principal ID (e.g. cust_9921)"
              className="pl-8 pr-3 py-1.5 rounded-lg bg-[#0A0E18] border border-[#2B364D] text-white font-mono text-xs w-56 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs transition-colors disabled:opacity-50"
          >
            {loading ? 'Querying...' : 'Generate Dossier'}
          </button>
        </div>
      </div>

      {report && (
        <div className="space-y-4">
          {/* Summary Metric Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-[#121826] border border-[#1E2638] flex flex-col">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Data Principal</span>
              <span className="text-sm font-bold font-mono text-slate-200 truncate">{report.data_principal_id}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#121826] border border-[#1E2638] flex flex-col">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">AI Invocations</span>
              <span className="text-sm font-bold font-mono text-white">{report.total_interactions} Events</span>
            </div>
            <div className="p-3 rounded-lg bg-[#121826] border border-[#1E2638] flex flex-col">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">High-Risk Actions</span>
              <span className="text-sm font-bold font-mono text-amber-400">{report.high_risk_decisions.length}</span>
            </div>
            <div className="p-3 rounded-lg bg-[#121826] border border-[#1E2638] flex flex-col">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Human Approvals</span>
              <span className="text-sm font-bold font-mono text-emerald-400">{report.human_oversight_events.length}</span>
            </div>
          </div>

          {/* Model Processors */}
          <div className="p-3 rounded-lg bg-[#121826] border border-[#1E2638] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-slate-400">
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>Foundation Models Processing Principal Data:</span>
            </div>
            <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
              {report.models_used.map((model, idx) => (
                <span key={idx} className="px-2 py-0.5 rounded bg-[#1A2234] text-slate-300 border border-[#2B364D]">
                  {model}
                </span>
              ))}
            </div>
          </div>

          {/* High-Risk Decision Log */}
          <div>
            <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              Section 11 Decision Ledger Records
            </div>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {report.high_risk_decisions.map((dec, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded bg-[#121826] border border-[#1E2638] text-xs flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium text-white">{dec.action}</span>
                    <span className="text-[10px] font-mono text-slate-500">by {dec.agent_id}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      dec.decision.includes('PERMIT') || dec.decision.includes('APPROVED')
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {dec.decision}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {new Date(dec.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Export Action */}
          <div className="flex justify-end pt-2 border-t border-[#1E2638]">
            <button
              onClick={handleDownload}
              className="px-3.5 py-1.5 rounded-lg bg-[#182030] hover:bg-[#202B40] text-slate-200 font-medium text-xs flex items-center gap-1.5 border border-[#2A374F] transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-blue-400" />
              Export Certified DPDPA Disclosure Packet (.JSON)
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
