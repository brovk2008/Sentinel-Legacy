import React from 'react';
import { CheckCircle2, XCircle, Clock, Shield, ArrowUpRight } from 'lucide-react';

export interface ActivityItem {
  id: string;
  action: string;
  resource_id: string;
  decision: 'PERMIT' | 'FORBID' | 'HITL_PAUSED';
  policy_id?: string;
  latency_ms: number;
  timestamp: string;
}

interface RecentActivityProps {
  activities?: ActivityItem[];
}

export const RecentActivity: React.FC<RecentActivityProps> = ({ activities }) => {
  const defaultActivities: ActivityItem[] = [
    {
      id: 'act-1',
      action: 'process_refund',
      resource_id: 'cust-9921 / ord-441',
      decision: 'HITL_PAUSED',
      policy_id: 'REFUND-001',
      latency_ms: 1.2,
      timestamp: '2 mins ago',
    },
    {
      id: 'act-2',
      action: 'read_order_history',
      resource_id: 'cust-9921',
      decision: 'PERMIT',
      policy_id: 'BASE-001',
      latency_ms: 0.9,
      timestamp: '5 mins ago',
    },
    {
      id: 'act-3',
      action: 'export_customer_data',
      resource_id: 'cust-pii-batch-1',
      decision: 'FORBID',
      policy_id: 'DATA-012',
      latency_ms: 1.4,
      timestamp: '18 mins ago',
    },
    {
      id: 'act-4',
      action: 'update_shipping_address',
      resource_id: 'ord-3392',
      decision: 'PERMIT',
      policy_id: 'BASE-002',
      latency_ms: 1.1,
      timestamp: '42 mins ago',
    },
    {
      id: 'act-5',
      action: 'process_refund',
      resource_id: 'ord-1102 (₹2,500)',
      decision: 'PERMIT',
      policy_id: 'REFUND-001',
      latency_ms: 0.8,
      timestamp: '1 hour ago',
    },
  ];

  const items = activities && activities.length > 0 ? activities : defaultActivities;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold text-white">Recent Execution History</span>
        </div>
        <span className="text-[11px] font-mono text-slate-500">Live Evaluation Feed</span>
      </div>

      <div className="space-y-2">
        {items.map((item) => {
          let badgeStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
          let DecisionIcon = CheckCircle2;
          let label = 'PERMIT';

          if (item.decision === 'FORBID') {
            badgeStyle = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
            DecisionIcon = XCircle;
            label = 'FORBID';
          } else if (item.decision === 'HITL_PAUSED') {
            badgeStyle = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
            DecisionIcon = ArrowUpRight;
            label = 'HITL PAUSE';
          }

          return (
            <div
              key={item.id}
              className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold flex items-center gap-1 ${badgeStyle}`}>
                  <DecisionIcon className="w-3 h-3" />
                  {label}
                </span>

                <div className="flex flex-col">
                  <span className="font-mono font-semibold text-slate-200">
                    {item.action}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 truncate max-w-xs">
                    {item.resource_id}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {item.policy_id && (
                  <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-cyan-400/80 bg-cyan-950/30 px-1.5 py-0.5 rounded border border-cyan-800/40">
                    <Shield className="w-2.5 h-2.5" />
                    {item.policy_id}
                  </span>
                )}
                <span className="text-[10px] font-mono text-slate-400">
                  {item.latency_ms}ms
                </span>
                <span className="text-[10px] text-slate-500 min-w-[65px] text-right">
                  {item.timestamp}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
