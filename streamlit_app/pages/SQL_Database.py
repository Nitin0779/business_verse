"""
BusinessVerse - SQL Database Page
Connect to SQLite/MySQL/PostgreSQL, run queries, view analytics.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.db_connector import (
    get_engine, init_database, load_csv_to_db,
    query_monthly_revenue, query_top_products, query_region_sales,
    query_category_performance, query_customer_summary, query_kpis, query_recent_orders
)
from utils.chart_helpers import bar_chart, line_chart, pie_chart, PALETTE
import plotly.express as px

if not is_authenticated():
    show_login_page()
    st.stop()

require_auth()
inject_styles()
render_sidebar()

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🗄️ SQL Database</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Connect, load, and query your business database</div>', unsafe_allow_html=True)

# ── Connection + Load ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Database Connection</div>', unsafe_allow_html=True)

col_conn, col_status = st.columns([3, 2])

with col_conn:
    st.markdown("""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:18px 22px;">
        <div style="font-size:0.9rem;font-weight:600;color:#1E293B;margin-bottom:12px;">Connection Settings</div>
    """, unsafe_allow_html=True)
    
    db_type = st.selectbox("Database Type", ["SQLite (local)", "MySQL", "PostgreSQL"])
    
    if "SQLite" not in db_type:
        c1, c2 = st.columns(2)
        with c1: host = st.text_input("Host", "localhost")
        with c2: port = st.text_input("Port", "3306" if "MySQL" in db_type else "5432")
        c3, c4 = st.columns(2)
        with c3: db_name = st.text_input("Database", "businessverse")
        with c4: db_user = st.text_input("Username", "root")
        db_pass = st.text_input("Password", type="password")
        
        os.environ["DB_TYPE"]     = "mysql" if "MySQL" in db_type else "postgresql"
        os.environ["DB_HOST"]     = host
        os.environ["DB_PORT"]     = port
        os.environ["DB_NAME"]     = db_name
        os.environ["DB_USER"]     = db_user
        os.environ["DB_PASSWORD"] = db_pass
    else:
        os.environ["DB_TYPE"] = "sqlite"
        st.info("Using local SQLite database at `data/businessverse.db`")
    
    st.markdown("</div>", unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:18px 22px;height:100%;">
        <div style="font-size:0.9rem;font-weight:600;color:#1E293B;margin-bottom:12px;">Quick Actions</div>
    """, unsafe_allow_html=True)
    
    if st.button("🔌 Test Connection", use_container_width=True):
        try:
            engine = get_engine()
            init_database(engine)
            st.success("✅ Connected successfully!")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
    
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    
    if st.button("📥 Load Sample Data to DB", use_container_width=True, type="primary"):
        try:
            c_path = os.path.join(base, "customers.csv")
            p_path = os.path.join(base, "products.csv")
            o_path = os.path.join(base, "orders.csv")
            if not all(os.path.exists(p) for p in [c_path, p_path, o_path]):
                st.error("Sample CSV files not found. Run `python generate_data.py` first.")
            else:
                engine = get_engine()
                init_database(engine)
                nc, np_, no = load_csv_to_db(engine, c_path, p_path, o_path)
                st.success(f"✅ Loaded: {nc} customers, {np_} products, {no} orders")
                st.session_state["db_loaded"] = True
        except Exception as e:
            st.error(f"❌ Load failed: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ── SQL Analytics ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">SQL Analytics Queries</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 KPIs", "📅 Monthly Revenue", "🏆 Top Products",
    "🗺️ Region Sales", "📂 Categories", "🔍 Custom Query"
])

@st.cache_data(ttl=120, show_spinner=False)
def cached_kpis():
    return query_kpis(get_engine())

@st.cache_data(ttl=120, show_spinner=False)
def cached_monthly():
    return query_monthly_revenue(get_engine())

@st.cache_data(ttl=120, show_spinner=False)
def cached_products(limit=10):
    return query_top_products(get_engine(), limit)

@st.cache_data(ttl=120, show_spinner=False)
def cached_region():
    return query_region_sales(get_engine())

@st.cache_data(ttl=120, show_spinner=False)
def cached_category():
    return query_category_performance(get_engine())


def try_load(fn, *args, **kwargs):
    """Attempt to run a DB query; show helpful error on failure."""
    try:
        engine = get_engine()
        init_database(engine)
        return fn(*args, **kwargs)
    except Exception as e:
        st.error(f"Query failed: {e}. Make sure data is loaded first.")
        return None


