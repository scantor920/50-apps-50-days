# FP&A Dashboard Standards — MarketAxess

> Reusable template for FP&A analytics projects. Covers organizational model, data conventions, UX patterns, design system, and formatting rules. Drop this file into any new project workspace so an AI assistant or developer inherits the full context.
>
> Stack-agnostic — the specs describe *behavior* and *rules*, not implementation. Appendix A covers the current Streamlit reference implementation.

---

## 1) Role Context

The end user is Head of FP&A at MarketAxess. Dashboards serve:
- Variance analysis (actual vs. budget, actual vs. prior year)
- Organizational drill-down (Function → Department → ART-CPM → Account → Vendor)
- Headcount tracking (point-in-time counts, not dollars)
- Vendor spend intelligence
- Transaction-level auditability

Key stakeholder behaviors:
- Needs to quickly identify **what is driving a variance** and **who owns it**
- Drills from summary → detail; never starts at detail level
- Expects parentheses for negatives, never minus signs
- Expects $M at summary level, $K at detail level
- Compares either vs. Prior Year or vs. Budget (toggle)

---

## 2) Organizational Hierarchy

### 2.1 Structure

```
Function (6 values)
  └── Department (derived from Level Name)
        └── ART-CPM (46 values)
```

**Exception**: Technology & Research skips Department and goes directly Function → ART-CPM.

### 2.2 Functions (preferred display order)

| Raw Source Value     | Display Label          | Order |
|---------------------|------------------------|-------|
| TechnologyResearch  | Technology & Research  | 1     |
| Product             | Product                | 2     |
| SalesTrading        | Sales & Trading        | 3     |
| OpsMiddleOffice     | Ops & Middle Office    | 4     |
| Corporate           | Corporate              | 5     |
| Administration      | Administration         | 6     |

### 2.3 Department Derivation

- Parsed from `Level Name` column: right side of the hyphen delimiter
- Example: `"MAPT - 220 IT DEVELOPMENT"` → Department = `"220 IT Development"`
- Deduplicate case variants: prefer title-case over ALL CAPS
- Fallback to `Department_Reporting` column if no hyphen present

### 2.4 Corporate Department Ordering

When Function = Corporate, departments display in this order:
1. 105 Legal/Compliance
2. 110 Human Resources
3. 120 Marketing
4. 125 Finance
5. 115 Payroll/Human Resources
6. 127 Audit
7. 130 Risk
8. 132 Credit

**Consolidation groups** (optional toggle):
- "Finance, Marketing & Audit" = 125 Finance + 115 Payroll/Human Resources + 120 Marketing + 127 Audit
- "Risk & Credit" = 130 Risk + 132 Credit

### 2.5 ART-CPM

Column name in source data: `ART - CPM`
- 46 distinct values (e.g., "MGMT & General", "Core Trading", "Post Trade", "Open Trading")
- Used as the primary organizational breakdown for Technology & Research (skips Department)

---

## 3) Account Hierarchy (Expense Categories)

### 3.1 Structure

```
Level 0 (10 categories)
  └── Level 1
        └── Level 2
              └── Level 3
                    └── Level 4
                          └── Level 5
```

### 3.2 Level 0 Preferred Order

1. Employee Compensation & Benefits
2. Depreciation & Amortization
3. Professional & Consultancy
4. Technology
5. Communication
6. Clearing Fees
7. Marketing
8. Rent and Utilities
9. Travel & Entertainment
10. Other
11. Headcount *(non-dollar metric, always last)*

### 3.3 Label Normalization Rules

Applied to Level 0–5 and Account Name:
- Remove `(Summary)` suffix (case-insensitive)
- Remove leading account-code prefixes (e.g., `"601 - Travel"` → `"Travel"`)
- Canonical aliases:

| Source Variants | Canonical Label |
|----------------|----------------|
| Employee Compensation and Benefits | Employee Compensation & Benefits |
| Professional and Consulting / Professional & Consulting | Professional & Consultancy |
| Communications | Communication |
| Credit Clearing Fees / Clearing Fees and Commissions | Clearing Fees |
| Occupancy / Rent & Utilities | Rent and Utilities |
| Travel and Entertainment | Travel & Entertainment |
| Headcount (End of Period) | Headcount |

