"""
FastAPI REST API Routes for Linelist Cleaner and Spatial Cascade Geocoding.
"""

import io
import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel
import pandas as pd
import numpy as np

from linelist_cleaner.schemas.config import CleaningConfig
from linelist_cleaner.schemas.epi_dictionary import CANONICAL_TAGS
from linelist_cleaner.core.pipeline import LinelistCleaner, load_dataset
from linelist_cleaner.core.column_standardizer import map_linelist_columns
from linelist_cleaner.core.epi_analytics import EpiAnalytics
from linelist_cleaner.datasets import get_sample_dataset

router = APIRouter(prefix="/api")

# In-memory storage for active sessions
SESSIONS: Dict[str, Dict[str, Any]] = {}


def df_to_json_records(df: pd.DataFrame, limit: int = 100) -> List[Dict[str, Any]]:
    """Safely converts DataFrame slice to JSON-serializable records with None for NaNs."""
    sub = df.head(limit).copy()
    sub_obj = sub.astype(object).where(pd.notna(sub), None)
    return sub_obj.to_dict(orient="records")


class CleanRequest(BaseModel):
    session_id: str
    config: Optional[CleaningConfig] = None
    column_mapping: Optional[Dict[str, str]] = None
    spatial_mapping: Optional[Dict[str, str]] = None


@router.get("/samples")
async def list_samples():
    """Returns available sample outbreak datasets."""
    return [
        {
            "id": "borno",
            "name": "Borno Cholera Outbreak Linelist (180 cases - Nigeria)",
            "description": "Field line list with typos on IDP camps, LGAs, wards, and mixed dates ready for OCHA COD-AB cascade matching.",
            "disease": "Cholera (OCHA COD-AB)",
            "records": 180,
            "has_pcode_ref": True
        },
        {
            "id": "cholera",
            "name": "Kivu Cholera Outbreak Linelist (152 cases - DRC)",
            "description": "Bilingual (FR/EN) cholera line list with health zone variations, dehydration, and outcome status.",
            "disease": "Cholera",
            "records": 152,
            "has_pcode_ref": False
        },
        {
            "id": "covid19",
            "name": "COVID-19 Surveillance Linelist (120 cases)",
            "description": "Surveillance dataset with vaccination doses, PCR lab results, and timeline inconsistencies.",
            "disease": "COVID-19",
            "records": 120,
            "has_pcode_ref": False
        },
        {
            "id": "ebola",
            "name": "Ebola Virus Disease Linelist (100 cases)",
            "description": "EVD linelist with hemorrhagic signs, ETC admissions, and high case fatality.",
            "disease": "Ebola",
            "records": 100,
            "has_pcode_ref": False
        }
    ]


@router.get("/dictionary")
async def get_dictionary():
    """Returns canonical epidemiological variable dictionary."""
    return CANONICAL_TAGS


