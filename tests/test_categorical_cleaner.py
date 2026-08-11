import pandas as pd
import pytest
from linelist_cleaner.core.categorical_cleaner import (
    standardize_sex_value,
    standardize_case_definition_value,
    standardize_outcome_value,
    standardize_binary_value,
    harmonize_facility_names,
    clean_missing_sentinels_df,
)


def test_standardize_sex_value():
    assert standardize_sex_value("M") == "Male"
    assert standardize_sex_value("homme") == "Male"
    assert standardize_sex_value("1") == "Male"
    assert standardize_sex_value("F") == "Female"
    assert standardize_sex_value("femme") == "Female"
    assert standardize_sex_value("2") == "Female"
    assert standardize_sex_value("Other") == "Other"
    assert standardize_sex_value("unknown") == "Unknown"
    assert standardize_sex_value("NA") is None


def test_standardize_case_definition_value():
    assert standardize_case_definition_value("Confirme") == "Confirmed"
    assert standardize_case_definition_value("PCR+") == "Confirmed"
    assert standardize_case_definition_value("Prob") == "Probable"
    assert standardize_case_definition_value("Suspect") == "Suspect"
    assert standardize_case_definition_value("Non-case") == "Discarded"


def test_standardize_outcome_value():
    assert standardize_outcome_value("DCD") == "Dead"
    assert standardize_outcome_value("Mort") == "Dead"
    assert standardize_outcome_value("Gueri") == "Recovered"
    assert standardize_outcome_value("Sortie") == "Discharged"
    assert standardize_outcome_value("Evade") == "LAMA"
    assert standardize_outcome_value("Vivant") == "Alive"


def test_standardize_binary_value():
    assert standardize_binary_value("Oui") == "Yes"
    assert standardize_binary_value("1") == "Yes"
    assert standardize_binary_value("+") == "Yes"
    assert standardize_binary_value("Non") == "No"
    assert standardize_binary_value("0") == "No"
    assert standardize_binary_value("-") == "No"


def test_harmonize_facility_names():
    series = pd.Series([
        "Hopital General", "Hopital Général", "Hopital General", "St Mary Clinic", "St Marys Clinic"
    ])
    clean_s, mapping = harmonize_facility_names(series, similarity_threshold=80.0)
    assert clean_s.iloc[0] == clean_s.iloc[1]


def test_clean_missing_sentinels_df():
    df = pd.DataFrame({
        "a": ["valid", "NA", "null", "none"],
        "b": ["-99", "999", "missing", "real_val"]
    })
    df_clean, count = clean_missing_sentinels_df(df)
    assert count == 6
    assert df_clean["a"].iloc[0] == "valid"
    assert df_clean["b"].iloc[3] == "real_val"
    assert pd.isna(df_clean["a"].iloc[1])
