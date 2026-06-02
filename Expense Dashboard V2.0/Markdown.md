# Expense Detail Dashboard — Copilot Handoff Package

This document is a set of prompts to feed GitHub Copilot (Chat) in order, to rebuild the
expense dashboard against your real data sources. Each prompt is self-contained — paste
it into Copilot Chat one at a time and let it generate code before moving on.

The architecture mirrors the design prototype:
  - 5 tabs in a strict drill-down funnel
  - Shared filter state that carries forward through the funnel
  - Variance vs prior year (YoY) and vs budget on every level
  - Theme palette swap (Light, Dark, Augusta, Imperial, Terminal)

Recommended stack (tell Copilot this up front):
  - React + Vite (or Next.js if you already have it)
  - TypeScript
  - Recharts or visx for charts (or keep the lightweight inline SVG approach)
  - TanStack Table for the transaction grid
  - A backend route layer (Node/Express, Next API routes, or FastAPI) that proxies your
    GL/ERP system. Do NOT hit the warehouse from the browser.

────────────────────────────────────────────────────────────────────────────
PROMPT 0 — Project bootstrap
────────────────────────────────────────────────────────────────────────────

Create a new React + TypeScript + Vite project named "expense-dashboard". Add the
following dependencies:

  - react-router-dom (for tab routing with shareable URLs)
  - @tanstack/react-table (transaction grid)
  - recharts (charts) — OR keep inline SVG if the team prefers no chart lib
  - zustand (lightweight global state for the drill-down filter context)
  - date-fns (date formatting)
  - clsx (className composition)

Set up:
  - src/lib/        → formatters, hooks, API client
  - src/data/       → typed data fetchers (one file per entity)
  - src/components/ → shared primitives (KpiTile, VariancePill, Breadcrumb, etc.)
  - src/charts/     → chart components
  - src/tabs/       → one file per tab (Overview, Pnl, CostCenters, Vendors, Transactions)
  - src/styles/     → tokens.css with CSS variables for the 5 themes

Set up ESLint + Prettier with strict TypeScript. No `any`.


────────────────────────────────────────────────────────────────────────────
PROMPT 1 — Type contracts
────────────────────────────────────────────────────────────────────────────

Create src/data/types.ts with these exact TypeScript interfaces. These are the contracts
every API endpoint must satisfy. Treat dollar amounts as numbers in $K (thousands) on
aggregates, and as full dollar amounts on the Transaction interface.

```ts
export type ISODate = string; // "2026-04-30"
export type Quarter = `Q${1|2|3|4} ${number}`; // "Q1 2026"

export interface GlAccount {
  id: string;            // canonical GL code, e.g. "60100" or "tech.cloud"
  name: string;          // human label
  parentId: string | null;
  level: number;         // 0 = parent, 1 = child, 2 = leaf, etc.
}

export interface PnlNode {
  id: string;            // GL id
  name: string;
  parentId: string | null;
  actual: number;        // current period $K
  prior: number;         // same period prior year $K
  budget: number;        // current period budget $K
  forecast?: number;     // optional re-forecast
  children?: PnlNode[];  // server can pre-nest, or client can build the tree
}

export interface CostCenter {
  id: string;            // department / function code
  name: string;
  lead: string;          // owner (department head)
  headcount: number;     // FTE at period end
  actual: number;        // $K
  prior: number;
  budget: number;
}

export interface Vendor {
  id: string;            // ERP vendor ID
  name: string;
  category: string;      // taxonomy category
  primaryGlId: string;   // most common GL the vendor hits
  primaryCcId: string;   // most common cost center
  contractType: string;  // "Master EDP" | "SOW" | "Annual" | etc.
  renewalDate: ISODate | null;
  actual: number;
  prior: number;
  budget: number;
}

export interface Transaction {
  id: string;            // ERP txn id
  date: ISODate;
  vendorId: string;
  vendorName: string;
  glId: string;
  ccId: string;
  memo: string;
  amount: number;        // FULL DOLLARS, not $K
  status: 'Posted' | 'Pending' | 'Reclassed' | 'Voided';
  invoiceNumber: string;
}

export interface TrendPoint {
  period: Quarter;
  actual: number;        // $K
  budget: number;
}

export interface PeriodFilter {
  period: Quarter | 'YTD' | 'TTM';
  comparePeriod?: Quarter | null;
}

export interface DrillFilter {
  glId: string | null;
  ccId: string | null;
  vendorId: string | null;
}
```


────────────────────────────────────────────────────────────────────────────
PROMPT 2 — API client & data fetchers
────────────────────────────────────────────────────────────────────────────

