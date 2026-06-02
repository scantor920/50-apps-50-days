interface RowBarProps {
  value: number;
}

export function RowBar({ value }: RowBarProps) {
  const width = Math.max(0, Math.min(100, value));

  return (
    <div style={{ height: 8, background: 'var(--bg-sunk)', borderRadius: 999, overflow: 'hidden' }}>
      <div
        style={{
          width: `${width}%`,
          height: '100%',
          background: 'linear-gradient(90deg, var(--accent), var(--accent-2))',
        }}
      />
    </div>
  );
}
