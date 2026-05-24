"""
BusinessVerse - Shared CSS Styles & Sidebar
Call inject_styles() and render_sidebar() at the top of every page.
"""

import streamlit as st


def inject_styles():
    st.markdown("""
<style>
/* Hide Streamlit's auto-generated pages nav in sidebar */
[data-testid="stSidebarNav"] { display: none !important; }

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.stApp { background-color: #F8FAFC !important; }

[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}

.main .block-container {
    padding-top: 24px !important;
    padding-left: 28px !important;
    padding-right: 28px !important;
    max-width: 1400px !important;
}

.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s ease;
}
.kpi-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.07); }
.kpi-card .kpi-label {
    font-size: 0.78rem; font-weight: 600; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;
}
.kpi-card .kpi-value {
    font-size: 1.9rem; font-weight: 700; color: #1E293B;
    line-height: 1; margin-bottom: 8px;
}
.kpi-card .kpi-delta { font-size: 0.8rem; font-weight: 500; color: #10B981; }
.kpi-card .kpi-delta.down { color: #EF4444; }

.section-header {
    font-size: 1.05rem; font-weight: 700; color: #1E293B;
    margin-bottom: 14px; padding-bottom: 8px;
    border-bottom: 2px solid #E2E8F0;
}

.chart-card {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 10px; padding: 20px; margin-bottom: 16px;
}

.page-title {
    font-size: 1.5rem; font-weight: 800; color: #0F172A; margin-bottom: 4px;
}
.page-subtitle {
    font-size: 0.88rem; color: #64748B; margin-bottom: 24px;
}

.stButton > button {
    border-radius: 8px !important; font-weight: 500 !important;
    font-size: 0.88rem !important; border: none !important;
    padding: 0.5rem 1.2rem !important; transition: all 0.15s ease !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important; overflow: hidden !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #F1F5F9; padding: 4px; border-radius: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px; font-size: 0.86rem; font-weight: 500;
    color: #64748B; padding: 6px 18px;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important; color: #1E293B !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.7rem !important; font-weight: 700 !important; color: #1E293B !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important; font-weight: 600 !important;
    color: #64748B !important; text-transform: uppercase; letter-spacing: 0.05em;
}

.divider { height: 1px; background: #E2E8F0; margin: 20px 0; }

.badge { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.72rem; font-weight: 600; }
.badge-blue   { background: #DBEAFE; color: #1D4ED8; }
.badge-green  { background: #D1FAE5; color: #059669; }
.badge-red    { background: #FEE2E2; color: #DC2626; }
.badge-yellow { background: #FEF9C3; color: #B45309; }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
    """Render the standard sidebar navigation. Call once per page."""
    from utils.auth import is_authenticated, logout

    with st.sidebar:
        st.markdown("""
        <div style="padding:16px 0 20px 0;">
            <div style="font-size:1.3rem;font-weight:800;color:#2563EB;letter-spacing:-0.5px;">
                📊 BusinessVerse
            </div>
            <div style="font-size:0.75rem;color:#94A3B8;margin-top:2px;">Analytics Platform</div>
        </div>""", unsafe_allow_html=True)

        if is_authenticated():
            user = st.session_state.get("username", "User")
            role = st.session_state.get("role", "Viewer")
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                        padding:10px 14px;margin-bottom:20px;font-size:0.82rem;">
                <div style="font-weight:600;color:#1E293B;">👤 {user.title()}</div>
                <div style="color:#64748B;">{role}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown("**Navigation**")
            st.page_link("pages/Home.py",            label="🏠 Dashboard")
            st.page_link("pages/Data_Upload.py",     label="📤 Data Upload")
            st.page_link("pages/Data_Cleaning.py",   label="🧹 Data Cleaning")
            st.page_link("pages/SQL_Database.py",    label="🗄️ SQL Database")
            st.page_link("pages/Analytics.py",       label="📈 Analytics")
            st.page_link("pages/ML_Predictions.py",  label="🤖 ML Predictions")
            st.page_link("pages/Reports.py",         label="📄 Reports")
            st.markdown("---")
            if st.button("🚪 Sign Out", use_container_width=True, key="signout_btn"):
                logout()