@router.post("/load_sample")
async def load_sample_dataset(sample_id: str = Form(...)):
    """Loads a built-in sample dataset into a new session."""
    try:
        df = get_sample_dataset(sample_id)
        session_id = f"sample_{sample_id}_{pd.Timestamp.now().strftime('%H%M%S')}"

        mapping_res = map_linelist_columns(df)
        mapped_dict = {col: m["mapped_tag"] for col, m in mapping_res.items() if m["mapped_tag"]}

        # Load reference P-code dataset
        ref_df = get_sample_dataset("pcode_reference")

        SESSIONS[session_id] = {
            "raw_df": df,
            "filename": f"{sample_id}_linelist.csv",
            "mapping": mapped_dict,
            "ref_df": ref_df,
            "ref_filename": "ocha_pcode_reference_nigeria.csv"
        }

        preview = df_to_json_records(df, 25)
        ref_preview = df_to_json_records(ref_df, 15) if ref_df is not None else []

        return {
            "session_id": session_id,
            "filename": f"{sample_id}_linelist.csv",
            "rows_count": len(df),
            "columns_count": len(df.columns),
            "columns": list(df.columns),
            "detected_mappings": mapping_res,
            "preview": preview,
            "reference_columns": list(ref_df.columns) if ref_df is not None else [],
            "reference_preview": ref_preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads raw line list CSV or Excel file."""
    try:
        contents = await file.read()
        df = load_dataset(contents)

        session_id = f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        mapping_res = map_linelist_columns(df)
        mapped_dict = {col: m["mapped_tag"] for col, m in mapping_res.items() if m["mapped_tag"]}

        ref_df = get_sample_dataset("pcode_reference")

        SESSIONS[session_id] = {
            "raw_df": df,
            "filename": file.filename,
            "mapping": mapped_dict,
            "ref_df": ref_df,
            "ref_filename": "ocha_pcode_reference_nigeria.csv"
        }

        preview = df_to_json_records(df, 25)

        return {
            "session_id": session_id,
            "filename": file.filename,
            "rows_count": len(df),
            "columns_count": len(df.columns),
            "columns": list(df.columns),
            "detected_mappings": mapping_res,
            "preview": preview,
            "reference_columns": list(ref_df.columns) if ref_df is not None else [],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process uploaded file: {str(e)}")


@router.post("/upload_reference")
async def upload_reference(session_id: str = Form(...), file: UploadFile = File(...)):
    """Uploads custom P-Code reference dataset (e.g. OCHA COD-AB)."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        contents = await file.read()
        ref_df = load_dataset(contents)

        session["ref_df"] = ref_df
        session["ref_filename"] = file.filename

        return {
            "success": True,
            "ref_filename": file.filename,
            "reference_rows": len(ref_df),
            "reference_columns": list(ref_df.columns),
            "reference_preview": df_to_json_records(ref_df, 15)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process reference file: {str(e)}")


@router.post("/clean")
async def execute_clean(request: CleanRequest):
    """Runs cleaning pipeline and hierarchical spatial fallback cascade on session dataset."""
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please upload dataset again.")

    raw_df = session["raw_df"]
    ref_df = session.get("ref_df")
    config = request.config or CleaningConfig()
    custom_mapping = request.column_mapping or session.get("mapping", {})

    if request.spatial_mapping:
        config.spatial_reference_mapping.update(request.spatial_mapping)

    try:
        cleaner = LinelistCleaner(config=config)
        df_clean, report = cleaner.clean(raw_df, custom_mapping=custom_mapping, reference_pcode_df=ref_df)

        # Compute epidemiological analytics
        tag_to_col = {v: k for k, v in report.columns_mapped.items()}
        epi = EpiAnalytics(df_clean, tag_to_col)
        indicators = epi.get_summary_indicators()
        epi_curve_daily = epi.get_epi_curve(time_unit="day", stratify_by="case_definition")
        epi_curve_weekly = epi.get_epi_curve(time_unit="week", stratify_by="outcome")
        delays = epi.get_delay_distributions()
        pyramid = epi.get_demographic_pyramid()

        # Extract map points for Leaflet.js
        map_points = []
        if "LATITUDE" in df_clean.columns and "LONGITUDE" in df_clean.columns:
            valid_coords = df_clean[df_clean["LATITUDE"].notna() & df_clean["LONGITUDE"].notna()]
            for idx, r in valid_coords.head(200).iterrows():
                map_points.append({
                    "id": str(r.get("case_id", f"Case {idx+1}")),
                    "lat": float(r["LATITUDE"]),
                    "lng": float(r["LONGITUDE"]),
                    "name": str(r.get("MATCHED_NAME", "")),
                    "pcode": str(r.get("PCODE_ASSIGNED", "")),
                    "match_level": str(r.get("MATCH_LEVEL", "")),
                    "score": float(r.get("MATCH_SCORE", 100.0)),
                    "epi_week": str(r.get("EPI_WEEK", ""))
                })

        session["cleaned_df"] = df_clean
        session["report"] = report
        session["config"] = config

        cleaned_preview = df_to_json_records(df_clean, 100)
        raw_preview = df_to_json_records(raw_df, 100)

        return {
            "success": True,
            "report": report.model_dump(),
            "indicators": indicators,
            "epi_curve_daily": epi_curve_daily,
            "epi_curve_weekly": epi_curve_weekly,
            "delays": delays,
            "pyramid": pyramid,
            "map_points": map_points,
            "cleaned_columns": list(df_clean.columns),
            "cleaned_preview": cleaned_preview,
            "raw_preview": raw_preview,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error cleaning linelist: {str(e)}")


@router.get("/export/excel/{session_id}")
async def export_excel_download(session_id: str):
    """Generates and streams the 3-tab Excel report workbook."""
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Cleaned data not available for this session.")

    df_clean = session["cleaned_df"]
    report = session["report"]
    ref_df = session.get("ref_df")

    buffer = io.BytesIO()
    LinelistCleaner.export_excel(df_clean, report, buffer, reference_df=ref_df)
    buffer.seek(0)

    filename = f"Linelist_Nettoyee_{session.get('filename', 'dataset')}.xlsx"
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/csv/{session_id}")
async def export_csv_download(session_id: str):
    """Generates and streams cleaned CSV."""
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Cleaned data not available for this session.")

    df_clean = session["cleaned_df"]
    csv_str = df_clean.to_csv(index=False)
    filename = f"Linelist_Nettoyee_{session.get('filename', 'dataset')}.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/script/{session_id}")
async def export_script_download(session_id: str):
    """Generates reproducible Python script for this cleaning configuration."""
    session = SESSIONS.get(session_id)
    config = session.get("config", CleaningConfig()) if session else CleaningConfig()
    script_text = LinelistCleaner.generate_reproducible_python_script(config)

    return Response(
        content=script_text,
        media_type="text/x-python",
        headers={"Content-Disposition": "attachment; filename=linelist_spatial_pipeline.py"}
    )
