"""
Column Standardization and Semantic Epidemiological Tag Mapping.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from rapidfuzz import fuzz

from linelist_cleaner.schemas.epi_dictionary import CANONICAL_TAGS


def clean_string_identifier(name: str) -> str:
    """
    Standardize a string into snake_case format:
    - Normalizes unicode (removes diacritics / accents: e.g., 'prénom' -> 'prenom')
    - Strips leading/trailing spaces
    - Replaces non-alphanumeric chars with underscore
    - Collapses multiple underscores into single underscore
    - Converts to lowercase
    """
    if not isinstance(name, str):
        name = str(name)

    # Unicode normalization to strip accents
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))

    # Replace special chars, dots, hyphens, slashes with underscore
    name = re.sub(r"[^\w\s]", "_", name)
    # Replace whitespace with underscore
    name = re.sub(r"\s+", "_", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    # Strip leading/trailing underscores
    name = name.strip("_").lower()

    if not name:
        return "unnamed_column"
    return name


def standardize_dataframe_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Standardizes all column names in a DataFrame.
    Resolves potential collisions by appending a counter.
    Returns the modified DataFrame and a dictionary of {old_name: new_name}.
    """
    renamed_map: Dict[str, str] = {}
    used_names: set = set()
    new_columns: List[str] = []

    for col in df.columns:
        clean_name = clean_string_identifier(str(col))
        final_name = clean_name
        counter = 1
        while final_name in used_names:
            final_name = f"{clean_name}_{counter}"
            counter += 1

        used_names.add(final_name)
        renamed_map[str(col)] = final_name
        new_columns.append(final_name)

    df_renamed = df.copy()
    df_renamed.columns = new_columns
    return df_renamed, renamed_map


def find_best_epi_tag_for_column(
    col_name: str,
    similarity_threshold: float = 0.78,
    custom_mapping: Optional[Dict[str, str]] = None
) -> Tuple[Optional[str], float]:
    """
    Matches a single column name against known epidemiological tags and synonyms.
    Returns (matched_tag, match_score) or (None, 0.0).
    """
    clean_col = clean_string_identifier(col_name)

    # 1. Check custom mapping first
    if custom_mapping and (col_name in custom_mapping or clean_col in custom_mapping):
        mapped = custom_mapping.get(col_name) or custom_mapping.get(clean_col)
        if mapped in CANONICAL_TAGS:
            return mapped, 1.0

    # 2. Check exact tag match
    if clean_col in CANONICAL_TAGS:
        return clean_col, 1.0

    # 3. Check exact synonym match
    best_tag = None
    best_score = 0.0

    for tag, meta in CANONICAL_TAGS.items():
        synonyms = meta.get("synonyms", [])
        for syn in synonyms:
            syn_clean = clean_string_identifier(syn)
            if clean_col == syn_clean:
                return tag, 1.0

            # Compute fuzzy score
            # Use max of partial ratio and token_sort_ratio
            score_ratio = fuzz.ratio(clean_col, syn_clean) / 100.0
            score_token = fuzz.token_sort_ratio(clean_col, syn_clean) / 100.0
            score = max(score_ratio, score_token)

            if score > best_score:
                best_score = score
                best_tag = tag

    if best_score >= similarity_threshold:
        return best_tag, best_score

    return None, best_score


def map_linelist_columns(
    df: pd.DataFrame,
    similarity_threshold: float = 0.78,
    custom_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Maps all columns in a dataframe to standard epidemiological tags.
    Returns dictionary:
    {
        col_name: {
            "mapped_tag": str or None,
            "score": float,
            "label": str,
            "category": str,
            "is_mapped": bool
        }
    }
    """
    results: Dict[str, Dict[str, Any]] = {}
    assigned_tags: set = set()

    # Pass 1: Exact matches
    unmatched_cols: List[str] = []
    for col in df.columns:
        tag, score = find_best_epi_tag_for_column(
            col,
            similarity_threshold=similarity_threshold,
            custom_mapping=custom_mapping
        )
        if tag and score == 1.0 and tag not in assigned_tags:
            meta = CANONICAL_TAGS.get(tag, {})
            results[col] = {
                "mapped_tag": tag,
                "score": score,
                "label": meta.get("label", tag),
                "category": meta.get("category", "other"),
                "is_mapped": True
            }
            assigned_tags.add(tag)
        else:
            unmatched_cols.append(col)

    # Pass 2: Fuzzy matches for remaining columns
    for col in unmatched_cols:
        tag, score = find_best_epi_tag_for_column(
            col,
            similarity_threshold=similarity_threshold,
            custom_mapping=custom_mapping
        )
        if tag and score >= similarity_threshold and tag not in assigned_tags:
            meta = CANONICAL_TAGS.get(tag, {})
            results[col] = {
                "mapped_tag": tag,
                "score": score,
                "label": meta.get("label", tag),
                "category": meta.get("category", "other"),
                "is_mapped": True
            }
            assigned_tags.add(tag)
        else:
            results[col] = {
                "mapped_tag": None,
                "score": score if tag else 0.0,
                "label": "Unmapped",
                "category": "unclassified",
                "is_mapped": False
            }

    return results
