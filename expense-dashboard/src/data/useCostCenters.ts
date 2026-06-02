import { useQuery } from '@tanstack/react-query';
import { useApiGet } from '../lib/api';
import { buildFilterQuery } from '../lib/queryParams';
import type { CostCenter, DrillFilter, PeriodFilter } from './types';

// Backend SQL contract:
//
//   SELECT cc.id, cc.name, cc.lead, cc.headcount,
//          SUM(CASE WHEN f.period = :p THEN f.amount END) / 1000 AS actual,
//          SUM(CASE WHEN f.period = :prior THEN f.amount END) / 1000 AS prior,
//          SUM(CASE WHEN b.period = :p THEN b.amount END) / 1000 AS budget
//   FROM dim_cost_center cc
//   LEFT JOIN f_gl_actuals f ON f.cc_id = cc.id
//   LEFT JOIN f_gl_budget  b ON b.cc_id = cc.id
//   WHERE (:glId IS NULL OR f.gl_id = :glId)
//   GROUP BY cc.id, cc.name, cc.lead, cc.headcount;
export function useCostCenters(period: PeriodFilter, filter: DrillFilter) {
  const apiGet = useApiGet();
  return useQuery({
    queryKey: ['cost-centers', period, filter],
    queryFn: () => apiGet<CostCenter[]>(`/api/cost-centers?${buildFilterQuery(period, filter)}`),
  });
}