Create src/lib/api.ts — a thin fetch wrapper that:
  - Reads VITE_API_BASE from env
  - Handles auth (assume Bearer token from a useAuth hook — write a TODO if not
    yet implemented)
  - Returns typed responses
  - Throws structured errors with request context

Then create one file per entity in src/data/, each exporting a React Query hook
(install @tanstack/react-query first):

  src/data/usePnl.ts          → GET /api/pnl?period=...     → PnlNode[]
  src/data/useCostCenters.ts  → GET /api/cost-centers?...   → CostCenter[]
  src/data/useVendors.ts      → GET /api/vendors?...        → Vendor[]
  src/data/useTransactions.ts → GET /api/transactions?...   → Transaction[]
  src/data/useTrend.ts        → GET /api/trend?quarters=5   → TrendPoint[]

All hooks accept a PeriodFilter and a DrillFilter. The server is responsible for
applying the drill filter (so transactions only return rows matching the active
GL/CC/Vendor). Cache key must include both filters.

For the backend (separate prompt later), document the expected SQL shape in a
comment block at the top of each data file. Example for usePnl:

```ts
// Backend SQL contract (assumes a fact table f_gl_actuals + dim_gl):
//
//   SELECT g.id, g.name, g.parent_id,
//          SUM(CASE WHEN f.period = :p THEN f.amount END) / 1000 AS actual,
//          SUM(CASE WHEN f.period = :prior THEN f.amount END) / 1000 AS prior,
//          SUM(CASE WHEN b.period = :p THEN b.amount END) / 1000 AS budget
//   FROM dim_gl g
//   LEFT JOIN f_gl_actuals f ON f.gl_id = g.id
//   LEFT JOIN f_gl_budget  b ON b.gl_id = g.id
//   GROUP BY g.id, g.name, g.parent_id
//   ORDER BY g.sort_order;
```


────────────────────────────────────────────────────────────────────────────
PROMPT 3 — Backend route layer (Node/Express OR Next API)
────────────────────────────────────────────────────────────────────────────

Create a server/ directory with Express + a database client. Use whichever your
warehouse supports:
  - Snowflake → snowflake-sdk
  - BigQuery → @google-cloud/bigquery
  - Postgres → pg
  - SQL Server → mssql

Create one route per data fetcher in PROMPT 2. Each route must:
  1. Parse and validate query params (zod)
  2. Resolve the period to a date range
  3. Run a parameterized SQL query (NEVER string-concat user input)
  4. Map the SQL rows to the TypeScript interface
  5. Apply a 5-minute server-side cache (node-cache) keyed by query

Add an /api/health endpoint that returns 200 + warehouse connectivity status.

Add CORS, helmet, rate limiting, and an audit-log middleware that records:
  - userId
  - endpoint
  - filter params
  - response time

Do NOT log the response body — the GL data is sensitive.


────────────────────────────────────────────────────────────────────────────
PROMPT 4 — Design tokens & theming
────────────────────────────────────────────────────────────────────────────

