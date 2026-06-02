import { useDrill } from '../lib/useDrill';

describe('useDrill store', () => {
  test('setFilter merges incoming values', () => {
    useDrill.setState({
      period: { period: 'Q1 2026' },
      filter: { glId: '60100', ccId: null, vendorId: null },
    });

    useDrill.getState().setFilter({ ccId: 'FIN' });

    expect(useDrill.getState().filter).toEqual({ glId: '60100', ccId: 'FIN', vendorId: null });
  });

  test('clearFilters resets all values', () => {
    useDrill.setState({
      period: { period: 'Q1 2026' },
      filter: { glId: '60100', ccId: 'FIN', vendorId: 'V100' },
    });

    useDrill.getState().clearFilters();

    expect(useDrill.getState().filter).toEqual({ glId: null, ccId: null, vendorId: null });
  });
});
