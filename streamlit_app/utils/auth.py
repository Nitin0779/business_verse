"""
BusinessVerse - Authentication Module
Simple session-based login system for the dashboard.
"""

import streamlit as st
import hashlib

# ─── User Store (extend with DB-backed auth in production) ────────────────────
USERS = {
    "admin":   hashlib.sha256("admin123".encode()).hexdigest(),
    "analyst": hashlib.sha256("analyst123".encode()).hexdigest(),
    "viewer":  hashlib.sha256("viewer123".encode()).hexdigest(),
}

USER_ROLES = {
    "admin":   "Administrator",
    "analyst": "Business Analyst",
    "viewer":  "Viewer",
}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str) -> bool:
    """Verify credentials and set session state."""
    hashed = hash_password(password)
    if username in USERS and USERS[username] == hashed:
        st.session_state["authenticated"] = True
        st.session_state["username"]      = username
        st.session_state["role"]          = USER_ROLES.get(username, "Viewer")
        return True
    return False


def logout():
    """Clear all session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def require_auth():
    """Call at top of each page to enforce login."""
    if not is_authenticated():
        st.warning("🔒 Please log in to access this page.")
        st.stop()


def show_login_page():
    """Render the login page."""
    st.markdown("""
    <style>
    .login-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 80px;
    }
    .login-logo {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2563EB;
        letter-spacing: -0.5px;
        margin-bottom: 6px;
    }
    .login-tagline {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 32px;
    }
    .login-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 40px 48px;
        max-width: 420px;
        width: 100%;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown('<div class="login-logo">📊 BusinessVerse</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-tagline">Business Analytics Platform</div>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown("#### Sign In")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit   = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif authenticate(username, password):
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        

