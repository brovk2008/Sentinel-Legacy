import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, XCircle, Info } from 'lucide-react';
import { TrustScoreBreakdown } from '../../types';

interface TrustScoreGaugeProps {
  score: number;
  status: string;
  breakdown?: TrustScoreBreakdown;
  size?: number;
}

export const TrustScoreGauge: React.FC<TrustScoreGaugeProps> = ({
  score,
  status,
  breakdown,
  size = 190,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Score 0-1000 mapping
  const normalizedScore = Math.max(0, Math.min(1000, score));
  const percentage = (normalizedScore / 1000) * 100;

  // Professional semantic colors & tier labels
  let strokeColor = '#10B981'; // Balanced Emerald
  let tierLabel = 'Full Autonomy';
  let tierBadge = 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
  let StatusIcon = ShieldCheck;

  if (normalizedScore < 400) {
    strokeColor = '#EF4444'; // Red
    tierLabel = 'Autonomy Revoked';
    tierBadge = 'border-rose-500/30 bg-rose-500/10 text-rose-400';
    StatusIcon = XCircle;
  } else if (normalizedScore < 600) {
    strokeColor = '#F97316'; // Orange
    tierLabel = 'Escalation Required';
    tierBadge = 'border-orange-500/30 bg-orange-500/10 text-orange-400';
    StatusIcon = AlertTriangle;
  } else if (normalizedScore < 800) {
    strokeColor = '#F59E0B'; // Amber
    tierLabel = 'Restricted / Monitored';
    tierBadge = 'border-amber-500/30 bg-amber-500/10 text-amber-400';
    StatusIcon = ShieldAlert;
  }

  // SVG parameters
  const strokeWidth = 12;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center relative">
      <div
        className="relative flex items-center justify-center cursor-pointer group"
        style={{ width: size, height: size }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
      >
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#1E2638"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeLinecap="round"
          />
          {/* Progress Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.8s ease-in-out, stroke 0.4s ease',
            }}
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="flex items-baseline space-x-1">
            <span className="text-3xl font-extrabold text-white font-mono tracking-tight">
              {Math.round(score)}
            </span>
            <span className="text-xs text-slate-500 font-mono">/ 1000</span>
          </div>
          <div className="text-[11px] font-medium text-slate-400 mt-1 uppercase tracking-wider flex items-center gap-1">
            <StatusIcon className="w-3.5 h-3.5" style={{ color: strokeColor }} />
            <span>{status}</span>
          </div>
        </div>

        {/* Info Icon Indicator */}
        <div className="absolute bottom-2 right-2 p-1 rounded-full bg-[#161D2B] border border-[#2B364D] text-slate-400 group-hover:text-blue-400 transition-colors">
          <Info className="w-3 h-3" />
        </div>
      </div>

      {/* Tier Label */}
      <div className={`mt-3 px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-1.5 shadow-sm ${tierBadge}`}>
        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: strokeColor }} />
        <span>{tierLabel}</span>
      </div>

      {/* Breakdown Tooltip */}
      {showTooltip && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-72 p-4 rounded-xl bg-[#0F1420] border border-[#2B364D] shadow-modal z-50 text-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#1E2638]">
            <span className="font-semibold text-white flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
              Trust Score Breakdown
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Continuous</span>
          </div>

          <div className="space-y-2 font-mono text-[11px]">
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Base Score:</span>
              <span className="text-white font-semibold">
                {breakdown ? breakdown.base_score : 800}
              </span>
            </div>

            <div className="flex justify-between items-center text-emerald-400">
              <span>+ Actions ({breakdown?.success_count ?? 0} × 0.5):</span>
              <span>+{(breakdown?.success_contribution ?? 0).toFixed(1)}</span>
            </div>

            <div className="flex justify-between items-center text-rose-400">
              <span>- Violations ({breakdown?.violation_count ?? 0} × 150):</span>
              <span>-{(breakdown?.violation_penalty ?? 0).toFixed(1)}</span>
            </div>

            <div className="flex justify-between items-center text-amber-400">
              <span>- HITL Rejections ({breakdown?.rejection_count ?? 0} × 50):</span>
              <span>-{(breakdown?.rejection_penalty ?? 0).toFixed(1)}</span>
            </div>

            {breakdown?.temporal_decay_adjustment !== undefined && breakdown.temporal_decay_adjustment !== 0 && (
              <div className="flex justify-between items-center text-slate-400">
                <span>Decay Adjustment:</span>
                <span>{breakdown.temporal_decay_adjustment.toFixed(1)}</span>
              </div>
            )}

            <div className="pt-2 mt-2 border-t border-[#1E2638] flex justify-between items-center text-white font-bold text-xs">
              <span>Total Calculated:</span>
              <span className="font-mono" style={{ color: strokeColor }}>
                {Math.round(breakdown?.total ?? score)} / 1000
              </span>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-[#1E2638] text-[10px] text-slate-400">
            Formula: T(t) = T_base + Σ S - Σ V_pen - Σ R_pen - λΔt
          </div>
        </div>
      )}
    </div>
  );
};
