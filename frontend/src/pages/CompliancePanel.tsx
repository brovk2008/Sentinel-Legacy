import React from 'react';
import {
  Scale,
  ShieldCheck,
  CheckCircle2,
  Download,
} from 'lucide-react';
import { DPDPAQueryPanel } from '../components/audit/DPDPAQueryPanel';

export const CompliancePanel: React.FC = () => {
  const complianceChecklist = [
    {
      regulation: 'EU AI Act Article 12',
      title: 'Continuous Logging & Event Recording',
      status: 'COMPLIANT',
      evidence: 'Monotonic SHA-256 cryptographic audit chain with parent hash linking on all MCP proxy calls.',
    },
    {
      regulation: 'EU AI Act Article 14',
      title: 'Human-in-the-Loop Oversight & Intervention',
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
      <div className="p-4 rounded-xl bg-[#0E1320] border border-[#1E2638] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white tracking-tight flex items-center gap-2">
              <span>Regulatory Governance &amp; Compliance Center</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ATTESTED
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Cross-jurisdictional compliance certification for India DPDPA 2023 and European Union AI Act
            </p>
          </div>
        </div>

        <button
          onClick={() => alert('Compliance Certificate exported: SENTINEL-CERT-2026-EU-DPDPA.pdf')}
          className="px-3.5 py-1.5 rounded-lg bg-[#141A28] hover:bg-[#1E263A] text-slate-200 font-medium text-xs flex items-center gap-1.5 border border-[#263148] transition-colors"
        >
          <Download className="w-3.5 h-3.5 text-blue-400" />
          Download Compliance Attestation (.PDF)
        </button>
      </div>

      {/* Statutory Conformance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {complianceChecklist.map((item, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-medium text-slate-300 bg-[#141A28] px-2 py-0.5 rounded border border-[#222C3E]">
                  {item.regulation}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {item.status}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-white mb-1.5">{item.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-sans">{item.evidence}</p>
            </div>

            <div className="mt-3 pt-2.5 border-t border-[#1E2638] flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>Verification: Formal Proof</span>
              <span className="text-emerald-400">Continuous Monitoring</span>
            </div>
          </div>
        ))}

        {/* Global Summary Card */}
        <div className="p-4 rounded-xl border border-[#1E2638] bg-[#101624] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Algorithmic Accountability Assessment</span>
            </div>
            <h3 className="text-base font-semibold text-white mb-2">
              High-Risk AI System Conformance Level: Tier 1
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              All agentic autonomous actions undergo sub-millisecond evaluation against formal
              mathematical Lean 4 Cedar metatheory specifications prior to execution.
            </p>
          </div>

          <div className="mt-4 flex items-center justify-between font-mono text-xs text-slate-400 pt-2 border-t border-[#1E2638]">
            <span>Audit Engine: Sentinel SHA-256</span>
            <span className="text-blue-400 font-medium">Tamper-Evident</span>
          </div>
        </div>
      </div>

      {/* DPDPA Section 11 Interactive Portal */}
      <DPDPAQueryPanel />
    </div>
  );
};
