import { useQuery } from '@tanstack/react-query';
import { useApiGet } from '../lib/api';
import { buildFilterQuery } from '../lib/queryParams';
import type { DrillFilter, PeriodFilter, Transaction } from './types';

export interface TransactionPage {
  rows: Transaction[];
  totalRows: number;
  page: number;
  pageSize: number;
}

// Backend SQL contract:
//
//   SELECT t.id, t.date, t.vendor_id, v.name AS vendor_name, t.gl_id, t.cc_id,
//          t.memo, t.amount, t.status, t.invoice_number
//   FROM f_ap_txn t
//   JOIN dim_vendor v ON v.id = t.vendor_id
//   WHERE t.date BETWEEN :startDate AND :endDate
//     AND (:glId IS NULL OR t.gl_id = :glId)
//     AND (:ccId IS NULL OR t.cc_id = :ccId)
//     AND (:vendorId IS NULL OR t.vendor_id = :vendorId)
//   ORDER BY t.date DESC
//   LIMIT :limit OFFSET :offset;
export function useTransactions(period: PeriodFilter, filter: DrillFilter, page = 1, pageSize = 200) {
  const apiGet = useApiGet();
  return useQuery({
    queryKey: ['transactions', period, filter, page, pageSize],
    queryFn: () =>
      apiGet<TransactionPage>(
        `/api/transactions?${buildFilterQuery(period, filter)}&page=${page}&pageSize=${pageSize}`,
      ),
  });
}
