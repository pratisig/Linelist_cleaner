"""
Epidemiological Week (WHO / CDC / ISO Standard) Normalization and Calculation Engine.
"""

import datetime
from typing import Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

from linelist_cleaner.core.date_cleaner import parse_single_date


def calculate_who_epi_week(d: datetime.date) -> Tuple[int, int, str]:
    """
    Computes the WHO Epidemiological Week and Year for a given date.
    WHO / ISO 8601 standard:
    - Week 1 is the week containing the first Thursday of the year.
    Returns: (epi_year, epi_week_num, epi_week_str) e.g. (2023, 42, "2023-W42")
    """
    iso_year, iso_week, _ = d.isocalendar()
    epi_week_str = f"{iso_year}-W{iso_week:02d}"
    return int(iso_year), int(iso_week), epi_week_str


def parse_and_compute_epi_week(
    val: Any,
    day_first: bool = True
) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[int]]:
    """
    Parses messy date and calculates ISO date, EPI_WEEK string, EPI_WEEK_NUM, and EPI_YEAR.
    Returns: (clean_date_str, epi_week_str, epi_week_num, epi_year)
    """
    if pd.isna(val) or val is None:
        return None, None, None, None

    date_str, date_obj, is_valid = parse_single_date(val, day_first=day_first)
    if not is_valid or date_obj is None:
        return None, None, None, None

    try:
        epi_year, epi_week_num, epi_week_str = calculate_who_epi_week(date_obj)
        return date_str, epi_week_str, epi_week_num, epi_year
    except Exception:
        return date_str, None, None, None


class EpiWeekProcessor:
    """Batch processes date series to extract ISO dates, EpiWeeks, and week numbers."""

    def __init__(self, day_first: bool = True):
        self.day_first = day_first

    def process_series(
        self,
        series: pd.Series
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Processes date column and returns:
        (clean_date_series, epi_week_series, epi_week_num_series, epi_year_series)
        """
        clean_dates = []
        epi_weeks = []
        epi_week_nums = []
        epi_years = []

        for val in series:
            d_str, w_str, w_num, y_num = parse_and_compute_epi_week(val, day_first=self.day_first)
            clean_dates.append(d_str)
            epi_weeks.append(w_str)
            epi_week_nums.append(w_num)
            epi_years.append(y_num)

        idx = series.index
        return (
            pd.Series(clean_dates, index=idx, name="DATE_ADMISSION_CLEAN"),
            pd.Series(epi_weeks, index=idx, name="EPI_WEEK"),
            pd.Series(epi_week_nums, index=idx, name="EPI_WEEK_NUM", dtype="object"),
            pd.Series(epi_years, index=idx, name="EPI_YEAR", dtype="object")
        )
