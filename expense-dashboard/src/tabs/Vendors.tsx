import { useNavigate } from 'react-router-dom';
import { CompositionBar } from '../charts/CompositionBar';
import { Breadcrumb } from '../components/Breadcrumb';
import { KpiTile } from '../components/KpiTile';
import { QueryState } from '../components/QueryState';
import { RowBar } from '../components/RowBar';
import { VariancePill } from '../components/VariancePill';
import { useVendors } from '../data/useVendors';
import { formatK } from '../lib/formatters';
import { useDrill } from '../lib/useDrill';

export function VendorsTab() {
  const navigate = useNavigate();
  const period = useDrill((s) => s.period);
  const filter = useDrill((s) => s.filter);
  const setFilter = useDrill((s) => s.setFilter);

  const query = useVendors(period, filter);
  const rows = query.data ?? [];

  const total = rows.reduce((sum, row) => sum + row.actual, 0);
  const totalPrior = rows.reduce((sum, row) => sum + row.prior, 0);
  const totalBudget = rows.reduce((sum, row) => sum + row.budget, 0);

  const byCategory = Array.from(
    rows.reduce((map, row) => {
      map.set(row.category, (map.get(row.category) ?? 0) + row.actual);
      return map;
    }, new Map<string, number>()),
  ).map(([name, amount], index) => ({ id: `${name}-${index}`, name, amount }));

  return (
    <QueryState isLoading={query.isLoading} isError={query.isError} onRetry={() => void query.refetch()}>
      <div className="page">
        <Breadcrumb crumbs={[{ label: 'Overview', href: '/overview' }, { label: 'P&L', href: '/pnl' }, { label: 'Cost Centers', href: '/cost-centers' }, { label: 'Vendors' }]} />

        <div className="grid grid-3">
          <KpiTile eyebrow="Total Spend" value={formatK(total)} deltaValue={0} deltaMode="budget" footnote="Current period" />
          <KpiTile eyebrow="vs Prior Year" value={formatK(total - totalPrior)} deltaValue={total - totalPrior} deltaMode="prior" footnote="Spend delta" deltaNode={<VariancePill value={total - totalPrior} mode="prior" isPercent={false} />} />
          <KpiTile eyebrow="vs Budget" value={formatK(total - totalBudget)} deltaValue={total - totalBudget} deltaMode="budget" footnote="Plan variance" deltaNode={<VariancePill value={total - totalBudget} mode="budget" isPercent={false} />} />
        </div>

        <div style={{ marginTop: 16 }}>
          <CompositionBar data={byCategory} />
        </div>

        <div className="panel" style={{ marginTop: 16, padding: 16 }}>
          <table style={{ width: '100%' }}>
            <thead>
              <tr>
                <th align="left">Name</th>
                <th align="left">Category</th>
                <th align="left">Contract</th>
                <th align="left">Renewal</th>
                <th align="right">$</th>
                <th align="right">YoY%</th>
                <th align="right">Budget%</th>
                <th align="right">Share</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const yoyPct = row.prior === 0 ? 0 : ((row.actual - row.prior) / Math.abs(row.prior)) * 100;
                const budgetPct = row.budget === 0 ? 0 : ((row.actual - row.budget) / Math.abs(row.budget)) * 100;
                const share = total === 0 ? 0 : (row.actual / total) * 100;
                return (
                  <tr
                    key={row.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => {
                      setFilter({ vendorId: row.id });
                      navigate('/transactions');
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        setFilter({ vendorId: row.id });
                        navigate('/transactions');
                      }
                    }}
                  >
                    <td>{row.name}</td>
                    <td>{row.category}</td>
                    <td>{row.contractType}</td>
                    <td>{row.renewalDate ?? 'N/A'}</td>
                    <td className="tabular-nums" align="right">{formatK(row.actual)}</td>
                    <td align="right"><VariancePill value={yoyPct} mode="prior" isPercent /></td>
                    <td align="right"><VariancePill value={budgetPct} mode="budget" isPercent /></td>
                    <td align="right" style={{ width: 120 }}><RowBar value={share} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </QueryState>
  );
}
