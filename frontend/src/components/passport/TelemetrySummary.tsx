import React from 'react';
import { Activity, Zap, DollarSign, Clock, ShieldAlert, Users } from 'lucide-react';

interface TelemetryData {
  totalActions: number;
  totalTokens: number;
  estimatedCostUsd: number;
  avgLatencyMs: number;
  violationCount: number;
  hitlCount: number;
}

interface TelemetrySummaryProps {
  telemetry?: TelemetryData;
}

export const TelemetrySummary: React.FC<TelemetrySummaryProps> = ({ telemetry }) => {
  const data: TelemetryData = telemetry || {
    totalActions: 1420,
    totalTokens: 894500,
    estimatedCostUsd: 17.89,
    avgLatencyMs: 1.4,
    violationCount: 2,
    hitlCount: 14,
  };

  const cards = [
    {
      title: 'Invocations',
      value: data.totalActions.toLocaleString(),
      subtitle: '30-day evaluated requests',
      icon: Activity,
      color: 'text-blue-400',
    },
    {
      title: 'Token Usage',
      value: `${(data.totalTokens / 1000).toFixed(1)}k`,
      subtitle: 'Prompt + Completion',
      icon: Zap,
      color: 'text-indigo-400',
    },
    {
      title: 'Attributed Cost',
      value: `$${data.estimatedCostUsd.toFixed(2)}`,
      subtitle: 'OpenTelemetry gen_ai.cost',
      icon: DollarSign,
      color: 'text-emerald-400',
    },
    {
      title: 'Policy Latency',
      value: `${data.avgLatencyMs.toFixed(1)} ms`,
      subtitle: 'Cedar evaluation time',
      icon: Clock,
      color: 'text-slate-300',
    },
    {
      title: 'Violations Blocked',
      value: data.violationCount.toString(),
      subtitle: 'Cedar forbid triggers',
      icon: ShieldAlert,
      color: data.violationCount > 0 ? 'text-rose-400' : 'text-slate-400',
    },
    {
      title: 'HITL Escalations',
      value: data.hitlCount.toString(),
      subtitle: 'Human approval requests',
      icon: Users,
      color: 'text-amber-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="p-3.5 rounded-xl border border-[#1E2638] bg-[#0E1320] flex flex-col justify-between"
          >
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-[11px] font-medium tracking-wide uppercase">{card.title}</span>
              <Icon className={`w-4 h-4 ${card.color}`} />
            </div>
            <div>
              <div className="text-xl font-bold font-mono text-white tracking-tight">
                {card.value}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 truncate">
                {card.subtitle}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
