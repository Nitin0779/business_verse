"""
BusinessVerse - FastAPI Machine Learning Router
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from utils.auth import get_current_user
from routers.data import SESSION_DATA

from sklearn.linear_model    import LinearRegression
from sklearn.ensemble        import RandomForestClassifier
from sklearn.cluster         import KMeans
from sklearn.preprocessing   import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics         import mean_absolute_error, r2_score, accuracy_score, confusion_matrix

router = APIRouter(prefix="/ml", tags=["ml"])

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))
os.makedirs(MODELS_DIR, exist_ok=True)


def load_default_data(file_name: str) -> pd.DataFrame:
    """Helper to load default dataset from the project's data directory."""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../data/{file_name}"))
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Default data file '{file_name}' not found. Please generate sample data first.")
    return pd.read_csv(path)


def get_active_or_default_df(session_id: str, file_name: str) -> pd.DataFrame:
    """Check if a clean dataset exists in the session, else fallback to standard file."""
    if session_id in SESSION_DATA and "clean" in SESSION_DATA[session_id]:
        df = SESSION_DATA[session_id]["clean"]
        # Verify if column signatures match what we need
        if file_name == "orders.csv" and "total_amount" in df.columns:
            return df
        if file_name == "customers.csv" and "churn" in df.columns:
            return df
    
    return load_default_data(file_name)


# ─── Sales Prediction Models & Routes ─────────────────────────────────────────

class SalesForecastResponse(BaseModel):
    r2: float
    mae: float
    historical: List[Dict[str, Any]]
    forecast: List[Dict[str, Any]]


