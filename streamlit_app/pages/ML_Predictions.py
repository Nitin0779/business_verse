"""
BusinessVerse - ML Predictions Page
Sales Prediction (Linear Regression), Churn Prediction (Random Forest),
Customer Segmentation (K-Means).
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model    import LinearRegression
from sklearn.ensemble        import RandomForestClassifier
from sklearn.cluster         import KMeans
from sklearn.preprocessing   import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics         import (
    mean_absolute_error, r2_score,
    accuracy_score, classification_report, confusion_matrix
)

from utils.auth import require_auth, is_authenticated, show_login_page
from utils.styles import inject_styles, render_sidebar
from utils.chart_helpers import line_chart, PALETTE, COLORS

if not is_authenticated():
    show_login_page()
    st.stop()

require_auth()
inject_styles()
render_sidebar()

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    orders    = pd.read_csv(os.path.join(base, "orders.csv"))
    customers = pd.read_csv(os.path.join(base, "customers.csv"))
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    return orders, customers

try:
    orders_df, customers_df = load_data()
    data_ok = True
except FileNotFoundError:
    data_ok = False

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🤖 ML Predictions</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Machine learning models for sales forecasting, churn prediction, and customer segmentation</div>', unsafe_allow_html=True)

if not data_ok:
    st.warning("⚠️ Sample data not found. Run `python generate_data.py` first.")
    st.stop()

tab1, tab2, tab3 = st.tabs([
    "📈 Sales Prediction",
    "⚠️ Churn Prediction",
    "🎯 Customer Segmentation"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SALES PREDICTION (Linear Regression)
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Sales Prediction — Linear Regression</div>', unsafe_allow_html=True)
    
    col_info, col_train = st.columns([3, 2])
    
    with col_info:
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:18px 22px;">
            <div style="font-weight:600;color:#1E293B;margin-bottom:8px;">Model Overview</div>
            <ul style="font-size:0.84rem;color:#64748B;margin:0;padding-left:18px;line-height:2;">
                <li><b>Algorithm:</b> Linear Regression</li>
                <li><b>Target:</b> Monthly Revenue</li>
                <li><b>Features:</b> Month, Quarter, Year, Lag variables</li>
                <li><b>Output:</b> Predicted future monthly revenue</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_train:
        forecast_months = st.slider("Months to forecast", 1, 12, 6)
        train_btn = st.button("🚀 Train & Forecast", type="primary", use_container_width=True, key="train_sales")
    
    if train_btn:
        with st.spinner("Training model..."):
            # Prepare monthly data
            active = orders_df[orders_df["status"] != "Cancelled"].copy()
            active["ym"] = active["order_date"].dt.to_period("M")
            monthly = active.groupby("ym")["total_amount"].sum().reset_index()
            monthly.columns = ["period", "revenue"]
            monthly["month_num"] = range(len(monthly))
            monthly["month"]     = monthly["period"].dt.month
            monthly["quarter"]   = monthly["period"].dt.quarter
            monthly["year"]      = monthly["period"].dt.year
            
            # Lag features
            monthly["lag_1"]  = monthly["revenue"].shift(1)
            monthly["lag_2"]  = monthly["revenue"].shift(2)
            monthly["lag_3"]  = monthly["revenue"].shift(3)
            monthly = monthly.dropna()
            
            X = monthly[["month_num","month","quarter","year","lag_1","lag_2","lag_3"]]
            y = monthly["revenue"]
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Metrics
            mae = mean_absolute_error(y_test, y_pred)
            r2  = r2_score(y_test, y_pred)
            
            # Save model
            joblib.dump(model, os.path.join(MODELS_DIR, "sales_model.pkl"))
            
            # Forecast future
            last_row    = monthly.iloc[-1]
            last_num    = last_row["month_num"]
            last_period = last_row["period"]
            last_rev    = monthly["revenue"].values
            
            future_rows = []
            lag_window  = list(last_rev[-3:])
            
            for i in range(1, forecast_months + 1):
                next_period  = last_period + i
                next_month   = next_period.month
                next_quarter = (next_month - 1) // 3 + 1
                next_year    = next_period.year
                next_num     = last_num + i
                
                row = [next_num, next_month, next_quarter, next_year,
                       lag_window[-1], lag_window[-2], lag_window[-3]]
                pred = model.predict([row])[0]
                lag_window.append(pred)
                future_rows.append({
                    "period":  str(next_period),
                    "revenue": pred,
                    "type":    "Forecast"
                })
            
            # Plot: historical + forecast
            hist_plot = monthly[["period","revenue"]].copy()
            hist_plot["period"] = hist_plot["period"].astype(str)
            hist_plot["type"]   = "Historical"
            
            combined = pd.concat([hist_plot, pd.DataFrame(future_rows)], ignore_index=True)
            
            fig = go.Figure()
            hist = combined[combined["type"] == "Historical"]
            fore = combined[combined["type"] == "Forecast"]
            
            fig.add_trace(go.Scatter(
                x=hist["period"], y=hist["revenue"], name="Historical",
                mode="lines+markers", line=dict(color="#2563EB", width=2.5), marker=dict(size=5)
            ))
            fig.add_trace(go.Scatter(
                x=fore["period"], y=fore["revenue"], name="Forecast",
                mode="lines+markers", line=dict(color="#F59E0B", width=2.5, dash="dash"),
                marker=dict(size=7, symbol="diamond"), fill="tozeroy",
                fillcolor="rgba(245,158,11,0.08)"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=400, margin=dict(l=0,r=10,t=10,b=0),
                legend=dict(orientation="h", y=1.02, x=0),
                xaxis=dict(showgrid=False, tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
                font=dict(family="Inter, sans-serif")
            )
            
            # Metrics display
            m1, m2, m3 = st.columns(3)
            m1.metric("R² Score",    f"{r2:.3f}")
            m2.metric("MAE",         f"${mae:,.0f}")
            m3.metric("Model Saved", "✅ sales_model.pkl")
            
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown(f"**Historical Revenue + {forecast_months}-Month Forecast**")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show forecast table
            st.markdown("**Forecast Values:**")
            fore_display = fore.copy()
            fore_display["revenue"] = fore_display["revenue"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(fore_display[["period","revenue"]].rename(
                columns={"period":"Month","revenue":"Predicted Revenue"}
            ), use_container_width=True, hide_index=True)
    
    # Load existing model
    model_path = os.path.join(MODELS_DIR, "sales_model.pkl")
    if os.path.exists(model_path) and not train_btn:
        st.info("✅ A trained sales model exists. Click **Train & Forecast** to retrain and forecast.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: CHURN PREDICTION (Random Forest)
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Customer Churn Prediction — Random Forest</div>', unsafe_allow_html=True)
    
    col_ov, col_params = st.columns([3, 2])
    
    with col_ov:
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:18px 22px;">
            <div style="font-weight:600;color:#1E293B;margin-bottom:8px;">Model Overview</div>
            <ul style="font-size:0.84rem;color:#64748B;margin:0;padding-left:18px;line-height:2;">
                <li><b>Algorithm:</b> Random Forest Classifier</li>
                <li><b>Target:</b> Customer Churn (0 = Retained, 1 = Churned)</li>
                <li><b>Features:</b> Purchase frequency, avg spend, days since purchase, support tickets, satisfaction</li>
                <li><b>Output:</b> Churn probability per customer</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_params:
        n_estimators = st.slider("Number of trees", 50, 300, 100, step=50)
        churn_btn = st.button("🚀 Train Churn Model", type="primary", use_container_width=True, key="train_churn")
    
    if churn_btn:
        with st.spinner("Training Random Forest..."):
            feat_cols = ["purchase_frequency","avg_order_value","last_purchase_days_ago",
                         "support_tickets","satisfaction_score","total_spent"]
            
            df_churn = customers_df[feat_cols + ["churn"]].dropna()
            X = df_churn[feat_cols]
            y = df_churn["churn"]
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
            
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s  = scaler.transform(X_test)
            
            rf = RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1)
            rf.fit(X_train_s, y_train)
            y_pred = rf.predict(X_test_s)
            y_prob = rf.predict_proba(X_test_s)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            cm  = confusion_matrix(y_test, y_pred)
            
            joblib.dump(rf,     os.path.join(MODELS_DIR, "churn_model.pkl"))
            joblib.dump(scaler, os.path.join(MODELS_DIR, "churn_scaler.pkl"))
            
            # Metrics
            churn_rate = y.mean()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Accuracy",    f"{acc:.1%}")
            m2.metric("Churn Rate",  f"{churn_rate:.1%}")
            m3.metric("Train Size",  f"{len(X_train):,}")
            m4.metric("Model Saved", "✅ churn_model.pkl")
            
            col_cm, col_fi = st.columns(2)
            
            with col_cm:
                # Confusion matrix heatmap
                fig_cm = px.imshow(
                    cm, text_auto=True,
                    labels=dict(x="Predicted", y="Actual"),
                    x=["Retained","Churned"], y=["Retained","Churned"],
                    color_continuous_scale=[[0,"#EFF6FF"],[1,"#1D4ED8"]]
                )
                fig_cm.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=300,
                                      font=dict(family="Inter, sans-serif"),
                                      margin=dict(l=0,r=0,t=30,b=0),
                                      coloraxis_showscale=False)
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown("**Confusion Matrix**")
                st.plotly_chart(fig_cm, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_fi:
                # Feature importances
                importances = pd.DataFrame({
                    "Feature":    feat_cols,
                    "Importance": rf.feature_importances_
                }).sort_values("Importance")
                
                fig_fi = go.Figure(go.Bar(
                    x=importances["Importance"], y=importances["Feature"],
                    orientation="h",
                    marker=dict(color=importances["Importance"],
                                colorscale=[[0,"#DBEAFE"],[1,"#1D4ED8"]], showscale=False),
                ))
                fig_fi.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    height=300, margin=dict(l=0,r=10,t=30,b=0),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False),
                    font=dict(family="Inter, sans-serif")
                )
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown("**Feature Importance**")
                st.plotly_chart(fig_fi, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Churn probability distribution
            fig_prob = px.histogram(pd.DataFrame({"Churn Probability": y_prob}),
                                    x="Churn Probability", nbins=30,
                                    color_discrete_sequence=["#2563EB"])
            fig_prob.update_traces(marker_line_width=0)
            fig_prob.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=280, margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(showgrid=False, title="Predicted Churn Probability"),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="# Customers"),
                font=dict(family="Inter, sans-serif")
            )
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("**Predicted Churn Probability Distribution**")
            st.plotly_chart(fig_prob, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ── Single customer churn predictor ──────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">Predict Churn for a Single Customer</div>', unsafe_allow_html=True)
    
    model_path = os.path.join(MODELS_DIR, "churn_model.pkl")
    scaler_path = os.path.join(MODELS_DIR, "churn_scaler.pkl")
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            pf  = st.number_input("Purchase Frequency",     1, 50, 5)
            aov = st.number_input("Avg Order Value ($)",     10.0, 5000.0, 200.0, step=50.0)
        with col_i2:
            lpd = st.number_input("Days Since Last Purchase", 1, 500, 60)
            st_t = st.number_input("Support Tickets",         0, 20, 1)
        with col_i3:
            sat  = st.slider("Satisfaction Score (1–10)", 1, 10, 7)
            ts   = st.number_input("Total Spent ($)",      10.0, 50000.0, 1000.0, step=100.0)
        
        if st.button("🔍 Predict Churn Risk", use_container_width=True, type="primary"):
            rf_loaded  = joblib.load(model_path)
            sc_loaded  = joblib.load(scaler_path)
            inp = np.array([[pf, aov, lpd, st_t, sat, ts]])
            inp_s = sc_loaded.transform(inp)
            prob  = rf_loaded.predict_proba(inp_s)[0][1]
            pred  = rf_loaded.predict(inp_s)[0]
            
            if pred == 1:
                st.error(f"⚠️ **High Churn Risk** — Probability: **{prob:.1%}**")
            else:
                st.success(f"✅ **Low Churn Risk** — Probability: **{prob:.1%}**")
            
            # Gauge chart
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(prob * 100, 1),
                domain=dict(x=[0,1], y=[0,1]),
                title=dict(text="Churn Risk %", font=dict(size=16)),
                gauge=dict(
                    axis=dict(range=[0,100]),
                    bar=dict(color="#2563EB"),
                    steps=[
                        dict(range=[0,33], color="#D1FAE5"),
                        dict(range=[33,66], color="#FEF9C3"),
                        dict(range=[66,100], color="#FEE2E2"),
                    ],
                    threshold=dict(line=dict(color="black", width=2), thickness=0.75, value=50)
                )
            ))
            fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280,
                                  font=dict(family="Inter, sans-serif", color="#1E293B"),
                                  margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(fig_g, use_container_width=True)
    else:
        st.info("Train the churn model above first to enable single-customer predictions.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: CUSTOMER SEGMENTATION (K-Means)
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Customer Segmentation — K-Means Clustering</div>', unsafe_allow_html=True)
    
    col_seg_ov, col_seg_params = st.columns([3, 2])
    
    with col_seg_ov:
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:18px 22px;">
            <div style="font-weight:600;color:#1E293B;margin-bottom:8px;">Model Overview</div>
            <ul style="font-size:0.84rem;color:#64748B;margin:0;padding-left:18px;line-height:2;">
                <li><b>Algorithm:</b> K-Means Clustering</li>
                <li><b>Features:</b> Total spend, purchase frequency, avg order value, days since last purchase</li>
                <li><b>Output:</b> Customer segments with business labels</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_seg_params:
        n_clusters = st.slider("Number of clusters (K)", 2, 8, 4, key="n_clusters")
        seg_btn = st.button("🚀 Run Segmentation", type="primary", use_container_width=True, key="run_seg")
    
    if seg_btn:
        with st.spinner("Running K-Means clustering..."):
            seg_features = ["total_spent","purchase_frequency","avg_order_value","last_purchase_days_ago","satisfaction_score"]
            df_seg = customers_df[seg_features + ["customer_id","name","region"]].dropna()
            
            scaler_km = StandardScaler()
            X_scaled = scaler_km.fit_transform(df_seg[seg_features])
            
            km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df_seg["Cluster"] = km.fit_predict(X_scaled)
            
            # Auto-label segments based on spend + frequency
            cluster_summary = df_seg.groupby("Cluster").agg(
                avg_spend=("total_spent","mean"),
                avg_freq=("purchase_frequency","mean"),
                avg_days=("last_purchase_days_ago","mean"),
                count=("customer_id","count")
            ).reset_index()
            
            segment_labels = {
                0: "💎 Champions",
                1: "🔥 Loyal Customers",
                2: "🌱 Promising",
                3: "😴 At Risk",
                4: "💤 Lost",
                5: "⭐ New Customers",
                6: "📈 Growing",
                7: "🔄 Need Attention"
            }
            
            # Rank by spend to assign labels
            cluster_summary = cluster_summary.sort_values("avg_spend", ascending=False).reset_index(drop=True)
            cluster_summary["Label"] = [segment_labels.get(i, f"Segment {i}") for i in range(len(cluster_summary))]
            label_map = dict(zip(cluster_summary["Cluster"], cluster_summary["Label"]))
            df_seg["Segment"] = df_seg["Cluster"].map(label_map)
            
            joblib.dump(km,        os.path.join(MODELS_DIR, "kmeans_model.pkl"))
            joblib.dump(scaler_km, os.path.join(MODELS_DIR, "kmeans_scaler.pkl"))
            
            # Cluster sizes
            size_df = df_seg.groupby("Segment").size().reset_index(name="Count")
            
            col_sz, col_sc = st.columns(2)
            with col_sz:
                fig_sz = px.pie(size_df, names="Segment", values="Count",
                                color_discrete_sequence=PALETTE, hole=0.4)
                fig_sz.update_traces(textinfo="percent+label",
                                     marker=dict(line=dict(color="white", width=2)))
                fig_sz.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=340,
                                      showlegend=False,
                                      font=dict(family="Inter, sans-serif"),
                                      margin=dict(l=0,r=0,t=10,b=0))
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown("**Segment Distribution**")
                st.plotly_chart(fig_sz, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_sc:
                # Scatter: spend vs frequency colored by segment
                fig_sc = px.scatter(
                    df_seg, x="total_spent", y="purchase_frequency",
                    color="Segment", color_discrete_sequence=PALETTE,
                    hover_data=["name","region"],
                    opacity=0.75, size_max=10
                )
                fig_sc.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    height=340, margin=dict(l=0,r=0,t=10,b=0),
                    legend=dict(orientation="v", x=1.02, y=0.5),
                    xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickprefix="$", title="Total Spent"),
                    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Purchase Frequency"),
                    font=dict(family="Inter, sans-serif")
                )
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown("**Spend vs Frequency by Segment**")
                st.plotly_chart(fig_sc, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Segment summary table
            st.markdown('<div class="section-header">Segment Summary</div>', unsafe_allow_html=True)
            seg_table = df_seg.groupby("Segment").agg(
                Customers=("customer_id","count"),
                Avg_Spend=("total_spent","mean"),
                Avg_Frequency=("purchase_frequency","mean"),
                Avg_Days_Inactive=("last_purchase_days_ago","mean"),
                Avg_Satisfaction=("satisfaction_score","mean")
            ).reset_index().round(1)
            seg_table["Avg_Spend"] = seg_table["Avg_Spend"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(seg_table.rename(columns={
                "Avg_Spend":"Avg Spend", "Avg_Frequency":"Avg Frequency",
                "Avg_Days_Inactive":"Avg Days Inactive", "Avg_Satisfaction":"Avg Satisfaction"
            }), use_container_width=True, hide_index=True)
            
            st.success(f"✅ Segmented **{len(df_seg):,}** customers into **{n_clusters}** groups. Models saved.")
