"""
BusinessVerse - Data Cleaning Page
Remove nulls, fill missing values, remove duplicates, convert types, select features.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import io

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.data_processing import (
    get_dataframe_stats, get_missing_value_report,
    clean_remove_nulls, clean_fill_nulls, clean_remove_duplicates,
    convert_column_types
)

if not is_authenticated():
    show_login_page()
    st.stop()

require_auth()
inject_styles()
render_sidebar()

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🧹 Data Cleaning</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Clean and prepare your dataset for analysis</div>', unsafe_allow_html=True)

# ── Check for data ─────────────────────────────────────────────────────────────
if "uploaded_df" not in st.session_state:
    st.warning("⚠️ No dataset loaded. Please go to **📤 Data Upload** first.")
    st.stop()

# Working copy
if "clean_df" not in st.session_state:
    st.session_state["clean_df"] = st.session_state["uploaded_df"].copy()

df_orig  = st.session_state["uploaded_df"]
df_clean = st.session_state["clean_df"]

# ── Before/After Stats ────────────────────────────────────────────────────────
orig_stats  = get_dataframe_stats(df_orig)
clean_stats = get_dataframe_stats(df_clean)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:16px 20px;">
    <div style="font-weight:700;color:#64748B;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">
    ORIGINAL DATASET</div>""", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Rows",       f"{orig_stats['rows']:,}")
    c2.metric("Columns",    str(orig_stats['columns']))
    c3.metric("Missing",    f"{orig_stats['missing']:,}")
    c4.metric("Duplicates", f"{orig_stats['duplicates']:,}")
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown("""<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:16px 20px;">
    <div style="font-weight:700;color:#059669;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">
    CLEANED DATASET</div>""", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    row_delta = clean_stats['rows'] - orig_stats['rows']
    col_delta = clean_stats['columns'] - orig_stats['columns']
    mis_delta = clean_stats['missing'] - orig_stats['missing']
    dup_delta = clean_stats['duplicates'] - orig_stats['duplicates']
    c1.metric("Rows",       f"{clean_stats['rows']:,}",       delta=str(row_delta))
    c2.metric("Columns",    str(clean_stats['columns']),      delta=str(col_delta))
    c3.metric("Missing",    f"{clean_stats['missing']:,}",    delta=str(mis_delta))
    c4.metric("Duplicates", f"{clean_stats['duplicates']:,}", delta=str(dup_delta))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Cleaning Operations ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Cleaning Operations</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "❓ Handle Missing", "🔁 Duplicates", "🔄 Type Conversion",
    "✂️ Feature Selection", "👁️ Preview"
])

# ── Tab 1: Missing Values ─────────────────────────────────────────────────────
with tab1:
    missing_report = get_missing_value_report(df_clean)
    if missing_report.empty:
        st.success("✅ No missing values in the current dataset.")
    else:
        st.markdown(f"**{len(missing_report)} column(s) have missing values:**")
        st.dataframe(missing_report, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("**Drop rows with missing values**")
        if st.button("🗑️ Drop All Null Rows", use_container_width=True):
            cleaned, dropped = clean_remove_nulls(df_clean)
            st.session_state["clean_df"] = cleaned
            st.success(f"Removed **{dropped}** rows with null values.")
            st.rerun()
    
    with col_m2:
        st.markdown("**Fill missing values with:**")
        strategy = st.selectbox("Strategy", ["mean", "median", "mode", "zero"],
                                format_func=lambda x: x.title())
        if st.button("🔧 Fill Missing Values", use_container_width=True):
            filled = clean_fill_nulls(df_clean, strategy=strategy)
            st.session_state["clean_df"] = filled
            st.success(f"Filled missing values using **{strategy}** strategy.")
            st.rerun()

# ── Tab 2: Duplicates ─────────────────────────────────────────────────────────
with tab2:
    dup_count = df_clean.duplicated().sum()
    if dup_count == 0:
        st.success("✅ No duplicate rows found.")
    else:
        st.warning(f"⚠️ Found **{dup_count}** duplicate rows.")
        st.dataframe(df_clean[df_clean.duplicated()].head(10), use_container_width=True)
    
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1:
        if st.button("🗑️ Remove Duplicates", use_container_width=True, disabled=(dup_count == 0)):
            cleaned, removed = clean_remove_duplicates(df_clean)
            st.session_state["clean_df"] = cleaned
            st.success(f"Removed **{removed}** duplicate rows.")
            st.rerun()

# ── Tab 3: Type Conversion ────────────────────────────────────────────────────
with tab3:
    st.markdown("Select columns to convert their data types:")
    
    col_list = df_clean.columns.tolist()
    selected_col  = st.selectbox("Column", col_list)
    current_dtype = str(df_clean[selected_col].dtype)
    st.markdown(f"Current type: `{current_dtype}`")
    
    new_type = st.selectbox("Convert to", ["numeric", "datetime", "str", "int", "float"])
    
    if st.button("🔄 Convert Column Type"):
        result, errors = convert_column_types(df_clean, {selected_col: new_type})
        if errors:
            st.error(f"Conversion error: {errors}")
        else:
            st.session_state["clean_df"] = result
            st.success(f"Converted **{selected_col}** to `{new_type}`.")
            st.rerun()

# ── Tab 4: Feature Selection ──────────────────────────────────────────────────
with tab4:
    st.markdown("Select the columns to **keep** in your dataset:")
    all_cols = df_clean.columns.tolist()
    selected_cols = st.multiselect("Columns to keep", all_cols, default=all_cols)
    
    if st.button("✂️ Apply Feature Selection"):
        if len(selected_cols) < 1:
            st.error("Please select at least one column.")
        else:
            st.session_state["clean_df"] = df_clean[selected_cols].copy()
            st.success(f"Dataset reduced to **{len(selected_cols)}** columns.")
            st.rerun()

# ── Tab 5: Preview ────────────────────────────────────────────────────────────
with tab5:
    st.dataframe(df_clean.head(30), use_container_width=True)

# ── Actions Row ───────────────────────────────────────────────────────────────
st.markdown("---")
col_act1, col_act2, col_act3, col_act4 = st.columns([2,2,2,4])

with col_act1:
    if st.button("🔄 Reset to Original", use_container_width=True):
        st.session_state["clean_df"] = st.session_state["uploaded_df"].copy()
        st.success("Dataset reset to original.")
        st.rerun()

with col_act2:
    if st.button("✅ Use for Analysis", use_container_width=True, type="primary"):
        st.session_state["analysis_df"] = st.session_state["clean_df"].copy()
        st.success("✅ Cleaned dataset saved for analysis!")

with col_act3:
    csv_buf = io.StringIO()
    df_clean.to_csv(csv_buf, index=False)
    st.download_button(
        "⬇️ Download Clean CSV",
        data=csv_buf.getvalue(),
        file_name="businessverse_cleaned.csv",
        mime="text/csv",
        use_container_width=True
    )
