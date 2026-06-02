import { axe, toHaveNoViolations } from 'jest-axe';
import { CostCentersTab } from '../tabs/CostCenters';
import { OverviewTab } from '../tabs/Overview';
import { PnlTab } from '../tabs/Pnl';
import { TransactionsTab } from '../tabs/Transactions';
import { VendorsTab } from '../tabs/Vendors';
import { renderWithProviders } from './renderWithProviders';
import { useDrill } from '../lib/useDrill';

expect.extend(toHaveNoViolations);

vi.mock('../data/usePnl', () => ({
  usePnl: () => ({ isLoading: false, isError: false, data: [{ id: '60100', name: 'Cloud', parentId: null, actual: 120, prior: 100, budget: 110 }], refetch: vi.fn() }),
}));

vi.mock('../data/useTrend', () => ({
  useTrend: () => ({ isLoading: false, isError: false, data: [{ period: 'Q1 2026', actual: 120, budget: 110 }], refetch: vi.fn() }),
}));

vi.mock('../data/useVendors', () => ({
  useVendors: () => ({ isLoading: false, isError: false, data: [{ id: 'V1', name: 'Acme', category: 'Software', primaryGlId: '60100', primaryCcId: 'ENG', contractType: 'Annual', renewalDate: null, actual: 80, prior: 70, budget: 75 }], refetch: vi.fn() }),
}));

vi.mock('../data/useCostCenters', () => ({
  useCostCenters: () => ({ isLoading: false, isError: false, data: [{ id: 'ENG', name: 'Engineering', lead: 'Lead', headcount: 50, actual: 120, prior: 110, budget: 115 }], refetch: vi.fn() }),
}));

vi.mock('../data/useTransactions', () => ({
  useTransactions: () => ({ isLoading: false, isError: false, data: { rows: [{ id: 'TX1', date: '2026-01-01', vendorId: 'V1', vendorName: 'Acme', glId: '60100', ccId: 'ENG', memo: 'Cloud spend', amount: 1000, status: 'Posted', invoiceNumber: 'INV-1' }], totalRows: 1, page: 1, pageSize: 200 }, refetch: vi.fn() }),
}));

describe('axe accessibility checks', () => {
  beforeEach(() => {
    useDrill.setState({
      period: { period: 'Q1 2026' },
      filter: { glId: null, ccId: null, vendorId: null },
    });
  });

  test.each([
    ['Overview', <OverviewTab />],
    ['P&L', <PnlTab />],
    ['Cost Centers', <CostCentersTab />],
    ['Vendors', <VendorsTab />],
    ['Transactions', <TransactionsTab />],
  ])('%s has no critical axe violations', async (_name, node) => {
    const { container } = renderWithProviders(node);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
