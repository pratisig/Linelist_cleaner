import io
import pytest
from fastapi.testclient import TestClient
from linelist_cleaner.web.app import app

client = TestClient(app)


def test_api_samples():
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 4


def test_api_dictionary():
    response = client.get("/api/dictionary")
    assert response.status_code == 200
    dict_data = response.json()
    assert "case_id" in dict_data
    assert "date_onset" in dict_data


def test_api_load_sample_and_clean():
    # 1. Load sample
    res_load = client.post("/api/load_sample", data={"sample_id": "cholera"})
    assert res_load.status_code == 200
    data_load = res_load.json()
    session_id = data_load["session_id"]
    assert session_id is not None

    # 2. Clean
    res_clean = client.post("/api/clean", json={"session_id": session_id})
    assert res_clean.status_code == 200
    data_clean = res_clean.json()
    assert data_clean["success"] is True
    assert "report" in data_clean
    assert "indicators" in data_clean

    # 3. Export CSV
    res_csv = client.get(f"/api/export/csv/{session_id}")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    # 4. Export Excel
    res_xls = client.get(f"/api/export/excel/{session_id}")
    assert res_xls.status_code == 200

    # 5. Export Script
    res_scr = client.get(f"/api/export/script/{session_id}")
    assert res_scr.status_code == 200


def test_api_upload_file():
    csv_content = b"case_id,sex,age\nC1,M,25\nC2,F,30"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["rows_count"] == 2