@router.post("/sales/train", response_model=SalesForecastResponse)
def train_sales_forecast(
    forecast_months: int = Query(6, ge=1, le=24),
    session_id: str = Depends(get_current_user)
):
    """Train linear regression on historical revenue and return forecasts."""
    # Find username
    username = session_id["sub"]
    orders_df = get_active_or_default_df(username, "orders.csv")
    
    try:
        active = orders_df[orders_df["status"] != "Cancelled"].copy()
        active["order_date"] = pd.to_datetime(active["order_date"])
        active["ym"] = active["order_date"].dt.to_period("M")
        
        monthly = active.groupby("ym")["total_amount"].sum().reset_index()
        monthly.columns = ["period", "revenue"]
        monthly["month_num"] = range(len(monthly))
        monthly["month"]     = monthly["period"].dt.month
        monthly["quarter"]   = monthly["period"].dt.quarter
        monthly["year"]      = monthly["period"].dt.year
        
        # Create Lag features
        monthly["lag_1"]  = monthly["revenue"].shift(1)
        monthly["lag_2"]  = monthly["revenue"].shift(2)
        monthly["lag_3"]  = monthly["revenue"].shift(3)
        monthly = monthly.dropna()
        
        if len(monthly) < 6:
            raise HTTPException(status_code=400, detail="Insufficient chronological data points to train forecasting model (minimum 6 months required).")
        
        X = monthly[["month_num","month","quarter","year","lag_1","lag_2","lag_3"]]
        y = monthly["revenue"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))
        
        # Save model
        joblib.dump(model, os.path.join(MODELS_DIR, "sales_model.pkl"))
        
        # Forecast future
        last_row    = monthly.iloc[-1]
        last_num    = int(last_row["month_num"])
        last_period = last_row["period"]
        last_rev    = monthly["revenue"].values
        
        future_rows = []
        lag_window  = list(last_rev[-3:])
        
        for i in range(1, forecast_months + 1):
            next_period  = last_period + i
            next_month   = int(next_period.month)
            next_quarter = int((next_month - 1) // 3 + 1)
            next_year    = int(next_period.year)
            next_num     = last_num + i
            
            row = [next_num, next_month, next_quarter, next_year,
                   lag_window[-1], lag_window[-2], lag_window[-3]]
            
            pred = float(model.predict([row])[0])
            lag_window.append(pred)
            future_rows.append({
                "period":  str(next_period),
                "revenue": float(round(pred, 2)),
                "type":    "Forecast"
            })
            
        hist_plot = monthly[["period","revenue"]].copy()
        hist_plot["period"] = hist_plot["period"].astype(str)
        hist_plot["type"]   = "Historical"
        hist_records = hist_plot.to_dict(orient="records")
        
        return {
            "r2": r2,
            "mae": mae,
            "historical": hist_records,
            "forecast": future_rows
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")


# ─── Churn Classification Models & Routes ─────────────────────────────────────

class ChurnTrainResponse(BaseModel):
    accuracy: float
    churn_rate: float
    train_size: int
    confusion_matrix: List[List[int]]
    feature_importances: List[Dict[str, Any]]
    probability_distribution: List[float]


class ChurnPredictionRequest(BaseModel):
    purchase_frequency: float
    avg_order_value: float
    last_purchase_days_ago: float
    support_tickets: float
    satisfaction_score: float
    total_spent: float


class ChurnPredictionResponse(BaseModel):
    churn_prediction: int  # 0 = Retained, 1 = Churned
    churn_probability: float


@router.post("/churn/train", response_model=ChurnTrainResponse)
def train_churn_model(
    n_estimators: int = Query(100, ge=50, le=300),
    session_id: str = Depends(get_current_user)
):
    """Train Random Forest classifier on customer dataset."""
    username = session_id["sub"]
    customers_df = get_active_or_default_df(username, "customers.csv")
    
    try:
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
        
        acc = float(accuracy_score(y_test, y_pred))
        cm  = confusion_matrix(y_test, y_pred).tolist()
        churn_rate = float(y.mean())
        
        # Save model and scaler
        joblib.dump(rf,     os.path.join(MODELS_DIR, "churn_model.pkl"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, "churn_scaler.pkl"))
        
        importances = [
            {"feature": f, "importance": float(imp)}
            for f, imp in zip(feat_cols, rf.feature_importances_)
        ]
        importances = sorted(importances, key=lambda x: x["importance"], reverse=True)
        
        return {
            "accuracy": acc,
            "churn_rate": churn_rate,
            "train_size": len(X_train),
            "confusion_matrix": cm,
            "feature_importances": importances,
            "probability_distribution": [float(p) for p in y_prob]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Churn training error: {str(e)}")


@router.post("/churn/predict", response_model=ChurnPredictionResponse)
def predict_single_churn(
    request: ChurnPredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Predict churn probability for a single customer using saved model."""
    model_path = os.path.join(MODELS_DIR, "churn_model.pkl")
    scaler_path = os.path.join(MODELS_DIR, "churn_scaler.pkl")
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise HTTPException(status_code=400, detail="Churn model has not been trained yet. Please call /ml/churn/train first.")
        
    try:
        rf = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        inp = np.array([[
            request.purchase_frequency,
            request.avg_order_value,
            request.last_purchase_days_ago,
            request.support_tickets,
            request.satisfaction_score,
            request.total_spent
        ]])
        
        inp_s = scaler.transform(inp)
        prob  = float(rf.predict_proba(inp_s)[0][1])
        pred  = int(rf.predict(inp_s)[0])
        
        return {
            "churn_prediction": pred,
            "churn_probability": prob
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# ─── K-Means Customer Segmentation Routes ─────────────────────────────────────

class SegmentationResponse(BaseModel):
    n_clusters: int
    total_segmented: int
    cluster_distribution: List[Dict[str, Any]]
    scatter_data: List[Dict[str, Any]]
    segment_summary: List[Dict[str, Any]]


@router.post("/segmentation", response_model=SegmentationResponse)
def run_segmentation(
    n_clusters: int = Query(4, ge=2, le=8),
    session_id: str = Depends(get_current_user)
):
    """Execute K-Means Clustering on customer profile and yield named customer segments."""
    username = session_id["sub"]
    customers_df = get_active_or_default_df(username, "customers.csv")
    
    try:
        seg_features = ["total_spent","purchase_frequency","avg_order_value","last_purchase_days_ago","satisfaction_score"]
        df_seg = customers_df[seg_features + ["customer_id","name","region"]].dropna()
        
        scaler_km = StandardScaler()
        X_scaled = scaler_km.fit_transform(df_seg[seg_features])
        
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_seg["Cluster"] = km.fit_predict(X_scaled)
        
        # Summarize clusters by spend to assign segments
        cluster_summary = df_seg.groupby("Cluster").agg(
            avg_spend=("total_spent","mean"),
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
        
        # Rank by spend descending to assign labels nicely
        cluster_summary = cluster_summary.sort_values("avg_spend", ascending=False).reset_index(drop=True)
        cluster_summary["Label"] = [segment_labels.get(i, f"Segment {i}") for i in range(len(cluster_summary))]
        label_map = dict(zip(cluster_summary["Cluster"], cluster_summary["Label"]))
        df_seg["Segment"] = df_seg["Cluster"].map(label_map)
        
        # Save cluster models
        joblib.dump(km,        os.path.join(MODELS_DIR, "kmeans_model.pkl"))
        joblib.dump(scaler_km, os.path.join(MODELS_DIR, "kmeans_scaler.pkl"))
        
        # Segments count distribution
        size_df = df_seg.groupby("Segment").size().reset_index(name="count")
        cluster_distribution = size_df.to_dict(orient="records")
        
        # Scatter chart data records (sample up to 200 for frontend rendering efficiency)
        scatter_sample = df_seg.sample(min(len(df_seg), 200), random_state=42)
        scatter_data = [
            {
                "customer_id": row["customer_id"],
                "name": row["name"],
                "region": row["region"],
                "total_spent": float(row["total_spent"]),
                "purchase_frequency": int(row["purchase_frequency"]),
                "avg_order_value": float(row["avg_order_value"]),
                "last_purchase_days_ago": int(row["last_purchase_days_ago"]),
                "satisfaction_score": int(row["satisfaction_score"]),
                "segment": row["Segment"]
            }
            for _, row in scatter_sample.iterrows()
        ]
        
        # Table stats summary
        seg_table = df_seg.groupby("Segment").agg(
            customers=("customer_id","count"),
            avg_spend=("total_spent","mean"),
            avg_frequency=("purchase_frequency","mean"),
            avg_days_inactive=("last_purchase_days_ago","mean"),
            avg_satisfaction=("satisfaction_score","mean")
        ).reset_index()
        
        segment_summary = []
        for _, row in seg_table.iterrows():
            segment_summary.append({
                "segment": row["Segment"],
                "customers": int(row["customers"]),
                "avg_spend": float(round(row["avg_spend"], 2)),
                "avg_frequency": float(round(row["avg_frequency"], 1)),
                "avg_days_inactive": float(round(row["avg_days_inactive"], 1)),
                "avg_satisfaction": float(round(row["avg_satisfaction"], 1))
            })
            
        return {
            "n_clusters": n_clusters,
            "total_segmented": len(df_seg),
            "cluster_distribution": cluster_distribution,
            "scatter_data": scatter_data,
            "segment_summary": segment_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering error: {str(e)}")
