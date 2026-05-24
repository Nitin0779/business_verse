"""
BusinessVerse - Dashboard Page
Main KPI dashboard with charts, trends, and recent transactions.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.chart_helpers import pie_chart, PALETTE

if not is_authenticated():
    show_login_page()
    st.stop()

require_auth()
inject_styles()
render_sidebar()


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
st.markdown('<div class="page-title">📊 Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Overview of key business metrics and performance indicators</div>', unsafe_allow_html=True)

if not data_ok:
    st.warning("⚠️ Sample data not found. Run `python generate_data.py` from the project root first, then refresh.")
    st.stop()

# ── Date Filter ───────────────────────────────────────────────────────────────
active = orders_df[orders_df["status"] != "Cancelled"].copy()
min_d  = active["order_date"].min().date()
max_d  = active["order_date"].max().date()

col_f1, col_f2, _ = st.columns([2, 2, 6])
with col_f1:
    start_date = st.date_input("From", value=min_d, min_value=min_d, max_value=max_d)
with col_f2:
    end_date = st.date_input("To", value=max_d, min_value=min_d, max_value=max_d)

filtered = active[
    (active["order_date"] >= pd.Timestamp(start_date)) &
    (active["order_date"] <= pd.Timestamp(end_date))
].copy()
filtered = filtered.reset_index(drop=True)

st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_revenue   = filtered["total_amount"].sum()
total_orders    = len(filtered)
total_profit    = filtered["profit"].sum()
total_customers = filtered["customer_id"].nunique()
avg_order_val   = filtered["total_amount"].mean() if total_orders else 0
profit_margin   = (total_profit / total_revenue * 100) if total_revenue else 0

kpi_data = [
    ("💰 Total Revenue",    f"${total_revenue:,.0f}",  "+12.4%", True),
    ("📦 Total Orders",     f"{total_orders:,}",        "+8.1%",  True),
    ("👥 Active Customers", f"{total_customers:,}",     "+5.3%",  True),
    ("📈 Net Profit",       f"${total_profit:,.0f}",   "+15.2%", True),
    ("🛒 Avg Order Value",  f"${avg_order_val:,.2f}",  "+2.7%",  True),
    ("📊 Profit Margin",    f"{profit_margin:.1f}%",   "-0.4%",  False),
]

cols = st.columns(6)
for col, (label, value, delta, is_up) in zip(cols, kpi_data):
    delta_class = "" if is_up else "down"
    delta_icon  = "▲" if is_up else "▼"
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta {delta_class}">{delta_icon} {delta} vs last period</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Monthly Revenue + Profit ───────────────────────────────────────────────────
st.markdown('<div class="section-header">Revenue & Profit Trends</div>', unsafe_allow_html=True)

filtered = filtered.copy()
filtered["ym"] = filtered["order_date"].dt.to_period("M").astype(str)
monthly = filtered.groupby("ym").agg(
    revenue=("total_amount", "sum"),
    profit=("profit", "sum"),
    orders=("order_id", "count")
).reset_index().sort_values("ym")

col_chart1, col_chart2 = st.columns([3, 2])

with col_chart1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["ym"], y=monthly["revenue"], name="Revenue",
        mode="lines+markers", line=dict(color="#2563EB", width=2.5), marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.07)"
    ))
    fig.add_trace(go.Scatter(
        x=monthly["ym"], y=monthly["profit"], name="Profit",
        mode="lines+markers", line=dict(color="#10B981", width=2.5), marker=dict(size=5)
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(l=0, r=10, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        hoverlabel=dict(bgcolor="white", bordercolor="#E2E8F0")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_chart2:
    cat_sales = filtered.groupby("category")["total_amount"].sum().reset_index()
    cat_sales.columns = ["Category", "Revenue"]
    fig2 = pie_chart(cat_sales, names="Category", values="Revenue",
                     title="Revenue by Category", height=340)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Top Products + Region Sales ───────────────────────────────────────────────
st.markdown('<div class="section-header">Product & Regional Performance</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)

with col3:
    top_prods = (
        filtered.groupby("product_name")["total_amount"].sum()
        .nlargest(8).reset_index()
        .rename(columns={"product_name": "Product", "total_amount": "Revenue"})
        .sort_values("Revenue")
    )
    fig3 = go.Figure(go.Bar(
        x=top_prods["Revenue"], y=top_prods["Product"], orientation="h",
        marker=dict(color=top_prods["Revenue"],
                    colorscale=[[0, "#DBEAFE"], [1, "#1D4ED8"]], showscale=False),
        text=[f"${v:,.0f}" for v in top_prods["Revenue"]], textposition="outside"
    ))
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(l=0, r=80, t=10, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        font=dict(family="Inter, sans-serif", color="#1E293B")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Top 8 Products by Revenue**")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    region_sales = filtered.groupby("region").agg(
        Revenue=("total_amount", "sum"),
        Orders=("order_id", "count"),
        Profit=("profit", "sum")
    ).reset_index()
    fig4 = px.bar(region_sales, x="region", y="Revenue",
                  color="region", color_discrete_sequence=PALETTE,
                  text=region_sales["Revenue"].apply(lambda x: f"${x:,.0f}"))
    fig4.update_traces(textposition="outside", marker_line_width=0)
    fig4.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=340, margin=dict(l=0, r=10, t=10, b=0), showlegend=False,
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$", title=""),
        font=dict(family="Inter, sans-serif", color="#1E293B")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Revenue by Region**")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Orders by Status + Payment ────────────────────────────────────────────────
st.markdown('<div class="section-header">Orders Overview</div>', unsafe_allow_html=True)
col5, col6 = st.columns(2)

with col5:
    status_df = orders_df.groupby("status").size().reset_index(name="count")
    fig5 = pie_chart(status_df, names="status", values="count",
                     title="Order Status Distribution", height=300, hole=0.5)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col6:
    pay_df = filtered.groupby("payment_method")["total_amount"].sum().reset_index()
    pay_df.columns = ["Method", "Revenue"]
    pay_sorted = pay_df.sort_values("Revenue")
    fig6 = px.bar(pay_sorted, x="Revenue", y="Method", orientation="h",
                  color_discrete_sequence=["#2563EB"],
                  text=pay_sorted["Revenue"].apply(lambda x: f"${x:,.0f}"))
    fig6.update_traces(textposition="outside", marker_line_width=0)
    fig6.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=0, r=80, t=10, b=0), showlegend=False,
        xaxis=dict(showgrid=False, showticklabels=False, title=""),
        yaxis=dict(showgrid=False, title=""),
        font=dict(family="Inter, sans-serif", color="#1E293B")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Revenue by Payment Method**")
    st.plotly_chart(fig6, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Recent Transactions ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Recent Transactions</div>', unsafe_allow_html=True)

recent = (
    orders_df.merge(customers_df[["customer_id", "name"]], on="customer_id", how="left")
    .sort_values("order_date", ascending=False)
    .head(12)[["order_id", "name", "product_name", "category", "region",
               "order_date", "total_amount", "status"]]
    .rename(columns={
        "order_id": "Order ID", "name": "Customer", "product_name": "Product",
        "category": "Category", "region": "Region", "order_date": "Date",
        "total_amount": "Amount", "status": "Status"
    })
)
recent["Amount"] = recent["Amount"].apply(lambda x: f"${x:,.2f}")
recent["Date"]   = pd.to_datetime(recent["Date"]).dt.strftime("%b %d, %Y")

st.dataframe(recent, use_container_width=True, hide_index=True)
