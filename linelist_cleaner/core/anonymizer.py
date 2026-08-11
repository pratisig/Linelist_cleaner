"""
PII Anonymization and De-identification Engine.
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd


def mask_string(s: str) -> str:
    """Mask string e.g. 'John Doe' -> 'J*** D**'."""
    if not s or not isinstance(s, str):
        return ""
    words = s.strip().split()
    masked_words = []
    for w in words:
        if len(w) <= 1:
            masked_words.append(w)
        elif len(w) == 2:
            masked_words.append(w[0] + "*")
        else:
            masked_words.append(w[0] + "*" * (len(w) - 2) + w[-1])
    return " ".join(masked_words)


def hash_string(s: str, salt: str = "linelist_salt_2026") -> str:
    """Hashes string to a consistent 12-char hex token."""
    if not s or not isinstance(s, str):
        return ""
    raw = f"{salt}:{s.strip().lower()}"
    return "HASH_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()


class Anonymizer:
    """De-identifies linelists by masking, hashing, pseudonymizing, or dropping PII."""

    def __init__(
        self,
        method: str = "pseudonymize",  # "pseudonymize", "mask", "hash", "drop"
        fields_to_anonymize: Optional[List[str]] = None
    ):
        self.method = method
        self.fields_to_anonymize = fields_to_anonymize or [
            "full_name", "first_name", "last_name", "phone", "national_id", "address"
        ]

    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        tag_to_col: Dict[str, str]
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Anonymizes PII columns based on tag mapping.
        Returns: (anonymized_df, list_of_modified_columns)
        """
        df_out = df.copy()
        modified_cols: List[str] = []

        cols_to_process: List[str] = []
        for tag in self.fields_to_anonymize:
            col_name = tag_to_col.get(tag)
            if col_name and col_name in df_out.columns and col_name not in cols_to_process:
                cols_to_process.append(col_name)

        if self.method == "drop":
            df_out = df_out.drop(columns=cols_to_process)
            return df_out, cols_to_process

        for col in cols_to_process:
            if self.method == "mask":
                df_out[col] = df_out[col].apply(lambda x: mask_string(str(x)) if pd.notna(x) else None)
            elif self.method == "hash":
                df_out[col] = df_out[col].apply(lambda x: hash_string(str(x)) if pd.notna(x) else None)
            elif self.method == "pseudonymize":
                # Generate unique token per unique name
                unique_vals = df_out[col].dropna().unique()
                lookup = {val: f"PATIENT_{i+1:04d}" for i, val in enumerate(unique_vals)}
                df_out[col] = df_out[col].map(lookup)

            modified_cols.append(col)

        return df_out, modified_cols
