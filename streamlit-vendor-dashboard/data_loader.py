"""
Data loading and transformation for vendor spend analytics.
Loads Excel file, melts from wide format, parses quarters, detects projections.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────────────────────
# Candidate Excel files. The loader will pick the first one with valid quarter headers.
EXCEL_PATHS = [
    Path(__file__).parent / "Expense Vendor Detail.xlsx",
    Path(__file__).parent / "vendor_spend.xlsx",
]

# Projection cutoff: quarters >= this are marked as projected
PROJECTION_START = (2026, 1)  # (year, quarter_num) — Q1 2026 onward


def parse_quarter_column(col_name: str) -> Tuple[int, int] | None:
    """
    Parse a quarter column header like 'Q1 2019' or 'Q1-FY19' into (year, quarter_num).
    Returns None if parsing fails.
    """
    col_name = col_name.strip()
    
    # Try format: Q1-FY19 (or Q1-FY2019)
    if "-FY" in col_name:
        try:
            parts = col_name.split("-")
            if len(parts) == 2:
                q = int(parts[0][1])  # Extract digit from 'Q1'
                fy_str = parts[1].replace("FY", "")  # Extract '19' or '2019'
                y = int(fy_str)
                if len(fy_str) == 2:
                    y = 2000 + y  # Convert FY19 to 2019
                if 1 <= q <= 4 and y >= 2000:
                    return (y, q)
        except (ValueError, IndexError):
            pass
    
    # Try format: Q1 2019 (space-separated)
    parts = col_name.split()
    if len(parts) >= 2:
        try:
            q = int(parts[0][1])  # Extract digit from 'Q1'
            y = int(parts[1])     # Extract year
            if 1 <= q <= 4 and y >= 2000:
                return (y, q)
        except (ValueError, IndexError):
            pass
    
    return None


def is_projected(year: int, quarter_num: int) -> bool:
    """Check if a quarter is projected (Q1 2026 onward)."""
    return (year, quarter_num) >= PROJECTION_START


@st.cache_data
def load_and_transform_data() -> pd.DataFrame:
    """
    Load Excel file, melt from wide to long format.
    Returns DataFrame with columns: Vendor, Quarter, Spend, Year, QuarterNum, IsProjected
    """
    existing_paths = [p for p in EXCEL_PATHS if p.exists()]
    if not existing_paths:
        expected = ", ".join(str(p.name) for p in EXCEL_PATHS)
        raise FileNotFoundError(f"Excel file not found. Expected one of: {expected}")

    df = None
    quarter_cols = []
    quarter_meta = {}

    # Try each candidate file.
    for path in existing_paths:
        raw = pd.read_excel(path, header=None)

        # ── Try LONG format first ──────────────────────────────────────────
        # Long format: each row is vendor+quarter+spend.
        # Detect by looking for a column whose values match quarter patterns.
        quarter_col_idx = None
        for col_idx in range(raw.shape[1]):
            sample = raw.iloc[:, col_idx].dropna().astype(str)
            matches = sample.apply(lambda v: parse_quarter_column(v) is not None).sum()
            if matches >= 3:  # at least 3 matching quarter values
                quarter_col_idx = col_idx
                break

        if quarter_col_idx is not None:
            # Filter to rows that have a valid quarter value
            mask = raw.iloc[:, quarter_col_idx].astype(str).apply(
                lambda v: parse_quarter_column(v) is not None
            )
            data_rows = raw[mask].copy()

            # Vendor is column 0, spend is the numeric column closest to quarter col
            # Based on observed structure: col0=Vendor, col2=Spend, col4=Quarter
            vendor_col_idx = 0
            # Find spend column: first numeric column that isn't the quarter col or vendor col
            spend_col_idx = None
            for c in range(raw.shape[1]):
                if c in (vendor_col_idx, quarter_col_idx):
                    continue
                if pd.to_numeric(data_rows.iloc[:, c], errors="coerce").notna().sum() > len(data_rows) * 0.5:
                    spend_col_idx = c
                    break

            if spend_col_idx is None:
                continue  # can't find spend column, try next file

            df = pd.DataFrame({
                "Vendor": data_rows.iloc[:, vendor_col_idx].astype(str).str.strip().values,
                "Quarter": data_rows.iloc[:, quarter_col_idx].astype(str).str.strip().values,
                "Spend": pd.to_numeric(data_rows.iloc[:, spend_col_idx], errors="coerce").values,
            })
            df = df.dropna(subset=["Spend"])
            parsed = df["Quarter"].apply(parse_quarter_column)
            df["Year"] = parsed.apply(lambda x: x[0])
            df["QuarterNum"] = parsed.apply(lambda x: x[1])
            df["IsProjected"] = df.apply(
                lambda row: is_projected(row["Year"], row["QuarterNum"]), axis=1
            )
            df = df.sort_values(["Vendor", "Year", "QuarterNum"]).reset_index(drop=True)
            return df

        # ── Try WIDE format ────────────────────────────────────────────────
        # Wide format: first row is headers with quarter names as column names.
        candidate = pd.read_excel(path)
        vendor_col = candidate.columns[0]
        candidate = candidate.rename(columns={vendor_col: "Vendor"})

        candidate_quarter_cols = []
        candidate_quarter_meta = {}

        for col in candidate.columns[1:]:
            parsed = parse_quarter_column(str(col))
            if parsed:
                candidate_quarter_cols.append(col)
                candidate_quarter_meta[col] = parsed

        if candidate_quarter_cols:
            df = candidate
            quarter_cols = candidate_quarter_cols
            quarter_meta = candidate_quarter_meta
            break

    if df is None or not quarter_cols:
        raise ValueError(
            "No valid quarter columns found in available files "
            "(expected headers like Q1 2019 or Q1-FY19)."
        )

    # Melt to long format
    melted = df.melt(
        id_vars=["Vendor"],
        value_vars=quarter_cols,
        var_name="Quarter",
        value_name="Spend"
    )

    # Add Year, QuarterNum, IsProjected columns
    melted["Year"] = melted["Quarter"].map(lambda q: quarter_meta[q][0])
    melted["QuarterNum"] = melted["Quarter"].map(lambda q: quarter_meta[q][1])
    melted["IsProjected"] = melted.apply(
        lambda row: is_projected(row["Year"], row["QuarterNum"]),
        axis=1
    )

    # Clean spend (handle nulls, convert to float)
    melted["Spend"] = pd.to_numeric(melted["Spend"], errors="coerce")
    melted = melted.dropna(subset=["Spend"])

    # Sort by vendor, year, quarter
    melted = melted.sort_values(["Vendor", "Year", "QuarterNum"]).reset_index(drop=True)

    return melted


def get_quarters_range(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    """Returns (min_year, min_q, max_year, max_q) from the dataset."""
    min_year = df["Year"].min()
    max_year = df["Year"].max()
    min_q = df[df["Year"] == min_year]["QuarterNum"].min()
    max_q = df[df["Year"] == max_year]["QuarterNum"].max()
    return (min_year, min_q, max_year, max_q)


def quarter_to_index(year: int, quarter_num: int) -> int:
    """Convert (year, quarter_num) to a global quarter index for range sliders."""
    return (year - 2019) * 4 + (quarter_num - 1)


def index_to_quarter(idx: int) -> Tuple[int, int]:
    """Convert a global quarter index back to (year, quarter_num)."""
    year = 2019 + idx // 4
    quarter_num = (idx % 4) + 1
    return (year, quarter_num)


def format_currency(value: float) -> str:
    """Format a number as currency ($X.XM for millions, $X.XK for thousands)."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:.0f}"
