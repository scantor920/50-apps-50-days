import { useDrill } from '../lib/useDrill';

export function ActiveFilterChips() {
  const filter = useDrill((s) => s.filter);
  const setFilter = useDrill((s) => s.setFilter);
  const clearFilters = useDrill((s) => s.clearFilters);

  const chips = [
    filter.glId ? { key: 'glId', label: `GL ${filter.glId}` } : null,
    filter.ccId ? { key: 'ccId', label: `CC ${filter.ccId}` } : null,
    filter.vendorId ? { key: 'vendorId', label: `Vendor ${filter.vendorId}` } : null,
  ].filter((value): value is { key: 'glId' | 'ccId' | 'vendorId'; label: string } => value !== null);

  if (chips.length === 0) {
    return null;
  }

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', margin: '6px 0 18px' }}>
      {chips.map((chip) => (
        <span
          key={chip.key}
          style={{
            border: '1px solid var(--rule)',
            borderRadius: 999,
            background: 'var(--bg-elev)',
            fontSize: 12,
            padding: '4px 8px',
          }}
        >
          {chip.label}
          <button
            onClick={() => setFilter({ [chip.key]: null })}
            type="button"
            aria-label={`Remove ${chip.label}`}
            style={{ marginLeft: 8, border: 'none', background: 'transparent', color: 'var(--ink-2)', cursor: 'pointer' }}
          >
            x
          </button>
        </span>
      ))}
      <button
        onClick={clearFilters}
        type="button"
        style={{ border: 'none', background: 'transparent', color: 'var(--accent)', cursor: 'pointer', fontSize: 12 }}
      >
        Clear all
      </button>
    </div>
  );
}
