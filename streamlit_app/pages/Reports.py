"""
BusinessVerse - Reports Page
Download cleaned data, analytics reports, and export charts.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.chart_helpers import (
    line_chart, bar_chart, pie_chart, PALETTE
)
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

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
st.markdown('<div class="page-title">📄 Reports & Exports</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Download data, analytics reports, and chart exports</div>', unsafe_allow_html=True)

if not data_ok:
    st.warning("⚠️ Sample data not found. Run `python generate_data.py` first.")
    st.stop()

active = orders_df[orders_df["status"] != "Cancelled"].copy()

# ── Report Configuration ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">Report Configuration</div>', unsafe_allow_html=True)

col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    report_period = st.selectbox("Report Period", [
        "All Time", "Last 30 Days", "Last 90 Days", "Last 6 Months",
        "Last 12 Months", "Year 2022", "Year 2023", "Year 2024"
    ])
with col_cfg2:
    report_region = st.selectbox("Region", ["All Regions"] + sorted(active["region"].unique().tolist()))
with col_cfg3:
    report_cat = st.selectbox("Category", ["All Categories"] + sorted(active["category"].unique().tolist()))

# Apply period filter
today = active["order_date"].max()
if report_period == "Last 30 Days":
    rep_df = active[active["order_date"] >= today - pd.Timedelta(days=30)]
elif report_period == "Last 90 Days":
    rep_df = active[active["order_date"] >= today - pd.Timedelta(days=90)]
elif report_period == "Last 6 Months":
    rep_df = active[active["order_date"] >= today - pd.Timedelta(days=182)]
elif report_period == "Last 12 Months":
    rep_df = active[active["order_date"] >= today - pd.Timedelta(days=365)]
elif report_period == "Year 2022":
    rep_df = active[active["order_date"].dt.year == 2022]
elif report_period == "Year 2023":
    rep_df = active[active["order_date"].dt.year == 2023]
elif report_period == "Year 2024":
    rep_df = active[active["order_date"].dt.year == 2024]
else:
    rep_df = active.copy()

if report_region != "All Regions":
    rep_df = rep_df[rep_df["region"] == report_region]
if report_cat != "All Categories":
    rep_df = rep_df[rep_df["category"] == report_cat]

# ── Report Summary ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f'<div class="section-header">Report Summary — {report_period}</div>', unsafe_allow_html=True)

total_rev  = rep_df["total_amount"].sum()
total_prof = rep_df["profit"].sum()
total_ord  = len(rep_df)
total_cust = rep_df["customer_id"].nunique()
avg_ord    = rep_df["total_amount"].mean() if total_ord > 0 else 0.0
margin     = (total_prof / total_rev * 100) if total_rev > 0 else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)
metrics = [
    ("Total Revenue",    f"${total_rev:,.0f}"),
    ("Total Profit",     f"${total_prof:,.0f}"),
    ("Total Orders",     f"{total_ord:,}"),
    ("Customers",        f"{total_cust:,}"),
    ("Avg Order Value",  f"${avg_ord:,.2f}"),
    ("Profit Margin",    f"{margin:.1f}%"),
]
for col, (label, val) in zip([k1,k2,k3,k4,k5,k6], metrics):
    with col:
        st.markdown(f"""<div class="kpi-card" style="padding:14px 18px;">
            <div class="kpi-label">{label}</div>
            <div style="font-size:1.3rem;font-weight:700;color:#1E293B;">{val}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick Charts for Report Preview ──────────────────────────────────────────
col_rc1, col_rc2 = st.columns(2)

