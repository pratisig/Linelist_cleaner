import pandas as pd
import pytest
from linelist_cleaner.core.age_cleaner import (
    parse_age_string,
    categorize_age,
    create_age_group_labels,
    AgeCleaner,
)


def test_parse_age_string():
    assert parse_age_string("25") == (25.0, "Years")
    assert parse_age_string(25) == (25.0, "Years")
    assert parse_age_string("18 months") == (1.5, "Months")
    assert parse_age_string("6m") == (0.5, "Months")
    assert parse_age_string("14 days") == (0.04, "Days")
    assert parse_age_string("45 ans") == (45.0, "Years")
    assert parse_age_string("NA") == (None, None)
    assert parse_age_string("-5") == (None, None)
    assert parse_age_string("999") == (None, None)


def test_categorize_age():
    breaks = [0, 5, 15, 30, 50, 65, 80]
    labels = create_age_group_labels(breaks)
    assert labels == ["<5", "5-14", "15-29", "30-49", "50-64", "65-79", "80+"]

    assert categorize_age(2.5, breaks, labels) == "<5"
    assert categorize_age(10, breaks, labels) == "5-14"
    assert categorize_age(25, breaks, labels) == "15-29"
    assert categorize_age(70, breaks, labels) == "65-79"
    assert categorize_age(85, breaks, labels) == "80+"
    assert categorize_age(None, breaks, labels) is None


def test_age_cleaner_batch():
    series = pd.Series(["45 yo", "18 mos", "10d", "NA", "invalid", "65 ans"])
    cleaner = AgeCleaner()
    clean_ages, age_groups, stats = cleaner.clean_age_column(series)

    assert clean_ages.iloc[0] == 45.0
    assert age_groups.iloc[0] == "30-49"

    assert clean_ages.iloc[1] == 1.5
    assert age_groups.iloc[1] == "<5"

    assert clean_ages.iloc[2] == 0.03 or clean_ages.iloc[2] == 0.04
    assert age_groups.iloc[2] == "<5"

    assert pd.isna(clean_ages.iloc[3])
    assert pd.isna(clean_ages.iloc[4])
    assert clean_ages.iloc[5] == 65.0
    assert stats["parsed_count"] == 4
