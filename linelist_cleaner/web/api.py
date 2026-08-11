"""
FastAPI REST API Routes for Linelist Cleaner and Spatial Cascade Geocoding.
PratiSIG Consulting Services - Dakar, Sénégal.
Auteur : Youssoupha MBODJI (pratisig.consulting@gmail.com)
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
from linelist_cleaner.core.spatial_cascade import auto_detect_reference_mapping
from linelist_cleaner.core.epi_analytics import EpiAnalytics

router = APIRouter(prefix="/api")

SESSIONS: Dict[str, Dict[str, Any]] = {}


def df_to_json_records(df: pd.DataFrame, limit: int = 100) -> List[Dict[str, Any]]:
    """Safely converts DataFrame slice to JSON-serializable records with None for NaNs."""
    if df is None or df.empty:
        return []
    sub = df.head(limit).copy()
    sub_obj = sub.astype(object).where(pd.notna(sub), None)
    return sub_obj.to_dict(orient="records")


class CleanRequest(BaseModel):
    session_id: str
    config: Optional[CleaningConfig] = None
    column_mapping: Optional[Dict[str, str]] = None
    spatial_mapping: Optional[Dict[str, str]] = None


@router.get("/dictionary")
async def get_dictionary():
    """Returns canonical epidemiological variable dictionary."""
    return CANONICAL_TAGS


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """Uploads raw line list CSV or Excel file."""
    try:
        contents = await file.read()
        df = load_dataset(contents)

        active_session_id = session_id if (session_id and session_id in SESSIONS) else f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        mapping_res = map_linelist_columns(df)
        mapped_dict = {col: m["mapped_tag"] for col, m in mapping_res.items() if m["mapped_tag"]}

        existing_ref = SESSIONS.get(active_session_id, {}).get("ref_df")
        existing_ref_fn = SESSIONS.get(active_session_id, {}).get("ref_filename")

        SESSIONS[active_session_id] = {
            "raw_df": df,
            "filename": file.filename,
            "mapping": mapped_dict,
            "ref_df": existing_ref,
            "ref_filename": existing_ref_fn
        }

        preview = df_to_json_records(df, 25)

        return {
            "session_id": active_session_id,
            "filename": file.filename,
            "rows_count": len(df),
            "columns_count": len(df.columns),
            "columns": list(df.columns),
            "detected_mappings": mapping_res,
            "preview": preview,
            "has_reference": existing_ref is not None,
            "ref_filename": existing_ref_fn,
            "reference_columns": list(existing_ref.columns) if existing_ref is not None else [],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du traitement du fichier line list : {str(e)}")


@router.post("/upload_reference")
async def upload_reference(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """
    Uploads custom P-Code reference dataset (Excel .xlsx/.xls or CSV) independently.
    Automatically detects administrative columns and P-Codes.
    """
    try:
        contents = await file.read()
        ref_df = load_dataset(contents)

        if ref_df.empty:
            raise ValueError("Le fichier de référentiel est vide.")

        active_session_id = session_id if (session_id and session_id in SESSIONS) else f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        if active_session_id not in SESSIONS:
            SESSIONS[active_session_id] = {
                "raw_df": None,
                "filename": None,
                "mapping": {}
            }

        SESSIONS[active_session_id]["ref_df"] = ref_df
        SESSIONS[active_session_id]["ref_filename"] = file.filename

        auto_ref_mapping = auto_detect_reference_mapping(ref_df)

        return {
            "success": True,
            "session_id": active_session_id,
            "ref_filename": file.filename,
            "reference_rows": len(ref_df),
            "reference_columns": list(ref_df.columns),
            "detected_spatial_mapping": auto_ref_mapping,
            "reference_preview": df_to_json_records(ref_df, 15)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du chargement du référentiel P-Code : {str(e)}")


@router.post("/clean")
async def execute_clean(request: CleanRequest):
    """Runs cleaning pipeline and hierarchical spatial fallback cascade on session dataset."""
    session = SESSIONS.get(request.session_id)
    if not session or session.get("raw_df") is None:
        raise HTTPException(status_code=404, detail="Aucune line list chargée pour cette session. Veuillez charger un fichier.")

    raw_df = session["raw_df"]
    ref_df = session.get("ref_df")
    config = request.config or CleaningConfig()
    custom_mapping = request.column_mapping or session.get("mapping", {})

    if request.spatial_mapping:
        config.spatial_reference_mapping.update(request.spatial_mapping)

    try:
        cleaner = LinelistCleaner(config=config)
        df_clean, report = cleaner.clean(raw_df, custom_mapping=custom_mapping, reference_pcode_df=ref_df)

        tag_to_col = {v: k for k, v in report.columns_mapped.items()}
        epi = EpiAnalytics(df_clean, tag_to_col)
        indicators = epi.get_summary_indicators()
        epi_curve_daily = epi.get_epi_curve(time_unit="day", stratify_by="case_definition")
        epi_curve_weekly = epi.get_epi_curve(time_unit="week", stratify_by="outcome")
        delays = epi.get_delay_distributions()
        pyramid = epi.get_demographic_pyramid()

        map_points = []
        if "LATITUDE" in df_clean.columns and "LONGITUDE" in df_clean.columns:
            valid_coords = df_clean[df_clean["LATITUDE"].notna() & df_clean["LONGITUDE"].notna()]
            for idx, r in valid_coords.head(300).iterrows():
                map_points.append({
                    "id": str(r.get("case_id", f"Cas {idx+1}")),
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
            "has_reference": ref_df is not None and not ref_df.empty,
            "ref_filename": session.get("ref_filename"),
            "reference_columns": list(ref_df.columns) if ref_df is not None else [],
            "cleaned_columns": list(df_clean.columns),
            "cleaned_preview": cleaned_preview,
            "raw_preview": raw_preview,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors du nettoyage de la line list : {str(e)}")


@router.get("/export/excel/{session_id}")
async def export_excel_download(session_id: str):
    """Generates and streams the 3-tab Excel report workbook."""
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles pour cette session.")

    df_clean = session["cleaned_df"]
    report = session["report"]
    ref_df = session.get("ref_df")

    buffer = io.BytesIO()
    LinelistCleaner.export_excel(df_clean, report, buffer, reference_df=ref_df)
    buffer.seek(0)

    filename = f"LineList_Nettoyee_PCode_PratiSIG.xlsx"
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
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles.")

    df_clean = session["cleaned_df"]
    csv_str = df_clean.to_csv(index=False)
    filename = f"LineList_Nettoyee_PCode_PratiSIG.csv"

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
