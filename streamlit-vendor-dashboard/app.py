"""
Streamlit vendor spend analytics dashboard.
Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Tuple
from data_loader import (
    load_and_transform_data,
    get_quarters_range,
    quarter_to_index,
    index_to_quarter,
    format_currency,
)
from analytics import (
    filter_data,
    get_kpis,
    get_top_vendors,
    get_trends,
    get_pareto,
    get_anomalies,
    get_yoy_change,
)

# ── PAGE CONFIG ──────────────────────────────────────────────────────────
st.set_page_config(page_title="Vendor Spend Analytics", layout="wide")
st.title("📊 Vendor Spend Analytics Dashboard")

# ── LOAD DATA ────────────────────────────────────────────────────────────
try:
    df_raw = load_and_transform_data()
except FileNotFoundError as e:
    st.error(f"❌ {e}")
    st.info("Please ensure `vendor_spend.xlsx` exists in the app directory.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# ── SIDEBAR FILTERS ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Filters")

    # Date range slider
    min_y, min_q, max_y, max_q = get_quarters_range(df_raw)
    min_idx = quarter_to_index(min_y, min_q)
    max_idx = quarter_to_index(max_y, max_q)

    selected_range = st.slider(
        "📅 Quarter Range",
        min_value=min_idx,
        max_value=max_idx,
        value=(min_idx, max_idx),
        step=1,
    )
    selected_min_y, selected_min_q = index_to_quarter(selected_range[0])
    selected_max_y, selected_max_q = index_to_quarter(selected_range[1])

    # Vendor multiselect
    all_vendors = sorted(df_raw["Vendor"].unique())
    selected_vendors = st.multiselect(
        "🏢 Vendors",
        all_vendors,
        default=all_vendors,
    )

    # Include projections toggle
    include_projected = st.checkbox("🔮 Include Projections", value=True)

    # Top-N selector
    top_n = st.slider("🔝 Top N Vendors", min_value=5, max_value=50, value=10, step=1)

    # Anomaly detection toggle
    show_anomalies = st.checkbox("🚨 Show Anomalies", value=True)

# ── APPLY FILTERS ────────────────────────────────────────────────────────
df_filtered = filter_data(
    df_raw,
    vendors=selected_vendors if selected_vendors else None,
    year_q_range=(selected_min_y, selected_min_q, selected_max_y, selected_max_q),
    include_projected=include_projected,
)

if len(df_filtered) == 0:
    st.warning("⚠️ No data matches your filter selections. Try adjusting filters.")
    st.stop()

# ── KPI ROW ──────────────────────────────────────────────────────────────
st.header("📈 Key Metrics")
kpis = get_kpis(df_filtered)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Spend",
        format_currency(kpis["total_spend"]),
        delta=f"{kpis['delta_total']:.1f}%" if kpis["delta_total"] else None,
    )

with col2:
    st.metric("Active Vendors", kpis["vendor_count"])

with col3:
    st.metric(
        "Avg Quarterly Spend",
        format_currency(kpis["avg_quarterly"]),
    )

with col4:
    top_vendor_text = f"{kpis['top_vendor']} ({format_currency(kpis['top_vendor_spend'])})"
    st.metric("Top Vendor", top_vendor_text if kpis["top_vendor"] else "N/A")

# ── TOP VENDORS ──────────────────────────────────────────────────────────
st.header("🏆 Top Vendors")

col_rank, col_top_n = st.columns([3, 1])
with col_rank:
    rank_by = st.radio(
        "Rank by:",
        options=["total_spend", "avg_quarterly", "growth"],
        format_func=lambda x: {
            "total_spend": "Total Spend",
            "avg_quarterly": "Avg Quarterly Spend",
            "growth": "Growth Rate (Latest vs Earliest)",
        }[x],
        horizontal=True,
    )

top_vendors_df = get_top_vendors(df_filtered, top_n, rank_by=rank_by)

fig_top = go.Figure()
fig_top.add_trace(go.Bar(
    y=top_vendors_df["Vendor"],
    x=top_vendors_df["Value"],
    orientation="h",
    marker=dict(color=top_vendors_df["Value"], colorscale="Viridis"),
))
fig_top.update_layout(
    title=f"Top {top_n} Vendors by {rank_by.replace('_', ' ').title()}",
    xaxis_title="Spend ($)" if rank_by == "total_spend" else ("Growth (%)" if rank_by == "growth" else "Avg Spend ($)"),
    yaxis_title="Vendor",
    height=400,
    showlegend=False,
)
st.plotly_chart(fig_top, use_container_width=True)

# ── TRENDS ──────────────────────────────────────────────────────────────
st.header("📉 Spend Trends")

trends_df = get_trends(df_filtered, selected_vendors if selected_vendors else None)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trends_df["Quarter"],
    y=trends_df["TotalSpend"],
    mode="lines+markers",
    name="Total Spend",
    line=dict(
        color="#636EFA",
        width=3,
        dash="solid"
    ),
    marker=dict(size=6),
))

# Shade projected quarters
if not trends_df[trends_df["IsProjected"]].empty:
    proj_start_idx = trends_df[trends_df["IsProjected"]].index.min()
    fig_trend.add_vrect(
        x0=trends_df.iloc[proj_start_idx]["Quarter"],
        x1=trends_df.iloc[-1]["Quarter"],
        annotation_text="Projected",
        annotation_position="top left",
        fillcolor="#FF6692",
        opacity=0.1,
        line_width=0,
    )

fig_trend.update_layout(
    title="Quarterly Spend Trend",
    xaxis_title="Quarter",
    yaxis_title="Spend ($)",
    height=400,
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── YoY Change ──────────────────────────────────────────────────────────
yoy_df = get_yoy_change(df_filtered)

if not yoy_df.empty:
    fig_yoy = go.Figure()
    colors = ["green" if x >= 0 else "red" for x in yoy_df["YoYChange"]]
    fig_yoy.add_trace(go.Bar(
        x=yoy_df["Quarter"],
        y=yoy_df["YoYChange"],
        marker=dict(color=colors),
        name="YoY %"
    ))
    fig_yoy.update_layout(
        title="Year-over-Year % Change by Quarter",
        xaxis_title="Quarter",
        yaxis_title="YoY Change (%)",
        height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_yoy, use_container_width=True)

# ── PARETO ──────────────────────────────────────────────────────────────
st.header("⚖️ Spend Concentration (Pareto)")

pareto_df, vendors_at_80 = get_pareto(df_filtered)

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(
    x=pareto_df["Vendor"],
    y=pareto_df["Spend"],
    name="Vendor Spend",
    yaxis="y",
))
fig_pareto.add_trace(go.Scatter(
    x=pareto_df["Vendor"],
    y=pareto_df["CumulativePct"],
    name="Cumulative %",
    yaxis="y2",
    line=dict(color="red", width=3),
))

# Add 80% threshold line
fig_pareto.add_hline(
    y=80,
    line_dash="dash",
    line_color="orange",
    annotation_text=f"80% Threshold ({vendors_at_80} vendors)",
    annotation_position="right",
    yref="y2",
)

fig_pareto.update_layout(
    title="Pareto Analysis: Spend Concentration",
    xaxis_title="Vendor (sorted by spend)",
    yaxis_title="Vendor Spend ($)",
    yaxis2=dict(title="Cumulative %", overlaying="y", side="right"),
    height=450,
)
st.plotly_chart(fig_pareto, use_container_width=True)

# ── ANOMALIES ────────────────────────────────────────────────────────────
if show_anomalies:
    st.header("🚨 Anomaly Detection")

    anomalies_df = get_anomalies(df_filtered, z_threshold=2.0)

    if not anomalies_df.empty:
        col_sort, col_filter = st.columns([2, 2])
        with col_sort:
            sort_by = st.selectbox(
                "Sort by:",
                options=["ZScore", "Spend", "Vendor"],
                index=0,
            )

        anomalies_df_sorted = anomalies_df.sort_values(sort_by, ascending=False)

        # Table
        st.subheader("Anomalous Quarter-Vendor Combinations")
        st.dataframe(
            anomalies_df_sorted[[
                "Vendor", "Quarter", "Spend", "Expected", "ZScore", "Direction"
            ]].style.format({
                "Spend": lambda x: format_currency(x),
                "Expected": lambda x: format_currency(x),
            }),
            use_container_width=True,
        )

        # Scatter plot
        fig_anomaly = go.Figure()
        colors_map = {"High": "red", "Low": "blue"}
        for direction in ["High", "Low"]:
            subset = anomalies_df[anomalies_df["Direction"] == direction]
            fig_anomaly.add_trace(go.Scatter(
                x=subset["Quarter"],
                y=subset["ZScore"],
                mode="markers",
                name=direction,
                marker=dict(size=10, color=colors_map[direction]),
            ))

        fig_anomaly.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Z=2")
        fig_anomaly.add_hline(y=-2, line_dash="dash", line_color="blue", annotation_text="Z=-2")

        fig_anomaly.update_layout(
            title="Anomaly Z-Scores Over Time",
            xaxis_title="Quarter",
            yaxis_title="Z-Score",
            height=400,
        )
        st.plotly_chart(fig_anomaly, use_container_width=True)

    else:
        st.info("✅ No anomalies detected in the selected date range.")

# ── FOOTER ───────────────────────────────────────────────────────────────
st.divider()
st.caption("💡 Tip: Projections are shown with dashed lines and a shaded background. Toggle in the sidebar.")
