"""
BusinessVerse - Analytics Page
Interactive business analysis with date, region, and category filters.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.chart_helpers import line_chart, bar_chart, pie_chart, scatter_chart, PALETTE, COLORS

if not is_authenticated():
    show_login_page()
    st.stop()

require_auth()
inject_styles()
render_sidebar()

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    orders    = pd.read_csv(os.path.join(base, "orders.csv"))
    customers = pd.read_csv(os.path.join(base, "customers.csv"))
    products  = pd.read_csv(os.path.join(base, "products.csv"))
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    return orders, customers, products

try:
    orders_df, customers_df, products_df = load_data()
    data_ok = True
except FileNotFoundError:
    data_ok = False

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📈 Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Deep-dive into sales, customers, products, and time series</div>', unsafe_allow_html=True)

if not data_ok:
    st.warning("⚠️ Sample data not found. Run `python generate_data.py` from the project root first.")
    st.stop()

# ── Global Filters ─────────────────────────────────────────────────────────────
with st.expander("🔽 Filters", expanded=True):
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    
    active = orders_df[orders_df["status"] != "Cancelled"].copy()
    min_d  = active["order_date"].min().date()
    max_d  = active["order_date"].max().date()
    
    with fcol1:
        start_date = st.date_input("From Date", value=min_d, min_value=min_d, max_value=max_d)
    with fcol2:
        end_date   = st.date_input("To Date",   value=max_d, min_value=min_d, max_value=max_d)
    with fcol3:
        all_regions = ["All"] + sorted(active["region"].unique().tolist())
        region_filter = st.selectbox("Region", all_regions)
    with fcol4:
        all_cats = ["All"] + sorted(active["category"].unique().tolist())
        cat_filter = st.selectbox("Category", all_cats)

# Apply filters
filtered = active[
    (active["order_date"] >= pd.Timestamp(start_date)) &
    (active["order_date"] <= pd.Timestamp(end_date))
].copy().reset_index(drop=True)

if region_filter != "All":
    filtered = filtered[filtered["region"] == region_filter]
if cat_filter != "All":
    filtered = filtered[filtered["category"] == cat_filter]

st.markdown(f"**Showing {len(filtered):,} orders** | Revenue: **${filtered['total_amount'].sum():,.0f}** | Profit: **${filtered['profit'].sum():,.0f}**")
st.markdown("---")

# ── Analysis Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Sales Trends", "💰 Profit Analysis",
    "👥 Customer Analysis", "🛍️ Product Analysis", "📆 Time Series"
])

# ── Tab 1: Sales Trends ───────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Sales Trends</div>', unsafe_allow_html=True)
    
    filtered2 = filtered.copy()
    filtered2["ym"] = filtered2["order_date"].dt.to_period("M").astype(str)
    monthly = filtered2.groupby("ym").agg(
        revenue=("total_amount","sum"),
        orders=("order_id","count"),
        profit=("profit","sum")
    ).reset_index()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=monthly["ym"], y=monthly["revenue"],
                                name="Revenue", marker_color="#DBEAFE", marker_line_width=0))
    fig_trend.add_trace(go.Scatter(x=monthly["ym"], y=monthly["revenue"],
                                    name="Trend", mode="lines+markers",
                                    line=dict(color="#2563EB", width=2.5),
                                    marker=dict(size=5)))
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=380, margin=dict(l=0, r=10, t=10, b=0),
        legend=dict(orientation="h", y=1.02, x=0),
        xaxis=dict(showgrid=False, tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        barmode="overlay"
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Monthly Revenue Trend**")
    st.plotly_chart(fig_trend, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        weekly = filtered.copy()
        weekly["week"] = weekly["order_date"].dt.isocalendar().week.astype(str) + "-" + weekly["order_date"].dt.year.astype(str)
        weekly_agg = weekly.groupby("order_date")["total_amount"].sum().reset_index()
        weekly_agg.columns = ["Date", "Revenue"]
        fig_w = px.line(weekly_agg, x="Date", y="Revenue",
                        color_discrete_sequence=["#0EA5E9"])
        fig_w.update_traces(line=dict(width=1.8))
        fig_w.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             height=300, margin=dict(l=0,r=0,t=10,b=0),
                             font=dict(family="Inter, sans-serif"),
                             xaxis=dict(showgrid=False),
                             yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"))
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("**Daily Revenue**")
        st.plotly_chart(fig_w, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_t2:
        dow = filtered.copy()
        dow["day_name"] = dow["order_date"].dt.day_name()
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow_agg = dow.groupby("day_name")["total_amount"].mean().reindex(day_order).reset_index()
        dow_agg.columns = ["Day", "Avg Revenue"]
        fig_dow = px.bar(dow_agg, x="Day", y="Avg Revenue",
                         color_discrete_sequence=["#2563EB"])
        fig_dow.update_traces(marker_line_width=0)
        fig_dow.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               height=300, margin=dict(l=0,r=0,t=10,b=0),
                               font=dict(family="Inter, sans-serif"),
                               xaxis=dict(showgrid=False),
                               yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"))
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("**Avg Revenue by Day of Week**")
        st.plotly_chart(fig_dow, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 2: Profit Analysis ────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Profit Analysis</div>', unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        cat_profit = filtered.groupby("category").agg(
            Revenue=("total_amount","sum"), Profit=("profit","sum")
        ).reset_index()
        cat_profit["Margin %"] = (cat_profit["Profit"] / cat_profit["Revenue"] * 100).round(1)
        
        fig_pm = go.Figure()
        fig_pm.add_trace(go.Bar(x=cat_profit["category"], y=cat_profit["Revenue"],
                                 name="Revenue", marker_color="#DBEAFE", marker_line_width=0))
        fig_pm.add_trace(go.Bar(x=cat_profit["category"], y=cat_profit["Profit"],
                                 name="Profit",  marker_color="#2563EB", marker_line_width=0))
        fig_pm.update_layout(
            barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=340, margin=dict(l=0,r=0,t=10,b=0),
            legend=dict(orientation="h", y=1.02, x=0),
            xaxis=dict(showgrid=False, tickangle=-20),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
            font=dict(family="Inter, sans-serif")
        )
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("**Revenue vs Profit by Category**")
        st.plotly_chart(fig_pm, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_p2:
        fig_margin = px.bar(cat_profit.sort_values("Margin %"),
                            x="Margin %", y="category", orientation="h",
                            color="Margin %",
                            color_continuous_scale=["#DBEAFE", "#1D4ED8"],
                            text=cat_profit.sort_values("Margin %")["Margin %"].apply(lambda x: f"{x:.1f}%"))
        fig_margin.update_traces(textposition="outside", marker_line_width=0)
        fig_margin.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=340, margin=dict(l=0,r=80,t=10,b=0),
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showgrid=False, showticklabels=False, title=""),
            yaxis=dict(showgrid=False, title=""),
            font=dict(family="Inter, sans-serif")
        )
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("**Profit Margin % by Category**")
        st.plotly_chart(fig_margin, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Profit scatter
    prod_scatter = filtered.groupby("product_name").agg(
        Revenue=("total_amount","sum"), Profit=("profit","sum"), Orders=("order_id","count")
    ).reset_index()
    prod_scatter["Margin"] = (prod_scatter["Profit"] / prod_scatter["Revenue"] * 100).round(1)
    
    fig_sc = px.scatter(prod_scatter, x="Revenue", y="Profit",
                        size="Orders", color="Margin",
                        hover_name="product_name",
                        color_continuous_scale="Blues",
                        size_max=30, opacity=0.8)
    fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          height=380, font=dict(family="Inter, sans-serif"),
                          xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
                          yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"))
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Revenue vs Profit by Product** (bubble = order count, color = margin %)")
    st.plotly_chart(fig_sc, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 3: Customer Analysis ───────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">Customer Analysis</div>', unsafe_allow_html=True)
    
    cust_orders = filtered.merge(customers_df[["customer_id","name","age","region","churn"]],
                                  on="customer_id", how="left")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        region_cust = cust_orders.groupby("region_x")["customer_id"].nunique().reset_index()
        region_cust.columns = ["Region", "Customers"]
        fig_rc = pie_chart(region_cust, names="Region", values="Customers",
                           title="Customers by Region", height=320)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_rc, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_c2:
        top_custs = cust_orders.groupby(["customer_id","name"])["total_amount"].sum().nlargest(10).reset_index()
        top_custs.columns = ["ID","Customer","Revenue"]
        fig_tc = go.Figure(go.Bar(
            x=top_custs["Revenue"], y=top_custs["Customer"],
            orientation="h", marker_color="#2563EB", marker_line_width=0,
            text=[f"${v:,.0f}" for v in top_custs["Revenue"]], textposition="outside"
        ))
        fig_tc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=320, margin=dict(l=0,r=80,t=10,b=0),
                              xaxis=dict(showgrid=False,showticklabels=False),
                              yaxis=dict(showgrid=False),
                              font=dict(family="Inter, sans-serif"))
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("**Top 10 Customers by Revenue**")
        st.plotly_chart(fig_tc, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Customer spend distribution
    cust_spend = cust_orders.groupby("customer_id")["total_amount"].sum().reset_index()
    fig_hist = px.histogram(cust_spend, x="total_amount", nbins=40,
                             color_discrete_sequence=["#2563EB"])
    fig_hist.update_traces(marker_line_width=0)
    fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            height=300, margin=dict(l=0,r=0,t=10,b=0),
                            xaxis=dict(showgrid=False, tickprefix="$", title="Total Spend"),
                            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="# Customers"),
                            font=dict(family="Inter, sans-serif"))
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Customer Spend Distribution**")
    st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 4: Product Analysis ───────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">Product Analysis</div>', unsafe_allow_html=True)
    
    col_pr1, col_pr2 = st.columns(2)
    
    with col_pr1:
        units = filtered.groupby("category")["quantity"].sum().reset_index()
        units.columns = ["Category", "Units Sold"]
        fig_units = pie_chart(units, names="Category", values="Units Sold",
                              title="Units Sold by Category", height=340)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_units, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_pr2:
        prod_rev = filtered.groupby("product_name")["total_amount"].sum().nlargest(10).reset_index()
        prod_rev.columns = ["Product","Revenue"]
        prod_rev = prod_rev.sort_values("Revenue")
        fig_pr = go.Figure(go.Bar(
            x=prod_rev["Revenue"], y=prod_rev["Product"],
            orientation="h",
            marker=dict(color=prod_rev["Revenue"], colorscale=[[0,"#DBEAFE"],[1,"#1D4ED8"]], showscale=False),
            text=[f"${v:,.0f}" for v in prod_rev["Revenue"]], textposition="outside"
        ))
        fig_pr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=340, margin=dict(l=0,r=80,t=10,b=0),
                              xaxis=dict(showgrid=False, showticklabels=False),
                              yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                              font=dict(family="Inter, sans-serif"))
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("**Top 10 Products by Revenue**")
        st.plotly_chart(fig_pr, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Category trend over time
    cat_monthly = filtered.copy()
    cat_monthly["ym"] = cat_monthly["order_date"].dt.to_period("M").astype(str)
    cat_trend = cat_monthly.groupby(["ym","category"])["total_amount"].sum().reset_index()
    
    fig_ct = px.line(cat_trend, x="ym", y="total_amount", color="category",
                     color_discrete_sequence=PALETTE)
    fig_ct.update_traces(line=dict(width=2))
    fig_ct.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          height=360, margin=dict(l=0,r=0,t=10,b=0),
                          legend=dict(orientation="h", y=1.02, x=0),
                          xaxis=dict(showgrid=False, tickangle=-45),
                          yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
                          font=dict(family="Inter, sans-serif"))
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Category Revenue Trend Over Time**")
    st.plotly_chart(fig_ct, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 5: Time Series ────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">Time Series Analysis</div>', unsafe_allow_html=True)
    
    granularity = st.radio("Granularity", ["Daily", "Weekly", "Monthly", "Quarterly"],
                           horizontal=True)
    
    ts = filtered.set_index("order_date")["total_amount"]
    
    if granularity == "Daily":
        ts_agg = ts.resample("D").sum().reset_index()
    elif granularity == "Weekly":
        ts_agg = ts.resample("W").sum().reset_index()
    elif granularity == "Monthly":
        ts_agg = ts.resample("ME").sum().reset_index()
    else:
        ts_agg = ts.resample("QE").sum().reset_index()
    
    ts_agg.columns = ["Date", "Revenue"]
    ts_agg["Rolling 7"] = ts_agg["Revenue"].rolling(min(7, len(ts_agg))).mean()
    
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Bar(x=ts_agg["Date"], y=ts_agg["Revenue"],
                             name="Revenue", marker_color="#DBEAFE", marker_line_width=0, opacity=0.8))
    fig_ts.add_trace(go.Scatter(x=ts_agg["Date"], y=ts_agg["Rolling 7"],
                                 name="Rolling Avg", mode="lines",
                                 line=dict(color="#2563EB", width=2.5)))
    fig_ts.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=400, margin=dict(l=0,r=10,t=10,b=0),
        legend=dict(orientation="h", y=1.02, x=0),
        xaxis=dict(showgrid=False, rangeslider=dict(visible=True, thickness=0.06)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
        font=dict(family="Inter, sans-serif")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(f"**{granularity} Revenue with Rolling Average**")
    st.plotly_chart(fig_ts, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # QoQ comparison
    ts_filtered = filtered.copy()
    ts_filtered["year"]    = ts_filtered["order_date"].dt.year.astype(str)
    ts_filtered["quarter"] = ts_filtered["order_date"].dt.quarter
    qoq = ts_filtered.groupby(["year","quarter"])["total_amount"].sum().reset_index()
    qoq["Period"] = qoq["year"] + " Q" + qoq["quarter"].astype(str)
    
    fig_qoq = px.bar(qoq, x="Period", y="total_amount",
                     color="year", color_discrete_sequence=PALETTE,
                     text=qoq["total_amount"].apply(lambda x: f"${x/1000:.0f}K"))
    fig_qoq.update_traces(textposition="outside", marker_line_width=0)
    fig_qoq.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(l=0,r=0,t=10,b=0),
        barmode="group",
        legend=dict(orientation="h", y=1.02, x=0, title="Year"),
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$", title="Revenue"),
        font=dict(family="Inter, sans-serif")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Quarterly Revenue Comparison**")
    st.plotly_chart(fig_qoq, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
