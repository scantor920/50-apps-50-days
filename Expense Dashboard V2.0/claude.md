# Claude Handoff: Expense Dashboard V2.0

## 1) Executive Summary

This project began from a React + TypeScript architecture brief in Markdown.md, but implementation was completed as a Python Streamlit dashboard due local environment constraints (Node/npm unavailable during development).

The current production artifact is:
- app.py (single-file Streamlit app)
- Expense Dashboard Data.csv (source data)
- requirements.txt (streamlit, pandas, plotly)

The dashboard is designed for local hosting and currently runs at:
- http://localhost:8501

## 2) Source of Truth

Use these files as authoritative:
- Markdown.md: original target architecture and UX goals (React-first blueprint).
- app.py: actual implemented behavior and current working product.
- Expense Dashboard Data.csv: input data model.
- MKTX Theme.thmx: source for MarketAxess palette.

## 3) Key Constraints and Why Architecture Pivoted

Original brief requested React/Vite stack with layered APIs. During build:
- Node/npm tooling was unavailable.
- A working local solution was still required immediately.

Result:
- Implemented dashboard in Streamlit with pandas + plotly.
- Preserved core business outcomes from the React brief (filtering, drill paths, variances, trends, vendor views, transaction grid behavior) in a pragmatic local-host setup.

## 4) Current App Capabilities

### 4.1 Dashboard Views and Controls
- View selector: Aggregated or Monthly.
- Period selector adapts to view:
  - Aggregated: quarter/year buckets (for example Q1 2026, YTD 2026).
  - Monthly: month-level keys (for example Jan-26, Feb-26, Mar-26).
- Compare selector: Prior Year or Budget.
- Tabs:
  - 01 Overview
  - 02 Transactions

### 4.2 Sidebar Filters
Current filters:
- Department (derived from Level Name, right side of hyphen, with fallback)
- Function
- Expense Category Level 0
- Expense Category Level 1
- Expense Category Level 2
- Expense Category Level 3
- Expense Category Level 4
- Expense Category Level 5
- Vendor Parent

All multiselect controls include explicit placeholders (not generic "Choose Options").

### 4.3 KPI and Variance Logic
Core KPI logic is now corrected and validated:
- Actuals sourced from rows where Actuals.Value != 0.
- Budget sourced from all filtered rows (not only actual rows).
- Prior-year comparison built via period-label mapping (for example Jan-26 maps to Jan-25).

Known validated snapshot for Q1 2026:
- Actual: about $132.5M
- Prior-year delta: about +$12.3M (+10.2%)
- Budget variance: about +$2.0M (+1.6%)

### 4.4 Number Scaling Rules
- Dashboard numbers default to millions ($M).
- Drill table (Top Accounts by Spend) switches to thousands ($K) at deeper hierarchy levels (Level 3+).
- Negative values in table displays use parentheses format.

### 4.5 Top Accounts by Spend
- Drillable hierarchy enabled across Level 0 to Level 5.
- Back/Reset controls included.
- Level 0 rows ordered to user-required sequence:
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

### 4.6 Spend by Category and Top Movers
- Spend by Category now uses Level 0 categories and follows the same preferred ordering.
- Top Movers vs Budget uses Level 0 categories and follows the same preferred ordering.

### 4.7 Vendor and Transaction Behavior
- Vendor analytics default to Vendor Parent dimension.
- Transactions tab supports:
  - search
  - entry type segmentation (all/positive/negative)
  - pagination
  - filtered table rendering

## 5) Theme and Styling State (MKTX)

### 5.1 Theme Inputs
Palette extracted from MKTX Theme.thmx and mapped to app CSS tokens.

### 5.2 Background Options
Current background selector includes:
- MKTX Dark Blue (default)
- MKTX White
- MKTX Warm Light

### 5.3 Consistency Rules Applied
- Buttons styled to avoid unreadable foreground/background collisions.
- Axis labels and chart text made readable against themed chart surfaces.
- Sidebar and main canvas receive explicit tokenized styling.

## 6) Data Normalization Rules Implemented

To stabilize reporting labels and ordering:
- Removed "(Summary)" suffix variants case-insensitively.
- Removed account-code prefixes from rollup labels.
- Canonicalized Level 0 aliases, including common naming variants:
  - "Employee Compensation and Benefits" -> "Employee Compensation & Benefits"
  - "Professional and Consulting" -> "Professional & Consultancy"
  - "Communications" -> "Communication"
  - "Credit Clearing Fees" -> "Clearing Fees"
  - "Occupancy" -> "Rent and Utilities"
  - "Travel and Entertainment" -> "Travel & Entertainment"

Robustness fix included:
- text-cleaning functions now guard against NaN/non-string values before replacement logic.

## 7) Comparison to Original Markdown.md Blueprint

Original Markdown.md requested:
- React + TypeScript + Vite app
- 5-tab strict funnel
- routed API backend
- reusable component architecture

Current implemented app:
- Streamlit (Python) MVP with production-usable behavior for requested analytics and UX refinements.
- 2-tab structure (Overview + Transactions) with deep drill hierarchy and cross-filtering.
- No standalone API layer yet; all logic is local pandas over CSV.

This is a deliberate execution pivot to deliver immediate value under tooling constraints.

## 8) If You Continue in Streamlit

Recommended near-term enhancements:
1. Add persisted user state (saved filter presets, default period/theme per user).
2. Add export controls (CSV/XLSX) for key tables with current filters applied.
3. Add data freshness stamp and optional refresh cadence.
4. Add automated data QA checks at load time (schema, null rates, outlier flags).

## 9) If You Migrate Back to React Stack

Use Markdown.md as architecture target and app.py as business-logic reference.

Port these first:
- period/prior mapping logic
- actual vs budget row-source logic
- Level 0 ordering and label normalization
- Department derivation from Level Name
- number scaling behavior ($M baseline, deeper drill $K)

Then re-platform UI components incrementally.

## 10) Runbook

### Install
- pip install -r requirements.txt

### Run
- python -m streamlit run app.py --server.port 8501 --server.headless true

### Quick validation checklist
1. Open app and confirm default background is MKTX Dark Blue.
2. Confirm Department filter values align with right-of-hyphen from Level Name.
3. Confirm Q1 2026 budget variance is approximately +$2.0M.
4. Confirm Top Accounts Level 0 order matches required sequence.
5. Confirm Spend by Category and Top Movers follow same Level 0 ordering.
6. Confirm Top Accounts drill displays $K at deeper levels.

## 11) Current File Inventory

- app.py: active dashboard application code.
- claude.md: this consolidated handoff.
- Markdown.md: original architecture prompt package.
- Expense Dashboard Data.csv: source dataset.
- MKTX Theme.thmx: source theme file.
- requirements.txt: Python dependencies.
- diagnose.py: optional utility script used during diagnostics.
