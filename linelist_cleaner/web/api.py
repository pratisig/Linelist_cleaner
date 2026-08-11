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
from linelist_cleaner.core.coordinate_cleaner import clean_coordinate_columns
from linelist_cleaner.core.phone_cleaner import clean_phone_column

router = APIRouter(prefix="/api")

SESSIONS: Dict[str, Dict[str, Any]] = {}


def df_to_json_records(df: pd.DataFrame, limit: int = 100) -> List[Dict[str, Any]]:
    """Safely converts DataFrame slice to JSON-serializable records with None for NaNs."""
    if df is None or df.empty:
        return []
    sub = df.head(limit).copy()
    sub_obj = sub.astype(object).where(pd.notna(sub), None)
    return sub_obj.to_dict(orient="records")


def get_excel_sheets_if_any(contents: bytes) -> List[str]:
    """Inspects byte content and returns sheet names if Excel, or empty list if CSV."""
    try:
        f = pd.ExcelFile(io.BytesIO(contents), engine="openpyxl")
        return list(f.sheet_names)
    except Exception:
        return []


class CleanRequest(BaseModel):
    session_id: str
    config: Optional[CleaningConfig] = None
    column_mapping: Optional[Dict[str, str]] = None
    spatial_mapping: Optional[Dict[str, str]] = None
    skiprows: int = 0


@router.get("/health")
async def get_health():
    """V2 Health & version endpoint."""
    return {"status": "ok", "version": "2.0.0", "name": "Linelist Cleaner V2", "maintainer": "PratiSIG Consulting Services"}

@router.get("/dictionary")
async def get_dictionary():
    """Returns canonical epidemiological variable dictionary."""
    return CANONICAL_TAGS

