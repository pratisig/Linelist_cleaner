import pandas as pd
import pytest
from linelist_cleaner.core.column_standardizer import (
    clean_string_identifier,
    standardize_dataframe_columns,
    find_best_epi_tag_for_column,
    map_linelist_columns,
)


def test_clean_string_identifier():
    assert clean_string_identifier("Patient Name") == "patient_name"
    assert clean_string_identifier("Prénom & Nom") == "prenom_nom"
    assert clean_string_identifier("Date de Début (Symptômes)") == "date_de_debut_symptomes"
    assert clean_string_identifier("   age--years   ") == "age_years"
    assert clean_string_identifier("ID_Patient #1") == "id_patient_1"
    assert clean_string_identifier("") == "unnamed_column"


def test_standardize_dataframe_columns():
    df = pd.DataFrame(columns=["Case ID", "Patient Name", "Case ID", "Age (yrs)"])
    clean_df, mapping = standardize_dataframe_columns(df)
    assert clean_df.columns.tolist() == ["case_id", "patient_name", "case_id_1", "age_yrs"]
    assert mapping["Case ID"] in ["case_id", "case_id_1"]


def test_find_best_epi_tag_for_column():
    tag, score = find_best_epi_tag_for_column("date_debut_symptomes")
    assert tag == "date_onset"
    assert score == 1.0

    tag, score = find_best_epi_tag_for_column("genre")
    assert tag == "sex"
    assert score == 1.0

    tag, score = find_best_epi_tag_for_column("hospitalisation")
    assert tag == "hospitalized"
    assert score == 1.0


def test_map_linelist_columns():
    df = pd.DataFrame(columns=[
        "ID_Patient", "Sexe", "Age_Ans", "Date_Debut", "Issue_Clinique", "Unmapped_Field_XYZ"
    ])
    res = map_linelist_columns(df)
    assert res["ID_Patient"]["mapped_tag"] == "case_id"
    assert res["Sexe"]["mapped_tag"] == "sex"
    assert res["Date_Debut"]["mapped_tag"] == "date_onset"
    assert res["Issue_Clinique"]["mapped_tag"] == "outcome"
    assert res["Unmapped_Field_XYZ"]["is_mapped"] is False
