import { ReactNode } from 'react';

interface KpiTileProps {
  eyebrow: string;
  value: string;
  deltaValue: number;
  deltaMode: 'budget' | 'prior';
  footnote: string;
  onClick?: () => void;
  highlighted?: boolean;
  deltaNode?: ReactNode;
}

export function KpiTile({
  eyebrow,
  value,
  deltaValue,
  deltaMode,
  footnote,
  onClick,
  highlighted,
  deltaNode,
}: KpiTileProps) {
  return (
    <button
      className="panel tabular-nums"
      onClick={onClick}
      type="button"
      style={{
        padding: 16,
        textAlign: 'left',
        cursor: onClick ? 'pointer' : 'default',
        transform: 'translateY(0)',
        transition: 'transform 140ms ease, box-shadow 140ms ease',
        borderTop: highlighted ? '4px solid var(--accent)' : '4px solid transparent',
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-3px)';
          e.currentTarget.style.boxShadow = 'var(--shadow)';
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
      }}
    >
      <div style={{ fontSize: 11, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
        {eyebrow}
      </div>
      <div
        style={{
          marginTop: 10,
          fontFamily: 'Source Serif 4, Georgia, serif',
          fontSize: 34,
          lineHeight: 1.1,
          color: 'var(--ink)',
        }}
      >
        {value}
      </div>
      <div style={{ marginTop: 10, fontSize: 12, color: 'var(--ink-2)' }}>
        {deltaNode ?? `${deltaValue >= 0 ? '+' : '-'}${Math.abs(deltaValue).toFixed(1)}K vs ${deltaMode}`}
      </div>
      <div style={{ marginTop: 12, borderTop: '1px solid var(--rule)', paddingTop: 10, color: 'var(--ink-3)', fontSize: 12 }}>
        {footnote}
      </div>
    </button>
  );
}
