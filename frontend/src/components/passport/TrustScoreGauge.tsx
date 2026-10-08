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
  size = 200,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Score 0-1000 mapping
  const normalizedScore = Math.max(0, Math.min(1000, score));
  const percentage = (normalizedScore / 1000) * 100;

  // Colors & Tier calculation
  let strokeColor = '#10B981'; // Green
  let glowColor = 'rgba(16, 185, 129, 0.4)';
  let tierLabel = 'Full Autonomy';
  let tierBadge = 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
  let StatusIcon = ShieldCheck;

  if (normalizedScore < 400) {
    strokeColor = '#EF4444'; // Red
    glowColor = 'rgba(239, 68, 68, 0.4)';
    tierLabel = 'Autonomy Revoked';
    tierBadge = 'border-rose-500/30 bg-rose-500/10 text-rose-400';
    StatusIcon = XCircle;
  } else if (normalizedScore < 600) {
    strokeColor = '#F97316'; // Orange
    glowColor = 'rgba(249, 115, 22, 0.4)';
    tierLabel = 'Escalation Required';
    tierBadge = 'border-orange-500/30 bg-orange-500/10 text-orange-400';
    StatusIcon = AlertTriangle;
  } else if (normalizedScore < 800) {
    strokeColor = '#F59E0B'; // Amber
    glowColor = 'rgba(245, 158, 11, 0.4)';
    tierLabel = 'Restricted / Monitored';
    tierBadge = 'border-amber-500/30 bg-amber-500/10 text-amber-400';
    StatusIcon = ShieldAlert;
  }

  // SVG parameters
  const strokeWidth = 14;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  // Make gauge a 260-degree arc instead of full circle for dashboard style
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
            stroke="#1E293B"
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
              filter: `drop-shadow(0 0 10px ${glowColor})`,
              transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.5s ease',
            }}
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="flex items-baseline space-x-1">
            <span className="text-4xl font-extrabold text-white font-mono tracking-tight drop-shadow-md">
              {Math.round(score)}
            </span>
            <span className="text-xs text-slate-500 font-mono">/ 1000</span>
          </div>
          <div className="text-[11px] font-semibold text-slate-400 mt-1 uppercase tracking-wider flex items-center gap-1">
            <StatusIcon className="w-3.5 h-3.5" style={{ color: strokeColor }} />
            <span>{status}</span>
          </div>
        </div>

        {/* Info Icon Indicator */}
        <div className="absolute bottom-2 right-2 p-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-400 group-hover:text-cyan-400 transition-colors">
          <Info className="w-3 h-3" />
        </div>
      </div>

      {/* Tier Label */}
      <div className={`mt-3 px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-1.5 shadow-sm ${tierBadge}`}>
        <span className="w-1.5 h-1.5 rounded-full animate-ping" style={{ backgroundColor: strokeColor }} />
        <span>{tierLabel}</span>
      </div>

      {/* Breakdown Tooltip / Modal */}
      {showTooltip && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-72 p-4 rounded-xl bg-slate-900/95 border border-slate-700/80 backdrop-blur-md shadow-2xl z-50 text-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <span className="font-semibold text-white flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              Trust Score Breakdown
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Real-time</span>
          </div>

          <div className="space-y-2 font-mono text-[11px]">
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Base Sovereign Score:</span>
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

            <div className="pt-2 mt-2 border-t border-slate-800 flex justify-between items-center text-white font-bold text-xs">
              <span>Total Calculated:</span>
              <span className="font-mono" style={{ color: strokeColor }}>
                {Math.round(breakdown?.total ?? score)} / 1000
              </span>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 italic">
            Deterministic formula: T(t) = T_base + Σ S - Σ V_pen - Σ R_pen - λΔt
          </div>
        </div>
      )}
    </div>
  );
};