# ── Tab 1: KPIs ───────────────────────────────────────────────────────────────
with tab1:
    if st.button("▶ Run KPI Query", key="run_kpi"):
        result = try_load(query_kpis, get_engine())
        if result is not None:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Revenue",    f"${result['total_revenue']:,.2f}")
            c2.metric("Total Orders",     f"{int(result['total_orders']):,}")
            c3.metric("Total Profit",     f"${result['total_profit']:,.2f}")
            c4.metric("Avg Order Value",  f"${result['avg_order_value']:,.2f}")
    
    with st.expander("📄 View SQL Query"):
        st.code("""SELECT
    ROUND(SUM(total_amount), 2) AS total_revenue,
    COUNT(*)                    AS total_orders,
    ROUND(SUM(profit), 2)       AS total_profit,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE status != 'Cancelled'""", language="sql")

# ── Tab 2: Monthly Revenue ────────────────────────────────────────────────────
with tab2:
    if st.button("▶ Run Monthly Revenue Query", key="run_monthly"):
        df_m = try_load(query_monthly_revenue, get_engine())
        if df_m is not None:
            st.dataframe(df_m, use_container_width=True, hide_index=True)
            fig = line_chart(df_m, x="month", y="revenue", title="Monthly Revenue Trend")
            st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📄 View SQL Query"):
        st.code("""SELECT
    SUBSTR(order_date, 1, 7) AS month,
    SUM(total_amount)        AS revenue,
    SUM(profit)              AS profit,
    COUNT(*)                 AS order_count
FROM orders
WHERE status != 'Cancelled'
GROUP BY SUBSTR(order_date, 1, 7)
ORDER BY month""", language="sql")

# ── Tab 3: Top Products ───────────────────────────────────────────────────────
with tab3:
    n_top = st.slider("Number of products", 5, 20, 10, key="top_n")
    if st.button("▶ Run Top Products Query", key="run_products"):
        df_p = try_load(query_top_products, get_engine(), n_top)
        if df_p is not None:
            st.dataframe(df_p, use_container_width=True, hide_index=True)
            fig = bar_chart(
                df_p.sort_values("revenue"), x="revenue", y="product_name",
                title=f"Top {n_top} Products by Revenue", orientation="h"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📄 View SQL Query"):
        st.code("""SELECT
    product_name,
    category,
    COUNT(order_id)     AS total_orders,
    SUM(quantity)       AS units_sold,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(SUM(profit), 2)       AS profit
FROM orders
WHERE status != 'Cancelled'
GROUP BY product_name, category
ORDER BY revenue DESC
LIMIT 10""", language="sql")

# ── Tab 4: Region Sales ───────────────────────────────────────────────────────
with tab4:
    if st.button("▶ Run Region Sales Query", key="run_region"):
        df_r = try_load(query_region_sales, get_engine())
        if df_r is not None:
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            fig = px.bar(df_r, x="region", y=["revenue","profit"],
                         barmode="group", color_discrete_sequence=PALETTE[:2])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              height=380, font=dict(family="Inter, sans-serif"))
            st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📄 View SQL Query"):
        st.code("""SELECT
    region,
    COUNT(*)                    AS total_orders,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(SUM(profit), 2)       AS profit,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE status != 'Cancelled'
GROUP BY region
ORDER BY revenue DESC""", language="sql")

# ── Tab 5: Categories ─────────────────────────────────────────────────────────
with tab5:
    if st.button("▶ Run Category Query", key="run_category"):
        df_c = try_load(query_category_performance, get_engine())
        if df_c is not None:
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            fig = pie_chart(df_c, names="category", values="revenue",
                            title="Revenue by Category")
            st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📄 View SQL Query"):
        st.code("""SELECT
    category,
    COUNT(*)                    AS total_orders,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(SUM(profit), 2)       AS profit,
    SUM(quantity)               AS units_sold
FROM orders
WHERE status != 'Cancelled'
GROUP BY category
ORDER BY revenue DESC""", language="sql")

# ── Tab 6: Custom Query ───────────────────────────────────────────────────────
with tab6:
    st.markdown("**Write and run your own SQL query:**")
    custom_sql = st.text_area(
        "SQL Query",
        value="SELECT category, COUNT(*) as orders, ROUND(SUM(total_amount),2) as revenue\nFROM orders\nGROUP BY category\nORDER BY revenue DESC",
        height=130
    )
    
    if st.button("▶ Run Query", key="run_custom", type="primary"):
        try:
            from sqlalchemy import text as sqlt
            engine = get_engine()
            init_database(engine)
            result_df = pd.read_sql(sqlt(custom_sql), engine)
            st.success(f"✅ Query returned **{len(result_df)}** rows.")
            st.dataframe(result_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"❌ Query error: {e}")
