from __future__ import annotations

from pathlib import Path
import datetime as _dt
import re
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = "Expense Dashboard Data.csv"
PAGE_SIZE = 200
LEVEL_COLUMNS = ["Level 0", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]

# Function label normalization
FUNCTION_LABELS: dict[str, str] = {
    "TechnologyResearch": "Technology & Research",
    "SalesTrading": "Sales & Trading",
    "OpsMiddleOffice": "Ops & Middle Office",
    "Corporate": "Corporate",
    "Administration": "Administration",
    "Product": "Product",
}
PREFERRED_FUNCTION_ORDER = [
    "Technology & Research",
    "Product",
    "Sales & Trading",
    "Ops & Middle Office",
    "Corporate",
    "Administration",
]

# Corporate department ordering and grouping
CORPORATE_DEPT_ORDER = [
    "105 Legal/Compliance",
    "110 Human Resources",
    "120 Marketing",
    "125 Finance",
    "115 Payroll/Human Resources",
    "127 Audit",
    "130 Risk",
    "132 Credit",
]
CORPORATE_DEPT_GROUPS: dict[str, list[str]] = {
    "Finance, Marketing & Audit": ["125 Finance", "115 Payroll/Human Resources", "120 Marketing", "127 Audit"],
    "Risk & Credit": ["130 Risk", "132 Credit"],
}

STATIC_PERIOD_OPTIONS = {
    "Q1 2025": ["Jan-25", "Feb-25", "Mar-25"],
    "Q2 2025": ["Apr-25", "May-25", "Jun-25"],
    "Q3 2025": ["Jul-25", "Aug-25", "Sep-25"],
    "Q4 2025": ["Oct-25", "Nov-25", "Dec-25"],
    "FY 2025": [
        "Jan-25",
        "Feb-25",
        "Mar-25",
        "Apr-25",
        "May-25",
        "Jun-25",
        "Jul-25",
        "Aug-25",
        "Sep-25",
        "Oct-25",
        "Nov-25",
        "Dec-25",
    ],
    "Q1 2026": ["Jan-26", "Feb-26", "Mar-26"],
    "Q2 2026": ["Apr-26", "May-26", "Jun-26"],
}
DEFAULT_PERIOD = "Q1 2026"
DEFAULT_MONTH = "Mar-26"

# Reverse lookup: month labels → quarter key
MONTH_TO_QUARTER: dict[str, str] = {}
for _qk, _months in STATIC_PERIOD_OPTIONS.items():
    if _qk.startswith("Q"):
        for _m in _months:
            MONTH_TO_QUARTER[_m] = _qk


def build_period_options(available_labels: set[str]) -> dict[str, list[str]]:
    """Build period options including a dynamic YTD entry based on available data."""
    opts = {k: v for k, v in STATIC_PERIOD_OPTIONS.items() if any(m in available_labels for m in v)}
    # Determine the latest year with data and build YTD dynamically
    latest_year: int | None = None
    for label in available_labels:
        try:
            yr = int(label.split("-")[1]) + 2000
            if latest_year is None or yr > latest_year:
                latest_year = yr
        except (ValueError, IndexError):
            continue
    if latest_year:
        yr_suffix = f"{latest_year % 100:02d}"
        ytd_months = [m for m in ALL_PERIODS_ORDERED if m.endswith(f"-{yr_suffix}") and m in available_labels]
        if ytd_months:
            opts[f"YTD {latest_year}"] = ytd_months
    return opts

ALL_PERIODS_ORDERED = [
    "Jan-25",
    "Feb-25",
    "Mar-25",
    "Apr-25",
    "May-25",
    "Jun-25",
    "Jul-25",
    "Aug-25",
    "Sep-25",
    "Oct-25",
    "Nov-25",
    "Dec-25",
    "Jan-26",
    "Feb-26",
    "Mar-26",
    "Apr-26",
]

THEMES: dict[str, dict[str, str]] = {
    "MKTX Dark Blue": {
        "--bg": "#0F2740",
        "--bg-elev": "#14334F",
        "--bg-sunk": "#0B2238",
        "--ink": "#F5F8FC",
        "--ink-2": "#D4E0EC",
        "--ink-3": "#A8BCD3",
        "--accent": "#6786B8",
        "--accent-s": "#1D5B7F",
        "--pos": "#76B34D",
        "--pos-soft": "#1D3B2A",
        "--neg": "#F3A2B6",
        "--neg-soft": "#4B2430",
        "--rule": "#2F4E6D",
        "--tile": "#173857",
        "--shadow": "0 2px 10px rgba(0,0,0,.35)",
        "--font": "Calibri, 'Segoe UI', sans-serif",
        "--plotly-bg": "rgba(0,0,0,0)",
        "--grid": "#3A5A79",
        "--chart-surface": "#1A3C5D",
    },
    "MKTX White": {
        "--bg": "#FFFFFF",
        "--bg-elev": "#FFFFFF",
        "--bg-sunk": "#E7E2D9",
        "--ink": "#090909",
        "--ink-2": "#636569",
        "--ink-3": "#848486",
        "--accent": "#1D5B7F",
        "--accent-s": "#6786B8",
        "--pos": "#76B34D",
        "--pos-soft": "#E9F4E2",
        "--neg": "#A42A47",
        "--neg-soft": "#F7E6EA",
        "--rule": "#D6D2C8",
        "--tile": "#FFFFFF",
        "--shadow": "0 2px 8px rgba(9,9,9,.08)",
        "--font": "Calibri, 'Segoe UI', sans-serif",
        "--plotly-bg": "rgba(255,255,255,0)",
        "--grid": "#E3DED4",
        "--chart-surface": "#DDE8F1",
    },
    "MKTX Warm Light": {
        "--bg": "#EFEDE7",
        "--bg-elev": "#FFFFFF",
        "--bg-sunk": "#E7E2D9",
        "--ink": "#090909",
        "--ink-2": "#636569",
        "--ink-3": "#848486",
        "--accent": "#1D5B7F",
        "--accent-s": "#6786B8",
        "--pos": "#76B34D",
        "--pos-soft": "#E9F4E2",
        "--neg": "#A42A47",
        "--neg-soft": "#F7E6EA",
        "--rule": "#D6D2C8",
        "--tile": "#FFFFFF",
        "--shadow": "0 2px 8px rgba(9,9,9,.08)",
        "--font": "Calibri, 'Segoe UI', sans-serif",
        "--plotly-bg": "rgba(255,255,255,0)",
        "--grid": "#E3DED4",
        "--chart-surface": "#DDE8F1",
    },
}

