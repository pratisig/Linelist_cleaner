"""
Categorical and Demographic Standardization Engine.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any, Set
import pandas as pd
import numpy as np
from rapidfuzz import fuzz

from linelist_cleaner.schemas.epi_dictionary import (
    SEX_MAPPINGS,
    CASE_DEFINITION_MAPPINGS,
    OUTCOME_MAPPINGS,
    BINARY_MAPPINGS,
    MISSING_SENTINELS,
)


def normalize_text_token(val: Any) -> str:
    """Normalize string token for categorical mapping."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip().lower()
    # Normalize accents
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def standardize_sex_value(val: Any) -> Optional[str]:
    """Maps single value to canonical Sex ('Male', 'Female', 'Other', 'Unknown')."""
    if pd.isna(val) or val is None:
        return None
    token = normalize_text_token(val)
    if not token:
        return None

    # Check direct dictionary mapping first
    if token in SEX_MAPPINGS:
        return SEX_MAPPINGS[token]

    if token in MISSING_SENTINELS:
        return None

    # Check prefix heuristics
    if token.startswith("m") and "fem" not in token and "muj" not in token:
        return "Male"
    if token.startswith("f") or token.startswith("w") or "muj" in token or "fem" in token:
        return "Female"
    return "Unknown"


def standardize_case_definition_value(val: Any) -> Optional[str]:
    """Maps single value to canonical Case Classification."""
    if pd.isna(val) or val is None:
        return None
    token = normalize_text_token(val)
    if not token:
        return None

    if token in CASE_DEFINITION_MAPPINGS:
        return CASE_DEFINITION_MAPPINGS[token]

    if token in MISSING_SENTINELS:
        return None

    # Check keyword substring matches
    if "conf" in token or "pos" in token:
        return "Confirmed"
    if "prob" in token or "epi" in token:
        return "Probable"
    if "susp" in token or "doute" in token or "sosp" in token:
        return "Suspect"
    if "disc" in token or "excl" in token or "neg" in token or "non" in token:
        return "Discarded"
    return "Unknown"


def standardize_outcome_value(val: Any) -> Optional[str]:
    """Maps single value to canonical Outcome."""
    if pd.isna(val) or val is None:
        return None
    token = normalize_text_token(val)
    if not token:
        return None

    if token in OUTCOME_MAPPINGS:
        return OUTCOME_MAPPINGS[token]

    if token in MISSING_SENTINELS:
        return None

    if "dead" in token or "mort" in token or "deced" in token or "fallec" in token or "dcd" in token:
        return "Dead"
    if "recov" in token or "guer" in token or "cur" in token:
        return "Recovered"
    if "discharg" in token or "sorti" in token or "alta" in token:
        return "Discharged"
    if "trans" in token or "refer" in token:
        return "Transferred"
    if "lama" in token or "fuit" in token or "evad" in token or "aband" in token:
        return "LAMA"
    if "aliv" in token or "viv" in token or "hosp" in token:
        return "Alive"
    return "Unknown"


def standardize_binary_value(val: Any) -> Optional[str]:
    """Maps boolean/symptom/status value to 'Yes', 'No', 'Unknown'."""
    if pd.isna(val) or val is None:
        return None
    token = normalize_text_token(val)
    if not token:
        return None

    if token in BINARY_MAPPINGS:
        return BINARY_MAPPINGS[token]

    if token in MISSING_SENTINELS:
        return None

    if token.startswith("y") or token.startswith("o") or token.startswith("s") or token.startswith("v"):
        return "Yes"
    if token.startswith("n") or token.startswith("f"):
        return "No"
    return "Unknown"


def harmonize_facility_names(
    series: pd.Series,
    similarity_threshold: float = 85.0
) -> Tuple[pd.Series, Dict[str, str]]:
    """
    Harmonizes facility or administrative location names using fuzzy clustering.
    e.g. 'St. Mary Hospital', 'St Marys Hosp', 'st mary hospital' -> 'St. Mary Hospital'
    Returns cleaned series and mapping dictionary.
    """
    clean_series = series.copy()
    valid_mask = clean_series.notna() & (clean_series.astype(str).str.strip() != "")
    values = clean_series[valid_mask].astype(str).str.strip().str.title().tolist()

    if not values:
        return clean_series, {}

    freq = pd.Series(values).value_counts().to_dict()
    unique_names = sorted(list(freq.keys()), key=lambda x: -freq[x])

    canonical_map: Dict[str, str] = {}
    assigned: Set[str] = set()

    for primary in unique_names:
        if primary in assigned:
            continue
        canonical_map[primary] = primary
        assigned.add(primary)

        for other in unique_names:
            if other not in assigned:
                score = fuzz.token_sort_ratio(primary.lower(), other.lower())
                if score >= similarity_threshold:
                    canonical_map[other] = primary
                    assigned.add(other)

    def _map_name(val):
        if pd.isna(val) or not str(val).strip():
            return None
        title_val = str(val).strip().title()
        return canonical_map.get(title_val, title_val)

    harmonized = clean_series.apply(_map_name)
    return harmonized, canonical_map


def clean_missing_sentinels_df(
    df: pd.DataFrame,
    custom_sentinels: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Replaces all sentinel missing tokens across all columns with np.nan / None.
    Returns (cleaned_df, count_of_values_replaced).
    """
    sentinels_set = set(MISSING_SENTINELS)
    if custom_sentinels:
        for s in custom_sentinels:
            sentinels_set.add(s.strip().lower())

    count_replaced = 0
    df_clean = df.copy()

    for col in df_clean.columns:
        if df_clean[col].dtype == object or pd.api.types.is_string_dtype(df_clean[col]):
            mask = df_clean[col].astype(str).str.strip().str.lower().isin(sentinels_set)
            matches = mask.sum()
            if matches > 0:
                count_replaced += int(matches)
                df_clean.loc[mask, col] = None

    return df_clean, count_replaced
