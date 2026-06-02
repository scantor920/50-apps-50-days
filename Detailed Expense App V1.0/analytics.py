"""
Analytics calculations for the Detailed Expense Analytics Dashboard.

All functions accept a pre-filtered DataFrame and return data ready to render.
"""

import pandas as pd
from typing import Optional, Dict, Any
from data_loader import AMOUNT_COL


def get_kpis(
    df: pd.DataFrame,
    prior_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Compute executive KPI metrics.

    Returns a dict with keys:
      total_spend, tx_count, avg_monthly, top_vendor, top_vendor_spend,
      top_dept, top_dept_spend, top_category, delta_spend (% vs prior period).
    """
    total_spend  = float(df[AMOUNT_COL].sum())
    tx_count     = len(df)

    monthly      = df.groupby("YearMonth")[AMOUNT_COL].sum()
    avg_monthly  = float(monthly.mean()) if len(monthly) else 0.0

    # Top vendor (rows without a vendor are excluded)
    vendor_df = df[df["Vendor_Name"].notna()]
    top_vendor, top_vendor_spend = None, 0.0
    if len(vendor_df):
        vt = vendor_df.groupby("Vendor_Name")[AMOUNT_COL].sum()
        if len(vt):
            top_vendor       = str(vt.idxmax())
            top_vendor_spend = float(vt.max())

    # Top department
    dept_totals   = df.groupby("Department_Name")[AMOUNT_COL].sum()
    top_dept      = str(dept_totals.idxmax()) if len(dept_totals) else None
    top_dept_spend = float(dept_totals.max()) if len(dept_totals) else 0.0

    # Top account category
    cat_totals   = df.groupby("Account_Category")[AMOUNT_COL].sum()
    top_category = str(cat_totals.idxmax()) if len(cat_totals) else None

    # Period-over-period delta
    delta_spend: Optional[float] = None
    if prior_df is not None and len(prior_df):
        prior_total = float(prior_df[AMOUNT_COL].sum())
        if prior_total != 0:
            delta_spend = (total_spend - prior_total) / abs(prior_total) * 100.0

    return {
        "total_spend":      total_spend,
        "tx_count":         tx_count,
        "avg_monthly":      avg_monthly,
        "top_vendor":       top_vendor,
        "top_vendor_spend": top_vendor_spend,
        "top_dept":         top_dept,
        "top_dept_spend":   top_dept_spend,
        "top_category":     top_category,
        "delta_spend":      delta_spend,
    }


def get_monthly_trend(
    df: pd.DataFrame,
    group_by: Optional[str] = None,
) -> pd.DataFrame:
    """
    Aggregate spend by calendar month, optionally broken out by a dimension.
    Returns a DataFrame with a 'Date' (Timestamp) column for Plotly ordering.
    """
    if group_by:
        trend = (
            df.groupby(["YearMonth", group_by])[AMOUNT_COL]
            .sum()
            .reset_index()
        )
    else:
        trend = df.groupby("YearMonth")[AMOUNT_COL].sum().reset_index()

    trend["Date"] = trend["YearMonth"].dt.to_timestamp()
    return trend.sort_values("Date")


def get_vendor_breakdown(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Top N vendors by net spend (excludes rows with no vendor)."""
    vendor_df = df[df["Vendor_Name"].notna()]
    result = (
        vendor_df.groupby("Vendor_Name")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Vendor", "Spend"]
    return result


def get_vendor_parent_breakdown(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Top N vendor parent groups by net spend."""
    vp_df = df[df["Vendor Parent"].notna()]
    result = (
        vp_df.groupby("Vendor Parent")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Vendor Group", "Spend"]
    return result


def get_department_breakdown(df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    """Top N departments by net spend."""
    result = (
        df.groupby("Department_Name")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Department", "Spend"]
    return result


def get_account_category_breakdown(df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    """Top N account categories by net spend."""
    result = (
        df.groupby("Account_Category")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Category", "Spend"]
    return result


def get_account_subcategory_breakdown(
    df: pd.DataFrame,
    category: Optional[str] = None,
    top_n: int = 25,
) -> pd.DataFrame:
    """
    Top N account subcategories by net spend.
    If category is provided, filters to that category first.
    """
    sub_df = df[df["Account_Category"] == category] if category else df
    result = (
        sub_df.groupby(["Account_Category", "Account_Subcategory"])[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Category", "Subcategory", "Spend"]
    return result


def get_subsidiary_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Net spend by subsidiary, sorted descending."""
    result = (
        df.groupby("Subsidiary_Name_NetSuite")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    result.columns = ["Subsidiary", "Spend"]
    return result


def get_vendors_by_vendor_parent(
    df: pd.DataFrame,
    vendor_parent: str,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top N vendors within a specific vendor parent group by net spend."""
    vp_df = df[df["Vendor Parent"] == vendor_parent]
    result = (
        vp_df.groupby("Vendor_Name")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Vendor", "Spend"]
    return result


def get_accounts_by_vendor_parent(
    df: pd.DataFrame,
    vendor_parent: str,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top N account categories hit by a specific vendor parent group."""
    vp_df = df[df["Vendor Parent"] == vendor_parent]
    result = (
        vp_df.groupby("Account_Category")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Account Category", "Spend"]
    return result


def get_vendors_by_department(
    df: pd.DataFrame,
    department: str,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top N vendors spending in a specific department."""
    dept_df = df[(df["Department_Name"] == department) & (df["Vendor_Name"].notna())]
    result = (
        dept_df.groupby("Vendor_Name")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Vendor", "Spend"]
    return result


def get_accounts_by_department(
    df: pd.DataFrame,
    department: str,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top N account categories where a specific department spends money."""
    dept_df = df[df["Department_Name"] == department]
    result = (
        dept_df.groupby("Account_Category")[AMOUNT_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    result.columns = ["Account Category", "Spend"]
    return result
