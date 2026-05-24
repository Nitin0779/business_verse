"""
BusinessVerse - Main Application Entry Point
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.auth import is_authenticated, show_login_page
from utils.styles import inject_styles

st.set_page_config(
    page_title="BusinessVerse — Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "BusinessVerse v1.0 — Professional Business Analytics Platform"}
)

inject_styles()

if not is_authenticated():
    show_login_page()
else:
    st.switch_page("pages/Home.py")