st.set_page_config(
    page_title="Expense Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme(theme_name: str) -> None:
    t = THEMES[theme_name]
    vars_block = "\n".join(f"  {k}: {v};" for k, v in t.items())
    st.markdown(
        f"""
<style>
:root {{
{vars_block}
}}

[data-testid="stApp"], .stApp {{
  background-color: var(--bg) !important;
  font-family: var(--font) !important;
  color: var(--ink) !important;
}}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    background-color: var(--bg) !important;
}}

[data-testid="stSidebar"] {{
  background-color: var(--bg-elev) !important;
  border-right: 1px solid var(--rule) !important;
}}

.stButton > button {{
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent) !important;
}}

[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"] {{
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent) !important;
}}

.stButton > button:hover {{
    background-color: var(--accent-s) !important;
    border-color: var(--accent-s) !important;
    color: #FFFFFF !important;
}}

[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-primary"]:hover {{
    background-color: var(--accent-s) !important;
    border-color: var(--accent-s) !important;
    color: #FFFFFF !important;
}}

.stButton > button:disabled {{
    background-color: var(--bg-sunk) !important;
    color: var(--ink-3) !important;
    border-color: var(--rule) !important;
}}

[data-baseweb="select"] > div,
[data-baseweb="base-input"] > div,
[data-testid="stNumberInput"] input,
[data-testid="stMultiSelect"] > div,
[data-testid="stDateInput"] input {{
    background-color: var(--bg-elev) !important;
    color: var(--ink) !important;
    border-color: var(--rule) !important;
}}

label, .stSelectbox label, .stMultiSelect label, .stTextInput label {{
    color: var(--ink) !important;
}}

h1, h2, h3 {{
  color: var(--ink) !important;
  font-family: var(--font) !important;
}}

.stMarkdown p {{
  color: var(--ink-2) !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
  background: transparent !important;
  border-bottom: 2px solid var(--rule) !important;
}}

[data-testid="stTabs"] [data-baseweb="tab"] {{
  background: transparent !important;
  color: var(--ink-2) !important;
  border: none !important;
  padding: 0.5rem 1.2rem !important;
  font-weight: 600 !important;
}}

[data-testid="stTabs"] [aria-selected="true"] {{
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
}}

.kpi-band {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}}

.kpi-card {{
  background: var(--tile);
  border: 1px solid var(--rule);
  border-top: 3px solid var(--rule);
  border-radius: 10px;
  padding: 1rem 1.1rem 0.85rem;
  box-shadow: var(--shadow);
}}

.kpi-card.hl {{
  border-top-color: var(--accent);
}}

.kpi-eyebrow {{
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3) !important;
  margin-bottom: 0.3rem;
}}

.kpi-value {{
  font-size: 1.65rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--ink) !important;
  line-height: 1.15;
}}

.kpi-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  margin-top: 0.35rem;
  padding: 0.18rem 0.5rem;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}}

.pill-pos {{ background: var(--pos-soft); color: var(--pos) !important; }}
.pill-neg {{ background: var(--neg-soft); color: var(--neg) !important; }}
.pill-flat {{ background: var(--bg-sunk); color: var(--ink-2) !important; }}

.section-header {{
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3) !important;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.3rem;
  margin: 1.2rem 0 0.6rem;
}}

[data-testid="stDataFrame"] {{
  border: 1px solid var(--rule) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}}

[data-testid="stDataFrame"] table {{
  font-variant-numeric: tabular-nums;
}}

[data-testid="stDataFrame"] th {{
  background: var(--bg-sunk) !important;
  color: var(--ink-3) !important;
  font-size: 0.75rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  border-bottom: 2px solid var(--rule) !important;
}}

[data-testid="stDataFrame"] td {{
  color: var(--ink) !important;
  font-size: 0.82rem !important;
  border-bottom: 1px solid var(--rule) !important;
}}

.themed-table {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--rule);
  border-radius: 8px;
  overflow: hidden;
  font-variant-numeric: tabular-nums;
  font-size: 0.82rem;
}}

.themed-table thead th {{
  background: var(--tile);
  color: var(--ink-2);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.6rem 0.7rem;
  border-bottom: 2px solid var(--rule);
  text-align: left;
  white-space: nowrap;
}}

.themed-table thead th:not(:first-child) {{
  text-align: right;
}}

.themed-table tbody tr {{
  background: var(--bg-elev);
  transition: background 0.15s;
}}

.themed-table tbody tr:hover {{
  background: var(--tile);
}}

.themed-table tbody td {{
  color: var(--ink);
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid var(--rule);
  white-space: nowrap;
}}

.themed-table tbody td:not(:first-child) {{
  text-align: right;
}}

.themed-table tbody td:first-child {{
  font-weight: 600;
  color: var(--ink-2);
}}

.drill-breadcrumb {{
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  color: var(--ink-3);
  margin-bottom: 0.3rem;
}}

.drill-breadcrumb .crumb {{
  color: var(--ink-2);
  font-weight: 600;
}}

.drill-breadcrumb .crumb-active {{
  color: var(--accent);
  font-weight: 700;
}}

.dash-footer {{
  font-size: 0.72rem;
  color: var(--ink-3) !important;
  margin-top: 2rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--rule);
}}

@media (max-width: 900px) {{
  .kpi-band {{
    grid-template-columns: repeat(2, 1fr);
  }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    cols = [
        "Vendor",
        "Vendor Parent",
        "Account Code",
        "Account Name",
        "Level Name",
        "Department_Reporting",
        "Date Label",
        "Start Date",
        "Function",
        "ART - CPM",
        "Org_Level_1",
        "Org_Level_2",
        "Level 0",
        "Level 1",
        "Level 2",
        "Level 3",
        "Level 4",
        "Level 5",
        "Actuals.Value",
        "Working.Value",
        "Budget.Value",
        "PriorYear.Amount",
        "NetSuite.Amount",
        "NetSuite.TransactionCount",
    ]

    df = pd.read_csv(csv_path, usecols=cols, low_memory=False)

    # Schema validation: ensure all expected columns are present
    missing = set(cols) - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing expected columns: {sorted(missing)}")

    num_cols = [
        "Actuals.Value",
        "Working.Value",
        "Budget.Value",
        "PriorYear.Amount",
        "NetSuite.Amount",
        "NetSuite.TransactionCount",
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df = df.dropna(subset=["Start Date"]).copy()

    text_cols = [
        "Vendor",
        "Vendor Parent",
        "Account Code",
        "Account Name",
        "Level Name",
        "Department_Reporting",
        "Date Label",
        "Function",
        "ART - CPM",
        "Org_Level_1",
        "Org_Level_2",
        "Level 0",
        "Level 1",
        "Level 2",
        "Level 3",
        "Level 4",
        "Level 5",
    ]
    for col in text_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .replace({"": "Unspecified", "None": "Unspecified", "nan": "Unspecified"})
        )

    for col in ["Level Name", "Level 5"]:
        if col not in df.columns:
            df[col] = "Unspecified"

    # Normalize labels used across rollups so account numbers are hidden in hierarchy views.
    def _clean_rollup_label(text: str) -> str:
        if pd.isna(text):
            return "Unspecified"
        if not isinstance(text, str):
            text = str(text)
        text = re.sub(r"\(\s*summary\s*\)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^[A-Za-z0-9]{3,}\s*[-:]\s*", "", text)
        text = text.strip()

        aliases = {
            "employee compensation & benefits": "Employee Compensation & Benefits",
            "employee compensation and benefits": "Employee Compensation & Benefits",
            "depreciation and amortization": "Depreciation & Amortization",
            "professional and consulting": "Professional & Consultancy",
            "professional & consulting": "Professional & Consultancy",
            "communications": "Communication",
            "communication": "Communication",
            "credit clearing fees": "Clearing Fees",
            "clearing fees": "Clearing Fees",
            "clearing fees and commissions": "Clearing Fees",
            "occupancy": "Rent and Utilities",
            "rent & utilities": "Rent and Utilities",
            "travel and entertainment": "Travel & Entertainment",
            "headcount (end of period)": "Headcount",
        }
        text = aliases.get(text.lower(), text)
        return text.strip() or "Unspecified"

    for col in ["Account Name", *LEVEL_COLUMNS]:
        df[col] = df[col].map(_clean_rollup_label)

    level_name_right = df["Level Name"].where(df["Level Name"].str.contains("-", regex=False), "")
    df["Department"] = level_name_right.str.split("-", n=1).str[-1].str.strip()
    df["Department"] = df["Department"].replace({"": "Unspecified"})
    df["Department"] = df["Department"].where(df["Department"] != "Unspecified", df["Department_Reporting"])

    # Deduplicate departments: prefer non-all-caps (title-case) variants
    dept_values = df["Department"].unique()
    dept_lower_map: dict[str, str] = {}
    for d in dept_values:
        key = d.lower()
        if key not in dept_lower_map:
            dept_lower_map[key] = d
        else:
            existing = dept_lower_map[key]
            # Prefer the version that is NOT all uppercase
            if existing == existing.upper() and d != d.upper():
                dept_lower_map[key] = d
    dept_canonical = {d: dept_lower_map[d.lower()] for d in dept_values}
    df["Department"] = df["Department"].map(dept_canonical)

    # Normalize Function labels
    df["Function"] = df["Function"].fillna("Unspecified").map(lambda f: FUNCTION_LABELS.get(f, f))

    df["vendor_dim"] = df["Vendor Parent"].where(df["Vendor Parent"] != "Unspecified", df["Vendor"])

    # Remove rows with no Level 0 classification (orphan headcount "Net of Vacancy" rows)
    df = df[df["Level 0"] != "Unspecified"].copy()

    # Headcount: only keep "Regular Headcount" rows; drop Consultant, Temp, Intern, Vendor HC
    hc_mask = df["Level 0"] == "Headcount"
    regular_hc_mask = df["Account Name"].str.contains("Regular Headcount", case=False, na=False)
    df = df[~hc_mask | regular_hc_mask].copy()

    df["is_actuals_row"] = df["Working.Value"] != 0
    df["is_netsuite_row"] = df["NetSuite.Amount"] != 0
    return df


def fmt_short_dollars(val: float, decimals: int = 1) -> str:
    core = f"${abs(val)/1_000_000:,.{decimals}f}M"
    return f"({core})" if val < 0 else core


def fmt_full_dollars(val: float) -> str:
    return f"${val:,.0f}"


def fmt_millions_paren(val: float, decimals: int = 1) -> str:
    core = f"${abs(val)/1_000_000:,.{decimals}f}M"
    return f"({core})" if val < 0 else core


def fmt_thousands_paren(val: float, decimals: int = 1) -> str:
    core = f"${abs(val)/1_000:,.{decimals}f}K"
    return f"({core})" if val < 0 else core


def fmt_currency_by_level(val: float, level_idx: int) -> str:
    return fmt_thousands_paren(val) if level_idx >= 3 else fmt_millions_paren(val)


def fmt_headcount(val: float) -> str:
    """Format a headcount value as an unrounded integer."""
    v = int(round(val))
    if v < 0:
        return f"({abs(v):,})"
    return f"{v:,}"


def fmt_pct_paren(val: float, decimals: int = 1) -> str:
    if pd.isna(val):
        return "n/a"
    core = f"{abs(val):,.{decimals}f}%"
    return f"({core})" if val < 0 else core


def variance_pill(delta: float, base: float) -> str:
    if base == 0:
        return '<span class="kpi-pill pill-flat">n/a</span>'
    pct = delta / base * 100
    direction = "+" if delta >= 0 else ""
    css = "pill-neg" if delta > 0 else "pill-pos"
    return (
        f'<span class="kpi-pill {css}">'
        f"{direction}{fmt_short_dollars(delta)} ({pct:+.1f}%)"
        f"</span>"
    )


def prior_period_labels(current_labels: list[str], available_labels: set[str]) -> list[str]:
    out: list[str] = []
    for label in current_labels:
        try:
            month, year = label.split("-")
            prior = f"{month}-{int(year) - 1:02d}"
            if prior in available_labels:
                out.append(prior)
        except ValueError:
            continue
    return out


def _hc_exit_only(data: pd.DataFrame, period_labels: list[str]) -> pd.DataFrame:
    """For headcount rows, keep only the exit (last) month.

    Headcount is a point-in-time count and must not be summed across months.
    For multi-month periods (quarters, YTD), use the period-ending month value.
    """
    if len(period_labels) <= 1 or data.empty:
        return data
    exit_month = period_labels[-1]
    hc = data["Level 0"] == "Headcount"
    if not hc.any():
        return data
    return pd.concat([data[~hc], data[hc & (data["Date Label"] == exit_month)]])


def plotly_layout(theme: str, title: str = "", height: int = 320) -> dict[str, Any]:
    t = THEMES[theme]
    return {
        "title": {"text": title, "font": {"size": 13, "color": t["--ink"], "family": t["--font"]}},
        "paper_bgcolor": t["--plotly-bg"],
        "plot_bgcolor": t["--chart-surface"],
        "font": {"color": t["--ink"], "size": 11, "family": t["--font"]},
        "margin": {"l": 8, "r": 8, "t": 40 if title else 8, "b": 8},
        "height": height,
        "hovermode": "x unified",
        "legend": {"bgcolor": "rgba(0,0,0,0)", "borderwidth": 0, "orientation": "h", "y": 1.12},
        "xaxis": {
            "gridcolor": t["--grid"],
            "linecolor": t["--rule"],
            "tickfont": {"size": 10, "color": t["--ink"]},
            "title": {"font": {"color": t["--ink"]}},
        },
        "yaxis": {
            "gridcolor": t["--grid"],
            "linecolor": t["--rule"],
            "tickfont": {"size": 10, "color": t["--ink"]},
            "title": {"font": {"color": t["--ink"]}},
        },
    }


def apply_dimension_filters(
    src: pd.DataFrame,
    period_labels: list[str],
    dept_filter: list[str],
    fn_filter: list[str],
    expense_level_filters: dict[str, list[str]],
    vendor_filter: list[str],
) -> pd.DataFrame:
    out = src[src["Date Label"].isin(period_labels)]
    if dept_filter:
        out = out[out["Department"].isin(dept_filter)]
    if fn_filter:
        out = out[out["Function"].isin(fn_filter)]
    for level_col, selected in expense_level_filters.items():
        if selected:
            out = out[out[level_col].isin(selected)]
    if vendor_filter:
        out = out[out["vendor_dim"].isin(vendor_filter)]
    return out


def ordered_month_labels(df: pd.DataFrame) -> list[str]:
    available = set(df["Date Label"].unique())
    return [m for m in ALL_PERIODS_ORDERED if m in available]


def render_kpi_band(
    period_label: str,
    total_actual: float,
    comp_delta: float,
    comp_base: float,
    comp_label: str,
    compare_mode: str,
    total_budget: float,
    total_prior: float,
    budget_delta: float,
    is_partial_period: bool = False,
    open_months: list[str] | None = None,
) -> None:
    # Build the headline eyebrow and footnote
    if is_partial_period:
        eyebrow = f"{period_label} Forecast"
        footnote = fmt_short_dollars(total_actual, 2)
        if open_months:
            footnote_extra = f"({', '.join(open_months)} = forecast)"
        else:
            footnote_extra = ""
    else:
        eyebrow = f"{period_label} Actuals"
        footnote = fmt_short_dollars(total_actual, 2)
        footnote_extra = ""

    st.markdown(
        f"""
<div class="kpi-band">
  <div class="kpi-card hl">
    <div class="kpi-eyebrow">{eyebrow}</div>
    <div class="kpi-value">{fmt_short_dollars(total_actual)}</div>
    <div style="font-size:.78rem;color:var(--ink-3);margin-top:.15rem">{footnote}</div>
    {"<div style='font-size:.7rem;color:var(--ink-3);margin-top:.1rem'>" + footnote_extra + "</div>" if footnote_extra else ""}
  </div>
  <div class="kpi-card">
    <div class="kpi-eyebrow">$ Variance {comp_label}</div>
    <div class="kpi-value">{fmt_short_dollars(comp_delta)}</div>
    {variance_pill(comp_delta, comp_base)}
  </div>
  <div class="kpi-card">
    <div class="kpi-eyebrow">% Variance {comp_label}</div>
    <div class="kpi-value">{"n/a" if comp_base == 0 else f"{comp_delta/comp_base*100:+.1f}%"}</div>
    <div style="font-size:.78rem;color:var(--ink-3);margin-top:.5rem">
      {"Budget: " + fmt_short_dollars(total_budget) if compare_mode == "Budget" else "Prior Yr: " + fmt_short_dollars(total_prior)}
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-eyebrow">Budget Variance</div>
    <div class="kpi-value">{fmt_short_dollars(budget_delta)}</div>
    {variance_pill(budget_delta, total_budget)}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_trend_chart(
    df: pd.DataFrame,
    period_labels: list[str],
    dept_filter: list[str],
    fn_filter: list[str],
    expense_level_filters: dict[str, list[str]],
    vendor_filter: list[str],
    theme: str,
    t: dict[str, str],
    granularity: str = "Aggregated",
    spend_label: str = "Actual",
) -> go.Figure:
    """Render the expense trend chart. When granularity is Aggregated, show quarterly
    bars for prior year Q1-Q4 + current year quarters available. When Monthly, show
    a rolling 12-month line chart."""

    if granularity == "Aggregated":
        st.markdown('<div class="section-header">Expense Trend (Quarterly)</div>', unsafe_allow_html=True)
        # Determine current year from selected period
        try:
            current_yr = int(period_labels[0].split("-")[1]) + 2000
        except (ValueError, IndexError):
            current_yr = 2026
        prior_yr = current_yr - 1

        # Build list of quarters: Q1-Q4 prior year + available quarters current year
        quarter_keys_ordered: list[str] = []
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            quarter_keys_ordered.append(f"{q} {prior_yr}")
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            quarter_keys_ordered.append(f"{q} {current_yr}")

        available_labels = set(df["Date Label"].unique())
        # Only include quarters where at least one month has data
        quarters_with_data: list[str] = []
        for qk in quarter_keys_ordered:
            months = STATIC_PERIOD_OPTIONS.get(qk, [])
            if any(m in available_labels for m in months):
                quarters_with_data.append(qk)

        # Aggregate data by quarter
        all_months_needed = []
        for qk in quarters_with_data:
            all_months_needed.extend(STATIC_PERIOD_OPTIONS.get(qk, []))

        trend_base = apply_dimension_filters(
            df, all_months_needed, dept_filter, fn_filter, expense_level_filters, vendor_filter,
        )

        # Map each row's Date Label to its quarter
        trend_base = trend_base.copy()
        trend_base["_quarter"] = trend_base["Date Label"].map(MONTH_TO_QUARTER)
        trend_base = trend_base.dropna(subset=["_quarter"])

        trend_actual = (
            trend_base[trend_base["is_actuals_row"]]
            .groupby("_quarter", as_index=False)["Working.Value"]
            .sum()
            .rename(columns={"Working.Value": "Actual", "_quarter": "Period"})
        )
        trend_budget = (
            trend_base.groupby("_quarter", as_index=False)["Budget.Value"]
            .sum()
            .rename(columns={"Budget.Value": "Budget", "_quarter": "Period"})
        )
        trend = trend_actual.merge(trend_budget, on="Period", how="outer").fillna(0.0)
        trend["Actual"] = trend["Actual"] / 1_000_000
        trend["Budget"] = trend["Budget"] / 1_000_000
        # Sort by our ordered list
        qorder = {qk: i for i, qk in enumerate(quarters_with_data)}
        trend["_ord"] = trend["Period"].map(qorder).fillna(99)
        trend = trend.sort_values("_ord").drop(columns="_ord")

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Bar(
                x=trend["Period"],
                y=trend["Budget"],
                name="Budget",
                marker_color=t["--ink-3"],
                opacity=0.4,
            )
        )
        fig_trend.add_trace(
            go.Bar(
                x=trend["Period"],
                y=trend["Actual"],
                name=spend_label,
                marker_color=t["--accent"],
            )
        )
        fig_trend.update_layout(**plotly_layout(theme, height=300), barmode="group")
        fig_trend.update_xaxes(title="Quarter")
        fig_trend.update_yaxes(title="Expense ($M)", tickprefix="$", tickformat=",.1f")

    else:
        st.markdown('<div class="section-header">Expense Trend (12 months)</div>', unsafe_allow_html=True)

        try:
            last_i = max(ALL_PERIODS_ORDERED.index(m) for m in period_labels if m in ALL_PERIODS_ORDERED)
            first_i = max(0, last_i - 11)
            trend_range = ALL_PERIODS_ORDERED[first_i : last_i + 1]
        except ValueError:
            trend_range = period_labels

        trend_base = apply_dimension_filters(
            df, trend_range, dept_filter, fn_filter, expense_level_filters, vendor_filter,
        )
        trend_actual = (
            trend_base[trend_base["is_actuals_row"]]
            .groupby("Date Label", as_index=False)["Working.Value"]
            .sum()
            .rename(columns={"Working.Value": "Actual"})
        )
        trend_budget = (
            trend_base.groupby("Date Label", as_index=False)["Budget.Value"]
            .sum()
            .rename(columns={"Budget.Value": "Budget"})
        )
        trend = trend_actual.merge(trend_budget, on="Date Label", how="outer").fillna(0.0)
        trend["Actual"] = trend["Actual"] / 1_000_000
        trend["Budget"] = trend["Budget"] / 1_000_000
        trend["_ord"] = trend["Date Label"].map({m: i for i, m in enumerate(ALL_PERIODS_ORDERED)}).fillna(99)
        trend = trend.sort_values("_ord").drop(columns="_ord")

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=trend["Date Label"],
                y=trend["Budget"],
                name="Budget",
                mode="lines",
                line={"color": t["--ink-3"], "dash": "dot", "width": 1.5},
            )
        )
        fig_trend.add_trace(
            go.Scatter(
                x=trend["Date Label"],
                y=trend["Actual"],
                name=spend_label,
                mode="lines+markers",
                line={"color": t["--accent"], "width": 2.5},
                marker={"size": 6, "color": t["--accent"]},
                fill="tozeroy",
                fillcolor="rgba(29,91,127,0.12)",
            )
        )
        fig_trend.update_layout(**plotly_layout(theme, height=300))
        fig_trend.update_xaxes(title="Period")
        fig_trend.update_yaxes(title="Expense ($M)", tickprefix="$", tickformat=",.1f")

    return fig_trend


