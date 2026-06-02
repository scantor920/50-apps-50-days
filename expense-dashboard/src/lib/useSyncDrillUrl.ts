import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDrill } from './useDrill';

export function useSyncDrillUrl() {
  const [params, setParams] = useSearchParams();
  const period = useDrill((s) => s.period);
  const filter = useDrill((s) => s.filter);
  const setPeriod = useDrill((s) => s.setPeriod);
  const setFilter = useDrill((s) => s.setFilter);

  useEffect(() => {
    const nextPeriod = params.get('period');
    const glId = params.get('glId');
    const ccId = params.get('ccId');
    const vendorId = params.get('vendorId');

    if (nextPeriod && nextPeriod !== period.period) {
      setPeriod({ period: nextPeriod as typeof period.period });
    }
    if (glId !== filter.glId || ccId !== filter.ccId || vendorId !== filter.vendorId) {
      setFilter({ glId, ccId, vendorId });
    }
  }, []);

  useEffect(() => {
    const next = new URLSearchParams();
    next.set('period', period.period);
    if (filter.glId) {
      next.set('glId', filter.glId);
    }
    if (filter.ccId) {
      next.set('ccId', filter.ccId);
    }
    if (filter.vendorId) {
      next.set('vendorId', filter.vendorId);
    }
    setParams(next, { replace: true });
  }, [period, filter, setParams]);
}