@router.get("/config/presets")
async def get_presets():
    """V2: List available disease presets and their defaults."""
    return {
        "presets": {
            "cholera": {"age_group_breaks": [0, 5, 15, 30, 50, 65, 80], "spatial_similarity_threshold": 78, "description": "Choléra / AWD - foyers urbains"},
            "measles": {"age_group_breaks": [0, 1, 5, 10, 15, 30, 50], "spatial_similarity_threshold": 80, "description": "Rougeole - sensibilité enfants <5 ans"},
            "ebola": {"age_group_breaks": [0, 5, 15, 30, 50, 65, 80], "spatial_similarity_threshold": 85, "description": "Ebola - haute précision géocodage"},
            "covid19": {"age_group_breaks": [0, 10, 20, 30, 40, 50, 60, 70, 80], "spatial_similarity_threshold": 80, "description": "COVID-19 - pyramide large"},
            "generic": {"age_group_breaks": [0, 5, 15, 30, 50, 65, 80], "spatial_similarity_threshold": 80, "description": "Générique"}
        }
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    skiprows: int = Form(0),
    sheet_name: Optional[str] = Form(None)
):
    """Uploads raw line list CSV or Excel file with optional header offset (skiprows) and sheet selection."""
    try:
        contents = await file.read()
        sheets = get_excel_sheets_if_any(contents)
        df = load_dataset(contents, skiprows=skiprows, sheet_name=sheet_name)

        active_session_id = session_id if (session_id and session_id in SESSIONS) else f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        mapping_res = map_linelist_columns(df)
        mapped_dict = {col: m["mapped_tag"] for col, m in mapping_res.items() if m["mapped_tag"]}

        existing_ref = SESSIONS.get(active_session_id, {}).get("ref_df")
        existing_ref_fn = SESSIONS.get(active_session_id, {}).get("ref_filename")

        SESSIONS[active_session_id] = {
            "raw_df": df,
            "filename": file.filename,
            "mapping": mapped_dict,
            "skiprows": skiprows,
            "sheet_name": sheet_name,
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
            "sheets": sheets,
            "selected_sheet": sheet_name or (sheets[0] if sheets else None),
            "skiprows": skiprows,
            "detected_mappings": mapping_res,
            "preview": preview,
            "has_reference": existing_ref is not None,
            "ref_filename": existing_ref_fn,
            "reference_columns": list(existing_ref.columns) if existing_ref is not None else [],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du traitement du fichier line list : {str(e)}")


@router.post("/upload_reference")
async def upload_reference(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    skiprows: int = Form(0),
    sheet_name: Optional[str] = Form(None)
):
    """
    Uploads custom P-Code reference dataset (Excel .xlsx/.xls or CSV) independently.
    Supports multi-sheet selection and skipping title header lines.
    """
    try:
        contents = await file.read()
        sheets = get_excel_sheets_if_any(contents)
        ref_df = load_dataset(contents, skiprows=skiprows, sheet_name=sheet_name)

        if ref_df.empty:
            raise ValueError("Le fichier de référentiel est vide ou toutes les lignes ont été ignorées.")

        active_session_id = session_id if (session_id and session_id in SESSIONS) else f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        if active_session_id not in SESSIONS:
            SESSIONS[active_session_id] = {
                "raw_df": None,
                "filename": None,
                "mapping": {}
            }

        SESSIONS[active_session_id]["ref_df"] = ref_df
        SESSIONS[active_session_id]["ref_filename"] = file.filename
        SESSIONS[active_session_id]["ref_skiprows"] = skiprows
        SESSIONS[active_session_id]["ref_sheet_name"] = sheet_name

        auto_ref_mapping = auto_detect_reference_mapping(ref_df)

        return {
            "success": True,
            "session_id": active_session_id,
            "ref_filename": file.filename,
            "reference_rows": len(ref_df),
            "reference_columns": list(ref_df.columns),
            "sheets": sheets,
            "selected_sheet": sheet_name or (sheets[0] if sheets else None),
            "skiprows": skiprows,
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
        df_clean, report = cleaner.clean(
            raw_df,
            custom_mapping=custom_mapping,
            reference_pcode_df=ref_df,
            skiprows=0
        )

        tag_to_col = {v: k for k, v in report.columns_mapped.items()}
        epi = EpiAnalytics(df_clean, tag_to_col)
        indicators = epi.get_summary_indicators()
        epi_curve_daily = epi.get_epi_curve(time_unit="day", stratify_by="case_definition")
        epi_curve_weekly = epi.get_epi_curve(time_unit="week", stratify_by="outcome")
        delays = epi.get_delay_distributions()
        pyramid = epi.get_demographic_pyramid()
        advanced = epi.get_advanced_metrics()
        # V2 diff stats: before/after quality
        quality_delta = round(report.quality_scores_after.overall_score - report.quality_scores_before.overall_score, 1)

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
            "advanced_metrics": advanced,
            "quality_delta": quality_delta,
            "outbreak_alerts": report.outbreak_alerts,
            "incidence_trend": report.incidence_trend,
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
    """Generates and streams the 6-tab Excel report workbook V2."""
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles pour cette session.")

    df_clean = session["cleaned_df"]
    report = session["report"]
    ref_df = session.get("ref_df")

    buffer = io.BytesIO()
    LinelistCleaner.export_excel(df_clean, report, buffer, reference_df=ref_df)
    buffer.seek(0)

    filename = f"LineList_Nettoyee_PCode_PratiSIG_V2.xlsx"
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/geojson/{session_id}")
async def export_geojson_download(session_id: str):
    """V2: Generates and streams cleaned GeoJSON FeatureCollection."""
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles pour GeoJSON.")
    df_clean = session["cleaned_df"]
    # Build geojson
    geo = LinelistCleaner.export_geojson(df_clean)
    import json as _json
    return Response(
        content=_json.dumps(geo, ensure_ascii=False, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename=LineList_Geocoded_V2.geojson"}
    )

@router.get("/analytics/advanced/{session_id}")
async def get_advanced_analytics(session_id: str):
    """V2: Returns advanced epidemiological metrics for a session without re-cleaning."""
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles.")
    df_clean = session["cleaned_df"]
    report = session["report"]
    tag_to_col = {v: k for k, v in report.columns_mapped.items()}
    epi = EpiAnalytics(df_clean, tag_to_col)
    return {
        "advanced_metrics": epi.get_advanced_metrics(),
        "delays": epi.get_delay_distributions(),
        "pyramid": epi.get_demographic_pyramid(),
        "outbreak_alerts": getattr(report, "outbreak_alerts", []),
        "incidence_trend": getattr(report, "incidence_trend", None),
        "epi_curve_weekly": epi.get_epi_curve(time_unit="week", stratify_by="outcome"),
    }

@router.post("/validate")
async def validate_dataset(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """V2: Quick validation without full cleaning (profile + issues preview)."""
    try:
        contents = await file.read()
        df = load_dataset(contents)
        from linelist_cleaner.core.column_standardizer import map_linelist_columns as _map
        from linelist_cleaner.core.logic_validator import LogicValidator
        from linelist_cleaner.core.deduplicator import Deduplicator as _Dup
        from linelist_cleaner.core.auditor import DataQualityAuditor as _Aud
        m = _map(df)
        tag_to_col = {v["mapped_tag"]: k for k, v in m.items() if v["mapped_tag"]}
        validator = LogicValidator()
        issues = validator.validate(df, tag_to_col)
        dups = _Dup().find_duplicates(df, tag_to_col)
        qs = _Aud.calculate_quality_scores(df, issues, dups, tag_to_col)
        profiles = _Aud.profile_columns(df, tag_to_col, issues)
        return {
            "rows": len(df),
            "columns": list(df.columns),
            "detected_mappings": m,
            "quality_scores": qs.model_dump(),
            "issues_count": len(issues),
            "issues_by_severity": {k: sum(1 for i in issues if i.severity==k) for k in ["ERROR","WARNING","INFO"]},
            "duplicate_groups": len(dups),
            "profiles": {k: v.model_dump() for k, v in profiles.items()},
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur validation: {str(e)}")

@router.post("/preview_diff/{session_id}")
async def preview_diff(session_id: str):
    """V2: Returns side-by-side diff of raw vs cleaned preview (first 50 rows)."""
    session = SESSIONS.get(session_id)
    if not session or "raw_df" not in session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Previews non disponibles (lancer nettoyage d'abord).")
    raw = session["raw_df"].head(50)
    cleaned = session["cleaned_df"].head(50)
    # Build column diff
    added_cols = [c for c in cleaned.columns if c not in raw.columns]
    return {
        "raw_columns": list(raw.columns),
        "cleaned_columns": list(cleaned.columns),
        "added_columns": added_cols,
        "raw_preview": df_to_json_records(raw, 50),
        "cleaned_preview": df_to_json_records(cleaned, 50),
    }


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
