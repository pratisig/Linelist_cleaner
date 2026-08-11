"""
Age Cleaning, Unit Conversion, and Age Group Categorization Engine.
"""

import re
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np

from linelist_cleaner.schemas.epi_dictionary import MISSING_SENTINELS


def parse_age_string(val: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Parses a messy age string or number into (age_in_years, original_unit).
    Examples:
    - 25 -> (25.0, 'Years')
    - '18 months' -> (1.5, 'Months')
    - '6m' -> (0.5, 'Months')
    - '14 days' -> (0.04, 'Days')
    - '3w' -> (0.06, 'Weeks')
    - '45 ans' -> (45.0, 'Years')
    """
    if pd.isna(val) or val is None:
        return None, None

    if isinstance(val, (int, float)) and not isinstance(val, bool):
        num = float(val)
        if 0 <= num <= 120:
            return round(num, 2), "Years"
        return None, None

    s = str(val).strip().lower()
    if not s or s in MISSING_SENTINELS:
        return None, None

    # Replace comma decimal with dot (e.g., '1,5 ans' -> '1.5 ans')
    s = s.replace(",", ".")

    # Check Months pattern: '6m', '6 m', '18 months', '6 mois', '6 meses', '6mos'
    m_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:m|mo|mos|month|months|mois|mes|meses)$", s)
    if m_match:
        months = float(m_match.group(1))
        years = months / 12.0
        return round(years, 2), "Months"

    # Check Days pattern: '15d', '15 days', '15 jours', '15 dias'
    d_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:d|day|days|jour|jours|dia|dias|j)$", s)
    if d_match:
        days = float(d_match.group(1))
        years = days / 365.25
        return round(years, 2), "Days"

    # Check Weeks pattern: '3w', '3 weeks', '3 semaines', '3 sem'
    w_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:w|wk|wks|week|weeks|semaine|semaines|sem)$", s)
    if w_match:
        weeks = float(w_match.group(1))
        years = (weeks * 7) / 365.25
        return round(years, 2), "Weeks"

    # Check Years pattern: '25y', '25yrs', '25 yo', '25 years', '25 ans', '25 a', '25 años'
    y_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:y|yr|yrs|yo|year|years|an|ans|ano|anos|años|a)?$", s)
    if y_match:
        years = float(y_match.group(1))
        if 0 <= years <= 120:
            return round(years, 2), "Years"
        return None, None

    return None, None


def calculate_age_from_dates(
    dob: Union[str, datetime.date, pd.Timestamp],
    onset: Union[str, datetime.date, pd.Timestamp]
) -> Optional[float]:
    """
    Computes patient age in years from Date of Birth and Date of Onset/Consultation.
    """
    try:
        if isinstance(dob, str):
            dob = datetime.date.fromisoformat(dob[:10])
        elif isinstance(dob, pd.Timestamp):
            dob = dob.date()

        if isinstance(onset, str):
            onset = datetime.date.fromisoformat(onset[:10])
        elif isinstance(onset, pd.Timestamp):
            onset = onset.date()

        if dob and onset and onset >= dob:
            diff_days = (onset - dob).days
            years = diff_days / 365.25
            return round(years, 2)
    except Exception:
        pass
    return None


def create_age_group_labels(breaks: List[int]) -> List[str]:
    """
    Generates standard epidemiological age bracket labels from breaks.
    e.g., [0, 5, 15, 30, 50, 65, 80] -> ['<5', '5-14', '15-29', '30-49', '50-64', '65-79', '80+']
    """
    breaks = sorted(list(set(breaks)))
    labels = []
    for i in range(len(breaks)):
        if i == 0 and breaks[i] == 0 and len(breaks) > 1:
            labels.append(f"<{breaks[1]}")
        elif i == len(breaks) - 1:
            labels.append(f"{breaks[i]}+")
        else:
            lower = breaks[i]
            upper = breaks[i + 1] - 1
            if lower == upper:
                labels.append(f"{lower}")
            else:
                labels.append(f"{lower}-{upper}")
    return labels


def categorize_age(
    age: Optional[float],
    breaks: List[int] = [0, 5, 15, 30, 50, 65, 80],
    labels: Optional[List[str]] = None
) -> Optional[str]:
    """
    Assigns an age (in decimal years) to an age group bracket.
    """
    if age is None or pd.isna(age):
        return None

    if labels is None or len(labels) != len(breaks):
        labels = create_age_group_labels(breaks)

    for i in range(len(breaks) - 1):
        if breaks[i] <= age < breaks[i + 1]:
            return labels[i]

    if age >= breaks[-1]:
        return labels[-1]

    return None


class AgeCleaner:
    """Engine for batch cleaning ages and deriving age groups."""

    def __init__(
        self,
        breaks: List[int] = [0, 5, 15, 30, 50, 65, 80],
        labels: Optional[List[str]] = None
    ):
        self.breaks = breaks
        self.labels = labels or create_age_group_labels(breaks)

    def clean_age_column(
        self,
        age_series: pd.Series,
        unit_series: Optional[pd.Series] = None
    ) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
        """
        Cleans age column, calculates decimal years, and computes age groups.
        Returns: (cleaned_age_years, age_groups_series, stats)
        """
        cleaned_ages: List[Optional[float]] = []
        age_groups: List[Optional[str]] = []
        parsed_count = 0
        invalid_count = 0

        has_separate_unit = unit_series is not None and len(unit_series) == len(age_series)

        for idx, val in age_series.items():
            unit_val = unit_series.iloc[idx] if has_separate_unit else None
            
            # If unit is explicitly in unit_series
            if has_separate_unit and pd.notna(unit_val) and pd.notna(val):
                unit_str = str(unit_val).strip().lower()
                try:
                    num_val = float(str(val).replace(",", ".").strip())
                    if "m" in unit_str or "mois" in unit_str or "mes" in unit_str:
                        yrs = round(num_val / 12.0, 2)
                    elif "d" in unit_str or "jour" in unit_str or "dia" in unit_str:
                        yrs = round(num_val / 365.25, 2)
                    elif "w" in unit_str or "sem" in unit_str:
                        yrs = round((num_val * 7) / 365.25, 2)
                    else:
                        yrs = round(num_val, 2)

                    if 0 <= yrs <= 120:
                        cleaned_ages.append(yrs)
                        age_groups.append(categorize_age(yrs, self.breaks, self.labels))
                        parsed_count += 1
                        continue
                except ValueError:
                    pass

            # Otherwise parse string expression
            yrs, unit = parse_age_string(val)
            if yrs is not None:
                cleaned_ages.append(yrs)
                age_groups.append(categorize_age(yrs, self.breaks, self.labels))
                parsed_count += 1
            else:
                cleaned_ages.append(None)
                age_groups.append(None)
                if pd.notna(val) and str(val).strip().lower() not in MISSING_SENTINELS:
                    invalid_count += 1

        cleaned_age_series = pd.Series(cleaned_ages, index=age_series.index, name="age_years")
        age_group_series = pd.Series(age_groups, index=age_series.index, name="age_group")

        stats = {
            "total_rows": len(age_series),
            "parsed_count": parsed_count,
            "invalid_count": invalid_count,
            "mean_age": float(cleaned_age_series.mean()) if parsed_count > 0 else 0.0,
            "median_age": float(cleaned_age_series.median()) if parsed_count > 0 else 0.0,
        }

        return cleaned_age_series, age_group_series, stats
