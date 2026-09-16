import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from linelist_cleaner.web.app import app

client = TestClient(app)


def test_api_dictionary():
    response = client.get("/api/dictionary")
    assert response.status_code == 200
    dict_data = response.json()
    assert "case_id" in dict_data
    assert "date_onset" in dict_data


def test_api_upload_excel_linelist_and_reference():
    # 1. Creation d'une line list Excel en memoire
    df_cases = pd.DataFrame({
        "ID_Patient": ["CASE-01", "CASE-02", "CASE-03"],
        "Village": ["Custom House IDP Camp", "Village Inconnu", "Monday Market"],
        "Ward": ["Bolori I", "Bolori II", "Shehuri North"],
        "LGA": ["Maiduguri", "Maiduguri", "Maiduguri"],
        "State": ["Borno", "Borno", "Borno"],
        "Date_Admission": ["12/09/2023", "2023-09-14", "15/09/2023"],
        "Age": ["25 ans", "18 mois", "40"],
        "Sexe": ["M", "F", "Homme"]
    })
    buf_cases = io.BytesIO()
    df_cases.to_excel(buf_cases, index=False, engine="openpyxl")
    buf_cases.seek(0)

    # 2. Upload de la Line List
    files_case = {"file": ("cases_field.xlsx", buf_cases, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res_upload = client.post("/api/upload", files=files_case)
    assert res_upload.status_code == 200
    data_upload = res_upload.json()
    session_id = data_upload["session_id"]
    assert session_id is not None
    assert data_upload["rows_count"] == 3

    # 3. Creation d'un referentiel P-Code Excel en memoire
    df_ref = pd.DataFrame({
        "Admin1_Name": ["Borno", "Borno"],
        "Admin1_Pcode": ["NG008", "NG008"],
        "Admin2_Name": ["Maiduguri", "Maiduguri"],
        "Admin2_Pcode": ["NG008018", "NG008018"],
        "Admin3_Name": ["Bolori I", "Bolori II"],
        "Admin3_Pcode": ["NG008018001", "NG008018002"],
        "Locality_Name": ["Custom House IDP Camp", "El-Miskin Camp"],
        "Locality_Pcode": ["NG008018001001", "NG008018002001"],
        "Latitude": [11.8333, 11.8450],
        "Longitude": [13.1500, 13.1620]
    })
    buf_ref = io.BytesIO()
    df_ref.to_excel(buf_ref, index=False, engine="openpyxl")
    buf_ref.seek(0)

    # 4. Upload du Referentiel P-Code Excel
    files_ref = {"file": ("referentiel_pcode.xlsx", buf_ref, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res_ref = client.post("/api/upload_reference", files=files_ref, data={"session_id": session_id})
    assert res_ref.status_code == 200
    data_ref = res_ref.json()
    assert data_ref["success"] is True
    assert data_ref["reference_rows"] == 2
    assert "detected_spatial_mapping" in data_ref

    # 5. Execution du Nettoyage et de la Cascade Spatiale
    res_clean = client.post("/api/clean", json={"session_id": session_id})
    assert res_clean.status_code == 200
    data_clean = res_clean.json()
    assert data_clean["success"] is True
    assert data_clean["report"]["spatial_summary"]["geocoded_count"] >= 2
    assert "EPI_WEEK" in data_clean["cleaned_columns"]
    assert "PCODE_ASSIGNED" in data_clean["cleaned_columns"]

    # 6. Export du Classeur Excel
    res_xls = client.get(f"/api/export/excel/{session_id}")
    assert res_xls.status_code == 200
    assert len(res_xls.content) > 0


def test_api_upload_csv_file():
    csv_content = b"case_id,sex,age,village\nC1,M,25,Camp A\nC2,F,30,Camp B"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["rows_count"] == 2


def test_api_load_sample():
    response = client.post("/api/load_sample", data={"sample_type": "cholera", "load_ref": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["rows_count"] > 0
    assert data["has_reference"] is True
    session_id = data["session_id"]

    res_clean = client.post("/api/clean", json={"session_id": session_id})
    assert res_clean.status_code == 200
    clean_data = res_clean.json()
    assert clean_data["success"] is True
    assert len(clean_data["cleaned_columns"]) > 0


def test_api_upload_reference_with_partial_columns_and_clean():
    """Ensure uploading a reference with only locality names and None mappings does not fail with 422."""
    csv_cases = b"case_id,patient_age,date_onset,locality\nC1,25,2023-08-01,VillageA\nC2,30,2023-08-02,VillageB\n"
    res_cases = client.post("/api/upload", files={"file": ("cases.csv", io.BytesIO(csv_cases), "text/csv")})
    assert res_cases.status_code == 200
    sess_id = res_cases.json()["session_id"]

    csv_villages = b"Nom_Village,Latitude,Longitude\nVillageA,14.5,-17.2\nVillageB,14.6,-17.3\n"
    res_ref = client.post("/api/upload_reference", files={"file": ("villages.csv", io.BytesIO(csv_villages), "text/csv")}, data={"session_id": sess_id})
    assert res_ref.status_code == 200
    det_map = res_ref.json()["detected_spatial_mapping"]
    assert det_map["locality_name"] == "Nom_Village"

    res_clean = client.post("/api/clean", json={
        "session_id": sess_id,
        "spatial_mapping": det_map
    })
    assert res_clean.status_code == 200
    clean_data = res_clean.json()
    assert clean_data["success"] is True
    assert clean_data["report"]["spatial_summary"]["geocoded_count"] == 2
    assert len(clean_data["map_points"]) == 2
