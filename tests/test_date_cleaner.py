import datetime
import pandas as pd
import pytest
from linelist_cleaner.core.date_cleaner import (
    parse_single_date,
    is_excel_serial_number,
    excel_serial_to_date,
    detect_day_first_preference,
    DateCleaner,
)


def test_parse_single_date_iso():
    s, d, ok = parse_single_date("2023-08-15")
    assert ok is True
    assert s == "2023-08-15"
    assert d == datetime.date(2023, 8, 15)


def test_parse_single_date_dmy():
    s, d, ok = parse_single_date("25/12/2022", day_first=True)
    assert ok is True
    assert s == "2022-12-25"


def test_parse_single_date_mdy():
    s, d, ok = parse_single_date("12/25/2022", day_first=False)
    assert ok is True
    assert s == "2022-12-25"


def test_parse_single_date_french():
    s, d, ok = parse_single_date("14 juillet 2023")
    assert ok is True
    assert s == "2023-07-14"

    s, d, ok = parse_single_date("03 déc. 2022")
    assert ok is True
    assert s == "2022-12-03"


def test_parse_single_date_spanish():
    s, d, ok = parse_single_date("12 de octubre de 2023")
    assert ok is True
    assert s == "2023-10-12"


def test_excel_serial_date():
    assert is_excel_serial_number(44856) is True
    d = excel_serial_to_date(44856)
    assert d == datetime.date(2022, 10, 22)

    s, d_parsed, ok = parse_single_date(44856)
    assert ok is True
    assert s == "2022-10-22"


def test_date_cleaner_batch():
    series = pd.Series([
        "2023-01-01",
        "25/02/2023",
        "15 mars 2023",
        44856,
        "NA",
        "invalid_date_text"
    ])
    cleaner = DateCleaner(output_format="%Y-%m-%d")
    clean_s, stats = cleaner.clean_column(series)

    assert clean_s.iloc[0] == "2023-01-01"
    assert clean_s.iloc[1] == "2023-02-25"
    assert clean_s.iloc[2] == "2023-03-15"
    assert clean_s.iloc[3] == "2022-10-22"
    assert pd.isna(clean_s.iloc[4])
    assert pd.isna(clean_s.iloc[5])
    assert stats["successfully_parsed"] == 4
    assert stats["failed_to_parse"] == 1
