import clsx from 'clsx';
import { formatPercent } from '../lib/formatters';

interface VariancePillProps {
  value: number;
  mode: 'budget' | 'prior';
  isPercent: boolean;
}

function getPresentation(value: number, mode: 'budget' | 'prior'): { tone: 'pos' | 'neg' | 'flat'; arrow: string } {
  if (mode === 'budget') {
    return value > 0 ? { tone: 'neg', arrow: '▲' } : { tone: 'pos', arrow: '▼' };
  }

  if (Math.abs(value) < 0.5) {
    return { tone: 'flat', arrow: '■' };
  }
  return value > 0 ? { tone: 'neg', arrow: '▲' } : { tone: 'pos', arrow: '▼' };
}

export function VariancePill({ value, mode, isPercent }: VariancePillProps) {
  const { tone, arrow } = getPresentation(value, mode);
  const absValue = Math.abs(value);
  const labelValue = isPercent ? formatPercent(absValue) : `$${absValue.toFixed(1)}K`;
  const sign = value > 0 ? '+' : value < 0 ? '-' : '±';

  return (
    <span
      aria-label={`${sign} ${labelValue} versus ${mode === 'budget' ? 'budget' : 'prior year'}`}
      className={clsx('tabular-nums', `tone-${tone}`)}
      style={{
        borderRadius: 999,
        border: '1px solid var(--rule)',
        padding: '4px 10px',
        fontSize: 12,
        fontWeight: 700,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        background: tone === 'pos' ? 'var(--pos-soft)' : tone === 'neg' ? 'var(--neg-soft)' : 'var(--bg-sunk)',
        color: tone === 'pos' ? 'var(--pos)' : tone === 'neg' ? 'var(--neg)' : 'var(--ink-3)',
      }}
    >
      <span aria-hidden>{arrow}</span>
      <span>{`${sign}${labelValue}`}</span>
    </span>
  );
}
