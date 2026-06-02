interface VarianceBridgeDatum {
  name: string;
  value: number;
}

interface VarianceBridgeProps {
  data: VarianceBridgeDatum[];
}

export function VarianceBridge({ data }: VarianceBridgeProps) {
  const total = data.reduce((sum, row) => sum + row.value, 0);

  return (
    <div className="panel" style={{ padding: 16 }}>
      <h3 style={{ margin: '0 0 12px' }}>Variance Bridge</h3>
      <div style={{ display: 'grid', gap: 10 }}>
        {data.map((row) => {
          const width = Math.min(100, (Math.abs(row.value) / Math.max(1, Math.abs(total))) * 100);
          return (
            <div key={row.name} style={{ display: 'grid', gridTemplateColumns: '220px 1fr auto', gap: 10, alignItems: 'center' }}>
              <span style={{ color: 'var(--ink-2)' }}>{row.name}</span>
              <div style={{ borderBottom: '1px dotted var(--rule-strong)', position: 'relative', height: 14 }}>
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    bottom: 0,
                    width: `${width}%`,
                    background: row.value > 0 ? 'var(--neg)' : 'var(--pos)',
                  }}
                />
              </div>
              <span className="tabular-nums">{row.value > 0 ? '+' : ''}{row.value.toFixed(1)}K</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
