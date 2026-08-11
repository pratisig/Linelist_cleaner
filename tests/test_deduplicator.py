import pandas as pd
import pytest
from linelist_cleaner.core.deduplicator import Deduplicator


def test_exact_deduplication():
    df = pd.DataFrame({
        "case_id": ["C1", "C2", "C1", "C3"],
        "name": ["Alice", "Bob", "Alice", "Charlie"],
        "age": [25, 30, 25, 40]
    })
    tag_to_col = {"case_id": "case_id", "full_name": "name", "age": "age"}

    deduper = Deduplicator(method="exact", action="keep_first")
    groups = deduper.find_duplicates(df, tag_to_col)
    assert len(groups) >= 1

    df_clean, removed = deduper.resolve_duplicates(df, groups)
    assert removed == 1
    assert len(df_clean) == 3


def test_fuzzy_deduplication():
    df = pd.DataFrame({
        "case_id": ["C1", "C2", "C3"],
        "name": ["Johnathan Doe", "John Doe", "Sarah Connor"],
        "sex": ["Male", "Male", "Female"],
        "age": [35, 35, 28],
        "date_onset": ["2023-05-01", "2023-05-02", "2023-06-10"]
    })
    tag_to_col = {
        "case_id": "case_id",
        "full_name": "name",
        "sex": "sex",
        "age": "age",
        "date_onset": "date_onset"
    }

    deduper = Deduplicator(fuzzy_threshold=0.75, method="fuzzy", action="flag")
    groups = deduper.find_duplicates(df, tag_to_col)
    assert len(groups) == 1
    assert groups[0].duplicate_type == "fuzzy"

    df_flagged, _ = deduper.resolve_duplicates(df, groups)
    assert "is_duplicate" in df_flagged.columns
    assert bool(df_flagged["is_duplicate"].iloc[0]) is True
    assert bool(df_flagged["is_duplicate"].iloc[1]) is True
    assert bool(df_flagged["is_duplicate"].iloc[2]) is False