Create src/styles/tokens.css with CSS custom properties for these 5 themes,
selected via [data-theme="..."] on <html>:

  - light    — bone background (#F6F4EE), navy accent (#1B3A5B)
  - dark     — near-black background (#0B0E13), steel-blue accent (#6FA3D8)
  - masters  — butter (#F1ECD9), Augusta green (#0E5132), pimento red (#7E1A14)
  - imperial — black (#0A0A0C), Imperial red (#C8302A)
  - terminal — amber on black (#FFB300 on #0A0A06), monospace stack

Required token names (every theme MUST define ALL of these):

  --bg, --bg-elev, --bg-sunk
  --ink, --ink-2, --ink-3, --ink-4
  --rule, --rule-strong
  --accent, --accent-2
  --pos, --pos-soft     (good = under budget)
  --neg, --neg-soft     (bad = over budget)
  --warn, --gold, --hl
  --shadow, --shadow-sm
  --radius, --radius-lg

Add a useTheme() hook backed by localStorage that toggles the data-theme attribute.
The terminal theme additionally swaps the body font to "IBM Plex Mono".


────────────────────────────────────────────────────────────────────────────
PROMPT 5 — Shared primitives
────────────────────────────────────────────────────────────────────────────

Build these reusable components in src/components/:

  KpiTile.tsx
    Props: { eyebrow, value, deltaValue, deltaMode: 'budget' | 'prior',
             footnote, onClick, highlighted? }
    Big serif number (Source Serif 4), uppercase eyebrow, variance pill below,
    border-top divider before footnote. Clickable shows hover lift.

  VariancePill.tsx
    Props: { value: number, mode: 'budget' | 'prior', isPercent: boolean }
    For mode='budget': positive value is RED (over budget = bad).
    For mode='prior':  values < 0.5% absolute are flat/grey; otherwise positive
                       (growth) renders soft red, negative renders soft green.
    Display ▲ / ▼ glyph + sign + value.

  Breadcrumb.tsx
    Props: { crumbs: { label: string, href?: string }[] }
    Renders Overview › P&L › Cost Centers › Vendors › Transactions trail.

  ActiveFilterChips.tsx
    Reads from the drill-filter store. Renders a chip per active filter with
    an × dismiss button. Includes a "Clear all" link if any are active.

  PeriodSelector.tsx
    Pill-shaped segmented control: Q1 26 / Q4 25 / Q3 25 / YTD / TTM.

  ThemeSwitcher.tsx
    Segmented control matching PROMPT 4 themes.

  RowBar.tsx
    Inline progress bar for showing share-of-total inside table cells.

All primitives must use design tokens — no hardcoded colors. All numbers must use
font-variant-numeric: tabular-nums.


────────────────────────────────────────────────────────────────────────────
PROMPT 6 — Charts
────────────────────────────────────────────────────────────────────────────

Build these in src/charts/. Either use Recharts or hand-roll inline SVG (the
prototype hand-rolled them — it stays under 200 LOC each and is more controllable).

  TrendChart.tsx
    Props: { data: TrendPoint[] }
    Line chart of actual (solid, accent color) over budget (dashed, ink-3),
    soft area fill under actual line, last-point dot + dollar annotation.

  VarianceBridge.tsx
    Props: { data: { name: string, value: number }[] }  (positive = over budget)
    Waterfall: green bars for under, red bars for over, dotted connectors.

  GroupedBars.tsx
    Props: { data: { id, name, actual, budget, prior }[], mode: 'budget' | 'prior' }
    Side-by-side bars per category, accent for actual, ink-3 with opacity for
    comparison. Click handler for row drill.

  CompositionBar.tsx
    Single horizontal stacked bar showing each category's % of total.
    Legend below with name + dollar amount.


────────────────────────────────────────────────────────────────────────────
PROMPT 7 — Drill-down state (zustand)
────────────────────────────────────────────────────────────────────────────

Create src/lib/useDrill.ts:

```ts
import { create } from 'zustand';
import type { DrillFilter, PeriodFilter } from '../data/types';

interface DrillStore {
  period: PeriodFilter;
  filter: DrillFilter;
  setPeriod: (p: PeriodFilter) => void;
  setFilter: (next: Partial<DrillFilter>) => void;
  clearFilters: () => void;
}

export const useDrill = create<DrillStore>((set) => ({
  period: { period: 'Q1 2026' },
  filter: { glId: null, ccId: null, vendorId: null },
  setPeriod: (period) => set({ period }),
  setFilter: (next) => set((s) => ({ filter: { ...s.filter, ...next } })),
  clearFilters: () => set({ filter: { glId: null, ccId: null, vendorId: null } }),
}));
```

Sync this store to the URL (search params) using react-router-dom so drill state
is shareable and back/forward-navigable.


────────────────────────────────────────────────────────────────────────────
PROMPT 8 — Tabs (one prompt each, paste in order)
────────────────────────────────────────────────────────────────────────────

For each tab, give Copilot this template (substitute the tab name + spec):

  "Build src/tabs/<TabName>.tsx using the data hooks in src/data/, the primitives
   in src/components/, and the charts in src/charts/. Match this layout:

   <TAB SPEC>

   Wire every clickable element to update the drill filter store and route to
   the next tab. Add loading skeletons that match the card layout. Show an
   error boundary that retries the query."

Tab specs:

  OVERVIEW (broadest)
    - Page header: eyebrow + serif H1 with total quarterly expense
    - 4-up KPI grid: Quarterly Expense, $ Var YoY, % Var YoY, Budget Variance
      (the last one is highlighted with accent border)
    - 2/3 + 1/3 row: TrendChart (5 quarters) + GL composition list
    - 2-up row: Top 5 vendors table + Top movers vs budget list
    - Every tile/row clicks through to the next tab with the right filter set

  P&L VIEW
    - Breadcrumb: Overview ›
    - Toggle: vs Budget / vs Prior Year (controls every variance shown)
    - 3-up summary band: Total Actual, Plan/Prior, Variance
    - VarianceBridge — what moved the number
    - Expandable parent → child P&L tree table with $ var, % var, % of total,
      and a "By dept" / "Vendors" drill button per row

  COST CENTERS
    - Breadcrumb: Overview › P&L ›
    - 3-up KPI: # Cost Centers, Total Headcount, Avg Spend / FTE
    - GroupedBars — top 10 cost centers, actual vs budget
    - Sortable detail table: Name, Lead, Headcount, $, $/FTE, YoY%, Budget %
    - If a GL filter is active, show "Vendors mapped to this GL" preview card

  VENDORS
    - Breadcrumb: Overview › P&L › Cost Centers ›
    - 3-up KPI: Total Spend, vs Prior Year, vs Budget
    - CompositionBar by vendor category
    - Sortable table: Name, Category, Contract, Renewal, $, YoY%, Budget%, Share
    - Row click → Transactions tab filtered to that vendor

  TRANSACTIONS (deepest)
    - Breadcrumb: Overview › P&L › Cost Centers › Vendors ›
    - 4-up KPI: Total $, Posted count, Pending count, Reclassed count
    - Search box (memo / vendor / invoice)
    - Status filter segmented control
    - TanStack Table with virtualization for large datasets:
      Date, Txn ID, Vendor, Memo, GL, Cost Center, Invoice, Status, Amount
    - Status pill colored by Posted/Pending/Reclassed
    - Server-side pagination — 200 rows per page


────────────────────────────────────────────────────────────────────────────
PROMPT 9 — App shell, routing, topbar
────────────────────────────────────────────────────────────────────────────

Create src/App.tsx:
  - Top bar with: brand mark + "MarketAxess Expense Intelligence", spacer,
    PeriodSelector, ThemeSwitcher, user chip (read from useAuth)
  - Tab nav with step numbers (01 → 05) and › arrows between them
  - Active tab underline in accent color
  - Route each tab to /overview, /pnl, /cost-centers, /vendors, /transactions
  - Sticky top bar + tab nav

Make the layout 1480px max width with 32px gutters, optimized for desktop ≥ 1440.


────────────────────────────────────────────────────────────────────────────
PROMPT 10 — Tests & accessibility
────────────────────────────────────────────────────────────────────────────

Add Vitest + React Testing Library. Write tests for:
  - VariancePill — correct color/sign for budget vs prior modes
  - useDrill — setFilter merges, clearFilters resets
  - Each data hook — happy path + error path with mocked fetch
  - Each tab — renders without crashing given mock data

Run axe-core against each tab. Fix any violations. Ensure:
  - All clickable rows have role="button" and keyboard handlers
  - Variance pills include an aria-label that reads sign + value (screen readers
    won't pronounce ▲ correctly)
  - Color is never the only signal for variance — pair with the arrow glyph + sign


────────────────────────────────────────────────────────────────────────────
PROMPT 11 — Real data plumbing checklist
────────────────────────────────────────────────────────────────────────────

Once the UI builds against mock JSON fixtures, swap to real data by:

  1. Identifying the source-of-truth tables in your warehouse:
     - GL actuals fact (period grain, GL id, amount, currency)
     - GL budget fact (same shape)
     - GL dimension (id, name, parent_id, sort order, active flag)
     - Cost center / department dimension
     - Vendor master
     - AP transaction fact (date, vendor, GL, CC, memo, amount, status)

  2. Building the SQL contracts documented in PROMPT 2.

  3. Mapping your fiscal calendar — confirm whether Q1 2026 = Jan-Mar 2026 or
     your fiscal-year offset.

  4. Currency: if you have multi-currency, decide whether the dashboard reports
     in functional currency only, or supports an FX toggle. Add to PeriodFilter.

  5. Permissions: filter results by the user's cost center scope.
     Implement at the SQL level — never trust the client.

  6. Materialize a quarterly aggregate table (e.g. mart_expense_quarterly) for
     anything below transaction grain. Hitting the warehouse for every KPI on
     every dashboard load will not scale.

  7. Build a nightly job that refreshes this mart and writes a "freshness"
     timestamp the dashboard displays in the topbar.


────────────────────────────────────────────────────────────────────────────
NOTES FOR YOU (the human)
────────────────────────────────────────────────────────────────────────────

  - The HTML prototype's data.js is a faithful schema for what the real backend
    needs to return. Hand it to your data engineer alongside this doc.

  - The `mode='budget'` vs `mode='prior'` distinction in VariancePill is a
    deliberate design choice — for expenses, growth (positive YoY) is generally
    not "good" the way revenue growth is, so we color YoY pills neutrally
    unless the magnitude is large. Push back if your CFO disagrees.

  - The transaction tab in production must paginate server-side. The prototype
    fakes it with .slice(0, 200) — that won't work against real ERP volume.

  - If MarketAxess uses Workday Adaptive / Anaplan / Oracle EPM for budget
    rather than an in-warehouse table, replace the budget fact in PROMPT 3
    with an API integration to that planning system instead.
