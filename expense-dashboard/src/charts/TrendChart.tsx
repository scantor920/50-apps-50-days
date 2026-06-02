import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TrendPoint } from '../data/types';

interface TrendChartProps {
  data: TrendPoint[];
}

export function TrendChart({ data }: TrendChartProps) {
  return (
    <div className="panel" style={{ padding: 16 }}>
      <h3 style={{ margin: '0 0 12px' }}>Trend</h3>
      <div style={{ height: 260 }}>
        <ResponsiveContainer>
          <AreaChart data={data}>
            <CartesianGrid stroke="var(--rule)" strokeDasharray="3 3" />
            <XAxis dataKey="period" stroke="var(--ink-3)" />
            <YAxis stroke="var(--ink-3)" />
            <Tooltip />
            <Area type="monotone" dataKey="actual" fill="var(--accent)" fillOpacity={0.16} stroke="none" />
            <Line type="monotone" dataKey="actual" stroke="var(--accent)" strokeWidth={2.4} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="budget" stroke="var(--ink-3)" strokeDasharray="6 4" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
