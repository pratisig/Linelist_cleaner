"""
Comprehensive Security, Stress & Edge-Case Test Suite for Linelist Cleaner V2.
PratiSIG Consulting Services - Dakar, Sénégal.
"""

import io
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from linelist_cleaner.web.app import app
from linelist_cleaner import LinelistCleaner, CleaningConfig
from linelist_cleaner.datasets import get_sample_dataset
from linelist_cleaner.web.api import sanitize_csv_cell, sanitize_dataframe_for_csv

client = TestClient(app)


# ============================================================================
# 1. SECURITY TESTS
# ============================================================================

def test_security_csv_injection_sanitization():
    """Ensure formula injection triggers (=, +, -, @, \t, \r) are properly neutralized."""
    assert sanitize_csv_cell("=CMD|' /C calc'!A0") == "'=CMD|' /C calc'!A0"
    assert sanitize_csv_cell("@SUM(1+1)") == "'@SUM(1+1)"
    assert sanitize_csv_cell("+12345") == "+12345"  # Pure numbers remain numeric
    assert sanitize_csv_cell("-12.34") == "-12.34"  # Negative numbers remain numeric
    assert sanitize_csv_cell("-2+3*cmd") == "'-2+3*cmd"
    assert sanitize_csv_cell("\tmalicious_tab") == "'\tmalicious_tab"
    assert sanitize_csv_cell("Normal Text") == "Normal Text"

    df_test = pd.DataFrame({
        "Patient": ["=1+1", "Normal", "@exploit"],
        "Age": [25, 30, 45],
        "City": ["Dakar", "+malicious_func", "Thiès"]
    })
    sanitized = sanitize_dataframe_for_csv(df_test)
    assert sanitized["Patient"].iloc[0] == "'=1+1"
    assert sanitized["Patient"].iloc[1] == "Normal"
    assert sanitized["Patient"].iloc[2] == "'@exploit"
    assert sanitized["City"].iloc[1] == "'+malicious_func"


def test_security_invalid_session_id():
    """Ensure malicious session IDs (path traversal, script injection) are rejected."""
    bad_sessions = [
        "../../etc/passwd",
        "<script>alert(1)</script>",
        "session;DROP TABLE;",
        "sess with spaces",
        "sess/../../secret"
    ]
    for bad_id in bad_sessions:
        res = client.get(f"/api/export/excel/{bad_id}")
        assert res.status_code in [400, 404]

        res_clean = client.post("/api/clean", json={"session_id": bad_id})
        assert res_clean.status_code in [400, 404, 422]


def test_security_unsupported_file_extension():
    """Ensure executable or dangerous file extensions are rejected."""
    dangerous_content = b"fake binary payload"
    files = {"file": ("malicious.exe", io.BytesIO(dangerous_content), "application/x-msdownload")}
    res = client.post("/api/upload", files=files)
    assert res.status_code == 400
    assert "non supportée" in res.json().get("detail", "")


def test_security_empty_upload():
    """Ensure empty files are handled gracefully without 500 crashes."""
    empty_content = b""
    files = {"file": ("empty.csv", io.BytesIO(empty_content), "text/csv")}
    res = client.post("/api/upload", files=files)
    assert res.status_code == 400


def test_security_xss_payloads_in_data():
    """Ensure XSS payloads in case data do not crash backend and are preserved safely."""
    xss_df = pd.DataFrame({
        "case_id": ["<script>alert(1)</script>", "<b>Case 2</b>"],
        "patient_name": ["<img src=x onerror=alert(1)>", "John Doe"],
        "village": ["<svg onload=alert(1)>", "Dakar"],
        "age": ["25", "30"],
        "sex": ["M", "F"],
        "date_onset": ["2023-08-01", "2023-08-02"]
    })
    buf = io.BytesIO()
    xss_df.to_csv(buf, index=False)
    buf.seek(0)

    res_upload = client.post("/api/upload", files={"file": ("xss_test.csv", buf, "text/csv")})
    assert res_upload.status_code == 200
    sess_id = res_upload.json()["session_id"]

    res_clean = client.post("/api/clean", json={"session_id": sess_id})
    assert res_clean.status_code == 200
    data = res_clean.json()
    assert data["success"] is True


# ============================================================================
# 2. STRESS & EDGE CASES
# ============================================================================

def test_stress_all_nan_dataset():
    """Dataset with completely empty / NaN values across all rows and columns."""
    nan_df = pd.DataFrame({
        "id": [None, np.nan, ""],
        "date": [None, np.nan, ""],
        "village": [None, np.nan, ""],
        "age": [None, np.nan, ""],
        "sex": [None, np.nan, ""]
    })
    cleaner = LinelistCleaner()
    cleaned_df, report = cleaner.clean(nan_df)
    assert cleaned_df is not None
    assert len(cleaned_df) == 3


