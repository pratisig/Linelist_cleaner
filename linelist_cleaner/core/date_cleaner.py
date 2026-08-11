"""
Multi-format Epidemiological Date Cleaning and Standardization Engine.
"""

import re
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from dateutil import parser as date_parser

from linelist_cleaner.schemas.epi_dictionary import MISSING_SENTINELS

# Multilingual month names translation to English for uniform parsing
MONTH_TRANSLATIONS = {
    # French
    "janvier": "january", "janv": "jan", "février": "february", "fevrier": "february", "févr": "feb", "fevr": "feb",
    "mars": "march", "mar": "mar", "avril": "april", "avr": "apr", "mai": "may",
    "juin": "june", "juil": "jul", "juillet": "july", "août": "august", "aout": "august", "aou": "aug",
    "septembre": "september", "sept": "sep", "octobre": "october", "oct": "oct",
    "novembre": "november", "nov": "nov", "décembre": "december", "decembre": "december", "déc": "dec", "dec": "dec",
    # Spanish
    "enero": "january", "ene": "jan", "febrero": "february", "feb": "feb",
    "marzo": "march", "abril": "april", "abr": "apr", "mayo": "may",
    "junio": "june", "jun": "jun", "julio": "july", "jul": "jul", "agosto": "august", "ago": "aug",
    "septiembre": "september", "setiembre": "september", "octubre": "october",
    "noviembre": "november", "diciembre": "december", "dic": "dec",
}

EXCEL_BASE_DATE = datetime.date(1899, 12, 30)


def is_excel_serial_number(val: Any) -> bool:
    """Check if value is a numeric Excel serial date (approx 1970 to 2060)."""
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return 25569 <= val <= 60000
    if isinstance(val, str):
        val_strip = val.strip()
        if re.match(r"^\d{5}(\.\d+)?$", val_strip):
            num = float(val_strip)
            return 25569 <= num <= 60000
    return False


def excel_serial_to_date(serial: Union[int, float, str]) -> Optional[datetime.date]:
    """Convert Excel serial number to Python date."""
    try:
        num = float(serial)
        dt = EXCEL_BASE_DATE + datetime.timedelta(days=int(num))
        return dt
    except Exception:
        return None


def normalize_date_string(val_str: str) -> str:
    """
    Clean up date string: strip whitespace, remove time component if unnecessary,
    normalize multilingual months and delimiters.
    """
    s = val_str.strip()
    s = s.strip("'\"`.,")
    
    # Remove Spanish/French prepositions
    s = re.sub(r"\bde\b|\bdel\b|\ble\b", " ", s, flags=re.IGNORECASE)

    # Translate month names
    for foreign_month, eng_month in MONTH_TRANSLATIONS.items():
        s = re.sub(rf"\b{foreign_month}\.?\b", eng_month, s, flags=re.IGNORECASE)

    s = re.sub(r"\s+", " ", s).strip()
    return s


def detect_day_first_preference(series: pd.Series) -> bool:
    """
    Analyzes ambiguous slash/dash separated dates in a series to infer if DMY or MDY is used.
    """
    dmy_votes = 0
    mdy_votes = 0

    for val in series.dropna().astype(str):
        val_clean = val.strip()
        match = re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", val_clean)
        if match:
            n1, n2 = int(match.group(1)), int(match.group(2))
            if n1 > 12 and n2 <= 12:
                dmy_votes += 1
            elif n2 > 12 and n1 <= 12:
                mdy_votes += 1

    if mdy_votes > dmy_votes:
        return False
    return True


