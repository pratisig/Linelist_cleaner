"""
Coordinate Cleaning & Validation Engine for V2.
Standardizes latitude/longitude, validates WGS84 bounds, detects swapped coords.
PratiSIG Consulting Services - V2
"""
import re
from typing import Tuple, Optional, Any, Dict
import pandas as pd
import numpy as np


def parse_coordinate(val: Any, coord_type: str = "lat") -> Optional[float]:
    """Parse a single coordinate value to float, handling DMS, commas, etc."""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip().replace(",", ".")
    # DMS like 11°49'60" N
    s = s.replace("°", " ").replace("'", " ").replace('"', " ").strip()
    # Extract first float-like token
    m = re.search(r"(-?\d+(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        num = float(m.group(1))
        # Heuristic: if coord contains S/W, make negative
        if re.search(r"\b[SsWw]\b", str(val)) or "S" in str(val).upper()[-2:]:
            if num > 0 and ("S" in str(val).upper() or "W" in str(val).upper()):
                # Check south/west indicator
                if ("S" in str(val).upper() and coord_type == "lat") or ("W" in str(val).upper() and coord_type == "lon"):
                    num = -abs(num)
        # Validate plausible WGS84
        if coord_type == "lat" and not -90 <= num <= 90:
            # maybe swapped? try as lon? caller will handle
            return None if abs(num) > 90 else num
        if coord_type == "lon" and not -180 <= num <= 180:
            return None
        return round(num, 6)
    except:
        return None


def clean_coordinate_columns(
    df: pd.DataFrame,
    lat_col: Optional[str] = None,
    lon_col: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Attempts to find and clean lat/lon columns.
    Auto-detects if cols not specified.
    Returns cleaned df and stats.
    """
    df_out = df.copy()
    # Auto detect
    if not lat_col:
        for c in df.columns:
            cl = c.lower()
            if any(k in cl for k in ["latitude", "lat ", "lat_", "_lat", "y_coord", "y_coord"]):
                if "longitude" not in cl and "long" not in cl:
                    lat_col = c
                    break
        if not lat_col:
            for c in df.columns:
                if c.lower().strip() in ["lat", "y"]:
                    lat_col = c
                    break

    if not lon_col:
        for c in df.columns:
            cl = c.lower()
            if any(k in cl for k in ["longitude", "long ", "long_", "_lon", "_long", "x_coord"]):
                lon_col = c
                break
        if not lon_col:
            for c in df.columns:
                if c.lower().strip() in ["lon", "lng", "long", "x"]:
                    lon_col = c
                    break

    stats = {"lat_col": lat_col, "lon_col": lon_col, "cleaned": 0, "swapped_fixed": 0, "invalid": 0}

    if not lat_col or not lon_col or lat_col not in df.columns or lon_col not in df.columns:
        return df_out, stats

    lats_clean = []
    lons_clean = []
    for _, row in df.iterrows():
        raw_lat = row[lat_col]
        raw_lon = row[lon_col]
        lat = parse_coordinate(raw_lat, "lat")
        lon = parse_coordinate(raw_lon, "lon")
        # Detect swapped: lat looks like lon (|lat|>90 but lon valid_lat)
        if lat is None and lon is not None:
            # try swapping
            alt_lat = parse_coordinate(raw_lon, "lat")
            alt_lon = parse_coordinate(raw_lat, "lon")
            if alt_lat is not None and alt_lon is not None and -90 <= alt_lat <= 90 and -180 <= alt_lon <= 180:
                lat, lon = alt_lat, alt_lon
                stats["swapped_fixed"] += 1
        if lat is not None and lon is not None:
            stats["cleaned"] += 1
        else:
            stats["invalid"] += 1
            # keep None for invalid
        lats_clean.append(lat)
        lons_clean.append(lon)

    # Overwrite with standardized column names, but keep originals as well if they are LATITUDE/LONGITUDE already?
    # Create standardized columns for geocoding pipeline
    df_out[lat_col] = lats_clean
    df_out[lon_col] = lons_clean
    # Also ensure generic LATITUDE/LONGITUDE columns exist for map
    if "LATITUDE" not in df_out.columns:
        df_out["LATITUDE"] = lats_clean
    if "LONGITUDE" not in df_out.columns:
        df_out["LONGITUDE"] = lons_clean

    return df_out, stats
