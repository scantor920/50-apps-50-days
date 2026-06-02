# Expense Dashboard

This project implements the COPILOT_HANDOFF build sequence as a React + TypeScript + Vite dashboard with a secure Express route layer.

## Implemented prompts

1. Project bootstrap with strict TypeScript, ESLint, Prettier, and required folders.
2. Exact type contracts in `src/data/types.ts`.
3. Typed API client and React Query data hooks with SQL contract comments.
4. Express backend route layer with zod validation, period/date resolution, parameterized SQL, server cache, security middleware, audit logging, and health endpoint.
5. Design tokens for 5 themes and `useTheme` localStorage persistence.
6. Shared primitives (`KpiTile`, `VariancePill`, `Breadcrumb`, chips/selectors, etc.).
7. Charts (`TrendChart`, `VarianceBridge`, `GroupedBars`, `CompositionBar`).
8. Drill-down zustand store and URL query synchronization.
9. Tab pages: Overview, P&L, Cost Centers, Vendors, Transactions.
10. App shell, sticky topbar, nav routing, period and theme controls.
11. Test and accessibility scaffolding with Vitest, React Testing Library, and axe checks.

## Local setup

1. Install Node.js 20+.
2. Run `npm install` in this folder.
3. Copy `.env.example` to `.env` and fill database credentials.
4. Run frontend: `npm run dev`
5. Run backend: `npm run dev:server`

## Real data wiring checklist

- Confirm warehouse source tables for actuals, budgets, dimensions, and AP transactions.
- Confirm fiscal calendar mapping (calendar quarter vs fiscal offset).
- Decide currency behavior (single functional currency vs FX toggle).
- Add SQL-level user scope filters by cost center.
- Materialize and refresh a quarterly aggregate mart for dashboard performance.
- Expose data freshness timestamp in topbar.

## Notes

- Backend is currently configured for Postgres via `pg`. To swap drivers, replace `server/lib/db.ts` and route SQL syntax as needed.
- `useAuth` is a stub in `src/lib/auth.ts` and should be replaced with your identity provider.
