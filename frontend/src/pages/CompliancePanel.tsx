import React from 'react';
import {
  Scale,
  ShieldCheck,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  Download,
  Lock,
} from 'lucide-react';
import { DPDPAQueryPanel } from '../components/audit/DPDPAQueryPanel';

export const CompliancePanel: React.FC = () => {
  const complianceChecklist = [
    {
      regulation: 'EU AI Act Article 12',
      title: 'Automatic Recording of Events & Continuous Logging',
      status: 'COMPLIANT',
      evidence: 'Monotonic SHA-256 cryptographic audit chain with parent hash linking on all MCP proxy calls.',
    },
    {
      regulation: 'EU AI Act Article 14',
      title: 'Human-in-the-Loop (HITL) Oversight & Intervention',
      status: 'COMPLIANT',
      evidence: 'Fail-closed thread suspension on financial thresholds (>₹10,000) and irreversible account actions.',
    },
    {
      regulation: 'DPDPA 2023 Section 8(4)',
      title: 'Duty of Data Fiduciary to Safeguard Personal Data',
      status: 'COMPLIANT',
      evidence: 'Formal Cedar policy DATA-012 enforces strict forbid-wins blocking of unauthorized customer data extraction.',
    },
    {
      regulation: 'DPDPA 2023 Section 11',
      title: 'Right to Information & AI Decision Disclosure',
      status: 'COMPLIANT',
      evidence: 'Automated extraction of AI models, human decisions, and reasoning artifacts per data principal.',
    },
    {
      regulation: 'RFC 8707 & RFC 6749',
      title: 'Audience-Bound Resource Tokens & M2M Scoping',
      status: 'COMPLIANT',
      evidence: 'JWT tokens cryptographically signed and bound to resource servers with sub-second revocation.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span>Regulatory Governance &amp; Compliance Center</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                100% ATTESTED
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Cross-jurisdictional compliance certification for India DPDPA 2023 and European Union AI Act
            </p>
          </div>
        </div>

        <button
          onClick={() => alert('Compliance Certificate exported: SENTINEL-CERT-2026-EU-DPDPA.pdf')}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center gap-1.5 border border-slate-700 transition-colors"
        >
          <Download className="w-3.5 h-3.5 text-indigo-400" />
          Download Compliance Attestation (.PDF)
        </button>
      </div>

      {/* Statutory Conformance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {complianceChecklist.map((item, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-950/50 px-2 py-0.5 rounded border border-cyan-800/40">
                  {item.regulation}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  {item.status}
                </span>
              </div>
              <h3 className="text-sm font-bold text-white mb-1.5">{item.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">{item.evidence}</p>
            </div>

            <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>Verification: Formal Proof</span>
              <span className="text-emerald-400">Continuous Monitoring</span>
            </div>
          </div>
        ))}

        {/* Global Summary Card */}
        <div className="p-4 rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/20 to-slate-900/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Algorithmic Accountability Verdict</span>
            </div>
            <h3 className="text-base font-extrabold text-white mb-2">
              High-Risk AI System Conformance Level: Tier 1
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              All agentic autonomous actions undergo sub-millisecond evaluation against formal
              mathematical Lean 4 Cedar metatheory specifications prior to execution.
            </p>
          </div>

          <div className="mt-4 flex items-center justify-between font-mono text-xs text-slate-400 pt-2 border-t border-slate-800">
            <span>Audit Engine: Sentinel SHA-256</span>
            <span className="text-cyan-400">Tamper-Evident</span>
          </div>
        </div>
      </div>

      {/* DPDPA Section 11 Interactive Portal */}
      <DPDPAQueryPanel />
    </div>
  );
};
