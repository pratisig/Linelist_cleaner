"""
Phone Number Standardization Engine - V2.
Handles international formats, Senegal/Nigeria defaults, E.164-like cleaning.
"""
import re
from typing import Optional, Any, Dict, Tuple
import pandas as pd


def clean_phone_number(val: Any, default_country_code: str = "+221") -> Optional[str]:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ["na", "n/a", "unknown", "inconnu", "-"]:
        return None
    # Remove all except digits and +
    digits = re.sub(r"[^\d+]", "", s)
    # Remove multiple plus
    digits = re.sub(r"\++", "+", digits)
    # If starts with 00 replace with +
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    # If no plus and length plausible
    if not digits.startswith("+"):
        # Remove leading 0 for international
        if digits.startswith("0") and len(digits) >= 9:
            digits = digits.lstrip("0")
            digits = default_country_code + digits
        elif len(digits) == 9 and default_country_code == "+221":
            digits = "+221" + digits
        elif len(digits) >= 10 and len(digits) <= 15:
            if len(digits) == 10 and digits.startswith("7"):
                digits = "+221" + digits
            else:
                digits = "+" + digits if not digits.startswith("+") else digits
    # Validate: must be + followed by 8-15 digits
    if re.match(r"^\+\d{8,15}$", digits):
        return digits
    # Fallback: return digits with plus if at least 7 digits
    cleaned = re.sub(r"[^\d]", "", s)
    if 7 <= len(cleaned) <= 15:
        return "+" + cleaned if not s.strip().startswith("+") else "+" + cleaned
    return None


def clean_phone_column(series: pd.Series, default_country_code: str = "+221") -> Tuple[pd.Series, Dict[str, Any]]:
    cleaned = []
    valid = 0
    invalid = 0
    for v in series:
        c = clean_phone_number(v, default_country_code)
        cleaned.append(c)
        if c is not None:
            valid += 1
        elif pd.notna(v) and str(v).strip() not in ["", "NA", "nan", "None"]:
            invalid += 1
    out = pd.Series(cleaned, index=series.index)
    stats = {"valid": valid, "invalid": invalid, "total": len(series)}
    return out, stats
