import type { DrillFilter, PeriodFilter } from '../data/types';

export function buildFilterQuery(period: PeriodFilter, filter: DrillFilter): string {
  const params = new URLSearchParams();
  params.set('period', period.period);
  if (period.comparePeriod) {
    params.set('comparePeriod', period.comparePeriod);
  }
  if (filter.glId) {
    params.set('glId', filter.glId);
  }
  if (filter.ccId) {
    params.set('ccId', filter.ccId);
  }
  if (filter.vendorId) {
    params.set('vendorId', filter.vendorId);
  }
  return params.toString();
}
