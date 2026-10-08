import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { Zap, DollarSign } from 'lucide-react';

interface AgentUsage {
  agent: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
}

interface TokenCostChartProps {
  data?: AgentUsage[];
}

export const TokenCostChart: React.FC<TokenCostChartProps> = ({ data }) => {
  const defaultData: AgentUsage[] = [
    {
      agent: 'SupportAgent',
      inputTokens: 412000,
      outputTokens: 145000,
      costUsd: 8.92,
    },
    {
      agent: 'SalesAgent',
      inputTokens: 280000,
      outputTokens: 98000,
      costUsd: 5.42,
    },
    {
      agent: 'FinanceAgent',
      inputTokens: 195000,
      outputTokens: 74000,
      costUsd: 4.18,
    },
  ];

  const chartData = data && data.length > 0 ? data : defaultData;
  const totalCost = chartData.reduce((acc, curr) => acc + curr.costUsd, 0);
  const totalTokens = chartData.reduce((acc, curr) => acc + curr.inputTokens + curr.outputTokens, 0);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur-sm flex flex-col h-full">
      <div className="flex flex-wrap items-center justify-between pb-3 border-b border-slate-800 mb-3 gap-2">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold text-white">
            OpenTelemetry GenAI Token &amp; Cost Attribution
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1 text-slate-300">
            <span className="text-slate-500">Total Tokens:</span>
            <span className="text-white font-bold">{(totalTokens / 1000).toFixed(1)}k</span>
          </div>
          <div className="flex items-center gap-1 text-emerald-400 font-bold">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            <span>${totalCost.toFixed(2)}</span>
          </div>
        </div>
      </div>

      <div className="w-full h-56 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis
              dataKey="agent"
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              stroke="#64748B"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0F172A',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '11px',
                fontFamily: 'monospace',
                color: '#F8FAFC',
              }}
              formatter={(value: any, name: string) => {
                if (name === 'Cost ($)') return [`$${Number(value).toFixed(2)}`, name];
                return [`${(Number(value) / 1000).toFixed(1)}k tokens`, name];
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
              iconSize={8}
            />
            <Bar dataKey="inputTokens" name="Prompt Tokens" fill="#06B6D4" radius={[4, 4, 0, 0]} stackId="tokens" />
            <Bar dataKey="outputTokens" name="Completion Tokens" fill="#8B5CF6" radius={[4, 4, 0, 0]} stackId="tokens" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span>Semantic Schema: v1.37 gen_ai.client.token.usage</span>
        <span>Attribution: RFC 8707 Client ID</span>
      </div>
    </div>
  );
};