def render_category_chart(
    act: pd.DataFrame,
    total_actual: float,
    preferred_level0_order: list[str],
    theme: str,
    t: dict[str, str],
) -> go.Figure:
    cat_agg = (
        act[~act["Level 0"].isin(["Headcount", "Unspecified"])]
        .groupby("Level 0", as_index=False)["Working.Value"]
        .sum()
    )
    cat_rank_map = {name: idx for idx, name in enumerate(preferred_level0_order)}
    cat_agg["_order_rank"] = cat_agg["Level 0"].map(cat_rank_map).fillna(999).astype(int)
    cat_agg = cat_agg.sort_values(["_order_rank", "Working.Value"], ascending=[True, False])
    cat_agg = cat_agg.drop(columns="_order_rank").head(len(preferred_level0_order))
    cat_axis_order = [name for name in preferred_level0_order if name in set(cat_agg["Level 0"])]
    cat_agg["pct"] = cat_agg["Working.Value"] / total_actual * 100 if total_actual else 0
    cat_agg["Actual_M"] = cat_agg["Working.Value"] / 1_000_000

    fig_cat = go.Figure(
        go.Bar(
            x=cat_agg["Actual_M"],
            y=cat_agg["Level 0"],
            orientation="h",
            marker_color=t["--accent"],
            text=[
                f"{fmt_short_dollars(v)} ({p:.0f}%)"
                for v, p in zip(cat_agg["Working.Value"], cat_agg["pct"])
            ],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig_cat.update_layout(**plotly_layout(theme, "Spend by Category", height=300))
    fig_cat.update_xaxes(
        title="Spend ($M)",
        tickprefix="$",
        tickformat=",.1f",
        showticklabels=True,
        tickangle=0,
    )
    fig_cat.update_yaxes(
        title="Category",
        categoryorder="array",
        categoryarray=cat_axis_order,
    )
    return fig_cat


@st.fragment
def render_drill_table(
    act: pd.DataFrame,
    current_fdf: pd.DataFrame,
    prior_act: pd.DataFrame,
    total_actual: float,
    preferred_level0_order: list[str],
    period_label: str,
    spend_label: str = "Actual",
) -> None:
    st.markdown('<div class="section-header">Top Accounts by Spend</div>', unsafe_allow_html=True)

    if "acct_drill_path" not in st.session_state:
        st.session_state["acct_drill_path"] = []

    path = list(st.session_state["acct_drill_path"])
    level_idx = min(len(path), len(LEVEL_COLUMNS) - 1)
    current_level = LEVEL_COLUMNS[level_idx]

    # Themed breadcrumb
    if path:
        crumbs = ' <span style="color:var(--ink-3)">›</span> '.join(
            [f'<span class="crumb">Level 0</span>']
            + [f'<span class="crumb">{p}</span>' for p in path[:-1]]
            + [f'<span class="crumb-active">{path[-1]}</span>']
        )
    else:
        crumbs = '<span class="crumb-active">Level 0</span>'
    st.markdown(
        f'<div class="drill-breadcrumb">Drill Path: {crumbs}</div>'
        f'<div style="font-size:0.72rem;color:var(--ink-3);margin-bottom:0.5rem;">'
        f'Click a row and use Drill to move from {current_level} to the next level.</div>',
        unsafe_allow_html=True,
    )

    ctrl_spacer, ctrl_back, ctrl_reset = st.columns([6, 1, 1])
    with ctrl_back:
        if st.button("Back", disabled=len(path) == 0):
            st.session_state["acct_drill_path"] = path[:-1]
            st.rerun()
    with ctrl_reset:
        if st.button("Reset", disabled=len(path) == 0):
            st.session_state["acct_drill_path"] = []
            st.rerun()

    work_cur = act.copy()
    work_cur_all = current_fdf.copy()
    work_pri = prior_act.copy()
    for idx, node in enumerate(path):
        col = LEVEL_COLUMNS[idx]
        work_cur = work_cur[work_cur[col] == node]
        work_cur_all = work_cur_all[work_cur_all[col] == node]
        work_pri = work_pri[work_pri[col] == node]

    cur_group_actual = work_cur.groupby(current_level, as_index=False).agg(Actual=("Working.Value", "sum"))
    cur_group_budget = work_cur_all.groupby(current_level, as_index=False).agg(Budget=("Budget.Value", "sum"))
    pri_group = work_pri.groupby(current_level, as_index=False).agg(Prior=("Working.Value", "sum"))

    acct = cur_group_actual.merge(cur_group_budget, on=current_level, how="outer").merge(
        pri_group, on=current_level, how="left"
    )
    acct["Actual"] = acct["Actual"].fillna(0.0)
    acct["Budget"] = acct["Budget"].fillna(0.0)
    acct["Prior"] = acct["Prior"].fillna(0.0)
    acct["YoY $"] = acct["Actual"] - acct["Prior"]
    acct["YoY %"] = (acct["YoY $"] / acct["Prior"].replace(0, float("nan"))) * 100
    acct["Bdgt $"] = acct["Actual"] - acct["Budget"]
    acct["Bdgt %"] = (acct["Bdgt $"] / acct["Budget"].replace(0, float("nan"))) * 100
    acct["Share"] = acct["Actual"] / total_actual * 100 if total_actual else 0
    acct = acct.rename(columns={current_level: "Node"})

    # Remove "Unspecified" rows if they have zero spend
    unspec_mask = acct["Node"] == "Unspecified"
    if unspec_mask.any():
        unspec_actual = acct.loc[unspec_mask, "Actual"].sum()
        if abs(unspec_actual) < 0.01:
            acct = acct[~unspec_mask]

    if current_level == "Level 0":
        rank_map = {name: idx for idx, name in enumerate(preferred_level0_order)}
        acct["_order_rank"] = acct["Node"].map(rank_map).fillna(999).astype(int)
        acct = acct.sort_values(["_order_rank", "Actual"], ascending=[True, False]).drop(columns="_order_rank")
    else:
        acct = acct.sort_values("Actual", ascending=False)
    acct = acct.head(25)

    acct_display = acct.copy()
    # Detect headcount rows: if drilled into Headcount or at Level 0 with Headcount node
    is_headcount_drill = "Headcount" in path
    if is_headcount_drill:
        _fmt_val = fmt_headcount
    else:
        _fmt_val = lambda v: fmt_currency_by_level(v, level_idx)

    for col in ["Actual", "Budget", "Prior", "YoY $", "Bdgt $"]:
        if is_headcount_drill:
            acct_display[col] = acct_display[col].map(fmt_headcount)
        else:
            acct_display[col] = acct_display[col].map(lambda v: fmt_currency_by_level(v, level_idx))

    # At Level 0, format Headcount rows differently from dollar rows
    if current_level == "Level 0" and not is_headcount_drill:
        hc_mask = acct_display["Node"] == "Headcount"
        if hc_mask.any():
            for col in ["Actual", "Budget", "Prior", "YoY $", "Bdgt $"]:
                acct_display.loc[hc_mask, col] = acct.loc[hc_mask, col].map(fmt_headcount)

    acct_display["YoY %"] = acct_display["YoY %"].map(fmt_pct_paren)
    acct_display["Bdgt %"] = acct_display["Bdgt %"].map(fmt_pct_paren)
    acct_display["Share"] = acct_display["Share"].map(lambda x: f"{x:.1f}%")

    # Render as themed HTML table
    col_headers = {
        "Node": current_level,
        "Actual": spend_label,
        "Budget": "Budget",
        "Prior": "Prior Yr",
        "YoY $": "YoY $",
        "YoY %": "YoY %",
    }
    display_cols = ["Node", "Actual", "Budget", "Prior", "YoY $", "YoY %"]
    header_html = "".join(f"<th>{col_headers[c]}</th>" for c in display_cols)
    rows_html = ""
    for _, row in acct_display.iterrows():
        cells = "".join(f"<td>{row[c]}</td>" for c in display_cols)
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f'<table class="themed-table"><thead><tr>{header_html}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True,
    )

    # Drill selection via selectbox
    node_list = list(acct_display["Node"])
    if level_idx < len(LEVEL_COLUMNS) - 1 and node_list:
        st.markdown(
            '<div style="font-size:0.75rem;font-weight:600;color:var(--ink-3);margin-top:0.6rem;margin-bottom:0.2rem;">'
            'DRILL INTO CATEGORY</div>',
            unsafe_allow_html=True,
        )
        selected_node = st.selectbox(
            "Select row to drill into",
            options=[""] + node_list,
            index=0,
            key="drill_select",
            label_visibility="collapsed",
            placeholder="Select a row to drill deeper...",
        )
        if selected_node:
            if st.button(f"Drill into {selected_node}"):
                st.session_state["acct_drill_path"] = path + [selected_node]
                st.rerun()
    elif level_idx >= len(LEVEL_COLUMNS) - 1:
        st.info("You are at the deepest hierarchy level.")

    st.download_button(
        "Export Drill Table (CSV)",
        data=acct_display[["Node", "Actual", "Budget", "Prior", "YoY $", "YoY %", "Bdgt $", "Bdgt %", "Share"]].to_csv(index=False).encode("utf-8"),
        file_name=f"top_accounts_{current_level.replace(' ', '_')}_{period_label.replace(' ', '_')}.csv",
        mime="text/csv",
    )


def render_vendors_and_movers(
    act: pd.DataFrame,
    current_fdf: pd.DataFrame,
    preferred_level0_order: list[str],
    theme: str,
    t: dict[str, str],
    spend_label: str = "Actual",
) -> None:
    st.markdown('<div class="section-header">Vendors</div>', unsafe_allow_html=True)

    vendor_actual = (
        act[act["vendor_dim"] != "Unspecified"]
        .groupby("vendor_dim", as_index=False)
        .agg(Actual=("Working.Value", "sum"))
    )
    vendor_budget = (
        current_fdf[current_fdf["vendor_dim"] != "Unspecified"]
        .groupby("vendor_dim", as_index=False)
        .agg(Budget=("Budget.Value", "sum"))
    )
    vendor_prior = (
        act[act["vendor_dim"] != "Unspecified"]
        .groupby("vendor_dim", as_index=False)
        .agg(Prior=("PriorYear.Amount", "sum"))
    )
    vendors = (
        vendor_actual.merge(vendor_budget, on="vendor_dim", how="outer")
        .merge(vendor_prior, on="vendor_dim", how="left")
        .fillna(0.0)
        .sort_values("Actual", ascending=False)
        .head(15)
    )
    vendors["Actual_M"] = vendors["Actual"] / 1_000_000

    movers_actual = act[act["Level 0"] != "Headcount"].groupby("Level 0", as_index=False).agg(actual=("Working.Value", "sum"))
    movers_budget = current_fdf[current_fdf["Level 0"] != "Headcount"].groupby("Level 0", as_index=False).agg(budget=("Budget.Value", "sum"))
    movers = movers_actual.merge(movers_budget, on="Level 0", how="outer").fillna(0.0)
    movers["delta"] = movers["actual"] - movers["budget"]
    movers["delta_M"] = movers["delta"] / 1_000_000
    movers_rank_map = {name: idx for idx, name in enumerate(preferred_level0_order)}
    movers["_order_rank"] = movers["Level 0"].map(movers_rank_map).fillna(999).astype(int)
    movers = movers.sort_values(["_order_rank", "delta"], ascending=[True, False])
    movers = movers.drop(columns="_order_rank").head(len(preferred_level0_order))
    movers_axis_order = [name for name in preferred_level0_order if name in set(movers["Level 0"])]

    col_v, col_m = st.columns(2, gap="large")
    with col_v:
        fig_v = go.Figure(
            go.Bar(
                x=vendors["vendor_dim"].apply(lambda s: s[:25] + "\u2026" if len(s) > 28 else s),
                y=vendors["Actual_M"],
                marker_color=t["--accent"],
                text=[fmt_short_dollars(v) for v in vendors["Actual"]],
                textposition="outside",
                cliponaxis=False,
            )
        )
        fig_v.update_layout(**plotly_layout(theme, "Top Vendors (Vendor Parent)", height=340))
        fig_v.update_yaxes(title="Spend ($M)", tickprefix="$", tickformat=",.1f")
        fig_v.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_v, use_container_width=True)

    with col_m:
        colors = [t["--neg"] if v > 0 else t["--pos"] for v in movers["delta"]]
        fig_m = go.Figure(
            go.Bar(
                x=movers["delta_M"],
                y=movers["Level 0"],
                orientation="h",
                marker_color=colors,
                text=[fmt_short_dollars(abs(v)) for v in movers["delta"]],
                textposition="outside",
                cliponaxis=False,
            )
        )
        fig_m.add_vline(x=0, line_color=t["--rule"], line_width=1)
        fig_m.update_layout(**plotly_layout(theme, "Top Movers vs Budget", height=340))
        fig_m.update_xaxes(title="Variance ($M)", tickprefix="$", tickformat=",.1f")
        fig_m.update_yaxes(
            categoryorder="array",
            categoryarray=movers_axis_order,
        )
        st.plotly_chart(fig_m, use_container_width=True)


