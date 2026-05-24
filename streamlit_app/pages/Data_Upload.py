"""
BusinessVerse - Data Upload Page
Upload CSV files, preview data, and view dataset statistics.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.data_processing import get_dataframe_stats, get_missing_value_report, safe_load_csv

if not is_authenticated():
    show_login_page()
    st.stop()

require_auth()
inject_styles()
render_sidebar()

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📤 Data Upload</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Upload your business data files for analysis</div>', unsafe_allow_html=True)

# ── Upload Section ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Upload Dataset</div>', unsafe_allow_html=True)

col_up, col_info = st.columns([3, 2])

with col_up:
    uploaded_file = st.file_uploader(
        "Drop a CSV file here or click to browse",
        type=["csv"],
        help="Supported: CSV files up to 200MB"
    )

with col_info:
    st.markdown("""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:18px 22px;">
        <div style="font-weight:600;color:#1E293B;margin-bottom:10px;">📋 Upload Guidelines</div>
        <ul style="font-size:0.84rem;color:#64748B;margin:0;padding-left:18px;line-height:2;">
            <li>File format: <b>CSV</b></li>
            <li>Max size: <b>200 MB</b></li>
            <li>First row should be <b>column headers</b></li>
            <li>Date columns should be in <b>YYYY-MM-DD</b> format</li>
            <li>Numeric columns should <b>not contain commas</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ── Load sample datasets button ───────────────────────────────────────────────
st.markdown("---")
st.markdown("**Or load a built-in sample dataset:**")
col_s1, col_s2, col_s3, _ = st.columns([1,1,1,3])

with col_s1:
    load_orders = st.button("📦 Load Orders", use_container_width=True)
with col_s2:
    load_customers = st.button("👥 Load Customers", use_container_width=True)
with col_s3:
    load_products = st.button("🛍️ Load Products", use_container_width=True)

# ── Determine which data to display ───────────────────────────────────────────
base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
df = None
source_name = ""

if uploaded_file:
    df = safe_load_csv(uploaded_file)
    source_name = uploaded_file.name
    if df is not None:
        st.session_state["uploaded_df"]   = df
        st.session_state["uploaded_name"] = source_name
        st.success(f"✅ File uploaded: **{source_name}**")

elif load_orders:
    path = os.path.join(base, "orders.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        source_name = "orders.csv"
        st.session_state["uploaded_df"]   = df
        st.session_state["uploaded_name"] = source_name
    else:
        st.warning("Sample data not found. Run `python generate_data.py` first.")

elif load_customers:
    path = os.path.join(base, "customers.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        source_name = "customers.csv"
        st.session_state["uploaded_df"]   = df
        st.session_state["uploaded_name"] = source_name
    else:
        st.warning("Sample data not found. Run `python generate_data.py` first.")

elif load_products:
    path = os.path.join(base, "products.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        source_name = "products.csv"
        st.session_state["uploaded_df"]   = df
        st.session_state["uploaded_name"] = source_name
    else:
        st.warning("Sample data not found. Run `python generate_data.py` first.")

elif "uploaded_df" in st.session_state:
    df = st.session_state["uploaded_df"]
    source_name = st.session_state.get("uploaded_name", "Dataset")

# ── Display Data ──────────────────────────────────────────────────────────────
if df is not None:
    stats = get_dataframe_stats(df)
    
    # Stats row
    st.markdown("---")
    st.markdown(f'<div class="section-header">Dataset Overview — {source_name}</div>', unsafe_allow_html=True)
    
    s1, s2, s3, s4, s5 = st.columns(5)
    stat_items = [
        ("📏 Rows",        f"{stats['rows']:,}"),
        ("📋 Columns",     f"{stats['columns']}"),
        ("❓ Missing",     f"{stats['missing']:,}"),
        ("🔁 Duplicates",  f"{stats['duplicates']:,}"),
        ("💾 Memory",      f"{stats['memory_kb']:,} KB"),
    ]
    for col, (label, val) in zip([s1,s2,s3,s4,s5], stat_items):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="padding:14px 18px;">
                <div class="kpi-label">{label}</div>
                <div style="font-size:1.5rem;font-weight:700;color:#1E293B;">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Preview", "📊 Statistics", "❓ Missing Values", "🔤 Column Info"])

    with tab1:
        n_rows = st.slider("Rows to preview", 5, min(200, len(df)), 20)
        st.dataframe(df.head(n_rows), use_container_width=True)

    with tab2:
        num_df = df.select_dtypes(include=[np.number])
        if not num_df.empty:
            desc = num_df.describe().T.reset_index()
            desc.columns = ["Column", "Count", "Mean", "Std", "Min", "25%", "50%", "75%", "Max"]
            desc = desc.round(3)
            st.dataframe(desc, use_container_width=True, hide_index=True)
        else:
            st.info("No numeric columns found for statistics.")

    with tab3:
        missing_report = get_missing_value_report(df)
        if missing_report.empty:
            st.success("✅ No missing values found in this dataset!")
        else:
            st.warning(f"⚠️ Found missing values in **{len(missing_report)}** column(s).")
            st.dataframe(missing_report, use_container_width=True, hide_index=True)

    with tab4:
        col_info_df = pd.DataFrame({
            "Column":    df.columns,
            "Dtype":     df.dtypes.astype(str).values,
            "Non-Null":  df.notnull().sum().values,
            "Null":      df.isnull().sum().values,
            "Unique":    df.nunique().values,
            "Sample":    [str(df[c].dropna().iloc[0]) if df[c].notna().any() else "—" for c in df.columns]
        })
        st.dataframe(col_info_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info("💡 Head to **🧹 Data Cleaning** to clean and prepare this dataset for analysis.")

else:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#F8FAFC;border:2px dashed #E2E8F0;
                border-radius:12px;color:#94A3B8;">
        <div style="font-size:2.5rem;margin-bottom:12px;">📂</div>
        <div style="font-size:1rem;font-weight:600;color:#64748B;">No dataset loaded</div>
        <div style="font-size:0.85rem;margin-top:6px;">Upload a CSV file or load a sample dataset above</div>
    </div>
    """, unsafe_allow_html=True)
