"""
BusinessVerse - FastAPI Data Upload & Cleaning Router
"""

import io
from typing import List, Dict, Any
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from pydantic import BaseModel
from utils.auth import get_current_user
from utils.data_processing import (
    get_dataframe_stats,
    get_missing_value_report,
    clean_remove_nulls,
    clean_fill_nulls,
    clean_remove_duplicates,
    convert_column_types,
    safe_load_csv
)

router = APIRouter(prefix="/data", tags=["data"])

# Global in-memory storage mapping session_id -> { "original": df, "clean": df }
SESSION_DATA: Dict[str, Dict[str, pd.DataFrame]] = {}


def get_session_id(current_user: dict = Depends(get_current_user)) -> str:
    """Use the authenticated username as a simple session key."""
    return current_user["sub"]


class CleanStatsResponse(BaseModel):
    rows: int
    columns: int
    missing: int
    duplicates: int
    memory_kb: float


class TypeConversionRequest(BaseModel):
    conversions: Dict[str, str]  # { "col_name": "numeric|datetime|str|int|float" }


class FeatureSelectionRequest(BaseModel):
    columns: List[str]


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id)
):
    """Upload a CSV or Excel dataset, analyze stats, and cache it in memory."""
    filename = file.filename
    content = await file.read()
    
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    
    # Store in session memory
    SESSION_DATA[session_id] = {
        "original": df.copy(),
        "clean": df.copy()
    }
    
    stats = get_dataframe_stats(df)
    missing_report = get_missing_value_report(df).to_dict(orient="records")
    columns = df.columns.tolist()
    dtypes = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
    
    # Generate JSON-serializable preview (top 30 rows, replace NaNs with None)
    preview_df = df.head(30).where(pd.notnull(df), None)
    preview = preview_df.to_dict(orient="records")
    
    return {
        "message": "File uploaded successfully",
        "stats": stats,
        "columns": columns,
        "dtypes": dtypes,
        "missing_report": missing_report,
        "preview": preview
    }


@router.get("/stats")
def get_stats(session_id: str = Depends(get_session_id)):
    """Retrieve stats of the original vs cleaned datasets."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset loaded.")
    
    df_orig = SESSION_DATA[session_id]["original"]
    df_clean = SESSION_DATA[session_id]["clean"]
    
    stats_orig = get_dataframe_stats(df_orig)
    stats_clean = get_dataframe_stats(df_clean)
    missing_report = get_missing_value_report(df_clean).to_dict(orient="records")
    
    return {
        "original": stats_orig,
        "clean": stats_clean,
        "missing_report": missing_report
    }


@router.post("/clean/nulls/drop")
def drop_nulls(session_id: str = Depends(get_session_id)):
    """Drop rows containing any missing value."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    df = SESSION_DATA[session_id]["clean"]
    cleaned, dropped_count = clean_remove_nulls(df)
    SESSION_DATA[session_id]["clean"] = cleaned
    
    return {
        "message": f"Successfully dropped {dropped_count} row(s) with missing values.",
        "stats": get_dataframe_stats(cleaned)
    }


@router.post("/clean/nulls/fill")
def fill_nulls(
    strategy: str = Query("mean", enum=["mean", "median", "mode", "zero"]),
    session_id: str = Depends(get_session_id)
):
    """Fill missing values in the dataset using selected strategy."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    df = SESSION_DATA[session_id]["clean"]
    filled = clean_fill_nulls(df, strategy=strategy)
    SESSION_DATA[session_id]["clean"] = filled
    
    return {
        "message": f"Successfully filled missing values using {strategy}.",
        "stats": get_dataframe_stats(filled)
    }


@router.post("/clean/duplicates/remove")
def remove_duplicates(session_id: str = Depends(get_session_id)):
    """Remove duplicate rows from the dataset."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    df = SESSION_DATA[session_id]["clean"]
    cleaned, removed_count = clean_remove_duplicates(df)
    SESSION_DATA[session_id]["clean"] = cleaned
    
    return {
        "message": f"Successfully removed {removed_count} duplicate row(s).",
        "stats": get_dataframe_stats(cleaned)
    }


@router.post("/clean/types/convert")
def convert_types(
    request: TypeConversionRequest,
    session_id: str = Depends(get_session_id)
):
    """Convert column datatypes."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    df = SESSION_DATA[session_id]["clean"]
    result, errors = convert_column_types(df, request.conversions)
    SESSION_DATA[session_id]["clean"] = result
    
    if errors:
        return {
            "message": "Conversion completed with errors",
            "errors": errors,
            "stats": get_dataframe_stats(result)
        }
    
    return {
        "message": "Column datatypes successfully converted.",
        "stats": get_dataframe_stats(result)
    }


@router.post("/clean/features/select")
def select_features(
    request: FeatureSelectionRequest,
    session_id: str = Depends(get_session_id)
):
    """Keep only the specified columns in the dataset."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    df = SESSION_DATA[session_id]["clean"]
    invalid_cols = [c for c in request.columns if c not in df.columns]
    if invalid_cols:
        raise HTTPException(status_code=400, detail=f"Columns not found: {invalid_cols}")
    
    if len(request.columns) < 1:
        raise HTTPException(status_code=400, detail="Please keep at least 1 column.")
        
    selected_df = df[request.columns].copy()
    SESSION_DATA[session_id]["clean"] = selected_df
    
    return {
        "message": f"Kept {len(request.columns)} columns, dropped the rest.",
        "stats": get_dataframe_stats(selected_df)
    }


@router.post("/clean/reset")
def reset_clean_data(session_id: str = Depends(get_session_id)):
    """Reset clean DataFrame to its original uploaded state."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    SESSION_DATA[session_id]["clean"] = SESSION_DATA[session_id]["original"].copy()
    
    return {
        "message": "Dataset reset to its original state.",
        "stats": get_dataframe_stats(SESSION_DATA[session_id]["clean"])
    }


@router.get("/preview")
def get_preview(session_id: str = Depends(get_session_id)):
    """Return top 30 rows of current clean dataset as JSON."""
    if session_id not in SESSION_DATA:
        raise HTTPException(status_code=404, detail="No active dataset.")
    
    df = SESSION_DATA[session_id]["clean"]
    preview_df = df.head(30).where(pd.notnull(df), None)
    
    return {
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
        "preview": preview_df.to_dict(orient="records")
    }
