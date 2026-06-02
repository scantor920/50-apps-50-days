import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { ActiveFilterChips } from './components/ActiveFilterChips';
import { PeriodSelector } from './components/PeriodSelector';
import { ThemeSwitcher } from './components/ThemeSwitcher';
import { useDrill } from './lib/useDrill';
import { useSyncDrillUrl } from './lib/useSyncDrillUrl';
import { useAuth } from './lib/auth';
import { useTheme } from './lib/useTheme';
import { CostCentersTab } from './tabs/CostCenters';
import { OverviewTab } from './tabs/Overview';
import { PnlTab } from './tabs/Pnl';
import { TransactionsTab } from './tabs/Transactions';
import { VendorsTab } from './tabs/Vendors';

const navTabs = [
  { step: '01', label: 'Overview', href: '/overview' },
  { step: '02', label: 'P&L', href: '/pnl' },
  { step: '03', label: 'Cost Centers', href: '/cost-centers' },
  { step: '04', label: 'Vendors', href: '/vendors' },
  { step: '05', label: 'Transactions', href: '/transactions' },
];

export default function App() {
  useSyncDrillUrl();

  const period = useDrill((s) => s.period);
  const setPeriod = useDrill((s) => s.setPeriod);
  const { displayName } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">MX</div>
          <div style={{ fontWeight: 700 }}>MarketAxess Expense Intelligence</div>
          <div className="spacer" />
          <PeriodSelector value={period} onChange={setPeriod} />
          <ThemeSwitcher value={theme} onChange={setTheme} />
          <div className="panel" style={{ padding: '6px 10px', borderRadius: 999 }}>{displayName}</div>
        </div>

        <nav className="tab-nav">
          {navTabs.map((tab, index) => (
            <div key={tab.href} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <NavLink to={tab.href} className={({ isActive }) => `tab-link${isActive ? ' active' : ''}`}>
                {tab.step} {tab.label}
              </NavLink>
              {index < navTabs.length - 1 ? <span style={{ color: 'var(--ink-4)' }}>›</span> : null}
            </div>
          ))}
        </nav>
      </header>

      <main className="app-shell">
        <ActiveFilterChips />
        <Routes>
          <Route path="/overview" element={<OverviewTab />} />
          <Route path="/pnl" element={<PnlTab />} />
          <Route path="/cost-centers" element={<CostCentersTab />} />
          <Route path="/vendors" element={<VendorsTab />} />
          <Route path="/transactions" element={<TransactionsTab />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </main>
    </>
  );
}
