interface CompositionDatum {
  id: string;
  name: string;
  amount: number;
}

interface CompositionBarProps {
  data: CompositionDatum[];
}

const colors = ['var(--accent)', 'var(--accent-2)', 'var(--gold)', 'var(--warn)', 'var(--ink-3)'];

export function CompositionBar({ data }: CompositionBarProps) {
  const total = data.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="panel" style={{ padding: 16 }}>
      <h3 style={{ margin: '0 0 12px' }}>Composition</h3>
      <div style={{ height: 18, borderRadius: 999, overflow: 'hidden', display: 'flex' }}>
        {data.map((item, index) => (
          <div key={item.id} style={{ width: `${(item.amount / Math.max(total, 1)) * 100}%`, background: colors[index % colors.length] }} />
        ))}
      </div>
      <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
        {data.map((item) => (
          <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--ink-2)' }}>
            <span>{item.name}</span>
            <span className="tabular-nums">${item.amount.toFixed(1)}K</span>
          </div>
        ))}
      </div>
    </div>
  );
}
