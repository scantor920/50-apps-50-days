import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { VarianceBridge } from '../charts/VarianceBridge';
import { Breadcrumb } from '../components/Breadcrumb';
import { KpiTile } from '../components/KpiTile';
import { QueryState } from '../components/QueryState';
import { RowBar } from '../components/RowBar';
import { VariancePill } from '../components/VariancePill';
import { usePnl } from '../data/usePnl';
import { formatK } from '../lib/formatters';
import { useDrill } from '../lib/useDrill';

export function PnlTab() {
  const navigate = useNavigate();
  const period = useDrill((s) => s.period);
  const filter = useDrill((s) => s.filter);
  const setFilter = useDrill((s) => s.setFilter);
  const [mode, setMode] = useState<'budget' | 'prior'>('budget');

  const query = usePnl(period, filter);
  const rows = query.data ?? [];

  const totals = useMemo(() => {
    const actual = rows.reduce((sum, row) => sum + row.actual, 0);
    const compare = rows.reduce((sum, row) => sum + (mode === 'budget' ? row.budget : row.prior), 0);
    return { actual, compare, variance: actual - compare };
  }, [rows, mode]);

  return (
    <QueryState isLoading={query.isLoading} isError={query.isError} onRetry={() => void query.refetch()}>
      <div className="page">
        <Breadcrumb crumbs={[{ label: 'Overview', href: '/overview' }, { label: 'P&L' }]} />

        <div style={{ marginBottom: 14 }}>
          <button type="button" onClick={() => setMode('budget')}>vs Budget</button>
          <button type="button" onClick={() => setMode('prior')} style={{ marginLeft: 8 }}>vs Prior Year</button>
        </div>

        <div className="grid grid-3">
          <KpiTile eyebrow="Total Actual" value={formatK(totals.actual)} deltaValue={0} deltaMode={mode} footnote="Current period" />
          <KpiTile eyebrow={mode === 'budget' ? 'Plan' : 'Prior'} value={formatK(totals.compare)} deltaValue={0} deltaMode={mode} footnote="Comparison baseline" />
          <KpiTile eyebrow="Variance" value={formatK(totals.variance)} deltaValue={totals.variance} deltaMode={mode} footnote="Actual minus baseline" deltaNode={<VariancePill value={totals.variance} mode={mode} isPercent={false} />} />
        </div>

        <div style={{ marginTop: 16 }}>
          <VarianceBridge data={rows.slice(0, 10).map((row) => ({ name: row.name, value: row.actual - (mode === 'budget' ? row.budget : row.prior) }))} />
        </div>

        <div className="panel" style={{ marginTop: 16, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>P&L Tree</h3>
          <table style={{ width: '100%' }}>
            <thead>
              <tr>
                <th align="left">Account</th>
                <th align="right">Actual</th>
                <th align="right">$ Var</th>
                <th align="right">% Var</th>
                <th align="right">% Total</th>
                <th align="right">Drill</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const comp = mode === 'budget' ? row.budget : row.prior;
                const variance = row.actual - comp;
                const pct = comp === 0 ? 0 : (variance / Math.abs(comp)) * 100;
                const share = totals.actual === 0 ? 0 : (row.actual / totals.actual) * 100;
                return (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td className="tabular-nums" align="right">{formatK(row.actual)}</td>
                    <td align="right"><VariancePill value={variance} mode={mode} isPercent={false} /></td>
                    <td className="tabular-nums" align="right">{pct.toFixed(1)}%</td>
                    <td align="right" style={{ width: 160 }}><RowBar value={share} /></td>
                    <td align="right">
                      <button type="button" onClick={() => { setFilter({ glId: row.id }); navigate('/cost-centers'); }}>By dept</button>
                      <button type="button" onClick={() => { setFilter({ glId: row.id }); navigate('/vendors'); }} style={{ marginLeft: 6 }}>Vendors</button>
                    </td>
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