### 3.4 Guard Against NaN/Non-String

All text-cleaning functions must check `pd.isna(value)` and cast to `str` before applying `.replace()` or regex logic.

---

## 4) Data Model Conventions

### 4.1 Value Columns

| Column | Purpose | Usage |
|--------|---------|-------|
| `Working.Value` | Single source of truth for actuals/forecast | KPIs, trend, variance |
| `Budget.Value` | Budget comparison | Always from all filtered rows (not actuals-only) |
| `PriorYear.Amount` | Fallback prior-year value | Used when prior period labels have no data |
| `Actuals.Value` | Indicates closed months | Non-zero = month is closed |
| `NetSuite.Amount` | Transaction-level amounts | Transaction tab only |
| `NetSuite.TransactionCount` | Transaction counts | Transaction tab only |

### 4.2 Row Classification

- **Actuals row**: `Working.Value != 0`
- **NetSuite row**: `NetSuite.Amount != 0`
- **Headcount**: `Level 0 == "Headcount"` AND `Account Name contains "Regular Headcount"` (exclude Consultant, Temp, Intern, Vendor HC)
- **Unspecified**: `Level 0 == "Unspecified"` → filter out (orphan rows)

### 4.3 Period Model

- Periods are month-level labels: `Jan-25`, `Feb-25`, ..., `Apr-26`
- Quarters: `Q1 2026` = `[Jan-26, Feb-26, Mar-26]`
- YTD: all months in the latest year with data
- FY: all 12 months of a year
- Prior-year mapping: `Jan-26` → `Jan-25` (shift year by 1)

### 4.4 Headcount Rules

- **Point-in-time**: headcount is a count, not dollars — cannot be summed across time periods
- For multi-month periods (quarters, YTD), use only the **exit month** (last month in the period)
- Display as unrounded integers, not currency
- Only include "Regular Headcount" account rows

### 4.5 Partial-Period Detection

If any month in the selected period has `Actuals.Value == 0` for all rows, that month is "open" (forecast). The dashboard should:
- Label the KPI as "Forecast" instead of "Actual"
- Note which months are forecast in a footnote

---

## 5) Number Formatting Rules

| Context | Format | Example |
|---------|--------|---------|
| Summary KPIs | Millions with 1 decimal | $132.5M |
| Detailed KPIs | Millions with 2 decimals | $132.46M |
| Drill tables (Level 0–2) | Millions | $12.3M |
| Drill tables (Level 3+) | Thousands | $456.7K |
| Negatives | Parentheses | ($2.1M) |
| Percentages | 1 decimal + sign | +10.2% |
| Headcount | Integer, comma-separated | 1,247 |
| Negative headcount | Parentheses | (3) |
| N/A (zero base) | "n/a" | n/a |

---

## 6) Design System — MKTX Theme

### 6.1 Palette

**MKTX Dark Blue** (default):
```
--bg:           #0F2740
--bg-elev:      #14334F
--bg-sunk:      #0B2238
--ink:          #F5F8FC
--ink-2:        #D4E0EC
--ink-3:        #A8BCD3
--accent:       #6786B8
--accent-s:     #1D5B7F
--pos:          #76B34D      (favorable / under budget)
--pos-soft:     #1D3B2A
--neg:          #F3A2B6      (unfavorable / over budget)
--neg-soft:     #4B2430
--rule:         #2F4E6D
--tile:         #173857
--chart-surface:#1A3C5D
--grid:         #3A5A79
--shadow:       0 2px 10px rgba(0,0,0,.35)
--font:         Calibri, 'Segoe UI', sans-serif
```

**MKTX White**:
```
--bg: #FFFFFF, --ink: #090909, --accent: #1D5B7F, --neg: #A42A47, --pos: #76B34D
```

**MKTX Warm Light**:
```
--bg: #EFEDE7, --ink: #090909, --accent: #1D5B7F
```

### 6.2 Variance Color Convention

- **Over budget / overspend** = `--neg` (red/pink) — unfavorable
- **Under budget / underspend** = `--pos` (green) — favorable
- **Near zero / flat** = `--ink-2` (neutral)

