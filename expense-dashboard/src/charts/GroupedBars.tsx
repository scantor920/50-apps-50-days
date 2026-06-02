import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface GroupedBarsDatum {
  id: string;
  name: string;
  actual: number;
  budget: number;
  prior: number;
}

interface GroupedBarsProps {
  data: GroupedBarsDatum[];
  mode: 'budget' | 'prior';
  onBarClick?: (id: string) => void;
}

export function GroupedBars({ data, mode, onBarClick }: GroupedBarsProps) {
  const compareKey = mode === 'budget' ? 'budget' : 'prior';

  return (
    <div className="panel" style={{ padding: 16 }}>
      <h3 style={{ margin: '0 0 12px' }}>Actual vs {mode === 'budget' ? 'Budget' : 'Prior Year'}</h3>
      <div style={{ height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid stroke="var(--rule)" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="var(--ink-3)" />
            <YAxis stroke="var(--ink-3)" />
            <Tooltip />
            <Bar dataKey="actual" fill="var(--accent)" onClick={(entry) => onBarClick?.(entry.id)} />
            <Bar dataKey={compareKey} fill="var(--ink-3)" fillOpacity={0.45} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
