"""
BusinessVerse - Backend Data Processing Utilities
Helper functions for data cleaning, transformation, and statistics.
"""

import pandas as pd
import numpy as np


def get_dataframe_stats(df: pd.DataFrame) -> dict:
    """Return summary statistics for a DataFrame."""
    stats = {
        "rows":     int(len(df)),
        "columns":  int(len(df.columns)),
        "missing":  int(df.isnull().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "memory_kb": float(round(df.memory_usage(deep=True).sum() / 1024, 2)),
    }
    return stats


def get_missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame showing missing value counts and percentages."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    report = pd.DataFrame({
        "Column": missing.index,
        "Missing Count": missing.values,
        "Missing %": missing_pct.values,
        "Dtype": [str(d) for d in df.dtypes.values]
    })
    return report[report["Missing Count"] > 0].sort_values("Missing Count", ascending=False)


def clean_remove_nulls(df: pd.DataFrame) -> tuple:
    """Drop all rows with any null values."""
    before = len(df)
    df_clean = df.dropna()
    after = len(df_clean)
    return df_clean, int(before - after)


def clean_fill_nulls(df: pd.DataFrame, strategy: str = "mean") -> pd.DataFrame:
    """Fill null values with given strategy (mean/median/mode/zero)."""
    df_clean = df.copy()
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            if strategy == "mean":
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
            elif strategy == "median":
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            elif strategy == "zero":
                df_clean[col] = df_clean[col].fillna(0)
            elif strategy == "mode":
                df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])
    
    # Fill categorical with mode
    cat_cols = df_clean.select_dtypes(include=["object"]).columns
    for col in cat_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])
    
    return df_clean


def clean_remove_duplicates(df: pd.DataFrame) -> tuple:
    """Remove duplicate rows."""
    before = len(df)
    df_clean = df.drop_duplicates()
    return df_clean, int(before - len(df_clean))


def safe_load_csv(file_stream):
    """Safely load an uploaded CSV file from a binary/text stream."""
    try:
        df = pd.read_csv(file_stream)
        return df
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")


def convert_column_types(df: pd.DataFrame, conversions: dict) -> tuple:
    """Convert column dtypes based on conversions dict {col: dtype}."""
    df_out = df.copy()
    errors = []
    for col, dtype in conversions.items():
        try:
            if dtype == "datetime":
                df_out[col] = pd.to_datetime(df_out[col])
            elif dtype == "numeric":
                df_out[col] = pd.to_numeric(df_out[col], errors="coerce")
            else:
                df_out[col] = df_out[col].astype(dtype)
        except Exception as e:
            errors.append(f"{col}: {e}")
    return df_out, errors


def detect_date_columns(df: pd.DataFrame) -> list:
    """Auto-detect potential date columns."""
    date_cols = []
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            date_cols.append(col)
    return date_cols


def prepare_orders_for_ml(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare orders DataFrame for ML feature engineering."""
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["year"]  = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.month
    df["quarter"] = df["order_date"].dt.quarter
    df["day_of_week"] = df["order_date"].dt.dayofweek
    return df


def aggregate_monthly_sales(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate orders into monthly sales summary."""
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["year_month"] = df["order_date"].dt.to_period("M")
    
    monthly = df.groupby("year_month").agg(
        revenue=("total_amount", "sum"),
        orders=("order_id", "count"),
        profit=("profit", "sum"),
        avg_order=("total_amount", "mean")
    ).reset_index()
    monthly["year_month"] = monthly["year_month"].astype(str)
    return monthly
