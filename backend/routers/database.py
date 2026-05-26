"""
BusinessVerse - FastAPI Database Connector Router
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from utils.auth import get_current_user
from utils.db_connector import (
    get_engine,
    init_database,
    load_csv_to_db,
    query_kpis,
    query_recent_orders,
    query_monthly_revenue,
    query_region_sales,
    query_category_performance,
    DB_CONFIG
)

router = APIRouter(prefix="/database", tags=["database"])


class QueryRequest(BaseModel):
    sql: str


class DBConfigResponse(BaseModel):
    type: str
    host: str
    port: str
    database: str
    username: str


@router.get("/config", response_model=DBConfigResponse)
def get_db_config(current_user: dict = Depends(get_current_user)):
    """Retrieve active database credentials (hiding sensitive info)."""
    return {
        "type": DB_CONFIG["type"],
        "host": DB_CONFIG["host"],
        "port": DB_CONFIG["port"],
        "database": DB_CONFIG["database"],
        "username": DB_CONFIG["username"]
    }


@router.post("/connect")
def test_db_connection(current_user: dict = Depends(get_current_user)):
    """Establish connection, initialize schema, and confirm status."""
    try:
        engine = get_engine()
        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Initialize schema tables
        init_database(engine)
        return {"status": "connected", "message": f"Successfully connected to database type '{DB_CONFIG['type']}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@router.post("/load-mock-data")
def load_mock_data_to_db(current_user: dict = Depends(get_current_user)):
    """Seed the database with sample CSV data."""
    try:
        engine = get_engine()
        init_database(engine)
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
        cust_path = os.path.join(base_dir, "customers.csv")
        prod_path = os.path.join(base_dir, "products.csv")
        ord_path = os.path.join(base_dir, "orders.csv")
        
        if not (os.path.exists(cust_path) and os.path.exists(prod_path) and os.path.exists(ord_path)):
            raise HTTPException(status_code=400, detail="Mock CSV files not found. Generate mock files in backend/data first.")
            
        c_count, p_count, o_count = load_csv_to_db(engine, cust_path, prod_path, ord_path)
        return {
            "status": "success",
            "message": "Seeded database tables successfully.",
            "loaded_records": {
                "customers": c_count,
                "products": p_count,
                "orders": o_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


@router.post("/query")
def run_custom_query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute raw read-only SQL queries and return the result set as columns and data list."""
    sql = request.sql.strip()
    
    # Simple safety guards (readonly check)
    sql_lower = sql.lower()
    unsafe_keywords = ["drop", "delete", "insert", "update", "alter", "truncate", "create table", "grant"]
    for keyword in unsafe_keywords:
        if keyword in sql_lower:
            raise HTTPException(status_code=400, detail=f"Operation not allowed. SQL query is restricted to read-only statements.")
            
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            
            # Fetch headers
            columns = list(result.keys())
            
            # Fetch rows
            rows = []
            for row in result.fetchall():
                row_dict = {}
                for idx, col in enumerate(columns):
                    val = row[idx]
                    # Handle python float/int parsing to avoid serialization issues
                    if isinstance(val, (int, float)) or val is None or isinstance(val, str):
                        row_dict[col] = val
                    else:
                        row_dict[col] = str(val)
                rows.append(row_dict)
                
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL Query Execution Error: {str(e)}")


@router.get("/dashboard-kpis")
def get_db_kpis(current_user: dict = Depends(get_current_user)):
    """Fetch high-level business KPI stats from the database orders table."""
    try:
        engine = get_engine()
        kpis = query_kpis(engine)
        recent = query_recent_orders(engine, limit=6).to_dict(orient="records")
        monthly = query_monthly_revenue(engine).to_dict(orient="records")
        regional = query_region_sales(engine).to_dict(orient="records")
        categories = query_category_performance(engine).to_dict(orient="records")
        
        return {
            "kpis": {
                "total_revenue": float(kpis["total_revenue"]),
                "total_orders": int(kpis["total_orders"]),
                "total_profit": float(kpis["total_profit"]),
                "avg_order_value": float(kpis["avg_order_value"])
            },
            "recent_orders": recent,
            "monthly_sales": monthly,
            "regional_sales": regional,
            "category_performance": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch KPI stats: {str(e)}")
