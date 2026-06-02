import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { useCostCenters } from '../data/useCostCenters';
import { usePnl } from '../data/usePnl';
import { useTransactions } from '../data/useTransactions';
import { useTrend } from '../data/useTrend';
import { useVendors } from '../data/useVendors';
import type { DrillFilter, PeriodFilter } from '../data/types';

const period: PeriodFilter = { period: 'Q1 2026' };
const filter: DrillFilter = { glId: null, ccId: null, vendorId: null };

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('data hooks', () => {
  test.each([
    ['pnl', () => usePnl(period, filter), []],
    ['cost-centers', () => useCostCenters(period, filter), []],
    ['vendors', () => useVendors(period, filter), []],
    ['transactions', () => useTransactions(period, filter), { rows: [], totalRows: 0, page: 1, pageSize: 200 }],
    ['trend', () => useTrend(period, filter), []],
  ])('happy path %s', async (_name, hookFactory, payload) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => payload,
      }),
    );

    const { result } = renderHook(() => hookFactory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(payload);
  });

  test.each([
    ['pnl', () => usePnl(period, filter)],
    ['cost-centers', () => useCostCenters(period, filter)],
    ['vendors', () => useVendors(period, filter)],
    ['transactions', () => useTransactions(period, filter)],
    ['trend', () => useTrend(period, filter)],
  ])('error path %s', async (_name, hookFactory) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Server Error',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ error: 'boom' }),
      }),
    );

    const { result } = renderHook(() => hookFactory(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