with col_rc1:
    rep_monthly = rep_df.copy()
    rep_monthly["ym"] = rep_monthly["order_date"].dt.to_period("M").astype(str)
    monthly_agg = rep_monthly.groupby("ym").agg(
        revenue=("total_amount","sum"),
        profit=("profit","sum")
    ).reset_index()
    
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(x=monthly_agg["ym"], y=monthly_agg["revenue"],
                              name="Revenue", marker_color="#DBEAFE", marker_line_width=0))
    fig_rev.add_trace(go.Scatter(x=monthly_agg["ym"], y=monthly_agg["revenue"],
                                  name="Trend", line=dict(color="#2563EB", width=2),
                                  mode="lines+markers", marker=dict(size=4)))
    fig_rev.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h", y=1.02, x=0),
        xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
        font=dict(family="Inter, sans-serif")
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("**Monthly Revenue**")
    st.plotly_chart(fig_rev, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_rc2:
    cat_agg = rep_df.groupby("category")["total_amount"].sum().reset_index()
    cat_agg.columns = ["Category","Revenue"]
    fig_cat = pie_chart(cat_agg, names="Category", values="Revenue",
                        title="Revenue by Category", height=300)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig_cat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Download Section ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📥 Downloads</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Orders Data", "👥 Customers Data",
    "🛍️ Products Data", "📈 Analytics Report"
])

