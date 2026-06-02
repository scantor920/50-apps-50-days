# Vendor Spend Analytics Dashboard

A production-grade Streamlit dashboard for analyzing vendor spend trends, detecting anomalies, and visualizing spend concentration.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare data:**
   - Place an Excel file named `vendor_spend.xlsx` in the app directory
   - Schema: Column 1 = Vendor name, Columns 2+ = Quarter columns (e.g., "Q1 2019", "Q2 2019", ... "Q4 2026")
   - To generate sample data, run one of:
     ```bash
     python generate_sample_data.py          # Requires pandas
     # OR
     python generate_sample_data_simple.py   # Only requires openpyxl
     ```

3. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

## Features

- **KPI Metrics**: Total spend, vendor count, average quarterly spend, top vendor (with YoY delta)
- **Top Vendors**: Rank by total spend, average quarterly, or growth rate (latest vs. earliest quarter)
- **Spend Trends**: Line chart with projected quarters highlighted (dashed line, shaded background)
- **YoY Analysis**: Year-over-year % change by quarter
- **Pareto Analysis**: Spend concentration by vendor with cumulative % and 80% threshold annotation
- **Anomaly Detection**: Z-score based flagging of unusual quarter-vendor spend deviations (>2σ from 4-quarter rolling mean); excludes projections from baseline. Sortable table + scatter plot.

## Sidebar Filters

- **Quarter Range**: Slider to select date range (Q1 2019 through Q4 2026)
- **Vendors**: Multiselect dropdown (default: all vendors)
- **Include Projections**: Toggle to include/exclude projected quarters (Q1 2026 onward)
- **Top N Vendors**: Slider (5–50, default 10)
- **Show Anomalies**: Toggle to display anomaly section

## File Structure

```
streamlit-vendor-dashboard/
├── app.py                    # Main Streamlit application
├── data_loader.py            # Data loading and transformation logic
├── analytics.py              # Analytics calculations
├── requirements.txt          # Python dependencies (pinned versions)
├── generate_sample_data.py   # Utility to create sample vendor_spend.xlsx
├── vendor_spend.xlsx         # [Generated] Excel data file
└── README.md                 # This file
```

## Configuration

To use a different Excel file path, edit the `EXCEL_PATH` variable in `data_loader.py`:

```python
EXCEL_PATH = Path(__file__).parent / "your_file.xlsx"
```

To adjust the projection cutoff quarter (e.g., Q1 2025 instead of Q1 2026), edit:

```python
PROJECTION_START = (2025, 1)  # (year, quarter_num)
```

## Currency Formatting

Values are displayed as:
- `$X.XM` for millions (e.g., $5.2M)
- `$X.XK` for thousands (e.g., $123.5K)
- `$X` for values < $1,000

## Edge Cases Handled

- Empty filter selections gracefully fall back to showing all vendors
- Single-vendor selection works correctly for trends and Pareto
- All-projected date ranges display with visual distinction
- Anomaly detection skips vendors with insufficient historical data
- NaN/missing values in Spend column are dropped during load

## Technical Details

- **Data Format**: Wide to long format melt with proper quarter parsing
- **Caching**: `@st.cache_data` on data load for performance
- **Type Hints**: Full type annotations on all functions
- **Plotting**: Plotly for interactivity (no matplotlib)
- **Error Handling**: User-friendly error messages for missing/malformed data

---

**Built with Streamlit, Plotly, and Pandas.**
