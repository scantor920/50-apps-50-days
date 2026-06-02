export function formatK(value: number): string {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 1, minimumFractionDigits: 0 })}K`;
}

export function formatCurrency(value: number): string {
  return value.toLocaleString(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  });
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function deltaPct(actual: number, baseline: number): number {
  if (baseline === 0) {
    return 0;
  }
  return ((actual - baseline) / Math.abs(baseline)) * 100;
}