# ── Tab 1: Orders Download ────────────────────────────────────────────────────
with tab1:
    st.markdown(f"**{len(rep_df):,} orders** ready for download based on your filters.")
    
    col_o1, col_o2 = st.columns([3,1])
    with col_o1:
        st.dataframe(rep_df.head(10), use_container_width=True, hide_index=True)
        st.caption(f"Showing 10 of {len(rep_df):,} rows")
    
    with col_o2:
        # CSV
        csv_buf = io.StringIO()
        rep_df.to_csv(csv_buf, index=False)
        st.download_button(
            "⬇️ Download Orders CSV",
            data=csv_buf.getvalue(),
            file_name=f"businessverse_orders_{report_period.replace(' ','_').lower()}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        
        # Excel
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
            rep_df.to_excel(writer, sheet_name="Orders", index=False)
        st.download_button(
            "⬇️ Download Orders Excel",
            data=excel_buf.getvalue(),
            file_name=f"businessverse_orders_{report_period.replace(' ','_').lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ── Tab 2: Customers Download ─────────────────────────────────────────────────
with tab2:
    st.markdown(f"**{len(customers_df):,} customers** in the database.")
    
    col_c1, col_c2 = st.columns([3,1])
    with col_c1:
        st.dataframe(customers_df.head(10), use_container_width=True, hide_index=True)
        st.caption(f"Showing 10 of {len(customers_df):,} rows")
    
    with col_c2:
        csv_c = io.StringIO()
        customers_df.to_csv(csv_c, index=False)
        st.download_button(
            "⬇️ Download Customers CSV",
            data=csv_c.getvalue(),
            file_name="businessverse_customers.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        
        excel_c = io.BytesIO()
        with pd.ExcelWriter(excel_c, engine="xlsxwriter") as writer:
            customers_df.to_excel(writer, sheet_name="Customers", index=False)
        st.download_button(
            "⬇️ Download Customers Excel",
            data=excel_c.getvalue(),
            file_name="businessverse_customers.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ── Tab 3: Products Download ──────────────────────────────────────────────────
with tab3:
    st.markdown(f"**{len(products_df):,} products** in the catalogue.")
    
    col_p1, col_p2 = st.columns([3,1])
    with col_p1:
        st.dataframe(products_df, use_container_width=True, hide_index=True)
    
    with col_p2:
        csv_p = io.StringIO()
        products_df.to_csv(csv_p, index=False)
        st.download_button(
            "⬇️ Download Products CSV",
            data=csv_p.getvalue(),
            file_name="businessverse_products.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        
        excel_p = io.BytesIO()
        with pd.ExcelWriter(excel_p, engine="xlsxwriter") as writer:
            products_df.to_excel(writer, sheet_name="Products", index=False)
        st.download_button(
            "⬇️ Download Products Excel",
            data=excel_p.getvalue(),
            file_name="businessverse_products.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ── Tab 4: Analytics Report ───────────────────────────────────────────────────
with tab4:
    st.markdown("Generate a comprehensive analytics summary report.")
    
    if st.button("📊 Generate Analytics Report", type="primary", use_container_width=False):
        # Build summary DataFrames
        monthly_sum = rep_df.copy()
        monthly_sum["ym"] = monthly_sum["order_date"].dt.to_period("M").astype(str)
        monthly_report = monthly_sum.groupby("ym").agg(
            Revenue=("total_amount","sum"),
            Profit=("profit","sum"),
            Orders=("order_id","count"),
            Avg_Order_Value=("total_amount","mean")
        ).reset_index().rename(columns={"ym":"Month"}).round(2)
        
        region_report = rep_df.groupby("region").agg(
            Revenue=("total_amount","sum"),
            Profit=("profit","sum"),
            Orders=("order_id","count")
        ).reset_index().rename(columns={"region":"Region"}).round(2)
        
        category_report = rep_df.groupby("category").agg(
            Revenue=("total_amount","sum"),
            Profit=("profit","sum"),
            Units=("quantity","sum")
        ).reset_index().rename(columns={"category":"Category"}).round(2)
        
        top_products_report = (
            rep_df.groupby("product_name")["total_amount"].sum()
            .nlargest(20).reset_index()
            .rename(columns={"product_name":"Product","total_amount":"Revenue"})
            .round(2)
        )
        
        kpi_report = pd.DataFrame([{
            "Metric": "Total Revenue",        "Value": f"${total_rev:,.2f}"
        }, {
            "Metric": "Total Profit",         "Value": f"${total_prof:,.2f}"
        }, {
            "Metric": "Profit Margin",        "Value": f"{margin:.2f}%"
        }, {
            "Metric": "Total Orders",         "Value": f"{total_ord:,}"
        }, {
            "Metric": "Unique Customers",     "Value": f"{total_cust:,}"
        }, {
            "Metric": "Avg Order Value",      "Value": f"${avg_ord:,.2f}"
        }, {
            "Metric": "Report Period",        "Value": report_period
        }, {
            "Metric": "Report Region",        "Value": report_region
        }, {
            "Metric": "Report Category",      "Value": report_cat
        }, {
            "Metric": "Generated At",         "Value": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        
        # Write Excel with multiple sheets
        excel_report = io.BytesIO()
        with pd.ExcelWriter(excel_report, engine="xlsxwriter") as writer:
            kpi_report.to_excel(writer,            sheet_name="KPI Summary",    index=False)
            monthly_report.to_excel(writer,        sheet_name="Monthly Revenue", index=False)
            region_report.to_excel(writer,         sheet_name="Region Sales",    index=False)
            category_report.to_excel(writer,       sheet_name="Category Perf",  index=False)
            top_products_report.to_excel(writer,   sheet_name="Top Products",   index=False)
        
        fname = f"businessverse_report_{report_period.replace(' ','_').lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        st.download_button(
            "⬇️ Download Full Analytics Report (Excel)",
            data=excel_report.getvalue(),
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
        # Also offer JSON
        report_dict = {
            "meta": {
                "period": report_period, "region": report_region,
                "category": report_cat, "generated_at": datetime.now().isoformat()
            },
            "kpis": {
                "total_revenue": round(total_rev, 2),
                "total_profit": round(total_prof, 2),
                "profit_margin_pct": round(margin, 2),
                "total_orders": total_ord,
                "unique_customers": total_cust,
                "avg_order_value": round(avg_ord, 2)
            },
            "monthly_revenue": monthly_report.to_dict(orient="records"),
            "region_sales":    region_report.to_dict(orient="records"),
            "category_perf":   category_report.to_dict(orient="records"),
        }
        
        st.download_button(
            "⬇️ Download Report as JSON",
            data=json.dumps(report_dict, indent=2),
            file_name=f"businessverse_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        st.success("✅ Report generated! Click the download buttons above.")
        
        # Preview
        st.markdown("**Report Preview:**")
        st.dataframe(kpi_report, use_container_width=True, hide_index=True)
    
    # Upload cleaned data export
    st.markdown("---")
    st.markdown("**Export Cleaned Dataset (from Data Cleaning page):**")
    if "clean_df" in st.session_state:
        cdf = st.session_state["clean_df"]
        buf = io.StringIO()
        cdf.to_csv(buf, index=False)
        st.download_button(
            "⬇️ Download Cleaned Dataset CSV",
            data=buf.getvalue(),
            file_name="businessverse_cleaned_data.csv",
            mime="text/csv"
        )
    else:
        st.info("No cleaned dataset available. Go to **🧹 Data Cleaning** first.")
