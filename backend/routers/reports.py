"""
BusinessVerse - FastAPI Reports & Exports Router
"""

import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
import pandas as pd
from utils.auth import get_current_user
from routers.data import SESSION_DATA

router = APIRouter(prefix="/reports", tags=["reports"])


def load_report_base_data() -> tuple:
    """Helper to load base data for reporting."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    orders    = pd.read_csv(os.path.join(base, "orders.csv"))
    customers = pd.read_csv(os.path.join(base, "customers.csv"))
    products  = pd.read_csv(os.path.join(base, "products.csv"))
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    return orders, customers, products


import os
def get_filtered_df(
    session_id: str,
    period: str = "All Time",
    region: str = "All Regions",
    category: str = "All Categories"
) -> tuple:
    """Filter orders and load customers/products based on parameters."""
    # Try loading from session, else load default
    if session_id in SESSION_DATA and "clean" in SESSION_DATA[session_id]:
        orders_df = SESSION_DATA[session_id]["clean"].copy()
        # Verify columns, fallback if not orders
        if "total_amount" not in orders_df.columns:
            orders_df, _, _ = load_report_base_data()
    else:
        orders_df, _, _ = load_report_base_data()
        
    _, customers_df, products_df = load_report_base_data()
    
    orders_df["order_date"] = pd.to_datetime(orders_df["order_date"])
    active = orders_df[orders_df["status"] != "Cancelled"].copy()
    
    # Filter by period
    if not active.empty:
        today = active["order_date"].max()
        if period == "Last 30 Days":
            active = active[active["order_date"] >= today - pd.Timedelta(days=30)]
        elif period == "Last 90 Days":
            active = active[active["order_date"] >= today - pd.Timedelta(days=90)]
        elif period == "Last 6 Months":
            active = active[active["order_date"] >= today - pd.Timedelta(days=182)]
        elif period == "Last 12 Months":
            active = active[active["order_date"] >= today - pd.Timedelta(days=365)]
        elif period == "Year 2022":
            active = active[active["order_date"].dt.year == 2022]
        elif period == "Year 2023":
            active = active[active["order_date"].dt.year == 2023]
        elif period == "Year 2024":
            active = active[active["order_date"].dt.year == 2024]
            
    # Filter by region
    if region != "All Regions" and not active.empty:
        active = active[active["region"] == region]
        
    # Filter by category
    if category != "All Categories" and not active.empty:
        active = active[active["category"] == category]
        
    return active, customers_df, products_df


@router.get("/summary")
def get_report_summary(
    period: str = "All Time",
    region: str = "All Regions",
    category: str = "All Categories",
    session_id: str = Depends(get_current_user)
):
    """Calculate and return key KPI reports and metrics based on selected filters."""
    username = session_id["sub"]
    rep_df, _, _ = get_filtered_df(username, period, region, category)
    
    total_rev  = float(rep_df["total_amount"].sum())
    total_prof = float(rep_df["profit"].sum())
    total_ord  = int(len(rep_df))
    total_cust = int(rep_df["customer_id"].nunique()) if total_ord > 0 else 0
    avg_ord    = float(rep_df["total_amount"].mean()) if total_ord > 0 else 0.0
    margin     = float((total_prof / total_rev * 100)) if total_rev > 0 else 0.0
    
    # Regional list
    unique_regions = ["All Regions"]
    if "region" in rep_df.columns:
        unique_regions += sorted(rep_df["region"].dropna().unique().tolist())
        
    # Categories list
    unique_cats = ["All Categories"]
    if "category" in rep_df.columns:
        unique_cats += sorted(rep_df["category"].dropna().unique().tolist())
        
    # Monthly sales revenue aggregation
    monthly_sales = []
    if total_ord > 0:
        rep_df_copy = rep_df.copy()
        rep_df_copy["ym"] = rep_df_copy["order_date"].dt.to_period("M").astype(str)
        monthly_agg = rep_df_copy.groupby("ym").agg(
            revenue=("total_amount","sum"),
            profit=("profit","sum")
        ).reset_index()
        monthly_sales = [
            {"month": row["ym"], "revenue": float(round(row["revenue"], 2)), "profit": float(round(row["profit"], 2))}
            for _, row in monthly_agg.iterrows()
        ]
        
    # Product categories aggregation
    category_perf = []
    if total_ord > 0:
        cat_agg = rep_df.groupby("category")["total_amount"].sum().reset_index()
        category_perf = [
            {"category": row["category"], "revenue": float(round(row["total_amount"], 2))}
            for _, row in cat_agg.iterrows()
        ]
        
    return {
        "kpis": {
            "total_revenue": total_rev,
            "total_profit": total_prof,
            "total_orders": total_ord,
            "unique_customers": total_cust,
            "avg_order_value": avg_ord,
            "profit_margin_pct": margin
        },
        "regions": unique_regions,
        "categories": unique_cats,
        "monthly_sales": monthly_sales,
        "category_performance": category_perf
    }


@router.get("/download/csv")
def download_csv(
    target: str = Query("orders", enum=["orders", "customers", "products"]),
    period: str = "All Time",
    region: str = "All Regions",
    category: str = "All Categories",
    session_id: str = Depends(get_current_user)
):
    """Generate and download filtered tables as a CSV streaming file."""
    username = session_id["sub"]
    orders, customers, products = get_filtered_df(username, period, region, category)
    
    if target == "orders":
        df_target = orders
    elif target == "customers":
        df_target = customers
    else:
        df_target = products
        
    stream = io.StringIO()
    df_target.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=businessverse_{target}_{period.lower().replace(' ', '_')}.csv"
    return response


@router.get("/download/excel")
def download_excel(
    target: str = Query("analytics_report", enum=["orders", "customers", "products", "analytics_report"]),
    period: str = "All Time",
    region: str = "All Regions",
    category: str = "All Categories",
    session_id: str = Depends(get_current_user)
):
    """Generate multiple Excel summary sheets and return Excel spreadsheet binary."""
    username = session_id["sub"]
    orders, customers, products = get_filtered_df(username, period, region, category)
    
    excel_buf = io.BytesIO()
    
    with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
        if target == "orders":
            orders.to_excel(writer, sheet_name="Orders", index=False)
        elif target == "customers":
            customers.to_excel(writer, sheet_name="Customers", index=False)
        elif target == "products":
            products.to_excel(writer, sheet_name="Products", index=False)
        else:
            # Full multi-sheet analytical report
            total_rev  = float(orders["total_amount"].sum())
            total_prof = float(orders["profit"].sum())
            total_ord  = int(len(orders))
            total_cust = int(orders["customer_id"].nunique()) if total_ord > 0 else 0
            avg_ord    = float(orders["total_amount"].mean()) if total_ord > 0 else 0.0
            margin     = float((total_prof / total_rev * 100)) if total_rev > 0 else 0.0
            
            kpi_report = pd.DataFrame([
                {"Metric": "Total Revenue",        "Value": f"${total_rev:,.2f}"},
                {"Metric": "Total Profit",         "Value": f"${total_prof:,.2f}"},
                {"Metric": "Profit Margin",        "Value": f"{margin:.2f}%"},
                {"Metric": "Total Orders",         "Value": f"{total_ord:,}"},
                {"Metric": "Unique Customers",     "Value": f"{total_cust:,}"},
                {"Metric": "Avg Order Value",      "Value": f"${avg_ord:,.2f}"},
                {"Metric": "Report Period",        "Value": period},
                {"Metric": "Report Region",        "Value": region},
                {"Metric": "Report Category",      "Value": category},
                {"Metric": "Generated At",         "Value": datetime.now().strftime("%Y-%m-%d %H:%M")}
            ])
            
            # Aggregate monthly
            orders_copy = orders.copy()
            orders_copy["ym"] = orders_copy["order_date"].dt.to_period("M").astype(str)
            monthly_agg = orders_copy.groupby("ym").agg(
                Revenue=("total_amount","sum"),
                Profit=("profit","sum"),
                Orders=("order_id","count")
            ).reset_index().rename(columns={"ym":"Month"}).round(2)
            
            region_report = orders.groupby("region").agg(
                Revenue=("total_amount","sum"),
                Profit=("profit","sum"),
                Orders=("order_id","count")
            ).reset_index().rename(columns={"region":"Region"}).round(2)
            
            category_report = orders.groupby("category").agg(
                Revenue=("total_amount","sum"),
                Profit=("profit","sum"),
                Units=("quantity","sum")
            ).reset_index().rename(columns={"category":"Category"}).round(2)
            
            top_products_report = (
                orders.groupby("product_name")["total_amount"].sum()
                .nlargest(20).reset_index()
                .rename(columns={"product_name":"Product","total_amount":"Revenue"})
                .round(2)
            )
            
            kpi_report.to_excel(writer,            sheet_name="KPI Summary",    index=False)
            monthly_agg.to_excel(writer,           sheet_name="Monthly Revenue", index=False)
            region_report.to_excel(writer,         sheet_name="Region Sales",    index=False)
            category_report.to_excel(writer,       sheet_name="Category Perf",  index=False)
            top_products_report.to_excel(writer,   sheet_name="Top Products",   index=False)

    excel_buf.seek(0)
    response = StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=businessverse_{target}_{period.lower().replace(' ', '_')}.xlsx"
    return response
