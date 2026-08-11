import pandas as pd
import pytest
from linelist_cleaner.core.logic_validator import LogicValidator


def test_logic_validator_chronology():
    df = pd.DataFrame({
        "case_id": ["C1", "C2", "C3"],
        "date_onset": ["2023-01-10", "2023-01-15", "2023-01-10"],
        "date_consultation": ["2023-01-05", "2023-01-16", "2023-01-12"],  # C1 has consult BEFORE onset!
        "date_admission": ["2023-01-12", "2023-01-17", "2023-01-14"],
        "date_discharge": ["2023-01-18", "2023-01-10", "2023-01-20"],      # C2 has discharge BEFORE admit!
    })

    tag_to_col = {
        "case_id": "case_id",
        "date_onset": "date_onset",
        "date_consultation": "date_consultation",
        "date_admission": "date_admission",
        "date_discharge": "date_discharge",
    }

    validator = LogicValidator()
    issues = validator.validate(df, tag_to_col)

    types = [i.issue_type for i in issues]
    assert "DATE_CHRONOLOGY" in types
    
    # Check row indices
    chrono_rows = [i.row_idx for i in issues if i.issue_type == "DATE_CHRONOLOGY"]
    assert 1 in chrono_rows  # C1
    assert 2 in chrono_rows  # C2


def test_logic_validator_demographics_and_clinical():
    df = pd.DataFrame({
        "case_id": ["C1", "C2"],
        "age": [-5, 145],
        "sex": ["Male", "Female"],
        "pregnant": ["Yes", "No"],
        "outcome": ["Dead", "Alive"],
        "date_death": [None, "2023-01-20"]
    })

    tag_to_col = {
        "case_id": "case_id",
        "age": "age",
        "sex": "sex",
        "pregnant": "pregnant",
        "outcome": "outcome",
        "date_death": "date_death"
    }

    validator = LogicValidator()
    issues = validator.validate(df, tag_to_col)

    messages = [i.message for i in issues]
    assert any("Negative age" in m for m in messages)
    assert any("Implausibly high age" in m for m in messages)
    assert any("Pregnancy recorded as 'Yes' for a Male" in m for m in messages)
