import { useQuery } from '@tanstack/react-query';
import { useApiGet } from '../lib/api';
import { buildFilterQuery } from '../lib/queryParams';
import type { DrillFilter, PeriodFilter, Vendor } from './types';

// Backend SQL contract:
//
//   SELECT v.id, v.name, v.category, v.primary_gl_id, v.primary_cc_id,
//          v.contract_type, v.renewal_date,
//          SUM(CASE WHEN f.period = :p THEN f.amount END) / 1000 AS actual,
//          SUM(CASE WHEN f.period = :prior THEN f.amount END) / 1000 AS prior,
//          SUM(CASE WHEN b.period = :p THEN b.amount END) / 1000 AS budget
//   FROM dim_vendor v
//   LEFT JOIN f_ap_txn f ON f.vendor_id = v.id
//   LEFT JOIN f_vendor_budget b ON b.vendor_id = v.id
//   WHERE (:glId IS NULL OR f.gl_id = :glId)
//     AND (:ccId IS NULL OR f.cc_id = :ccId)
//   GROUP BY v.id, v.name, v.category, v.primary_gl_id, v.primary_cc_id,
//            v.contract_type, v.renewal_date;
export function useVendors(period: PeriodFilter, filter: DrillFilter) {
  const apiGet = useApiGet();
  return useQuery({
    queryKey: ['vendors', period, filter],
    queryFn: () => apiGet<Vendor[]>(`/api/vendors?${buildFilterQuery(period, filter)}`),
  });
}
