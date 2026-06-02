import { useNavigate } from 'react-router-dom';
import { CompositionBar } from '../charts/CompositionBar';
import { TrendChart } from '../charts/TrendChart';
import { KpiTile } from '../components/KpiTile';
import { QueryState } from '../components/QueryState';
import { VariancePill } from '../components/VariancePill';
import { usePnl } from '../data/usePnl';
import { useTrend } from '../data/useTrend';
import { useVendors } from '../data/useVendors';
import { formatK } from '../lib/formatters';
import { useDrill } from '../lib/useDrill';

export function OverviewTab() {
  const navigate = useNavigate();
  const period = useDrill((s) => s.period);
  const filter = useDrill((s) => s.filter);
  const setFilter = useDrill((s) => s.setFilter);

  const pnl = usePnl(period, filter);
  const trend = useTrend(period, filter, 5);
  const vendors = useVendors(period, filter);

  const total = (pnl.data ?? []).reduce((sum, row) => sum + row.actual, 0);
  const prior = (pnl.data ?? []).reduce((sum, row) => sum + row.prior, 0);
  const budget = (pnl.data ?? []).reduce((sum, row) => sum + row.budget, 0);

  return (
    <QueryState isLoading={pnl.isLoading || trend.isLoading || vendors.isLoading} isError={Boolean(pnl.error || trend.error || vendors.error)} onRetry={() => { void pnl.refetch(); void trend.refetch(); void vendors.refetch(); }}>
      <div className="page">
        <div style={{ marginBottom: 18 }}>
          <div style={{ textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--ink-3)', fontSize: 11 }}>Overview</div>
          <h1 style={{ margin: 0, fontFamily: 'Source Serif 4, Georgia, serif' }}>{formatK(total)} quarterly expense</h1>
        </div>

        <div className="grid grid-4">
          <KpiTile eyebrow="Quarterly Expense" value={formatK(total)} deltaValue={total - budget} deltaMode="budget" footnote="All departments" onClick={() => navigate('/pnl')} deltaNode={<VariancePill value={total - budget} mode="budget" isPercent={false} />} />
          <KpiTile eyebrow="$ Var YoY" value={formatK(total - prior)} deltaValue={total - prior} deltaMode="prior" footnote="Current vs prior" onClick={() => navigate('/pnl')} deltaNode={<VariancePill value={total - prior} mode="prior" isPercent={false} />} />
          <KpiTile eyebrow="% Var YoY" value={`${prior === 0 ? 0 : (((total - prior) / Math.abs(prior)) * 100).toFixed(1)}%`} deltaValue={prior === 0 ? 0 : ((total - prior) / Math.abs(prior)) * 100} deltaMode="prior" footnote="Relative change" onClick={() => navigate('/pnl')} deltaNode={<VariancePill value={prior === 0 ? 0 : ((total - prior) / Math.abs(prior)) * 100} mode="prior" isPercent />} />
          <KpiTile eyebrow="Budget Variance" value={formatK(total - budget)} deltaValue={total - budget} deltaMode="budget" footnote="Highlighted control metric" highlighted onClick={() => navigate('/pnl')} deltaNode={<VariancePill value={total - budget} mode="budget" isPercent={false} />} />
        </div>

        <div className="grid" style={{ gridTemplateColumns: '2fr 1fr', marginTop: 16, gap: 16 }}>
          <TrendChart data={trend.data ?? []} />
          <CompositionBar
            data={(pnl.data ?? []).slice(0, 6).map((row) => ({ id: row.id, name: row.name, amount: row.actual }))}
          />
        </div>

        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <div className="panel" style={{ padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>Top 5 Vendors</h3>
            <table style={{ width: '100%' }}>
              <tbody>
                {(vendors.data ?? []).slice(0, 5).map((row) => (
                  <tr
                    key={row.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => {
                      setFilter({ vendorId: row.id });
                      navigate('/vendors');
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        setFilter({ vendorId: row.id });
                        navigate('/vendors');
                      }
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>{row.name}</td>
                    <td className="tabular-nums" style={{ textAlign: 'right' }}>{formatK(row.actual)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="panel" style={{ padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>Top Movers vs Budget</h3>
            <div style={{ display: 'grid', gap: 10 }}>
              {(pnl.data ?? [])
                .map((row) => ({ ...row, variance: row.actual - row.budget }))
                .sort((a, b) => Math.abs(b.variance) - Math.abs(a.variance))
                .slice(0, 5)
                .map((row) => (
                  <button
                    key={row.id}
                    type="button"
                    onClick={() => {
                      setFilter({ glId: row.id });
                      navigate('/pnl');
                    }}
                    style={{ display: 'flex', justifyContent: 'space-between', border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--ink)' }}
                  >
                    <span>{row.name}</span>
                    <VariancePill value={row.variance} mode="budget" isPercent={false} />
                  </button>
                ))}
            </div>
          </div>
        </div>
      </div>
    </QueryState>
  );
}
