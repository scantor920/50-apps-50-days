"""
Data loading and transformation for the Detailed Expense Analytics Dashboard.

Loads the NetSuite CSV export, parses dates, derives account hierarchy from
the colon-separated Account_NetSuite_Name field, and caches the result.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH = Path(__file__).parent.parent / "Expense Export for App V1.0.csv"
SOURCE_AMOUNT_COL = "Line_Amount_USD_Reportable"
AMOUNT_COL = "Spend_USD"
DATE_COL = "Accounting_Period_End_Date"

TX_TYPE_LABELS: dict[str, str] = {
    "Journal":  "Journal Entry",
    "VendBill": "Vendor Bill",
    "Check":    "Check",
    "CustInvc": "Customer Invoice",
    "ExpRept":  "Expense Report",
    "CustPymt": "Customer Payment",
    "VendCred": "Vendor Credit",
    "CustCred": "Customer Credit",
    "Deposit":  "Deposit",
}


def format_currency(val: float) -> str:
    """Format a dollar amount as $XM / $XK / $X."""
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if abs(val) >= 1_000:
        return f"${val / 1_000:.1f}K"
    return f"${val:,.0f}"


@st.cache_data(show_spinner="Loading expense data…")
def load_data() -> pd.DataFrame:
    """
    Load the CSV export and enrich with derived columns:
      - Period_Date     : parsed datetime from Accounting_Period_End_Date
      - YearMonth       : pandas Period (M) for grouping
      - Year / Month    : integer year and month
      - Account_Category / Account_Subcategory : split on ' : '
      - Transaction_Type_Label : human-readable transaction type
      - Vendor_Name     : 'None' string → pd.NA
    """
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found at: {CSV_PATH}\n"
            f"Expected: 'Expense Export for App V1.0.csv' in the workspace root."
        )

    df = pd.read_csv(CSV_PATH, low_memory=False)

    # ── Amount ────────────────────────────────────────────────────────────────
    # Keep source signed amount for tie-outs and create a positive-spend display column.
    df[SOURCE_AMOUNT_COL] = pd.to_numeric(df[SOURCE_AMOUNT_COL], errors="coerce").fillna(0.0)
    df[AMOUNT_COL] = -df[SOURCE_AMOUNT_COL]

    # ── Date ──────────────────────────────────────────────────────────────────
    df["Period_Date"] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=["Period_Date"]).copy()
    df["YearMonth"] = df["Period_Date"].dt.to_period("M")
    df["Year"]  = df["Period_Date"].dt.year
    df["Month"] = df["Period_Date"].dt.month

    # ── Account hierarchy ─────────────────────────────────────────────────────
    # Account_NetSuite_Name uses 'Category : Subcategory' colon notation.
    account_names = df["Account_NetSuite_Name"].fillna("Unknown").astype(str)
    split_result = account_names.str.split(" : ", n=1, expand=True)
    df["Account_Category"] = split_result[0].str.strip()
    df["Account_Subcategory"] = (
        split_result[1].str.strip().fillna("")
        if 1 in split_result.columns
        else pd.Series("", index=df.index)
    )

    # ── Transaction type labels ────────────────────────────────────────────────
    df["Transaction_Type_Label"] = (
        df["Transaction_Type"].map(TX_TYPE_LABELS).fillna(df["Transaction_Type"])
    )

    # ── Vendor cleanup ────────────────────────────────────────────────────────
    df["Vendor_Name"]    = df["Vendor_Name"].replace("None", pd.NA)
    df["Vendor Parent"]  = df["Vendor Parent"].replace("", pd.NA)

    # ── Dimension fill-downs ──────────────────────────────────────────────────
    df["Department_Name"]         = df["Department_Name"].fillna("Unassigned")
    df["Subsidiary_Name_NetSuite"] = df["Subsidiary_Name_NetSuite"].fillna("Unknown")

    return df