def test_stress_single_row_single_column():
    """Dataset with 1 column and 1 row."""
    small_df = pd.DataFrame({"only_col": ["val"]})
    cleaner = LinelistCleaner()
    cleaned_df, report = cleaner.clean(small_df)
    assert len(cleaned_df) == 1
    assert report is not None


def test_stress_corrupted_dates():
    """Dates with bizarre, invalid or extreme values."""
    date_df = pd.DataFrame({
        "case_id": ["C1", "C2", "C3", "C4", "C5", "C6"],
        "date_admission": ["99/99/9999", "1800-01-01", "2099-12-31", "not_a_date", "45150", "2023-08-15"]
    })
    cleaner = LinelistCleaner(CleaningConfig(standardize_dates=True, compute_epi_weeks=True))
    cleaned_df, report = cleaner.clean(date_df)
    assert "EPI_WEEK" in cleaned_df.columns
    # 2023-08-15 and 45150 (Excel serial) should be parsed
    assert cleaned_df["EPI_WEEK"].notna().sum() >= 2


def test_stress_inverted_and_out_of_bound_coordinates():
    """Coordinates with swapped lat/lon and out of range values."""
    geo_df = pd.DataFrame({
        "case_id": ["C1", "C2", "C3"],
        # Latitude swapped with longitude (e.g. lat=13.15, lon=11.83 in Nigeria)
        "latitude": [13.15, 95.0, "invalid"],
        "longitude": [11.83, 200.0, "text"]
    })
    cleaner = LinelistCleaner(CleaningConfig(clean_coordinates=True))
    cleaned_df, report = cleaner.clean(geo_df)
    assert cleaned_df is not None
    geojson = cleaner.export_geojson(cleaned_df)
    assert geojson["type"] == "FeatureCollection"


def test_stress_latin1_and_xls_binary_signatures():
    """Ensure files starting with 0xd0 (Excel .xls or Latin-1) parse without utf-8 decoding crash."""
    # 1. Latin-1 text file starting with byte 0xd0 (Ð)
    latin1_data = b"\xd0_CODE;ADMIN1;ADMIN2\nNG01;Borno;Maiduguri\nNG02;Yobe;Damaturu\n"
    df_lat = LinelistCleaner().clean(latin1_data)[0]
    assert df_lat is not None
    assert len(df_lat) == 2

    # 2. Upload via API
    res = client.post("/api/upload_reference", files={"file": ("reference.csv", io.BytesIO(latin1_data), "text/csv")})
    assert res.status_code == 200
    assert res.json()["reference_rows"] == 2

    # 3. Comma-separated with Latin-1 accents
    accent_data = "PCode,Région,Localité\nSN01,Dakar,Médina\nSN02,Saint-Louis,Podor\n".encode("latin1")
    res_acc = client.post("/api/upload_reference", files={"file": ("ref_fr.csv", io.BytesIO(accent_data), "text/csv")})
    assert res_acc.status_code == 200
    assert res_acc.json()["reference_rows"] == 2


def test_stress_unicode_and_special_characters():
    """Handles accents, Wolof, Arabic and French special characters cleanly."""
    unicode_df = pd.DataFrame({
        "case_id": ["CAS-001", "CAS-002", "CAS-003", "CAS-004"],
        "nom": ["Ousmane N'Diaye", "Moussa Sène", "Fatou Thiam-Gaye", "مستشفى داكار"],
        "commune": ["Dakar-Plateau", "Grand-Dakar", "Kaolack/Médina", "Saint-Louis"],
        "statut": ["Guéri", "Décédé", "En cours", "Transféré"]
    })
    cleaner = LinelistCleaner()
    cleaned_df, report = cleaner.clean(unicode_df)
    assert len(cleaned_df) == 4
    assert report.quality_scores_after.overall_score >= 0


def test_all_sample_datasets_end_to_end():
    """Verify all built-in sample datasets (cholera, measles, covid19, ebola, borno) process cleanly."""
    samples = ["cholera", "measles", "covid19", "ebola", "borno"]
    ref_df = get_sample_dataset("pcode_reference")

    for sample_name in samples:
        df = get_sample_dataset(sample_name)
        assert len(df) > 0

        cleaner = LinelistCleaner(CleaningConfig(enable_spatial_cascade=True))
        cleaned_df, report = cleaner.clean(df, reference_pcode_df=ref_df)

        assert cleaned_df is not None
        assert len(cleaned_df) > 0
        assert report.cleaned_shape[0] == len(cleaned_df)
        assert report.quality_scores_after.overall_score > 0

        # Test GeoJSON export
        geo = LinelistCleaner.export_geojson(cleaned_df)
        assert geo["type"] == "FeatureCollection"

        # Test Excel export
        buf = io.BytesIO()
        LinelistCleaner.export_excel(cleaned_df, report, buf, reference_df=ref_df)
        assert buf.getvalue() is not None
        assert len(buf.getvalue()) > 0
