"""
FastAPI REST API Routes for Linelist Cleaner and Spatial Cascade Geocoding.
PratiSIG Consulting Services - Dakar, Sénégal.
Auteur : Youssoupha MBODJI (pratisig.consulting@gmail.com)
"""

import io
import re
import json
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel, field_validator
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

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".tsv", ".txt"}
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_session_id(session_id: str) -> str:
    """Validates session ID format to prevent injection attacks."""
    if not session_id or not SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Identifiant de session invalide.")
    return session_id


def validate_uploaded_file(file: UploadFile, contents: bytes) -> None:
    """Validates file extension and size limits."""
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux ({len(contents) / (1024 * 1024):.1f} Mo). La limite est de 50 Mo."
        )
    filename = file.filename or ""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension de fichier non supportée '{ext}'. Formats autorisés : {', '.join(ALLOWED_EXTENSIONS)}"
        )


def sanitize_csv_cell(val: Any) -> Any:
    """Mitigate CSV / Formula injection (DDE) by neutralizing leading formula symbols."""
    if isinstance(val, str) and val.startswith(("=", "+", "-", "@", "\t", "\r")):
        # If it's a negative number or pure number, don't prefix with quote
        try:
            float(val)
            return val
        except ValueError:
            return "'" + val
    return val


def sanitize_dataframe_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Applies formula injection sanitization to string columns in DataFrame."""
    df_copy = df.copy()
    for col in df_copy.columns:
        if pd.api.types.is_object_dtype(df_copy[col]) or pd.api.types.is_string_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].apply(sanitize_csv_cell)
    return df_copy


def df_to_json_records(df: pd.DataFrame, limit: int = 100) -> List[Dict[str, Any]]:
    """Safely converts DataFrame slice to JSON-serializable records with None for NaNs."""
    if df is None or df.empty:
        return []
    sub = df.head(limit).copy()
    sub_obj = sub.astype(object).where(pd.notna(sub), None)
    return sub_obj.to_dict(orient="records")


def get_excel_sheets_if_any(contents: bytes) -> List[str]:
    """Inspects byte content and returns sheet names if Excel (.xlsx, .xls), or empty list if CSV."""
    if not contents:
        return []
    is_xls_binary = contents.startswith(b"\xd0\xcf\x11\xe0")
    is_zip_excel = contents.startswith(b"PK\x03\x04")

    if is_xls_binary:
        try:
            f = pd.ExcelFile(io.BytesIO(contents), engine="xlrd")
            return list(f.sheet_names)
        except Exception:
            try:
                import xlrd
                b = xlrd.open_workbook(file_contents=contents)
                return b.sheet_names()
            except Exception:
                pass
    elif is_zip_excel:
        try:
            f = pd.ExcelFile(io.BytesIO(contents), engine="openpyxl")
            return list(f.sheet_names)
        except Exception:
            pass

    try:
        f = pd.ExcelFile(io.BytesIO(contents))
        return list(f.sheet_names)
    except Exception:
        return []


class CleanRequest(BaseModel):
    session_id: str
    config: Optional[CleaningConfig] = None
    column_mapping: Optional[Dict[str, Optional[str]]] = None
    spatial_mapping: Optional[Dict[str, Optional[str]]] = None
    skiprows: int = 0

    @field_validator("session_id")
    def validate_session(cls, v: str) -> str:
        if not v or not SESSION_ID_PATTERN.match(v):
            raise ValueError("Identifiant de session invalide.")
        return v


@router.get("/health")
async def get_health():
    """V2 Health & version endpoint."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "name": "Linelist Cleaner V2",
        "maintainer": "PratiSIG Consulting Services - Dakar, Sénégal"
    }


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


