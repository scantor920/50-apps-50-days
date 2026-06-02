import { useQuery } from '@tanstack/react-query';
import { useApiGet } from '../lib/api';
import { buildFilterQuery } from '../lib/queryParams';
import type { DrillFilter, PeriodFilter, PnlNode } from './types';

// Backend SQL contract (assumes a fact table f_gl_actuals + dim_gl):
//
//   SELECT g.id, g.name, g.parent_id,
//          SUM(CASE WHEN f.period = :p THEN f.amount END) / 1000 AS actual,
//          SUM(CASE WHEN f.period = :prior THEN f.amount END) / 1000 AS prior,
//          SUM(CASE WHEN b.period = :p THEN b.amount END) / 1000 AS budget
//   FROM dim_gl g
//   LEFT JOIN f_gl_actuals f ON f.gl_id = g.id
//   LEFT JOIN f_gl_budget  b ON b.gl_id = g.id
//   GROUP BY g.id, g.name, g.parent_id
//   ORDER BY g.sort_order;
export function usePnl(period: PeriodFilter, filter: DrillFilter) {
  const apiGet = useApiGet();
  return useQuery({
    queryKey: ['pnl', period, filter],
    queryFn: () => apiGet<PnlNode[]>(`/api/pnl?${buildFilterQuery(period, filter)}`),
  });
}
