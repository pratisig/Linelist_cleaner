import datetime
import pandas as pd
import pytest
from linelist_cleaner.core.epi_week import (
    calculate_who_epi_week,
    parse_and_compute_epi_week,
    EpiWeekProcessor,
)


def test_calculate_who_epi_week():
    # 2023-01-05 (Thursday) -> 2023-W01
    y, w, s = calculate_who_epi_week(datetime.date(2023, 1, 5))
    assert y == 2023
    assert w == 1
    assert s == "2023-W01"

    # 2023-08-15 -> 2023-W33
    y, w, s = calculate_who_epi_week(datetime.date(2023, 8, 15))
    assert y == 2023
    assert w == 33
    assert s == "2023-W33"


def test_parse_and_compute_epi_week():
    d_clean, epi_w, epi_wn, epi_y = parse_and_compute_epi_week("15/08/2023", day_first=True)
    assert d_clean == "2023-08-15"
    assert epi_w == "2023-W33"
    assert epi_wn == 33
    assert epi_y == 2023

    # Invalid date handled without crash
    d_clean, epi_w, epi_wn, epi_y = parse_and_compute_epi_week("not_a_date")
    assert d_clean is None
    assert epi_w is None


def test_epi_week_processor_batch():
    series = pd.Series(["2023-08-15", "12/09/2023", "45180", "NA", "invalid"])
    proc = EpiWeekProcessor(day_first=True)
    clean_d, epi_w, epi_wn, epi_y = proc.process_series(series)

    assert clean_d.iloc[0] == "2023-08-15"
    assert epi_w.iloc[0] == "2023-W33"
    assert epi_wn.iloc[0] == 33

    assert clean_d.iloc[1] == "2023-09-12"
    assert pd.isna(clean_d.iloc[3])
    assert pd.isna(epi_w.iloc[3])
