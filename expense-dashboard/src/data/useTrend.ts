import { useQuery } from '@tanstack/react-query';
import { useApiGet } from '../lib/api';
import { buildFilterQuery } from '../lib/queryParams';
import type { DrillFilter, PeriodFilter, TrendPoint } from './types';

// Backend SQL contract:
//
//   SELECT period,
//          SUM(actual_amount) / 1000 AS actual,
//          SUM(budget_amount) / 1000 AS budget
//   FROM mart_expense_quarterly
//   WHERE period IN (:fiveQuarterWindow)
//     AND (:glId IS NULL OR gl_id = :glId)
//     AND (:ccId IS NULL OR cc_id = :ccId)
//     AND (:vendorId IS NULL OR vendor_id = :vendorId)
//   GROUP BY period
//   ORDER BY period;
export function useTrend(period: PeriodFilter, filter: DrillFilter, quarters = 5) {
  const apiGet = useApiGet();
  return useQuery({
    queryKey: ['trend', period, filter, quarters],
    queryFn: () =>
      apiGet<TrendPoint[]>(`/api/trend?${buildFilterQuery(period, filter)}&quarters=${quarters}`),
  });
}
