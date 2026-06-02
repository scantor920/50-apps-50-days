"""
Detailed Expense Analytics Dashboard
=====================================
A Streamlit dashboard for analysing NetSuite expense exports.

Run with:
    streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta

from data_loader import load_data, format_currency, AMOUNT_COL, SOURCE_AMOUNT_COL
from analytics import (
    get_kpis,
    get_monthly_trend,
    get_vendor_breakdown,
    get_vendor_parent_breakdown,
    get_department_breakdown,
    get_account_category_breakdown,
    get_account_subcategory_breakdown,
    get_subsidiary_breakdown,
    get_vendors_by_vendor_parent,
    get_accounts_by_vendor_parent,
    get_vendors_by_department,
    get_accounts_by_department,
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Expense Analytics",
    layout="wide",
    page_icon="💰",
)
st.title("💰 Detailed Expense Analytics Dashboard")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
try:
    df_raw = load_data()
except FileNotFoundError as e:
    st.error(f"❌ {e}")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()


# ── HELPER ────────────────────────────────────────────────────────────────────
def filter_by_dates(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    return df[
        (df["Period_Date"].dt.date >= start)
        & (df["Period_Date"].dt.date <= end)
    ]


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Filters")

    data_min: date = df_raw["Period_Date"].min().date()
    data_max: date = df_raw["Period_Date"].max().date()

    # Default: previous full calendar year
    default_start = date(data_max.year - 1, 1, 1)
    default_end   = date(data_max.year - 1, 12, 31)

    st.subheader("📅 Date Range")
    start_date = st.date_input(
        "From", value=default_start, min_value=data_min, max_value=data_max
    )
    end_date = st.date_input(
        "To", value=default_end, min_value=data_min, max_value=data_max
    )

    if start_date > end_date:
        st.warning("⚠️ Start date must be before end date.")
        st.stop()

    st.divider()

    # Subsidiary
    subsidiaries = sorted(df_raw["Subsidiary_Name_NetSuite"].dropna().unique())
    selected_subsidiaries = st.multiselect(
        "🏦 Subsidiary", subsidiaries, default=[]
    )

    # Transaction type
    tx_types = sorted(df_raw["Transaction_Type_Label"].dropna().unique())
    selected_tx_types = st.multiselect(
        "📄 Transaction Type", tx_types, default=[]
    )

    # Department
    departments = sorted(df_raw["Department_Name"].dropna().unique())
    selected_departments = st.multiselect(
        "🏢 Department", departments, default=[]
    )

    st.divider()

    # Vendor search (text, not multiselect — too many unique values)
    vendor_search = st.text_input("🔍 Vendor name contains…", "")

    st.divider()

    # Exclude intercompany
    exclude_ic = st.checkbox("Exclude Intercompany Transactions", value=False)

    # Top N for charts
    top_n = st.slider("🔝 Top N in charts", min_value=5, max_value=50, value=15, step=5)


# ── APPLY FILTERS ─────────────────────────────────────────────────────────────
df = filter_by_dates(df_raw, start_date, end_date)

if selected_subsidiaries:
    df = df[df["Subsidiary_Name_NetSuite"].isin(selected_subsidiaries)]
if selected_tx_types:
    df = df[df["Transaction_Type_Label"].isin(selected_tx_types)]
if selected_departments:
    df = df[df["Department_Name"].isin(selected_departments)]
if vendor_search.strip():
    df = df[
        df["Vendor_Name"].fillna("").str.contains(
            vendor_search.strip(), case=False, regex=False
        )
    ]
if exclude_ic:
    df = df[df["Transaction_Is_Intercompany"].astype(str).str.upper() != "T"]

if len(df) == 0:
    st.warning("⚠️ No data matches your current filters. Try adjusting the sidebar.")
    st.stop()

# ── PRIOR PERIOD DATA (same duration, immediately before selected range) ──────
period_days  = (end_date - start_date).days
prior_end    = start_date - timedelta(days=1)
prior_start  = prior_end  - timedelta(days=period_days)

df_prior = filter_by_dates(df_raw, prior_start, prior_end)
if selected_subsidiaries:
    df_prior = df_prior[df_prior["Subsidiary_Name_NetSuite"].isin(selected_subsidiaries)]
if selected_tx_types:
    df_prior = df_prior[df_prior["Transaction_Type_Label"].isin(selected_tx_types)]
if selected_departments:
    df_prior = df_prior[df_prior["Department_Name"].isin(selected_departments)]


# ── KPI ROW ───────────────────────────────────────────────────────────────────
st.header("📊 Key Metrics")
kpis = get_kpis(df, prior_df=df_prior if len(df_prior) else None)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    delta_str = (
        f"{kpis['delta_spend']:+.1f}% vs prior period"
        if kpis["delta_spend"] is not None
        else None
    )
    st.metric(
        "Net Spend",
        format_currency(kpis["total_spend"]),
        delta=delta_str,
        delta_color="inverse",   # red = spend went up (bad), green = went down
        help="Displayed spend uses -1 x Line_Amount_USD_Reportable for selected filters",
    )

with col2:
    st.metric("Transactions", f"{kpis['tx_count']:,}")

with col3:
    st.metric("Avg Monthly Spend", format_currency(kpis["avg_monthly"]))

with col4:
    if kpis["top_vendor"]:
        st.metric(
            "Top Vendor",
            kpis["top_vendor"],
            help=format_currency(kpis["top_vendor_spend"]),
        )
    else:
        st.metric("Top Vendor", "N/A")

with col5:
    if kpis["top_dept"]:
        st.metric(
            "Top Department",
            kpis["top_dept"],
            help=format_currency(kpis["top_dept_spend"]),
        )
    else:
        st.metric("Top Department", "N/A")

with st.expander("Data Tie-Out (Selected Filters)", expanded=False):
    source_total = float(df[SOURCE_AMOUNT_COL].sum())
    displayed_total = float(df[AMOUNT_COL].sum())
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric("Source Signed Total", format_currency(source_total))
    with col_t2:
        st.metric("Displayed Net Spend", format_currency(displayed_total))
    with col_t3:
        st.metric("Check (Displayed + Source)", format_currency(displayed_total + source_total))
    st.caption("For this app, displayed spend is computed as -1 x source signed amount for the same filtered rows.")

    monthly_tieout = (
        df.groupby("YearMonth")[[SOURCE_AMOUNT_COL, AMOUNT_COL]]
        .sum()
        .reset_index()
        .sort_values("YearMonth")
    )
    monthly_tieout["Month"] = monthly_tieout["YearMonth"].astype(str)
    monthly_tieout["Check"] = monthly_tieout[AMOUNT_COL] + monthly_tieout[SOURCE_AMOUNT_COL]
    monthly_tieout = monthly_tieout[
        ["Month", SOURCE_AMOUNT_COL, AMOUNT_COL, "Check"]
    ].rename(
        columns={
            SOURCE_AMOUNT_COL: "Source Signed Total",
            AMOUNT_COL: "Displayed Net Spend",
        }
    )

    st.subheader("Monthly Reconciliation")
    tolerance = st.number_input(
        "Mismatch tolerance ($)",
        min_value=0.0,
        value=0.01,
        step=0.01,
        help="Rows with absolute Check above this value are flagged.",
    )
    mismatch_count = int((monthly_tieout["Check"].abs() > tolerance).sum())
    if mismatch_count > 0:
        st.warning(f"{mismatch_count} month(s) are outside tolerance.")
    else:
        st.success("All months reconcile within tolerance.")

    def _highlight_check(row):
        style = "background-color: #ffe5e5" if abs(row["Check"]) > tolerance else ""
        return ["", "", "", style]

    st.dataframe(
        monthly_tieout.style.format(
            {
                "Source Signed Total": "${:,.2f}",
                "Displayed Net Spend": "${:,.2f}",
                "Check": "${:,.2f}",
            }
        ).apply(_highlight_check, axis=1),
        width="stretch",
        hide_index=True,
    )

    tieout_csv = monthly_tieout.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download monthly reconciliation CSV",
        data=tieout_csv,
        file_name="monthly_reconciliation.csv",
        mime="text/csv",
    )

st.divider()

# ── FOCUSED ANALYTICS TABS ───────────────────────────────────────────────────
area_tab1, area_tab2, area_tab3, area_tab4 = st.tabs([
    "🏛️ Firm Expense Overview",
    "🏢 Department Composition",
    "🤝 Vendor Parent Analytics",
    "🌐 Entity View",
])

with area_tab1:
    st.header("Firm Expense Overview")

    trend_col_main, trend_col_opts = st.columns([3, 1])
    with trend_col_opts:
        trend_group = st.selectbox(
            "Break down trend by:",
            options=["None", "Subsidiary", "Department", "Transaction Type"],
            key="overview_trend_group",
        )
        chart_type = st.radio("Chart type:", ["Line", "Bar"], horizontal=True, key="overview_chart_type")

    group_map = {
        "Subsidiary": "Subsidiary_Name_NetSuite",
        "Department": "Department_Name",
        "Transaction Type": "Transaction_Type_Label",
    }
    trend_df = get_monthly_trend(df, group_by=group_map.get(trend_group))

    with trend_col_main:
        if group_map.get(trend_group):
            fig_trend = px.line(
                trend_df,
                x="Date",
                y=AMOUNT_COL,
                color=group_map.get(trend_group),
                labels={AMOUNT_COL: "Net Spend ($)", "Date": "Month"},
                title="Monthly Net Spend",
            ) if chart_type == "Line" else px.bar(
                trend_df,
                x="Date",
                y=AMOUNT_COL,
                color=group_map.get(trend_group),
                labels={AMOUNT_COL: "Net Spend ($)", "Date": "Month"},
                title="Monthly Net Spend",
            )
        else:
            fig_trend = px.line(
                trend_df,
                x="Date",
                y=AMOUNT_COL,
                labels={AMOUNT_COL: "Net Spend ($)", "Date": "Month"},
                title="Monthly Net Spend",
            ) if chart_type == "Line" else px.bar(
                trend_df,
                x="Date",
                y=AMOUNT_COL,
                labels={AMOUNT_COL: "Net Spend ($)", "Date": "Month"},
                title="Monthly Net Spend",
            )
        fig_trend.update_layout(height=360, legend_title_text="", margin=dict(t=40))
        st.plotly_chart(fig_trend, width="stretch")

    cat_df = get_account_category_breakdown(df, top_n=top_n)
    fig_cat = go.Figure(go.Bar(
        y=cat_df["Category"],
        x=cat_df["Spend"],
        orientation="h",
        marker=dict(color=cat_df["Spend"], colorscale="Blues", reversescale=True),
        text=[format_currency(v) for v in cat_df["Spend"]],
        textposition="auto",
    ))
    fig_cat.update_layout(
        title=f"Top {top_n} High-Level Categories",
        xaxis_title="Net Spend ($)",
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        height=max(360, top_n * 26),
        showlegend=False,
        margin=dict(t=40),
        font=dict(size=12),
    )
    st.plotly_chart(fig_cat, width="stretch")

    st.subheader("Subcategory Drilldown")
    sub_top_n = st.slider("Subcategory bars", min_value=10, max_value=75, value=25, step=5)
    selected_cat = st.selectbox(
        "Select a category to drill into:",
        options=["— All Categories —"] + list(cat_df["Category"]),
        key="overview_subcat_select",
    )
    drill_cat = None if selected_cat == "— All Categories —" else selected_cat
    sub_df = get_account_subcategory_breakdown(df, category=drill_cat, top_n=sub_top_n)
    if len(sub_df):
        sub_labels = sub_df.apply(
            lambda r: r["Subcategory"] if r["Subcategory"] else r["Category"],
            axis=1,
        )
        fig_sub = go.Figure(go.Bar(
            y=sub_labels,
            x=sub_df["Spend"],
            orientation="h",
            marker=dict(color=sub_df["Spend"], colorscale="Teal", reversescale=True),
            text=[format_currency(v) for v in sub_df["Spend"]],
            textposition="auto",
        ))
        fig_sub.update_layout(
            title=f"Subcategories — {selected_cat}",
            xaxis_title="Net Spend ($)",
            yaxis=dict(autorange="reversed", tickfont=dict(size=14)),
            xaxis=dict(tickfont=dict(size=12)),
            height=max(620, sub_top_n * 34),
            showlegend=False,
            margin=dict(t=40),
            font=dict(size=13),
        )
        st.plotly_chart(fig_sub, width="stretch")

        if drill_cat is None:
            scope_total = float(df.groupby(["Account_Category", "Account_Subcategory"])[AMOUNT_COL].sum().sum())
        else:
            scope_total = float(df[df["Account_Category"] == drill_cat].groupby("Account_Subcategory")[AMOUNT_COL].sum().sum())
        displayed_bars_total = float(sub_df["Spend"].sum())
        coverage = (displayed_bars_total / scope_total * 100.0) if scope_total != 0 else 0.0
        st.caption(
            f"Showing top {sub_top_n} bars only. Displayed bars = {format_currency(displayed_bars_total)} "
            f"({coverage:.1f}% of selected scope total {format_currency(scope_total)})."
        )

with area_tab2:
    st.header("Department Composition")
    dept_df = get_department_breakdown(df, top_n=top_n)

    fig_dept = go.Figure(go.Bar(
        y=dept_df["Department"],
        x=dept_df["Spend"],
        orientation="h",
        marker=dict(color=dept_df["Spend"], colorscale="Oranges", reversescale=True),
        text=[format_currency(v) for v in dept_df["Spend"]],
        textposition="auto",
    ))
    fig_dept.update_layout(
        title=f"Top {top_n} Departments by Net Spend",
        xaxis_title="Net Spend ($)",
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        xaxis=dict(tickfont=dict(size=11)),
        height=max(360, top_n * 26),
        showlegend=False,
        margin=dict(t=40),
        font=dict(size=12),
    )
    st.plotly_chart(fig_dept, width="stretch")

    st.subheader("Department Drilldown")
    selected_dept = st.selectbox(
        "Select a department:",
        options=["— Select Department —"] + list(dept_df["Department"]),
        key="dept_focus_select",
    )
    if selected_dept != "— Select Department —":
        col_dept_vendors, col_dept_accounts = st.columns(2)
        with col_dept_vendors:
            dept_vendors_df = get_vendors_by_department(df, selected_dept, top_n=top_n)
            if len(dept_vendors_df) > 0:
                fig_dept_v = go.Figure(go.Bar(
                    y=dept_vendors_df["Vendor"],
                    x=dept_vendors_df["Spend"],
                    orientation="h",
                    marker=dict(color=dept_vendors_df["Spend"], colorscale="Oranges"),
                    text=[format_currency(v) for v in dept_vendors_df["Spend"]],
                    textposition="auto",
                ))
                fig_dept_v.update_layout(
                    title=f"Top Vendors in {selected_dept}",
                    xaxis_title="Net Spend ($)",
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                    height=380,
                    showlegend=False,
                    margin=dict(t=40),
                )
                st.plotly_chart(fig_dept_v, width="stretch")
            else:
                st.info("No vendor data for this department.")

        with col_dept_accounts:
            dept_accounts_df = get_accounts_by_department(df, selected_dept, top_n=top_n)
            if len(dept_accounts_df) > 0:
                fig_dept_a = go.Figure(go.Bar(
                    y=dept_accounts_df["Account Category"],
                    x=dept_accounts_df["Spend"],
                    orientation="h",
                    marker=dict(color=dept_accounts_df["Spend"], colorscale="Reds"),
                    text=[format_currency(v) for v in dept_accounts_df["Spend"]],
                    textposition="auto",
                ))
                fig_dept_a.update_layout(
                    title="Top Account Categories",
                    xaxis_title="Net Spend ($)",
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                    height=380,
                    showlegend=False,
                    margin=dict(t=40),
                )
                st.plotly_chart(fig_dept_a, width="stretch")
            else:
                st.info("No account data for this department.")

with area_tab3:
    st.header("Vendor Parent Analytics")
    no_vendor_count = int(df["Vendor_Name"].isna().sum())
    vp_df = get_vendor_parent_breakdown(df, top_n=top_n)

    if len(vp_df) == 0:
        st.info("No vendor parent data available for current filters.")
    else:
        fig_vp = go.Figure(go.Bar(
            y=vp_df["Vendor Group"],
            x=vp_df["Spend"],
            orientation="h",
            marker=dict(color=vp_df["Spend"], colorscale="Greens", reversescale=True),
            text=[format_currency(v) for v in vp_df["Spend"]],
            textposition="auto",
        ))
        fig_vp.update_layout(
            title=f"Top {top_n} Vendor Parent Groups",
            xaxis_title="Net Spend ($)",
            yaxis=dict(autorange="reversed", tickfont=dict(size=13)),
            xaxis=dict(tickfont=dict(size=11)),
            height=max(420, top_n * 28),
            showlegend=False,
            margin=dict(t=40),
            font=dict(size=12),
        )
        st.plotly_chart(fig_vp, width="stretch")

        vp_table = vp_df.copy()
        vp_total = float(vp_table["Spend"].sum())
        vp_table["Share %"] = (vp_table["Spend"] / vp_total * 100.0).round(1) if vp_total else 0.0
        vp_table["Spend"] = vp_table["Spend"].apply(format_currency)
        st.dataframe(vp_table, width="stretch", hide_index=True)

        selected_vp = st.selectbox(
            "Select a vendor parent group for detail:",
            options=["— Select Group —"] + list(vp_df["Vendor Group"]),
            key="vendor_parent_detail_select",
        )
        if selected_vp != "— Select Group —":
            col_vp_vendors, col_vp_accounts = st.columns(2)

            with col_vp_vendors:
                vp_vendors_df = get_vendors_by_vendor_parent(df, selected_vp, top_n=top_n)
                if len(vp_vendors_df):
                    fig_vp_v = go.Figure(go.Bar(
                        y=vp_vendors_df["Vendor"],
                        x=vp_vendors_df["Spend"],
                        orientation="h",
                        marker=dict(color=vp_vendors_df["Spend"], colorscale="Greens"),
                        text=[format_currency(v) for v in vp_vendors_df["Spend"]],
                        textposition="auto",
                    ))
                    fig_vp_v.update_layout(
                        title=f"Top Vendors in {selected_vp}",
                        xaxis_title="Net Spend ($)",
                        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                        height=390,
                        showlegend=False,
                        margin=dict(t=40),
                    )
                    st.plotly_chart(fig_vp_v, width="stretch")

            with col_vp_accounts:
                vp_accounts_df = get_accounts_by_vendor_parent(df, selected_vp, top_n=top_n)
                if len(vp_accounts_df):
                    fig_vp_a = go.Figure(go.Bar(
                        y=vp_accounts_df["Account Category"],
                        x=vp_accounts_df["Spend"],
                        orientation="h",
                        marker=dict(color=vp_accounts_df["Spend"], colorscale="Blues"),
                        text=[format_currency(v) for v in vp_accounts_df["Spend"]],
                        textposition="auto",
                    ))
                    fig_vp_a.update_layout(
                        title="Top Account Categories Hit",
                        xaxis_title="Net Spend ($)",
                        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                        height=390,
                        showlegend=False,
                        margin=dict(t=40),
                    )
                    st.plotly_chart(fig_vp_a, width="stretch")

    st.caption(
        f"{no_vendor_count:,} rows have no vendor and are excluded from vendor-parent analytics."
    )

with area_tab4:
    st.header("Entity View")
    sub_entity_df = get_subsidiary_breakdown(df)

    col_pie, col_bar = st.columns(2)
    with col_pie:
        fig_pie = px.pie(
            sub_entity_df,
            names="Subsidiary",
            values="Spend",
            title="Net Spend Share by Subsidiary",
            hole=0.35,
        )
        fig_pie.update_traces(textinfo="label+percent")
        fig_pie.update_layout(legend_title_text="", margin=dict(t=40))
        st.plotly_chart(fig_pie, width="stretch")

    with col_bar:
        fig_sub_bar = go.Figure(go.Bar(
            y=sub_entity_df["Subsidiary"],
            x=sub_entity_df["Spend"],
            orientation="h",
            marker=dict(color=sub_entity_df["Spend"], colorscale="Purples", reversescale=True),
            text=[format_currency(v) for v in sub_entity_df["Spend"]],
            textposition="auto",
        ))
        fig_sub_bar.update_layout(
            title="Net Spend by Subsidiary",
            xaxis_title="Net Spend ($)",
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
            height=360,
            showlegend=False,
            margin=dict(t=40),
        )
        st.plotly_chart(fig_sub_bar, width="stretch")

    st.dataframe(
        sub_entity_df.assign(Spend=sub_entity_df["Spend"].apply(format_currency)),
        width="stretch",
        hide_index=True,
    )

st.divider()

# ── TRANSACTION DETAIL TABLE ──────────────────────────────────────────────────
with st.expander("📋 Transaction Detail", expanded=False):
    detail_cols_ordered = [
        "Accounting_Period_Name",
        "Transaction_Type_Label",
        "Subsidiary_Name_NetSuite",
        "Department_Name",
        "Vendor_Name",
        "Account_Category",
        "Account_Subcategory",
        "Account_NetSuite_Name",
        AMOUNT_COL,
        "Transaction_Name",
        "Transaction_Number",
        "Transaction_Memo",
        "Transaction_Date",
        "Subsidiary_Country_Name",
    ]
    display_cols = [c for c in detail_cols_ordered if c in df.columns]

    show_n = st.select_slider(
        "Rows to display",
        options=[100, 500, 1_000, 5_000],
        value=500,
    )
    st.dataframe(
        df[display_cols].head(show_n),
        width='stretch',
        hide_index=True,
    )

    csv_bytes = df[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_expenses.csv",
        mime="text/csv",
    )
