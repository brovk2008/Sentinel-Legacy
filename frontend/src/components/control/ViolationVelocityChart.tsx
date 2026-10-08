import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { Activity } from 'lucide-react';

interface VelocityPoint {
  time: string;
  violations: number;
  threshold: number;
}

interface ViolationVelocityChartProps {
  data?: VelocityPoint[];
}

export const ViolationVelocityChart: React.FC<ViolationVelocityChartProps> = ({ data }) => {
  const defaultData: VelocityPoint[] = [
    { time: '14:00', violations: 0, threshold: 3 },
    { time: '14:05', violations: 0, threshold: 3 },
    { time: '14:10', violations: 1, threshold: 3 },
    { time: '14:15', violations: 1, threshold: 3 },
    { time: '14:20', violations: 0, threshold: 3 },
    { time: '14:25', violations: 2, threshold: 3 },
    { time: '14:30', violations: 4, threshold: 3 }, // Spike above threshold
    { time: '14:35', violations: 2, threshold: 3 },
    { time: '14:40', violations: 1, threshold: 3 },
    { time: '14:45', violations: 0, threshold: 3 },
    { time: '14:50', violations: 0, threshold: 3 },
    { time: '14:55', violations: 0, threshold: 3 },
  ];

  const chartData = data && data.length > 0 ? data : defaultData;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 backdrop-blur-sm flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold text-white">
            Violation Velocity (Sliding 60-Sec Window)
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-0.5 bg-rose-500 inline-block" />
            <span>Critical Threshold (&gt; 3/min)</span>
          </div>
          <div className="flex items-center gap-1.5 text-cyan-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
            <span>Violations</span>
          </div>
        </div>
      </div>

      <div className="w-full h-56 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="violationGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis
              dataKey="time"
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
              domain={[0, 6]}
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
              formatter={(val: any) => [`${val} violations`, 'Rate']}
            />
            <ReferenceLine
              y={3}
              stroke="#EF4444"
              strokeDasharray="4 4"
              label={{
                value: 'KILL SWITCH TRIGGER',
                fill: '#EF4444',
                fontSize: 9,
                position: 'insideTopRight',
              }}
            />
            <Area
              type="monotone"
              dataKey="violations"
              stroke="#EF4444"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#violationGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span>Window: 60s sliding counter per RFC 8707 agent identity</span>
        <span>Detection Engine: Sentinel Redis Velocity Tracker</span>
      </div>
    </div>
  );
};