def render_transactions(txn: pd.DataFrame, tx_full: pd.DataFrame, period_label: str) -> None:
    pos_txn = txn[txn["NetSuite.Amount"] > 0]
    neg_txn = txn[txn["NetSuite.Amount"] < 0]

    st.markdown(
        f"""
<div class="kpi-band">
  <div class="kpi-card hl">
    <div class="kpi-eyebrow">NetSuite Total</div>
    <div class="kpi-value">{fmt_short_dollars(float(txn['NetSuite.Amount'].sum()))}</div>
    <div style="font-size:.78rem;color:var(--ink-3);margin-top:.15rem">{len(txn):,} rows</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-eyebrow">Positive (Charges)</div>
    <div class="kpi-value">{fmt_short_dollars(float(pos_txn['NetSuite.Amount'].sum()))}</div>
    <div style="font-size:.78rem;color:var(--ink-3);margin-top:.15rem">{len(pos_txn):,} entries</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-eyebrow">Negative (Credits)</div>
    <div class="kpi-value">{fmt_short_dollars(abs(float(neg_txn['NetSuite.Amount'].sum())))}</div>
    <div style="font-size:.78rem;color:var(--ink-3);margin-top:.15rem">{len(neg_txn):,} credits</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-eyebrow">Total Txn Count</div>
    <div class="kpi-value">{int(txn['NetSuite.TransactionCount'].sum()):,}</div>
    <div style="font-size:.78rem;color:var(--ink-3);margin-top:.15rem">NetSuite entries</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    sc1, sc2, _ = st.columns([3, 2, 5])
    with sc1:
        search = st.text_input("Search vendor parent / account / department", placeholder="Type to filter...")
    with sc2:
        entry_type = st.segmented_control("Entry type", ["All", "Positive", "Negative"], default="All")

    tx = txn.copy()
    tx = tx.sort_values("Start Date", ascending=False)
    if search:
        token = search.lower()
        tx = tx[
            tx["vendor_dim"].str.lower().str.contains(token, na=False)
            | tx["Account Name"].str.lower().str.contains(token, na=False)
            | tx["Department"].str.lower().str.contains(token, na=False)
            | tx["Account Code"].str.lower().str.contains(token, na=False)
        ]

    if entry_type == "Positive":
        tx = tx[tx["NetSuite.Amount"] > 0]
    elif entry_type == "Negative":
        tx = tx[tx["NetSuite.Amount"] < 0]

    total_rows = len(tx)
    page_count = max(1, (total_rows + PAGE_SIZE - 1) // PAGE_SIZE)

    p1, p2, _ = st.columns([1, 2, 7])
    with p1:
        page = st.number_input("Page", min_value=1, max_value=page_count, value=1, step=1)
    with p2:
        start = (page - 1) * PAGE_SIZE + 1
        end = min(page * PAGE_SIZE, total_rows)
        st.markdown(
            f'<div style="padding-top:1.8rem;font-size:.82rem;color:var(--ink-3)">{start:,}-{end:,} of {total_rows:,}</div>',
            unsafe_allow_html=True,
        )

    start_idx = (page - 1) * PAGE_SIZE
    page_df = (
        tx.iloc[start_idx : start_idx + PAGE_SIZE][
            [
                "Start Date",
                "vendor_dim",
                "Account Code",
                "Account Name",
                "Department",
                "Org_Level_2",
                "NetSuite.Amount",
                "NetSuite.TransactionCount",
            ]
        ]
        .rename(
            columns={
                "Start Date": "Date",
                "vendor_dim": "Vendor Parent",
                "Account Code": "GL",
                "Account Name": "Account",
                "Department": "Department",
                "Org_Level_2": "Org",
                "NetSuite.Amount": "Amount",
                "NetSuite.TransactionCount": "Txn #",
            }
        )
    )

    st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD"),
            "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "Txn #": st.column_config.NumberColumn("Txn #", format="%.0f"),
        },
    )

    if total_rows == 0:
        st.info("No NetSuite rows matched the current filters and period.")
    else:
        export_tx = tx[
            ["Start Date", "vendor_dim", "Account Code", "Account Name", "Department", "Org_Level_2", "NetSuite.Amount", "NetSuite.TransactionCount"]
        ].rename(columns={"Start Date": "Date", "vendor_dim": "Vendor Parent", "Account Code": "GL", "Account Name": "Account", "Org_Level_2": "Org", "NetSuite.Amount": "Amount", "NetSuite.TransactionCount": "Txn #"})
        st.download_button(
            "Export Transactions (CSV)",
            data=export_tx.to_csv(index=False).encode("utf-8"),
            file_name=f"transactions_{period_label.replace(' ', '_')}.csv",
            mime="text/csv",
        )


def render_pnl_tab(
    act: pd.DataFrame,
    current_fdf: pd.DataFrame,
    prior_act: pd.DataFrame,
    total_actual: float,
    total_budget: float,
    total_prior: float,
    preferred_level0_order: list[str],
    compare_mode: str,
    theme: str,
    t: dict[str, str],
    period_label: str,
    spend_label: str = "Actual",
) -> None:
    """P&L drill-down view — waterfall bridge + progressive hierarchy drill."""
    comp_label = "Budget" if compare_mode == "Budget" else "Prior Year"

    # Summary KPIs
    if compare_mode == "Budget":
        comp_total = total_budget
        variance = total_actual - total_budget
    else:
        comp_total = total_prior
        variance = total_actual - total_prior

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric(f"Total {spend_label}", fmt_short_dollars(total_actual))
    with k2:
        st.metric(f"Total {comp_label}", fmt_short_dollars(comp_total))
    with k3:
        pct = (variance / comp_total * 100) if comp_total else 0
        st.metric("Variance", fmt_short_dollars(variance), delta=f"{pct:+.1f}%", delta_color="inverse")

    # ─── Waterfall Bridge Chart ───
    st.markdown('<div class="section-header">Variance Bridge (Waterfall)</div>', unsafe_allow_html=True)

    bridge_actual = act[act["Level 0"] != "Headcount"].groupby("Level 0", as_index=False).agg(actual=("Working.Value", "sum"))
    if compare_mode == "Budget":
        bridge_comp = current_fdf[current_fdf["Level 0"] != "Headcount"].groupby("Level 0", as_index=False).agg(comp=("Budget.Value", "sum"))
    else:
        bridge_comp = prior_act[prior_act["Level 0"] != "Headcount"].groupby("Level 0", as_index=False).agg(comp=("Working.Value", "sum"))

    bridge = bridge_actual.merge(bridge_comp, on="Level 0", how="outer").fillna(0.0)
    bridge["delta"] = bridge["actual"] - bridge["comp"]
    rank_map = {name: idx for idx, name in enumerate(preferred_level0_order)}
    bridge["_order_rank"] = bridge["Level 0"].map(rank_map).fillna(999).astype(int)
    bridge = bridge.sort_values("_order_rank").drop(columns="_order_rank")

    # Build waterfall: Starting bar (comp total) + category deltas + Ending bar (actual total)
    wf_labels = [f"{comp_label} Total"] + list(bridge["Level 0"]) + [f"{spend_label} Total"]
    wf_values = [comp_total / 1_000_000] + list(bridge["delta"] / 1_000_000) + [total_actual / 1_000_000]
    wf_measures = ["absolute"] + ["relative"] * len(bridge) + ["total"]

    # Colors: starting bar = neutral, negatives = green (favorable), positives = red (unfavorable), total = accent
    wf_colors = []
    wf_colors.append(t["--ink-3"])  # starting bar
    for v in bridge["delta"]:
        wf_colors.append(t["--neg"] if v > 0 else t["--pos"])
    wf_colors.append(t["--accent"])  # ending bar

    fig_bridge = go.Figure(
        go.Waterfall(
            x=wf_labels,
            y=wf_values,
            measure=wf_measures,
            connector={"line": {"color": t["--rule"], "width": 1}},
            increasing={"marker": {"color": t["--neg"]}},
            decreasing={"marker": {"color": t["--pos"]}},
            totals={"marker": {"color": t["--accent"]}},
            text=[fmt_short_dollars(v * 1_000_000) for v in wf_values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig_bridge.update_layout(**plotly_layout(theme, f"Expense Walk: {comp_label} → {spend_label}", height=380))
    fig_bridge.update_xaxes(tickangle=-25)
    fig_bridge.update_yaxes(title="Expense ($M)", tickprefix="$", tickformat=",.1f")
    st.plotly_chart(fig_bridge, use_container_width=True)

    # ─── Progressive P&L Drill-Down ───
    st.markdown('<div class="section-header">P&L by Category (Drill-Down)</div>', unsafe_allow_html=True)

    if "pnl_drill_path" not in st.session_state:
        st.session_state["pnl_drill_path"] = []

    path = list(st.session_state["pnl_drill_path"])
    level_idx = min(len(path), len(LEVEL_COLUMNS) - 1)
    current_level = LEVEL_COLUMNS[level_idx]

    # Breadcrumb
    if path:
        crumbs = ' <span style="color:var(--ink-3)">›</span> '.join(
            [f'<span class="crumb">Level 0</span>']
            + [f'<span class="crumb">{p}</span>' for p in path[:-1]]
            + [f'<span class="crumb-active">{path[-1]}</span>']
        )
    else:
        crumbs = '<span class="crumb-active">Level 0</span>'
    st.markdown(
        f'<div class="drill-breadcrumb">Drill Path: {crumbs}</div>',
        unsafe_allow_html=True,
    )

    ctrl_spacer, ctrl_back, ctrl_reset = st.columns([6, 1, 1])
    with ctrl_back:
        if st.button("Back", disabled=len(path) == 0, key="pnl_back"):
            st.session_state["pnl_drill_path"] = path[:-1]
            st.rerun()
    with ctrl_reset:
        if st.button("Reset", disabled=len(path) == 0, key="pnl_reset"):
            st.session_state["pnl_drill_path"] = []
            st.rerun()

    # Filter data to current drill path
    work_act = act.copy()
    work_all = current_fdf.copy()
    work_pri = prior_act.copy()
    for idx, node in enumerate(path):
        col = LEVEL_COLUMNS[idx]
        work_act = work_act[work_act[col] == node]
        work_all = work_all[work_all[col] == node]
        work_pri = work_pri[work_pri[col] == node]

    # Aggregate by current level
    pnl_actual = work_act.groupby(current_level, as_index=False).agg(Actual=("Working.Value", "sum"))
    if compare_mode == "Budget":
        pnl_comp = work_all.groupby(current_level, as_index=False).agg(Comp=("Budget.Value", "sum"))
    else:
        pnl_comp = work_pri.groupby(current_level, as_index=False).agg(Comp=("Working.Value", "sum"))
    pnl = pnl_actual.merge(pnl_comp, on=current_level, how="outer").fillna(0.0)
    pnl["Variance $"] = pnl["Actual"] - pnl["Comp"]
    pnl["Variance %"] = (pnl["Variance $"] / pnl["Comp"].replace(0, float("nan"))) * 100
    pnl_total = pnl["Actual"].sum()
    pnl["% of Total"] = pnl["Actual"] / pnl_total * 100 if pnl_total else 0
    pnl = pnl.rename(columns={current_level: "Node"})

    # Remove zero-spend Unspecified rows
    unspec_mask = pnl["Node"] == "Unspecified"
    if unspec_mask.any() and abs(pnl.loc[unspec_mask, "Actual"].sum()) < 0.01:
        pnl = pnl[~unspec_mask]

    if current_level == "Level 0":
        pnl["_order_rank"] = pnl["Node"].map(rank_map).fillna(999).astype(int)
        pnl = pnl.sort_values(["_order_rank", "Actual"], ascending=[True, False]).drop(columns="_order_rank")
    else:
        pnl = pnl.sort_values("Actual", ascending=False)
    pnl = pnl.head(25)

    # Detect headcount
    is_headcount_drill = "Headcount" in path
    if is_headcount_drill:
        _fmt_val = fmt_headcount
    else:
        _fmt_val = lambda v: fmt_currency_by_level(v, level_idx)

    pnl_display = pnl.copy()
    for col in ["Actual", "Comp", "Variance $"]:
        if is_headcount_drill:
            pnl_display[col] = pnl_display[col].map(fmt_headcount)
        else:
            pnl_display[col] = pnl_display[col].map(lambda v: fmt_currency_by_level(v, level_idx))
    # Headcount formatting at Level 0 for mixed display
    if current_level == "Level 0" and not is_headcount_drill:
        hc_mask = pnl_display["Node"] == "Headcount"
        if hc_mask.any():
            for col in ["Actual", "Comp", "Variance $"]:
                pnl_display.loc[hc_mask, col] = pnl.loc[hc_mask, col].map(fmt_headcount)

    pnl_display["Variance %"] = pnl_display["Variance %"].map(fmt_pct_paren)
    pnl_display["% of Total"] = pnl_display["% of Total"].map(lambda x: f"{x:.1f}%")

    # Render themed HTML table
    col_headers = {"Node": current_level, "Actual": spend_label, "Comp": comp_label, "Variance $": "Var $", "Variance %": "Var %", "% of Total": "% Total"}
    display_cols = ["Node", "Actual", "Comp", "Variance $", "Variance %", "% of Total"]
    header_html = "".join(f"<th>{col_headers[c]}</th>" for c in display_cols)
    rows_html = ""
    for _, row in pnl_display.iterrows():
        cells = "".join(f"<td>{row[c]}</td>" for c in display_cols)
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f'<table class="themed-table"><thead><tr>{header_html}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True,
    )

    # Drill selectbox
    node_list = list(pnl_display["Node"])
    if level_idx < len(LEVEL_COLUMNS) - 1 and node_list:
        st.markdown(
            '<div style="font-size:0.75rem;font-weight:600;color:var(--ink-3);margin-top:0.6rem;margin-bottom:0.2rem;">'
            'DRILL INTO SUB-CATEGORY</div>',
            unsafe_allow_html=True,
        )
        selected_node = st.selectbox(
            "Select category to drill into",
            options=[""] + node_list,
            index=0,
            key="pnl_drill_select",
            label_visibility="collapsed",
            placeholder="Select a category to drill deeper...",
        )
        if selected_node:
            if st.button(f"Drill into {selected_node}", key="pnl_drill_btn"):
                st.session_state["pnl_drill_path"] = path + [selected_node]
                st.rerun()
    elif level_idx >= len(LEVEL_COLUMNS) - 1:
        st.info("You are at the deepest hierarchy level.")


def _resolve_org_hierarchy(path: list[str]) -> list[str]:
    """Return the drill column sequence based on the selected function.

    Technology & Research skips Department and goes straight to ART-CPM.
    All others follow Function → Department → ART-CPM.
    """
    if path and path[0] == "Technology & Research":
        return ["Function", "ART - CPM"] + LEVEL_COLUMNS
    return ["Function", "Department", "ART - CPM"] + LEVEL_COLUMNS


def _apply_corporate_grouping(df: pd.DataFrame, group_col: str = "Department") -> pd.DataFrame:
    """Apply consolidated department grouping for Corporate function."""
    mapping: dict[str, str] = {}
    for group_name, members in CORPORATE_DEPT_GROUPS.items():
        for m in members:
            mapping[m] = group_name
    df = df.copy()
    df[group_col] = df[group_col].map(lambda d: mapping.get(d, d))
    return df


def render_organization_tab(
    act: pd.DataFrame,
    current_fdf: pd.DataFrame,
    prior_act: pd.DataFrame,
    total_actual: float,
    compare_mode: str,
    theme: str,
    t: dict[str, str],
    period_labels: list[str],
    spend_label: str = "Actual",
) -> None:
    """Organization view: Function > Department > ART-CPM hierarchy with drill-down."""
    comp_label = "Budget" if compare_mode == "Budget" else "Prior Year"

    # ─── Summary KPIs ───
    fn_count = act["Function"].nunique()
    dept_count = act["Department"].nunique()
    art_count = act["ART - CPM"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(f"Total {spend_label}", fmt_short_dollars(total_actual))
    with k2:
        st.metric("Functions", f"{fn_count:,}")
    with k3:
        st.metric("Departments", f"{dept_count:,}")
    with k4:
        st.metric("ART-CPMs", f"{art_count:,}")

    # ─── Organizational Drill State ───
    if "org_drill_path" not in st.session_state:
        st.session_state["org_drill_path"] = []

    path = list(st.session_state["org_drill_path"])

    # Dynamic hierarchy based on selected function
    ORG_THEN_ACCT = _resolve_org_hierarchy(path)
    max_depth = len(ORG_THEN_ACCT)
    level_idx = min(len(path), max_depth - 1)
    current_dim = ORG_THEN_ACCT[level_idx] if level_idx < max_depth else ORG_THEN_ACCT[-1]

    # Consolidated dept toggle (only relevant when viewing Corporate departments)
    is_corporate_dept_view = (
        len(path) >= 1
        and path[0] == "Corporate"
        and current_dim == "Department"
    )
    consolidate_depts = False
    if is_corporate_dept_view:
        consolidate_depts = st.toggle("Consolidate departments", value=False, key="org_consolidate_depts")

    # Breadcrumb
    if path:
        crumb_parts = [f'<span class="crumb">Function</span>']
        for p in path[:-1]:
            crumb_parts.append(f'<span class="crumb">{p}</span>')
        crumb_parts.append(f'<span class="crumb-active">{path[-1]}</span>')
        crumbs = ' <span style="color:var(--ink-3)">›</span> '.join(crumb_parts)
    else:
        crumbs = '<span class="crumb-active">Function</span>'
    st.markdown(
        f'<div class="drill-breadcrumb">Org Path: {crumbs}</div>'
        f'<div style="font-size:0.72rem;color:var(--ink-3);margin-bottom:0.5rem;">'
        f'Current view: {current_dim}</div>',
        unsafe_allow_html=True,
    )

    ctrl_spacer, ctrl_back, ctrl_reset = st.columns([6, 1, 1])
    with ctrl_back:
        if st.button("Back", disabled=len(path) == 0, key="org_back"):
            st.session_state["org_drill_path"] = path[:-1]
            st.rerun()
    with ctrl_reset:
        if st.button("Reset", disabled=len(path) == 0, key="org_reset"):
            st.session_state["org_drill_path"] = []
            st.rerun()

    # Filter data to current drill path
    work_act = act.copy()
    work_all = current_fdf.copy()
    work_pri = prior_act.copy()
    for idx, node in enumerate(path):
        col = ORG_THEN_ACCT[idx]
        # When consolidated, a group name maps to multiple dept values
        if col == "Department" and node in CORPORATE_DEPT_GROUPS:
            members = CORPORATE_DEPT_GROUPS[node]
            work_act = work_act[work_act[col].isin(members)]
            work_all = work_all[work_all[col].isin(members)]
            work_pri = work_pri[work_pri[col].isin(members)]
        else:
            work_act = work_act[work_act[col] == node]
            work_all = work_all[work_all[col] == node]
            work_pri = work_pri[work_pri[col] == node]

    # Apply corporate dept grouping if toggle is on
    if is_corporate_dept_view and consolidate_depts:
        work_act = _apply_corporate_grouping(work_act)
        work_all = _apply_corporate_grouping(work_all)
        work_pri = _apply_corporate_grouping(work_pri)

    # ─── Expense Table at current level ───
    st.markdown(f'<div class="section-header">Expense by {current_dim}</div>', unsafe_allow_html=True)

    grp_actual = work_act.groupby(current_dim, as_index=False).agg(Actual=("Working.Value", "sum"))
    if compare_mode == "Budget":
        grp_comp = work_all.groupby(current_dim, as_index=False).agg(Comp=("Budget.Value", "sum"))
    else:
        grp_comp = work_pri.groupby(current_dim, as_index=False).agg(Comp=("Working.Value", "sum"))
    grp = grp_actual.merge(grp_comp, on=current_dim, how="outer").fillna(0.0)
    grp["Variance $"] = grp["Actual"] - grp["Comp"]
    grp["Variance %"] = (grp["Variance $"] / grp["Comp"].replace(0, float("nan"))) * 100
    grp_total = grp["Actual"].sum()
    grp["% of Total"] = grp["Actual"] / grp_total * 100 if grp_total else 0
    grp = grp.rename(columns={current_dim: "Node"})

    # Remove Unspecified with zero spend
    unspec_mask = grp["Node"] == "Unspecified"
    if unspec_mask.any() and abs(grp.loc[unspec_mask, "Actual"].sum()) < 0.01:
        grp = grp[~unspec_mask]

    # Apply preferred ordering
    if current_dim == "Function":
        fn_rank = {name: idx for idx, name in enumerate(PREFERRED_FUNCTION_ORDER)}
        grp["_order_rank"] = grp["Node"].map(fn_rank).fillna(999).astype(int)
        grp = grp.sort_values(["_order_rank", "Actual"], ascending=[True, False]).drop(columns="_order_rank")
    elif current_dim == "Department" and is_corporate_dept_view and not consolidate_depts:
        dept_rank = {name: idx for idx, name in enumerate(CORPORATE_DEPT_ORDER)}
        grp["_order_rank"] = grp["Node"].map(dept_rank).fillna(999).astype(int)
        grp = grp.sort_values(["_order_rank", "Actual"], ascending=[True, False]).drop(columns="_order_rank")
    else:
        grp = grp.sort_values("Actual", ascending=False)
    grp = grp.head(30)

    # Format display
    grp_display = grp.copy()
    for col in ["Actual", "Comp", "Variance $"]:
        grp_display[col] = grp_display[col].map(fmt_millions_paren)
    grp_display["Variance %"] = grp_display["Variance %"].map(fmt_pct_paren)
    grp_display["% of Total"] = grp_display["% of Total"].map(lambda x: f"{x:.1f}%")

    col_headers = {"Node": current_dim, "Actual": spend_label, "Comp": comp_label, "Variance $": "Var $", "Variance %": "Var %", "% of Total": "% Total"}
    display_cols = ["Node", "Actual", "Comp", "Variance $", "Variance %", "% of Total"]
    header_html = "".join(f"<th>{col_headers[c]}</th>" for c in display_cols)
    rows_html = ""
    for _, row in grp_display.iterrows():
        cells = "".join(f"<td>{row[c]}</td>" for c in display_cols)
        rows_html += f"<tr>{cells}</tr>"
    st.markdown(
        f'<table class="themed-table"><thead><tr>{header_html}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True,
    )

    # Drill selectbox
    node_list = list(grp_display["Node"])
    if level_idx < max_depth - 1 and node_list:
        st.markdown(
            f'<div style="font-size:0.75rem;font-weight:600;color:var(--ink-3);margin-top:0.6rem;margin-bottom:0.2rem;">'
            f'DRILL INTO NEXT LEVEL</div>',
            unsafe_allow_html=True,
        )
        selected_node = st.selectbox(
            "Select to drill",
            options=[""] + node_list,
            index=0,
            key="org_drill_select",
            label_visibility="collapsed",
            placeholder="Select a row to drill deeper...",
        )
        if selected_node:
            next_level = ORG_THEN_ACCT[level_idx + 1] if level_idx + 1 < max_depth else "Vendor"
            if st.button(f"Drill into {selected_node} → view by {next_level}", key="org_drill_btn"):
                st.session_state["org_drill_path"] = path + [selected_node]
                st.rerun()
    elif level_idx >= max_depth - 1:
        # At deepest account level, show vendor breakdown
        st.markdown('<div class="section-header">Vendor Breakdown</div>', unsafe_allow_html=True)
        vendor_grp = (
            work_act[work_act["vendor_dim"] != "Unspecified"]
            .groupby("vendor_dim", as_index=False)
            .agg(Actual=("Working.Value", "sum"))
            .sort_values("Actual", ascending=False)
            .head(20)
        )
        if not vendor_grp.empty:
            vendor_grp["Formatted"] = vendor_grp["Actual"].map(fmt_millions_paren)
            v_header = "<th>Vendor</th><th>Spend</th>"
            v_rows = ""
            for _, row in vendor_grp.iterrows():
                v_rows += f"<tr><td>{row['vendor_dim']}</td><td>{row['Formatted']}</td></tr>"
            st.markdown(
                f'<table class="themed-table"><thead><tr>{v_header}</tr></thead>'
                f'<tbody>{v_rows}</tbody></table>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No vendor data at this level.")

    # ─── Headcount Section ───
    st.markdown('<div class="section-header">Headcount</div>', unsafe_allow_html=True)

    # Headcount: use exit-month only for multi-period, filter to headcount rows
    hc_all = current_fdf[current_fdf["Level 0"] == "Headcount"].copy()
    hc_pri = prior_act[prior_act["Level 0"] == "Headcount"].copy() if not prior_act.empty else pd.DataFrame()

    # Apply same drill path filters for org levels
    for idx, node in enumerate(path):
        col = ORG_THEN_ACCT[idx]
        if col in hc_all.columns:
            if col == "Department" and node in CORPORATE_DEPT_GROUPS:
                members = CORPORATE_DEPT_GROUPS[node]
                hc_all = hc_all[hc_all[col].isin(members)]
                if not hc_pri.empty:
                    hc_pri = hc_pri[hc_pri[col].isin(members)]
            else:
                hc_all = hc_all[hc_all[col] == node]
                if not hc_pri.empty:
                    hc_pri = hc_pri[hc_pri[col] == node]

    # Determine headcount grouping dimension
    org_only = [c for c in ORG_THEN_ACCT if c in ("Function", "Department", "ART - CPM")]
    if level_idx < len(org_only):
        hc_dim = org_only[level_idx]
    else:
        hc_dim = "Department"  # fallback

    if not hc_all.empty and hc_dim in hc_all.columns:
        hc_work = hc_all.copy()
        if hc_dim == "Department" and is_corporate_dept_view and consolidate_depts:
            hc_work = _apply_corporate_grouping(hc_work)

        hc_actual_agg = (
            hc_work[hc_work["Working.Value"] != 0]
            .groupby(hc_dim, as_index=False)
            .agg(HC_Actual=("Working.Value", "sum"))
        )
        hc_budget_agg = hc_work.groupby(hc_dim, as_index=False).agg(HC_Budget=("Budget.Value", "sum"))
        hc_merged = hc_actual_agg.merge(hc_budget_agg, on=hc_dim, how="outer").fillna(0.0)
        hc_merged["HC_Var"] = hc_merged["HC_Actual"] - hc_merged["HC_Budget"]
        hc_merged = hc_merged.sort_values("HC_Actual", ascending=False)

        hc_disp = hc_merged.copy()
        hc_disp["Actual HC"] = hc_disp["HC_Actual"].map(fmt_headcount)
        hc_disp["Budget HC"] = hc_disp["HC_Budget"].map(fmt_headcount)
        hc_disp["Variance"] = hc_disp["HC_Var"].map(fmt_headcount)

        hc_header = f"<th>{hc_dim}</th><th>Actual HC</th><th>Budget HC</th><th>Variance</th>"
        hc_rows = ""
        for _, row in hc_disp.iterrows():
            hc_rows += f"<tr><td>{row[hc_dim]}</td><td>{row['Actual HC']}</td><td>{row['Budget HC']}</td><td>{row['Variance']}</td></tr>"
        st.markdown(
            f'<table class="themed-table"><thead><tr>{hc_header}</tr></thead>'
            f'<tbody>{hc_rows}</tbody></table>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No headcount data available at this level.")

    # ─── Variance Chart ───
    st.markdown(f'<div class="section-header">Variance by {current_dim}</div>', unsafe_allow_html=True)
    chart_data = grp[grp["Node"] != "Unspecified"].head(12).copy()
    if not chart_data.empty:
        colors = [t["--neg"] if v > 0 else t["--pos"] for v in chart_data["Variance $"]]
        fig_org = go.Figure(
            go.Bar(
                x=chart_data["Variance $"] / 1_000_000,
                y=chart_data["Node"],
                orientation="h",
                marker_color=colors,
                text=[fmt_short_dollars(v) for v in chart_data["Variance $"]],
                textposition="outside",
                cliponaxis=False,
            )
        )
        fig_org.add_vline(x=0, line_color=t["--rule"], line_width=1)
        fig_org.update_layout(**plotly_layout(theme, f"Variance vs {comp_label}", height=min(340, 100 + len(chart_data) * 28)))
        fig_org.update_xaxes(title="Variance ($M)", tickprefix="$", tickformat=",.1f")
        fig_org.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig_org, use_container_width=True)


def render_vendors_tab(
    act: pd.DataFrame,
    current_fdf: pd.DataFrame,
    prior_act: pd.DataFrame,
    total_actual: float,
    total_budget: float,
    total_prior: float,
    compare_mode: str,
    theme: str,
    t: dict[str, str],
    spend_label: str = "Actual",
) -> None:
    """Detailed vendor analysis view with account and org hierarchy breakdowns."""
    # Vendor KPIs
    vendor_count = act[act["vendor_dim"] != "Unspecified"]["vendor_dim"].nunique()
    vendor_total = float(act[act["vendor_dim"] != "Unspecified"]["Working.Value"].sum())

    if compare_mode == "Budget":
        vendor_comp_total = total_budget
        vendor_variance = vendor_total - total_budget
    else:
        vendor_comp_total = total_prior
        vendor_variance = vendor_total - total_prior

    comp_label = "Budget" if compare_mode == "Budget" else "Prior Year"

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total Vendor Spend", fmt_short_dollars(vendor_total))
    with k2:
        st.metric("Unique Vendors", f"{vendor_count:,}")
    with k3:
        pct = (vendor_variance / vendor_comp_total * 100) if vendor_comp_total else 0
        st.metric(f"vs {comp_label}", fmt_short_dollars(vendor_variance), delta=f"{pct:+.1f}%", delta_color="inverse")

    # ─── Vendor Detail Table ───
    st.markdown('<div class="section-header">Vendor Detail</div>', unsafe_allow_html=True)

    vendor_actual = (
        act[act["vendor_dim"] != "Unspecified"]
        .groupby("vendor_dim", as_index=False)
        .agg(Actual=("Working.Value", "sum"))
    )
    if compare_mode == "Budget":
        vendor_comp = (
            current_fdf[current_fdf["vendor_dim"] != "Unspecified"]
            .groupby("vendor_dim", as_index=False)
            .agg(Comp=("Budget.Value", "sum"))
        )
    else:
        vendor_comp = (
            prior_act[prior_act["vendor_dim"] != "Unspecified"]
            .groupby("vendor_dim", as_index=False)
            .agg(Comp=("Working.Value", "sum"))
        ) if not prior_act.empty else pd.DataFrame(columns=["vendor_dim", "Comp"])

    vendors = vendor_actual.merge(vendor_comp, on="vendor_dim", how="outer").fillna(0.0)
    vendors["Variance $"] = vendors["Actual"] - vendors["Comp"]
    vendors["Variance %"] = (vendors["Variance $"] / vendors["Comp"].replace(0, float("nan"))) * 100
    vendors["Share"] = vendors["Actual"] / vendor_total * 100 if vendor_total else 0
    vendors = vendors.sort_values("Actual", ascending=False)

    # Search filter
    v_search = st.text_input("Search vendors", placeholder="Type vendor name...", key="vendor_tab_search")
    if v_search:
        vendors = vendors[vendors["vendor_dim"].str.lower().str.contains(v_search.lower(), na=False)]

    vendors_top = vendors.head(50)
    v_disp = vendors_top.copy()
    v_disp[spend_label] = v_disp["Actual"].map(fmt_millions_paren)
    v_disp[comp_label] = v_disp["Comp"].map(fmt_millions_paren)
    v_disp["Variance $"] = v_disp["Variance $"].map(fmt_millions_paren)
    v_disp["Variance %"] = v_disp["Variance %"].map(fmt_pct_paren)
    v_disp["Share"] = v_disp["Share"].map(lambda x: f"{x:.1f}%")

    st.dataframe(
        v_disp[["vendor_dim", spend_label, comp_label, "Variance $", "Variance %", "Share"]].rename(
            columns={"vendor_dim": "Vendor Parent"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ─── Vendor Deep-Dive ───
    st.markdown('<div class="section-header">Vendor Deep-Dive</div>', unsafe_allow_html=True)
    vendor_options = list(vendors["vendor_dim"].head(100))
    selected_vendor = st.selectbox(
        "Select a vendor to explore",
        options=[""] + vendor_options,
        index=0,
        key="vendor_deep_dive",
        placeholder="Select a vendor...",
    )

    if selected_vendor:
        v_data = act[act["vendor_dim"] == selected_vendor]
        v_all = current_fdf[current_fdf["vendor_dim"] == selected_vendor]

        # ── Accounts this vendor hits ──
        st.markdown(
            f'<div style="font-size:0.75rem;font-weight:600;color:var(--ink-3);margin-top:1rem;margin-bottom:0.3rem;">'
            f'ACCOUNTS HIT BY {selected_vendor.upper()}</div>',
            unsafe_allow_html=True,
        )
        v_by_acct = (
            v_data.groupby(["Level 0", "Level 1", "Account Name"], as_index=False)
            .agg(Actual=("Working.Value", "sum"))
            .sort_values("Actual", ascending=False)
            .head(25)
        )
        if compare_mode == "Budget":
            v_acct_comp = (
                v_all.groupby(["Level 0", "Level 1", "Account Name"], as_index=False)
                .agg(Comp=("Budget.Value", "sum"))
            )
        else:
            v_pri = prior_act[prior_act["vendor_dim"] == selected_vendor] if not prior_act.empty else pd.DataFrame()
            if not v_pri.empty:
                v_acct_comp = v_pri.groupby(["Level 0", "Level 1", "Account Name"], as_index=False).agg(Comp=("Working.Value", "sum"))
            else:
                v_acct_comp = pd.DataFrame(columns=["Level 0", "Level 1", "Account Name", "Comp"])

        v_acct_merged = v_by_acct.merge(v_acct_comp, on=["Level 0", "Level 1", "Account Name"], how="left").fillna(0.0)
        v_acct_merged["Var $"] = v_acct_merged["Actual"] - v_acct_merged["Comp"]

        va_header = "<th>Category</th><th>Sub-Category</th><th>Account</th><th>Spend</th><th>" + comp_label + "</th><th>Var $</th>"
        va_rows = ""
        for _, row in v_acct_merged.iterrows():
            va_rows += (
                f"<tr><td>{row['Level 0']}</td><td>{row['Level 1']}</td><td>{row['Account Name']}</td>"
                f"<td>{fmt_thousands_paren(row['Actual'])}</td>"
                f"<td>{fmt_thousands_paren(row['Comp'])}</td>"
                f"<td>{fmt_thousands_paren(row['Var $'])}</td></tr>"
            )
        st.markdown(
            f'<table class="themed-table"><thead><tr>{va_header}</tr></thead>'
            f'<tbody>{va_rows}</tbody></table>',
            unsafe_allow_html=True,
        )

        # ── Organizational breakdown ──
        st.markdown(
            f'<div style="font-size:0.75rem;font-weight:600;color:var(--ink-3);margin-top:1rem;margin-bottom:0.3rem;">'
            f'ORGANIZATIONAL BREAKDOWN FOR {selected_vendor.upper()}</div>',
            unsafe_allow_html=True,
        )

        col_fn, col_dept, col_art = st.columns(3)

        with col_fn:
            st.markdown("**By Function**")
            v_fn = (
                v_data.groupby("Function", as_index=False)
                .agg(Spend=("Working.Value", "sum"))
                .sort_values("Spend", ascending=False)
            )
            for _, row in v_fn.iterrows():
                st.markdown(f"- {row['Function']}: {fmt_thousands_paren(row['Spend'])}")

        with col_dept:
            st.markdown("**By Department**")
            v_dept = (
                v_data.groupby("Department", as_index=False)
                .agg(Spend=("Working.Value", "sum"))
                .sort_values("Spend", ascending=False)
                .head(10)
            )
            for _, row in v_dept.iterrows():
                st.markdown(f"- {row['Department']}: {fmt_thousands_paren(row['Spend'])}")

        with col_art:
            st.markdown("**By ART-CPM**")
            v_art = (
                v_data.groupby("ART - CPM", as_index=False)
                .agg(Spend=("Working.Value", "sum"))
                .sort_values("Spend", ascending=False)
                .head(10)
            )
            for _, row in v_art.iterrows():
                st.markdown(f"- {row['ART - CPM']}: {fmt_thousands_paren(row['Spend'])}")

        # ── Period trend for selected vendor ──
        st.markdown(
            f'<div style="font-size:0.75rem;font-weight:600;color:var(--ink-3);margin-top:1rem;margin-bottom:0.3rem;">'
            f'MONTHLY TREND FOR {selected_vendor.upper()}</div>',
            unsafe_allow_html=True,
        )
        v_trend = (
            v_data.groupby("Date Label", as_index=False)
            .agg(Spend=("Working.Value", "sum"))
        )
        v_trend["_ord"] = v_trend["Date Label"].map({m: i for i, m in enumerate(ALL_PERIODS_ORDERED)}).fillna(99)
        v_trend = v_trend.sort_values("_ord").drop(columns="_ord")

        if len(v_trend) > 1:
            fig_vt = go.Figure(
                go.Bar(
                    x=v_trend["Date Label"],
                    y=v_trend["Spend"] / 1_000,
                    marker_color=t["--accent"],
                    text=[fmt_thousands_paren(v) for v in v_trend["Spend"]],
                    textposition="outside",
                    cliponaxis=False,
                )
            )
            fig_vt.update_layout(**plotly_layout(theme, height=260))
            fig_vt.update_yaxes(title="Spend ($K)", tickprefix="$", tickformat=",.0f")
            st.plotly_chart(fig_vt, use_container_width=True)
        else:
            st.info("Only one period of data available for this vendor.")

    # ─── Vendor by Category ───
    st.markdown('<div class="section-header">Vendor Spend by Category</div>', unsafe_allow_html=True)
    vendor_by_cat = (
        act[act["vendor_dim"] != "Unspecified"]
        .groupby("Level 0", as_index=False)
        .agg(Spend=("Working.Value", "sum"), Vendors=("vendor_dim", "nunique"))
        .sort_values("Spend", ascending=False)
    )
    vendor_by_cat["Spend_M"] = vendor_by_cat["Spend"] / 1_000_000
    vendor_by_cat["Share"] = vendor_by_cat["Spend"] / vendor_total * 100 if vendor_total else 0

    fig_comp = go.Figure(
        go.Bar(
            x=vendor_by_cat["Spend_M"],
            y=vendor_by_cat["Level 0"],
            orientation="h",
            marker_color=t["--accent"],
            text=[f"{fmt_short_dollars(v)} ({s:.0f}%)" for v, s in zip(vendor_by_cat["Spend"], vendor_by_cat["Share"])],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig_comp.update_layout(**plotly_layout(theme, "Vendor Spend by Expense Category", height=300))
    fig_comp.update_xaxes(title="Spend ($M)", tickprefix="$", tickformat=",.1f")
    fig_comp.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig_comp, use_container_width=True)

    # Export
    st.download_button(
        "Export Vendor Data (CSV)",
        data=vendors[["vendor_dim", "Actual", "Comp", "Variance $", "Variance %", "Share"]].rename(
            columns={"vendor_dim": "Vendor Parent", "Comp": comp_label}
        ).to_csv(index=False).encode("utf-8"),
        file_name="vendors_export.csv",
        mime="text/csv",
        key="vendor_export",
    )


def main() -> None:
    preferred_level0_order = [
        "Employee Compensation & Benefits",
        "Depreciation & Amortization",
        "Professional & Consultancy",
        "Technology",
        "Communication",
        "Clearing Fees",
        "Marketing",
        "Rent and Utilities",
        "Travel & Entertainment",
        "Other",
        "Headcount",
    ]

    with st.sidebar:
        st.markdown("### Dashboard Settings")
        theme = st.selectbox("Background", list(THEMES.keys()), index=0)
        st.caption("Theme: MKTX")
        st.divider()
        st.markdown("### Filters")

    inject_theme(theme)
    t = THEMES[theme]

    csv_path = Path(__file__).parent / DATA_FILE
    if not csv_path.exists():
        st.error(f"Data file not found: {csv_path}")
        st.stop()

    with st.spinner("Loading data..."):
        df = load_data(str(csv_path))

    with st.sidebar:
        dept_opts = sorted(str(v) for v in df["Department"].unique())
        fn_opts = sorted(str(v) for v in df["Function"].unique())
        vendor_opts = sorted(str(v) for v in df["vendor_dim"].unique() if v != "Unspecified")

        dept_filter = st.multiselect(
            "Department",
            dept_opts,
            placeholder="Filter by department",
        )
        fn_filter = st.multiselect(
            "Function",
            fn_opts,
            placeholder="Filter by function",
        )

        st.markdown("#### Expense Category")
        expense_level_filters: dict[str, list[str]] = {}
        for lvl in LEVEL_COLUMNS:
            lvl_opts = sorted(str(v) for v in df[lvl].unique() if str(v).strip())
            expense_level_filters[lvl] = st.multiselect(
                f"{lvl}",
                lvl_opts,
                placeholder=f"Filter by {lvl.lower()}",
            )

        vendor_filter = st.multiselect(
            "Vendor Parent",
            vendor_opts,
            placeholder="Filter by vendor parent",
        )

    st.markdown(
        '<h1 style="margin-bottom:0.05rem;letter-spacing:-.01em">Expense Dashboard</h1>'
        '<p style="margin-top:0;font-size:0.82rem;color:var(--ink-3)">MarketAxess · Expense Intelligence</p>',
        unsafe_allow_html=True,
    )

    c0, c1, c2, _ = st.columns([1.6, 2, 2, 4.4])
    with c0:
        granularity = st.selectbox("View", ["Aggregated", "Monthly"], index=0)

    period_options = build_period_options(set(df["Date Label"].unique())) if granularity == "Aggregated" else {m: [m] for m in ordered_month_labels(df)}
    period_default = DEFAULT_PERIOD if granularity == "Aggregated" else DEFAULT_MONTH
    period_keys = list(period_options.keys())
    period_index = period_keys.index(period_default) if period_default in period_keys else max(0, len(period_keys) - 1)

    with c1:
        period_label = st.selectbox(
            "Period",
            period_keys,
            index=period_index,
        )
    with c2:
        compare_mode = st.selectbox("Compare vs.", ["Prior Year", "Budget"])

    period_labels = period_options[period_label]
    prior_labels = prior_period_labels(period_labels, set(df["Date Label"].unique()))

    current_fdf = apply_dimension_filters(
        df,
        period_labels,
        dept_filter,
        fn_filter,
        expense_level_filters,
        vendor_filter,
    )
    prior_fdf = apply_dimension_filters(
        df,
        prior_labels,
        dept_filter,
        fn_filter,
        expense_level_filters,
        vendor_filter,
    ) if prior_labels else df.iloc[0:0].copy()

    act = current_fdf[current_fdf["is_actuals_row"]].copy()
    prior_act = prior_fdf[prior_fdf["is_actuals_row"]].copy()
    txn = current_fdf[current_fdf["is_netsuite_row"]].copy()

    # Headcount is point-in-time: use only exit month for multi-month periods
    act = _hc_exit_only(act, period_labels)
    prior_act = _hc_exit_only(prior_act, prior_labels) if prior_labels else prior_act
    current_fdf = _hc_exit_only(current_fdf, period_labels)

    if act.empty and txn.empty and current_fdf.empty:
        st.warning("No data for the current filters and period.")
        st.stop()

    # Determine which months are closed (have Actuals) vs open (Working only)
    closed_months = set(
        current_fdf[current_fdf["Actuals.Value"] != 0]["Date Label"].unique()
    ) if not current_fdf.empty else set()
    open_months = [m for m in period_labels if m not in closed_months]
    is_partial_period = len(open_months) > 0 and len(period_labels) > 1
    spend_label = "Forecast" if is_partial_period else "Actual"

    # Working.Value is the single source for actuals/forecast — never mix with Budget
    total_actual = float(act["Working.Value"].sum())
    total_budget = float(current_fdf["Budget.Value"].sum())
    total_prior = float(prior_act["Working.Value"].sum()) if not prior_act.empty else float(act["PriorYear.Amount"].sum())

    yoy_delta = total_actual - total_prior
    budget_delta = total_actual - total_budget

    comp_delta = yoy_delta if compare_mode == "Prior Year" else budget_delta
    comp_base = total_prior if compare_mode == "Prior Year" else total_budget
    if compare_mode == "Prior Year" and prior_labels:
        # Derive a friendly name for the prior period
        if granularity == "Aggregated":
            # Map back to the quarter key for the prior period
            prior_quarter_keys = sorted(set(MONTH_TO_QUARTER.get(m, m) for m in prior_labels))
            prior_friendly = ", ".join(prior_quarter_keys) if prior_quarter_keys else ", ".join(prior_labels)
        else:
            # Monthly: just show the single month we're comparing against
            prior_friendly = ", ".join(prior_labels)
        comp_label = f"vs {prior_friendly}"
    else:
        comp_label = "vs Prior Year" if compare_mode == "Prior Year" else "vs Budget"

    tab_overview, tab_pnl, tab_departments, tab_vendors, tab_transactions = st.tabs(
        ["01 Overview", "02 P&L", "03 Organization", "04 Vendors", "05 Transactions"]
    )

    with tab_overview:
        render_kpi_band(
            period_label, total_actual, comp_delta, comp_base, comp_label,
            compare_mode, total_budget, total_prior, budget_delta,
            is_partial_period=is_partial_period,
            open_months=open_months,
        )

        fig_trend = render_trend_chart(
            df, period_labels, dept_filter, fn_filter, expense_level_filters, vendor_filter, theme, t, granularity, spend_label,
        )
        fig_cat = render_category_chart(act, total_actual, preferred_level0_order, theme, t)

        col_trend, col_cat = st.columns([3, 2], gap="large")
        with col_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        with col_cat:
            st.plotly_chart(fig_cat, use_container_width=True)

        render_drill_table(act, current_fdf, prior_act, total_actual, preferred_level0_order, period_label, spend_label)
        render_vendors_and_movers(act, current_fdf, preferred_level0_order, theme, t, spend_label)

    with tab_pnl:
        render_pnl_tab(
            act, current_fdf, prior_act, total_actual, total_budget, total_prior,
            preferred_level0_order, compare_mode, theme, t, period_label, spend_label,
        )

    with tab_departments:
        render_organization_tab(
            act, current_fdf, prior_act, total_actual, compare_mode, theme, t, period_labels, spend_label,
        )

    with tab_vendors:
        render_vendors_tab(
            act, current_fdf, prior_act, total_actual, total_budget, total_prior,
            compare_mode, theme, t, spend_label,
        )

    with tab_transactions:
        render_transactions(txn, txn, period_label)

    # Diagnostic: show "Unspecified" Level 0 rows if they have non-zero actual spend
    unspec_rows = act[act["Level 0"] == "Unspecified"]
    if not unspec_rows.empty and abs(unspec_rows["Working.Value"].sum()) >= 0.01:
        st.markdown("---")
        st.warning("⚠️ 'Unspecified' Level 0 rows have non-zero spend — review source data.")
        st.dataframe(
            unspec_rows[["Date Label", "Account Name", "Level 1", "Level 2", "Department", "Vendor Parent", "Working.Value", "Budget.Value"]]
            .sort_values("Working.Value", ascending=False)
            .head(50),
            use_container_width=True,
            hide_index=True,
        )

    _mtime = csv_path.stat().st_mtime
    _freshness = _dt.datetime.fromtimestamp(_mtime).strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f'<div class="dash-footer">Source: {DATA_FILE} | '
        f'Data updated: {_freshness} | '
        f'Period: {period_label} ({", ".join(period_labels)}) | '
        f'Prior comparison period: {", ".join(prior_labels) if prior_labels else "n/a"} | '
        f'KPI source: Working.Value rows | '
        f'Transaction/vendor source: NetSuite.Amount rows + Vendor Parent</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
