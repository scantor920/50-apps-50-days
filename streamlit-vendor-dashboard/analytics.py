"""
Analytics calculations for vendor spend: KPIs, rankings, trends, Pareto, anomalies.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from data_loader import format_currency


def filter_data(
    df: pd.DataFrame,
    vendors: List[str],
    year_q_range: Tuple[int, int, int, int],
    include_projected: bool
) -> pd.DataFrame:
    """
    Filter dataset by vendors, date range, and projection flag.
    year_q_range is (min_year, min_q, max_year, max_q).
    """
    filtered = df.copy()

    # Vendors
    if vendors:
        filtered = filtered[filtered["Vendor"].isin(vendors)]

    # Date range: include any quarter >= (min_y, min_q) and <= (max_y, max_q)
    min_y, min_q, max_y, max_q = year_q_range
    filtered = filtered[
        ((filtered["Year"] > min_y) | ((filtered["Year"] == min_y) & (filtered["QuarterNum"] >= min_q))) &
        ((filtered["Year"] < max_y) | ((filtered["Year"] == max_y) & (filtered["QuarterNum"] <= max_q)))
    ]

    # Projections
    if not include_projected:
        filtered = filtered[~filtered["IsProjected"]]

    return filtered


def get_kpis(df: pd.DataFrame, prior_range: Tuple[int, int, int, int] | None = None) -> Dict[str, any]:
    """
    Compute KPI metrics: total_spend, vendor_count, avg_quarterly, top_vendor.
    If prior_range provided, compute delta vs. prior period.
    """
    total_spend = df["Spend"].sum()
    vendor_count = df["Vendor"].nunique()
    avg_quarterly = df.groupby(["Year", "QuarterNum"])["Spend"].sum().mean() if len(df) > 0 else 0
    
    top_vendor = None
    top_vendor_spend = 0
    if len(df) > 0:
        vendor_totals = df.groupby("Vendor")["Spend"].sum()
        top_vendor = vendor_totals.idxmax()
        top_vendor_spend = vendor_totals.max()

    # Delta calculation (vs. prior equivalent period)
    delta_total = None
    delta_top = None
    if prior_range:
        # Recompute for prior period (no projection filter applied here; caller handles)
        prior_filtered = df[
            ((df["Year"] > prior_range[0]) | ((df["Year"] == prior_range[0]) & (df["QuarterNum"] >= prior_range[1]))) &
            ((df["Year"] < prior_range[2]) | ((df["Year"] == prior_range[2]) & (df["QuarterNum"] <= prior_range[3])))
        ]
        prior_total = prior_filtered["Spend"].sum()
        if prior_total > 0:
            delta_total = ((total_spend - prior_total) / prior_total) * 100

    return {
        "total_spend": total_spend,
        "vendor_count": vendor_count,
        "avg_quarterly": avg_quarterly,
        "top_vendor": top_vendor,
        "top_vendor_spend": top_vendor_spend,
        "delta_total": delta_total,
    }


def get_top_vendors(
    df: pd.DataFrame,
    top_n: int,
    rank_by: str = "total_spend"  # "total_spend", "avg_quarterly", "growth"
) -> pd.DataFrame:
    """
    Rank vendors by selected metric. Returns top N.
    rank_by: "total_spend" | "avg_quarterly" | "growth" (latest vs earliest quarter)
    """
    if rank_by == "total_spend":
        vendor_metric = df.groupby("Vendor")["Spend"].sum().sort_values(ascending=False)
    elif rank_by == "avg_quarterly":
        vendor_metric = df.groupby("Vendor")["Spend"].mean().sort_values(ascending=False)
    elif rank_by == "growth":
        # Latest quarter spend vs earliest quarter spend
        vendor_by_q = df.groupby(["Vendor", "Year", "QuarterNum"])["Spend"].sum().reset_index()
        earliest = vendor_by_q.loc[vendor_by_q.groupby("Vendor")[["Year", "QuarterNum"]].idxmin().values]
        latest = vendor_by_q.loc[vendor_by_q.groupby("Vendor")[["Year", "QuarterNum"]].idxmax().values]
        growth = {}
        for vendor in df["Vendor"].unique():
            e_spend = earliest[earliest["Vendor"] == vendor]["Spend"].values
            l_spend = latest[latest["Vendor"] == vendor]["Spend"].values
            if len(e_spend) > 0 and len(l_spend) > 0 and e_spend[0] > 0:
                growth[vendor] = ((l_spend[0] - e_spend[0]) / e_spend[0]) * 100
            else:
                growth[vendor] = 0
        vendor_metric = pd.Series(growth).sort_values(ascending=False)
    else:
        vendor_metric = df.groupby("Vendor")["Spend"].sum().sort_values(ascending=False)

    top = vendor_metric.head(top_n).reset_index()
    top.columns = ["Vendor", "Value"]
    return top


def get_trends(df: pd.DataFrame, selected_vendors: List[str] | None = None) -> pd.DataFrame:
    """
    Aggregate spend by quarter. If selected_vendors list provided, filter to those.
    Returns DataFrame with columns: Year, QuarterNum, Quarter, IsProjected, spend_by_vendor, total_spend
    """
    if selected_vendors:
        df = df[df["Vendor"].isin(selected_vendors)]

    # Pivot by quarter
    quarterly = df.groupby(["Year", "QuarterNum", "IsProjected"]).agg({
        "Spend": "sum",
        "Vendor": "nunique"
    }).reset_index()

    quarterly.columns = ["Year", "QuarterNum", "IsProjected", "TotalSpend", "VendorCount"]
    quarterly["Quarter"] = quarterly.apply(lambda x: f"Q{x['QuarterNum']} {x['Year']}", axis=1)
    quarterly = quarterly.sort_values(["Year", "QuarterNum"])

    return quarterly


def get_pareto(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """
    Calculate Pareto: vendor spend sorted descending, plus cumulative %.
    Returns (DataFrame, cumulative_% at 80%).
    """
    vendor_spend = df.groupby("Vendor")["Spend"].sum().sort_values(ascending=False).reset_index()
    vendor_spend.columns = ["Vendor", "Spend"]
    total = vendor_spend["Spend"].sum()
    vendor_spend["CumulativePct"] = (vendor_spend["Spend"].cumsum() / total * 100).round(1)

    # Find how many vendors = 80%
    vendors_at_80 = len(vendor_spend[vendor_spend["CumulativePct"] <= 80])

    return vendor_spend, vendors_at_80


def get_anomalies(df: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    """
    Flag quarter-vendor combinations with spend > z_threshold std devs from
    rolling 4-quarter mean (excluding projections from baseline).
    Returns DataFrame with columns: Vendor, Quarter, Spend, Expected, ZScore, Direction
    """
    anomalies = []

    for vendor in df["Vendor"].unique():
        vendor_data = df[df["Vendor"] == vendor].sort_values(["Year", "QuarterNum"]).reset_index(drop=True)

        # Actual (non-projected) data for rolling baseline
        actual_data = vendor_data[~vendor_data["IsProjected"]]

        if len(actual_data) < 5:  # Need at least some data for rolling mean
            continue

        for idx, row in vendor_data.iterrows():
            # Rolling 4-quarter mean baseline (from actual data only)
            window_end = idx
            window_start = max(0, idx - 4)
            baseline_rows = actual_data[
                (actual_data["Year"] > vendor_data.loc[window_start, "Year"]) |
                ((actual_data["Year"] == vendor_data.loc[window_start, "Year"]) &
                 (actual_data["QuarterNum"] >= vendor_data.loc[window_start, "QuarterNum"]))
            ]
            baseline_rows = baseline_rows[
                (baseline_rows["Year"] < vendor_data.loc[window_end, "Year"]) |
                ((baseline_rows["Year"] == vendor_data.loc[window_end, "Year"]) &
                 (baseline_rows["QuarterNum"] <= vendor_data.loc[window_end, "QuarterNum"]))
            ]

            if len(baseline_rows) > 0:
                mean = baseline_rows["Spend"].mean()
                std = baseline_rows["Spend"].std()

                if std > 0:
                    z_score = (row["Spend"] - mean) / std
                    direction = "High" if z_score > 0 else "Low"

                    if abs(z_score) > z_threshold:
                        anomalies.append({
                            "Vendor": vendor,
                            "Quarter": f"Q{row['QuarterNum']} {row['Year']}",
                            "Spend": row["Spend"],
                            "Expected": mean,
                            "ZScore": round(z_score, 2),
                            "Direction": direction,
                        })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


def get_yoy_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate YoY % change by quarter. Returns DataFrame with columns:
    Year, QuarterNum, Quarter, YoYChange (%)
    """
    quarterly = df.groupby(["Year", "QuarterNum"])["Spend"].sum().reset_index()
    quarterly = quarterly.sort_values(["Year", "QuarterNum"])

    yoy = []
    for year in quarterly["Year"].unique():
        for q in quarterly["QuarterNum"].unique():
            current = quarterly[(quarterly["Year"] == year) & (quarterly["QuarterNum"] == q)]["Spend"].values
            prior = quarterly[(quarterly["Year"] == year - 1) & (quarterly["QuarterNum"] == q)]["Spend"].values

            if len(current) > 0 and len(prior) > 0 and prior[0] > 0:
                pct_change = ((current[0] - prior[0]) / prior[0]) * 100
                yoy.append({
                    "Year": year,
                    "QuarterNum": q,
                    "Quarter": f"Q{q} {year}",
                    "YoYChange": round(pct_change, 1),
                })

    return pd.DataFrame(yoy) if yoy else pd.DataFrame()
