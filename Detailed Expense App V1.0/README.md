# Detailed Expense Analytics Dashboard

A production-grade Streamlit dashboard for analysing NetSuite expense exports with monthly trend analysis, category drill-downs, vendor breakdowns, and department/subsidiary reporting.

## Setup

1. **Place your data file:**
   The app expects the following CSV at the workspace root:
   ```
   Expense Export for App V1.0.csv
   ```
   Column requirements:
   | Column | Description |
   |--------|-------------|
   | `Line_Amount_USD_Reportable` | Transaction amount in USD |
   | `Accounting_Period_End_Date` | Period end date (ISO format) |
   | `Account_NetSuite_Name` | GL account — parsed as `Category : Subcategory` |
   | `Vendor_Name` | Vendor (may be blank for journal entries) |
   | `Department_Name` | Department |
   | `Subsidiary_Name_NetSuite` | Entity / subsidiary |
   | `Transaction_Type` | Journal, VendBill, ExpRept, etc. |

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

## Features

### Sidebar Filters
- **Date Range** — From / To date pickers (defaults to previous full calendar year)
- **Subsidiary** — Multi-select
- **Transaction Type** — Multi-select (Journal Entry, Vendor Bill, Expense Report, etc.)
- **Department** — Multi-select (100+ departments supported via built-in search)
- **Vendor Name Contains** — Free-text substring search
- **Exclude Intercompany** — Toggle to remove intercompany transactions
- **Top N in Charts** — Slider (5–50, default 15)

### KPI Row (5 metrics)
| Metric | Description |
|--------|-------------|
| Net Spend | Sum of amounts with % delta vs prior equivalent period |
| Transactions | Row count for selected filters |
| Avg Monthly Spend | Mean spend per calendar month |
| Top Vendor | Highest-spend vendor in the period |
| Top Department | Highest-spend department |

### Monthly Trend
- Line or bar chart, monthly granularity
- Optional breakdown by Subsidiary, Department, or Transaction Type

### Spend Breakdowns (4 tabs)
| Tab | Chart | Notes |
|-----|-------|-------|
| Account Category | Horizontal bar | Parsed from NetSuite account colon notation |
| ↳ Subcategory drilldown | Horizontal bar | Select any category or view all |
| Vendor | Horizontal bar | Toggle individual vendor vs vendor parent group |
| Department | Horizontal bar | Includes leading number prefix for sort order |
| Subsidiary | Pie + horizontal bar + table | Full entity comparison |

### Transaction Detail
- Expandable table showing up to 5,000 rows
- Download filtered data as CSV

## File Structure

```
Detailed Expense App V1.0/
├── app.py            # Main Streamlit application
├── data_loader.py    # CSV loading, date parsing, column derivation
├── analytics.py      # KPI and aggregation functions
├── requirements.txt  # Pinned Python dependencies
└── README.md         # This file
```

## Configuration

To change the CSV path, edit `CSV_PATH` in `data_loader.py`:
```python
CSV_PATH = Path(__file__).parent.parent / "Expense Export for App V1.0.csv"
```

## Currency Formatting

| Range | Format |
|-------|--------|
| ≥ $1M | $X.XM |
| ≥ $1K | $X.XK |
| < $1K | $X |

## Notes on Data

- **Amount sign**: `Line_Amount_USD_Reportable` can be negative (credits, reversals). All charts show **net** spend.
- **Journal entries**: Most rows are journal entries (`Transaction_Type = Journal`) and do not carry a vendor. The Vendor tab excludes these rows and displays a count.
- **Account hierarchy**: The colon-separated format `Category : Subcategory` in `Account_NetSuite_Name` is parsed automatically. The subcategory drilldown uses this split.

---

**Built with Streamlit, Plotly, and Pandas.**