@router.post("/load_sample")
async def load_sample_dataset(
    sample_type: str = Form("cholera"),
    load_ref: bool = Form(True)
):
    """Loads built-in sample outbreak dataset with OCHA P-Code reference."""
    from linelist_cleaner.datasets import get_sample_dataset
    try:
        # Sanitize sample type
        safe_sample = re.sub(r"[^a-zA-Z0-9_]", "", sample_type).lower()
        df = get_sample_dataset(safe_sample)
        ref_df = get_sample_dataset("pcode_reference") if load_ref else None

        active_session_id = f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        mapping_res = map_linelist_columns(df)
        mapped_dict = {col: m["mapped_tag"] for col, m in mapping_res.items() if m["mapped_tag"]}

        ref_filename = "ocha_pcode_reference_nigeria.csv" if ref_df is not None else None

        SESSIONS[active_session_id] = {
            "raw_df": df,
            "filename": f"sample_{safe_sample}_linelist.csv",
            "mapping": mapped_dict,
            "skiprows": 0,
            "sheet_name": None,
            "ref_df": ref_df,
            "ref_filename": ref_filename
        }

        preview = df_to_json_records(df, 25)
        auto_ref_mapping = auto_detect_reference_mapping(ref_df) if ref_df is not None else {}

        return {
            "success": True,
            "session_id": active_session_id,
            "filename": f"sample_{safe_sample}_linelist.csv",
            "rows_count": len(df),
            "columns_count": len(df.columns),
            "columns": list(df.columns),
            "sheets": [],
            "selected_sheet": None,
            "skiprows": 0,
            "detected_mappings": mapping_res,
            "preview": preview,
            "has_reference": ref_df is not None,
            "ref_filename": ref_filename,
            "reference_rows": len(ref_df) if ref_df is not None else 0,
            "reference_columns": list(ref_df.columns) if ref_df is not None else [],
            "detected_spatial_mapping": auto_ref_mapping
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur chargement exemple : {str(e)}")


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
        validate_uploaded_file(file, contents)
        sheets = get_excel_sheets_if_any(contents)
        df = load_dataset(contents, skiprows=skiprows, sheet_name=sheet_name)

        if df is None or df.empty:
            raise ValueError("Le fichier chargé est vide ou illisible.")

        if session_id:
            validate_session_id(session_id)
        active_session_id = session_id if (session_id and session_id in SESSIONS) else f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        mapping_res = map_linelist_columns(df)
        mapped_dict = {col: m["mapped_tag"] for col, m in mapping_res.items() if m["mapped_tag"]}

        existing_ref = SESSIONS.get(active_session_id, {}).get("ref_df")
        existing_ref_fn = SESSIONS.get(active_session_id, {}).get("ref_filename")

        safe_filename = re.sub(r"[^\w\s\.-]", "_", file.filename or "linelist.csv")

        SESSIONS[active_session_id] = {
            "raw_df": df,
            "filename": safe_filename,
            "mapping": mapped_dict,
            "skiprows": skiprows,
            "sheet_name": sheet_name,
            "ref_df": existing_ref,
            "ref_filename": existing_ref_fn
        }

        preview = df_to_json_records(df, 25)

        return {
            "session_id": active_session_id,
            "filename": safe_filename,
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
    except HTTPException:
        raise
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
        validate_uploaded_file(file, contents)
        sheets = get_excel_sheets_if_any(contents)
        ref_df = load_dataset(contents, skiprows=skiprows, sheet_name=sheet_name)

        if ref_df is None or ref_df.empty:
            raise ValueError("Le fichier de référentiel est vide ou toutes les lignes ont été ignorées.")

        if session_id:
            validate_session_id(session_id)
        active_session_id = session_id if (session_id and session_id in SESSIONS) else f"sess_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}"
        if active_session_id not in SESSIONS:
            SESSIONS[active_session_id] = {
                "raw_df": None,
                "filename": None,
                "mapping": {}
            }

        safe_filename = re.sub(r"[^\w\s\.-]", "_", file.filename or "reference.csv")

        SESSIONS[active_session_id]["ref_df"] = ref_df
        SESSIONS[active_session_id]["ref_filename"] = safe_filename
        SESSIONS[active_session_id]["ref_skiprows"] = skiprows
        SESSIONS[active_session_id]["ref_sheet_name"] = sheet_name

        auto_ref_mapping = auto_detect_reference_mapping(ref_df)

        return {
            "success": True,
            "session_id": active_session_id,
            "ref_filename": safe_filename,
            "reference_rows": len(ref_df),
            "reference_columns": list(ref_df.columns),
            "sheets": sheets,
            "selected_sheet": sheet_name or (sheets[0] if sheets else None),
            "skiprows": skiprows,
            "detected_spatial_mapping": auto_ref_mapping,
            "reference_preview": df_to_json_records(ref_df, 15)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du chargement du référentiel P-Code : {str(e)}")


@router.post("/clean")
async def execute_clean(request: CleanRequest):
    """Runs cleaning pipeline and hierarchical spatial fallback cascade on session dataset."""
    validate_session_id(request.session_id)
    session = SESSIONS.get(request.session_id)
    if not session or session.get("raw_df") is None:
        raise HTTPException(status_code=404, detail="Aucune line list chargée pour cette session. Veuillez charger un fichier.")

    raw_df = session["raw_df"]
    ref_df = session.get("ref_df")
    config = request.config or CleaningConfig()
    raw_mapping = request.column_mapping if request.column_mapping is not None else session.get("mapping", {})
    custom_mapping = {k: v for k, v in raw_mapping.items() if v}

    if request.spatial_mapping:
        clean_spatial_mapping = {k: v for k, v in request.spatial_mapping.items() if v}
        config.spatial_reference_mapping.update(clean_spatial_mapping)

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
        quality_delta = round(report.quality_scores_after.overall_score - report.quality_scores_before.overall_score, 1)

        map_points = []
        if "LATITUDE" in df_clean.columns and "LONGITUDE" in df_clean.columns:
            valid_coords = df_clean[df_clean["LATITUDE"].notna() & df_clean["LONGITUDE"].notna()]
            for idx, r in valid_coords.head(300).iterrows():
                try:
                    lat_v = float(r["LATITUDE"])
                    lng_v = float(r["LONGITUDE"])
                    if -90 <= lat_v <= 90 and -180 <= lng_v <= 180:
                        map_points.append({
                            "id": str(r.get("case_id", f"Cas {idx+1}")),
                            "lat": lat_v,
                            "lng": lng_v,
                            "name": str(r.get("MATCHED_NAME", "")),
                            "pcode": str(r.get("PCODE_ASSIGNED", "")),
                            "match_level": str(r.get("MATCH_LEVEL", "")),
                            "score": float(r.get("MATCH_SCORE", 100.0)),
                            "epi_week": str(r.get("EPI_WEEK", ""))
                        })
                except (ValueError, TypeError):
                    continue

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
        raise HTTPException(status_code=500, detail=f"Erreur lors du nettoyage de la line list : {str(e)}")


@router.get("/export/excel/{session_id}")
async def export_excel_download(session_id: str):
    """Generates and streams the 6-tab Excel report workbook V2."""
    validate_session_id(session_id)
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles pour cette session.")

    df_clean = session["cleaned_df"]
    report = session["report"]
    ref_df = session.get("ref_df")

    buffer = io.BytesIO()
    LinelistCleaner.export_excel(df_clean, report, buffer, reference_df=ref_df)
    buffer.seek(0)

    filename = "LineList_Nettoyee_PCode_PratiSIG_V2.xlsx"
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/geojson/{session_id}")
async def export_geojson_download(session_id: str):
    """V2: Generates and streams cleaned GeoJSON FeatureCollection."""
    validate_session_id(session_id)
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles pour GeoJSON.")
    df_clean = session["cleaned_df"]
    geo = LinelistCleaner.export_geojson(df_clean)
    return Response(
        content=json.dumps(geo, ensure_ascii=False, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": 'attachment; filename="LineList_Geocoded_V2.geojson"'}
    )


@router.get("/analytics/advanced/{session_id}")
async def get_advanced_analytics(session_id: str):
    """V2: Returns advanced epidemiological metrics for a session without re-cleaning."""
    validate_session_id(session_id)
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
        validate_uploaded_file(file, contents)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur validation: {str(e)}")


@router.post("/preview_diff/{session_id}")
async def preview_diff(session_id: str):
    """V2: Returns side-by-side diff of raw vs cleaned preview (first 50 rows)."""
    validate_session_id(session_id)
    session = SESSIONS.get(session_id)
    if not session or "raw_df" not in session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Previews non disponibles (lancer nettoyage d'abord).")
    raw = session["raw_df"].head(50)
    cleaned = session["cleaned_df"].head(50)
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
    """Generates and streams cleaned CSV with CSV injection protection."""
    validate_session_id(session_id)
    session = SESSIONS.get(session_id)
    if not session or "cleaned_df" not in session:
        raise HTTPException(status_code=404, detail="Données nettoyées non disponibles.")

    df_clean = sanitize_dataframe_for_csv(session["cleaned_df"])
    csv_str = df_clean.to_csv(index=False)
    filename = "LineList_Nettoyee_PCode_PratiSIG.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/script/{session_id}")
async def export_script_download(session_id: str):
    """Generates reproducible Python script for this cleaning configuration."""
    validate_session_id(session_id)
    session = SESSIONS.get(session_id)
    config = session.get("config", CleaningConfig()) if session else CleaningConfig()
    script_text = LinelistCleaner.generate_reproducible_python_script(config)

    return Response(
        content=script_text,
        media_type="text/x-python",
        headers={"Content-Disposition": 'attachment; filename="linelist_spatial_pipeline.py"'}
    )