For waterfall charts: bars going UP represent overspend (unfavorable).

### 6.3 Typography

- Font: Calibri, fallback Segoe UI, sans-serif
- KPI values: 1.65rem, weight 700, tabular-nums
- Section headers: 0.72rem, weight 700, uppercase, letter-spacing 0.1em, color `--ink-3`
- Table headers: 0.72rem, weight 700, uppercase, color `--ink-2`
- Table body: 0.82rem, tabular-nums

### 6.4 Component Patterns

**KPI Band**: 4-column grid of cards. First card highlighted with `--accent` top border.

**Themed HTML Table** (`.themed-table`):
- 1px solid `--rule` border, 8px radius
- Header: `--tile` background, 2px solid bottom border
- Rows: `--bg-elev` background, hover → `--tile`
- First column: font-weight 600, color `--ink-2`
- Numeric columns: right-aligned

**Drill Breadcrumb**: Flex row, `›` separators, active crumb in `--accent`

**Variance Pill**: Inline-flex, border-radius 99px, padding 0.18rem 0.5rem
- `.pill-pos`: background `--pos-soft`, color `--pos`
- `.pill-neg`: background `--neg-soft`, color `--neg`

---

## 7) Dashboard Tab Structure

### 7.1 Tab Layout

| # | Tab Name | Purpose |
|---|----------|---------|
| 01 | Overview | KPIs, trend, category breakdown, top accounts drill, vendors, movers |
| 02 | P&L | Waterfall bridge + progressive account hierarchy drill-down |
| 03 | Organization | Function → Dept → ART-CPM → Account → Vendor drill with headcount |
| 04 | Vendors | Vendor detail + deep-dive (accounts hit, org breakdown, trend) |
| 05 | Transactions | NetSuite transaction grid with search, filters, pagination |

### 7.2 Global Controls

- **View**: Aggregated (quarters) or Monthly
- **Period**: Adapts to view — quarter/year keys or month labels
- **Compare vs.**: Prior Year or Budget

### 7.3 Sidebar Filters

- Department (multiselect)
- Function (multiselect)
- Expense Category Level 0–5 (multiselect per level)
- Vendor Parent (multiselect)

All filters use explicit placeholder text, not generic "Choose Options".

---

## 8) Key UX Patterns

### 8.1 Progressive Drill-Down

Used in: Tab 01 (Top Accounts), Tab 02 (P&L), Tab 03 (Organization)

Pattern:
1. Display themed table at current hierarchy level
2. Breadcrumb showing drill path
3. Back / Reset navigation controls
4. Row selection mechanism → "Drill into [selection]" action
5. Drill path state persisted (session state, URL params, or store)

### 8.2 Waterfall Chart (Tab 02)

- Left bar: Prior Year (or Budget) total — absolute measure
- Middle bars: Category-level variances — relative measures
- Right bar: Current period total — total measure
- Colors: increasing (overspend) = `--neg`, decreasing (underspend) = `--pos`, totals = `--accent`
- Connectors between bars

### 8.3 Organization Drill Logic

```
For Technology & Research:  Function → ART-CPM → Level 0 → Level 1 → ... → Level 5
For all other functions:    Function → Department → ART-CPM → Level 0 → Level 1 → ... → Level 5
At deepest level:           Show vendor breakdown
```

At each level, display:
- Expense table (actual, comparison, variance $, variance %, % of total)
- Headcount table (actual HC, budget HC, variance)
- Variance chart (horizontal bar)

### 8.4 Vendor Deep-Dive (Tab 04)

For a selected vendor, show:
- **Accounts hit**: Level 0, Level 1, Account Name with spend/comparison/variance
- **Organizational footprint**: breakdown by Function, Department, ART-CPM
- **Monthly spend trend**: bar chart by period

### 8.5 Headcount Display

- Separate from dollar metrics — never sum across time periods
- Show actual vs. budget at each organizational level
- Use integer formatting, not currency
- At Level 0, Headcount row formatted differently from dollar rows in same table

---

## 9) Validated Benchmarks (Q1 2026)

Use these to validate any reimplementation:

