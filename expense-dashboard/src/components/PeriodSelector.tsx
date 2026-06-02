import type { PeriodFilter } from '../data/types';

interface PeriodSelectorProps {
  value: PeriodFilter;
  onChange: (next: PeriodFilter) => void;
}

const choices: Array<PeriodFilter['period']> = ['Q1 2026', 'Q4 2025', 'Q3 2025', 'YTD', 'TTM'];

export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  return (
    <div
      role="group"
      aria-label="Period selector"
      style={{ display: 'inline-flex', borderRadius: 999, border: '1px solid var(--rule)', overflow: 'hidden' }}
    >
      {choices.map((choice) => (
        <button
          key={choice}
          type="button"
          onClick={() => onChange({ period: choice })}
          style={{
            border: 'none',
            padding: '7px 11px',
            cursor: 'pointer',
            background: value.period === choice ? 'var(--accent)' : 'transparent',
            color: value.period === choice ? 'var(--bg)' : 'var(--ink-2)',
            fontSize: 12,
          }}
        >
          {choice.replace('20', '')}
        </button>
      ))}
    </div>
  );
}
