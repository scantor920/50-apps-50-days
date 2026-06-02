import { useNavigate } from 'react-router-dom';
import { GroupedBars } from '../charts/GroupedBars';
import { Breadcrumb } from '../components/Breadcrumb';
import { KpiTile } from '../components/KpiTile';
import { QueryState } from '../components/QueryState';
import { VariancePill } from '../components/VariancePill';
import { useCostCenters } from '../data/useCostCenters';
import { useVendors } from '../data/useVendors';
import { formatK } from '../lib/formatters';
import { useDrill } from '../lib/useDrill';

export function CostCentersTab() {
  const navigate = useNavigate();
  const period = useDrill((s) => s.period);
  const filter = useDrill((s) => s.filter);
  const setFilter = useDrill((s) => s.setFilter);

  const query = useCostCenters(period, filter);
  const vendorsQuery = useVendors(period, filter);
  const rows = query.data ?? [];

  const totalSpend = rows.reduce((sum, row) => sum + row.actual, 0);
  const totalHeadcount = rows.reduce((sum, row) => sum + row.headcount, 0);

  return (
    <QueryState isLoading={query.isLoading} isError={query.isError} onRetry={() => void query.refetch()}>
      <div className="page">
        <Breadcrumb crumbs={[{ label: 'Overview', href: '/overview' }, { label: 'P&L', href: '/pnl' }, { label: 'Cost Centers' }]} />

        <div className="grid grid-3">
          <KpiTile eyebrow="# Cost Centers" value={String(rows.length)} deltaValue={0} deltaMode="prior" footnote="Active departments" />
          <KpiTile eyebrow="Total Headcount" value={String(totalHeadcount)} deltaValue={0} deltaMode="prior" footnote="Period-end FTE" />
          <KpiTile eyebrow="Avg Spend / FTE" value={formatK(totalHeadcount === 0 ? 0 : totalSpend / totalHeadcount)} deltaValue={0} deltaMode="budget" footnote="Efficiency view" />
        </div>

        <div style={{ marginTop: 16 }}>
          <GroupedBars
            data={rows.slice(0, 10).map((row) => ({ id: row.id, name: row.name, actual: row.actual, budget: row.budget, prior: row.prior }))}
            mode="budget"
            onBarClick={(id) => {
              setFilter({ ccId: id });
              navigate('/vendors');
            }}
          />
        </div>

        <div className="panel" style={{ marginTop: 16, padding: 16 }}>
          <table style={{ width: '100%' }}>
            <thead>
              <tr>
                <th align="left">Name</th>
                <th align="left">Lead</th>
                <th align="right">Headcount</th>
                <th align="right">$</th>
                <th align="right">$/FTE</th>
                <th align="right">YoY%</th>
                <th align="right">Budget%</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const yoyPct = row.prior === 0 ? 0 : ((row.actual - row.prior) / Math.abs(row.prior)) * 100;
                const budgetPct = row.budget === 0 ? 0 : ((row.actual - row.budget) / Math.abs(row.budget)) * 100;
                return (
                  <tr key={row.id} role="button" tabIndex={0} onClick={() => { setFilter({ ccId: row.id }); navigate('/vendors'); }} onKeyDown={(e) => { if (e.key === 'Enter') { setFilter({ ccId: row.id }); navigate('/vendors'); } }}>
                    <td>{row.name}</td>
                    <td>{row.lead}</td>
                    <td align="right" className="tabular-nums">{row.headcount}</td>
                    <td align="right" className="tabular-nums">{formatK(row.actual)}</td>
                    <td align="right" className="tabular-nums">{formatK(row.headcount === 0 ? 0 : row.actual / row.headcount)}</td>
                    <td align="right"><VariancePill value={yoyPct} mode="prior" isPercent /></td>
                    <td align="right"><VariancePill value={budgetPct} mode="budget" isPercent /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filter.glId ? (
          <div className="panel" style={{ marginTop: 16, padding: 16 }}>
            <h3 style={{ marginTop: 0 }}>Vendors mapped to this GL</h3>
            {(vendorsQuery.data ?? []).slice(0, 5).map((vendor) => (
              <div key={vendor.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>{vendor.name}</span>
                <span>{formatK(vendor.actual)}</span>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </QueryState>
  );
}
