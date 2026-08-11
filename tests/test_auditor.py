import io
import pandas as pd
import pytest
from linelist_cleaner.core.auditor import DataQualityAuditor
from linelist_cleaner.schemas.models import ValidationIssue, DuplicateGroup, CleaningReport, DataQualityScores


def test_calculate_quality_scores():
    df = pd.DataFrame({
        "case_id": ["C1", "C2", "C3", "C4"],
        "sex": ["Male", "Female", "Male", "Female"],
        "age": [20, 30, 40, 50],
        "date_onset": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "outcome": ["Recovered", "Dead", "Recovered", "Recovered"],
        "case_definition": ["Confirmed", "Probable", "Confirmed", "Suspect"]
    })
    tag_to_col = {
        "case_id": "case_id",
        "sex": "sex",
        "age": "age",
        "date_onset": "date_onset",
        "outcome": "outcome",
        "case_definition": "case_definition"
    }

    scores = DataQualityAuditor.calculate_quality_scores(df, [], [], tag_to_col)
    assert scores.overall_score == 100.0
    assert scores.grade == "A"
    assert scores.completeness_score == 100.0


def test_export_excel_workbook():
    df = pd.DataFrame({"case_id": ["C1", "C2"], "age": [25, 30]})
    qs = DataQualityScores(
        overall_score=95.0,
        grade="A",
        completeness_score=95.0,
        chronology_score=100.0,
        validity_score=95.0,
        uniqueness_score=100.0
    )
    report = CleaningReport(
        original_shape=(2, 2),
        cleaned_shape=(2, 2),
        quality_scores_before=qs,
        quality_scores_after=qs,
        columns_mapped={"case_id": "case_id", "age": "age"},
    )
    buf = io.BytesIO()
    DataQualityAuditor.export_excel_audit_workbook(df, report, buf)
    assert buf.tell() > 0