| Metric | Expected Value |
|--------|---------------|
| Total Actual | ~$132.5M |
| Prior-Year Delta | ~+$12.3M (+10.2%) |
| Budget Variance | ~+$2.0M (+1.6%) |
| Functions | 6 (after relabeling) |
| Departments | ~54 |
| ART-CPMs | 46 |
| Level 0 Categories | 10 + Headcount |

---

## 10) Data Pipeline Requirements

Regardless of stack, any implementation must perform these steps at data load:

1. Read source data with explicit column selection (minimize memory)
2. Numeric coercion on all value columns + fill nulls with 0
3. Date parsing + drop rows with no valid date
4. Text column cleanup (strip whitespace, NaN/None/empty → "Unspecified")
5. Account label normalization (aliases from Section 3.3, prefix removal)
6. Department derivation from Level Name (Section 2.3)
7. Department deduplication (case-insensitive, prefer title-case variant)
8. Function label normalization (Section 2.2)
9. Vendor dimension resolution (`Vendor Parent` preferred, fallback to `Vendor`)
10. Remove rows with no Level 0 classification (orphan rows)
11. Headcount filtering: keep only "Regular Headcount" account rows

---

## 11) Architecture Considerations

This spec is stack-agnostic. When choosing an implementation:

### For rapid prototyping / internal use
- Python + Streamlit or Dash
- pandas for transforms, Plotly for charts
- Single-file or small module structure
- Local CSV or database connection

### For production / multi-user deployment
- React + TypeScript (Vite or Next.js)
- State management (Zustand, URL params) for drill state
- TanStack Table for transaction grids
- API backend (Node/Express, FastAPI) proxying warehouse
- Server-side pagination for large datasets
- Role-based access control at the API layer

### Key logic to port between stacks
1. Period/prior-year mapping logic
2. Actual vs. budget row-source distinction (`Working.Value != 0`)
3. Level 0 ordering and label normalization
4. Department derivation from Level Name
5. Function relabeling and ordering
6. Number scaling ($M ↔ $K by hierarchy depth)
7. Headcount point-in-time rules (exit month only)
8. Organization hierarchy with Tech & Research exception
9. Corporate department grouping/consolidation

---

## 12) Quick Validation Checklist

After any rebuild or major change:

- [ ] Default theme is MKTX Dark Blue
- [ ] Department filter values = right-of-hyphen from Level Name
- [ ] Q1 2026 budget variance ≈ +$2.0M (benchmark)
- [ ] Top Accounts Level 0 order matches Section 3.2
- [ ] Functions display in preferred order (Section 2.2)
- [ ] Technology & Research skips Department in org drill
- [ ] Corporate departments in custom order with consolidation toggle
- [ ] Headcount shows as integers, not currency
- [ ] Waterfall has starting bar (comp) on left, ending bar (actual) on right
- [ ] Negative values use parentheses format
- [ ] P&L drill goes all the way from Level 0 to Level 5
- [ ] Vendor deep-dive shows accounts, org breakdown, and trend

---

## Appendix A) Current Reference Implementation (Streamlit)

| Detail | Value |
|--------|-------|
| Stack | Python 3.13, Streamlit, pandas, Plotly |
| Entry point | `app.py` (single file) |
| Data source | `Expense Dashboard Data.csv` (local) |
| Run command | `python -m streamlit run app.py --server.port 8501 --server.headless true` |
| Theme config | `.streamlit/config.toml` (base=dark) |
| Caching | `@st.cache_data` on CSV load |
| Drill state | `st.session_state` dictionaries |
| Themed tables | HTML via `st.markdown(unsafe_allow_html=True)` |
| Charts | `plotly.graph_objects` with custom layout helper |

---

## Appendix B) File Inventory (Expense Dashboard V2.0)

| File | Purpose |
|------|---------|
| `app.py` | Active dashboard application code |
| `fpa-dashboard-standards.md` | This reusable spec (you are here) |
| `claude.md` | Original project handoff (historical) |
| `Markdown.md` | Original React architecture prompt package |
| `Expense Dashboard Data.csv` | Source dataset |
| `MKTX Theme.thmx` | Source theme file |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | Streamlit dark theme config |