def parse_single_date(
    val: Any,
    day_first: bool = True,
    output_format: str = "%Y-%m-%d",
    min_year: int = 1900,
    max_year: int = 2100
) -> Tuple[Optional[str], Optional[datetime.date], bool]:
    """
    Parses a single date value from any common epidemiological format.
    Returns: (formatted_str, date_obj, is_valid)
    """
    if pd.isna(val) or val is None:
        return None, None, False

    # Check sentinel strings
    if isinstance(val, str):
        val_norm = val.strip().lower()
        if val_norm in MISSING_SENTINELS:
            return None, None, False

    # Already datetime.date or Timestamp
    if isinstance(val, (datetime.date, pd.Timestamp)):
        if isinstance(val, pd.Timestamp):
            if pd.isna(val):
                return None, None, False
            d = val.date()
        else:
            d = val
        if min_year <= d.year <= max_year:
            return d.strftime(output_format), d, True
        return None, None, False

    # Excel serial number
    if is_excel_serial_number(val):
        d = excel_serial_to_date(val)
        if d and min_year <= d.year <= max_year:
            return d.strftime(output_format), d, True
        return None, None, False

    # String parsing
    val_str = str(val).strip()
    if not val_str or val_str.lower() in MISSING_SENTINELS:
        return None, None, False

    # Check compact YYYYMMDD numeric string e.g. "20230514"
    if re.match(r"^(19\d\d|20\d\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])$", val_str):
        try:
            d = datetime.datetime.strptime(val_str, "%Y%m%d").date()
            if min_year <= d.year <= max_year:
                return d.strftime(output_format), d, True
        except ValueError:
            pass

    cleaned_str = normalize_date_string(val_str)

    # Fast ISO check: YYYY-MM-DD
    iso_match = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:\s+.*)?$", cleaned_str)
    if iso_match:
        try:
            y, m, d_num = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            d = datetime.date(y, m, d_num)
            if min_year <= d.year <= max_year:
                return d.strftime(output_format), d, True
        except ValueError:
            pass

    # Try standard dateutil parser
    try:
        dt = date_parser.parse(cleaned_str, dayfirst=day_first, default=datetime.datetime(2000, 1, 1))
        d = dt.date()
        if min_year <= d.year <= max_year:
            return d.strftime(output_format), d, True
    except (ValueError, OverflowError):
        try:
            dt = date_parser.parse(cleaned_str, dayfirst=not day_first, default=datetime.datetime(2000, 1, 1))
            d = dt.date()
            if min_year <= d.year <= max_year:
                return d.strftime(output_format), d, True
        except Exception:
            pass

    return None, None, False


class DateCleaner:
    """Engine for batch cleaning date columns in epidemiological linelists."""

    def __init__(
        self,
        output_format: str = "%Y-%m-%d",
        day_first_preference: str = "auto",
        min_year: int = 1900,
        max_year: int = 2100
    ):
        self.output_format = output_format
        self.day_first_preference = day_first_preference
        self.min_year = min_year
        self.max_year = max_year

    def clean_column(
        self,
        series: pd.Series,
        col_name: str = "date_column"
    ) -> Tuple[pd.Series, Dict[str, Any]]:
        """
        Cleans and standardizes an entire date series.
        Returns: (cleaned_series, stats_dict)
        """
        total_count = len(series)
        non_null_count = series.notna().sum()

        if self.day_first_preference == "DMY":
            day_first = True
        elif self.day_first_preference == "MDY":
            day_first = False
        else:
            day_first = detect_day_first_preference(series)

        cleaned_values: List[Optional[str]] = []
        parsed_count = 0
        failed_count = 0
        failed_samples: List[str] = []

        for idx, val in series.items():
            formatted_str, d_obj, is_valid = parse_single_date(
                val,
                day_first=day_first,
                output_format=self.output_format,
                min_year=self.min_year,
                max_year=self.max_year
            )
            if is_valid:
                cleaned_values.append(formatted_str)
                parsed_count += 1
            else:
                cleaned_values.append(None)
                if pd.notna(val) and str(val).strip().lower() not in MISSING_SENTINELS:
                    failed_count += 1
                    if len(failed_samples) < 5:
                        failed_samples.append(str(val))

        cleaned_series = pd.Series(cleaned_values, index=series.index, name=series.name)

        stats = {
            "column_name": col_name,
            "total_rows": total_count,
            "raw_non_null": int(non_null_count),
            "successfully_parsed": parsed_count,
            "failed_to_parse": failed_count,
            "day_first_inferred": day_first,
            "failed_samples": failed_samples
        }

        return cleaned_series, stats
