"""
Hierarchical Spatial Fallback Cascade Geocoding Engine (P-Code Matching).
Implements OCHA COD-AB and humanitarian spatial standard matching with multi-level fallbacks.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any, Set
import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process


def normalize_spatial_name(name: Any) -> str:
    """
    Normalizes a place name for robust string and fuzzy matching:
    - Strips accents/diacritics ('Béni' -> 'Beni', 'Équateur' -> 'Equateur')
    - Converts to lowercase
    - Removes common prefixes/suffixes ('ward', 'lga', 'district', 'village', 'cs', 'centre de sante')
    - Collapses whitespace and punctuation
    """
    if pd.isna(name) or name is None:
        return ""
    s = str(name).strip().lower()
    # Normalize unicode
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))

    # Remove noise prefixes/suffixes for matching
    s = re.sub(r"\b(village|localite|localité|ward|lga|district|zone de sante|commune|city|ville)\b", " ", s)
    # Remove punctuation
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class PCodeReferenceIndex:
    """Indexed reference hierarchy for fast exact and fuzzy lookup."""

    def __init__(self, ref_df: pd.DataFrame, mapping: Dict[str, str]):
        """
        mapping maps reference roles to ref_df column names:
        {
            "admin1_name": "adm1_name",
            "admin1_pcode": "adm1_pcode",
            "admin2_name": "adm2_name",
            "admin2_pcode": "adm2_pcode",
            "admin3_name": "adm3_name",
            "admin3_pcode": "adm3_pcode",
            "locality_name": "locality_name",
            "locality_pcode": "locality_pcode",
            "lat": "latitude",
            "long": "longitude"
        }
        """
        self.ref_df = ref_df.copy()
        self.mapping = mapping

        # Helper to get column
        def get_col(role: str) -> Optional[str]:
            col = mapping.get(role)
            if col and col in ref_df.columns:
                return col
            return None

        self.col_adm1_name = get_col("admin1_name")
        self.col_adm1_pcode = get_col("admin1_pcode")
        self.col_adm2_name = get_col("admin2_name")
        self.col_adm2_pcode = get_col("admin2_pcode")
        self.col_adm3_name = get_col("admin3_name")
        self.col_adm3_pcode = get_col("admin3_pcode")
        self.col_loc_name = get_col("locality_name")
        self.col_loc_pcode = get_col("locality_pcode")
        self.col_lat = get_col("lat")
        self.col_long = get_col("long")

        # Build level lookups: level -> {norm_name: {pcode, name, lat, long}}
        self.lookups: Dict[str, Dict[str, Dict[str, Any]]] = {
            "Locality": {},
            "Admin3_Ward": {},
            "Admin2_LGA": {},
            "Admin1_State": {}
        }
        self.unique_names: Dict[str, List[str]] = {
            "Locality": [],
            "Admin3_Ward": [],
            "Admin2_LGA": [],
            "Admin1_State": []
        }

        self._build_indices()

    def _build_indices(self):
        # 1. Localities
        if self.col_loc_name and self.col_loc_pcode:
            for _, row in self.ref_df.iterrows():
                raw_name = str(row[self.col_loc_name]) if pd.notna(row[self.col_loc_name]) else ""
                norm = normalize_spatial_name(raw_name)
                pcode = str(row[self.col_loc_pcode]) if pd.notna(row[self.col_loc_pcode]) else ""
                if norm and pcode:
                    lat = float(row[self.col_lat]) if (self.col_lat and pd.notna(row[self.col_lat])) else None
                    lon = float(row[self.col_long]) if (self.col_long and pd.notna(row[self.col_long])) else None
                    self.lookups["Locality"][norm] = {
                        "pcode": pcode,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }
            self.unique_names["Locality"] = list(self.lookups["Locality"].keys())

        # 2. Admin 3
        if self.col_adm3_name and self.col_adm3_pcode:
            for _, row in self.ref_df.iterrows():
                raw_name = str(row[self.col_adm3_name]) if pd.notna(row[self.col_adm3_name]) else ""
                norm = normalize_spatial_name(raw_name)
                pcode = str(row[self.col_adm3_pcode]) if pd.notna(row[self.col_adm3_pcode]) else ""
                if norm and pcode and norm not in self.lookups["Admin3_Ward"]:
                    lat = float(row[self.col_lat]) if (self.col_lat and pd.notna(row[self.col_lat])) else None
                    lon = float(row[self.col_long]) if (self.col_long and pd.notna(row[self.col_long])) else None
                    self.lookups["Admin3_Ward"][norm] = {
                        "pcode": pcode,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }
            self.unique_names["Admin3_Ward"] = list(self.lookups["Admin3_Ward"].keys())

        # 3. Admin 2
        if self.col_adm2_name and self.col_adm2_pcode:
            for _, row in self.ref_df.iterrows():
                raw_name = str(row[self.col_adm2_name]) if pd.notna(row[self.col_adm2_name]) else ""
                norm = normalize_spatial_name(raw_name)
                pcode = str(row[self.col_adm2_pcode]) if pd.notna(row[self.col_adm2_pcode]) else ""
                if norm and pcode and norm not in self.lookups["Admin2_LGA"]:
                    lat = float(row[self.col_lat]) if (self.col_lat and pd.notna(row[self.col_lat])) else None
                    lon = float(row[self.col_long]) if (self.col_long and pd.notna(row[self.col_long])) else None
                    self.lookups["Admin2_LGA"][norm] = {
                        "pcode": pcode,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }
            self.unique_names["Admin2_LGA"] = list(self.lookups["Admin2_LGA"].keys())

        # 4. Admin 1
        if self.col_adm1_name and self.col_adm1_pcode:
            for _, row in self.ref_df.iterrows():
                raw_name = str(row[self.col_adm1_name]) if pd.notna(row[self.col_adm1_name]) else ""
                norm = normalize_spatial_name(raw_name)
                pcode = str(row[self.col_adm1_pcode]) if pd.notna(row[self.col_adm1_pcode]) else ""
                if norm and pcode and norm not in self.lookups["Admin1_State"]:
                    lat = float(row[self.col_lat]) if (self.col_lat and pd.notna(row[self.col_lat])) else None
                    lon = float(row[self.col_long]) if (self.col_long and pd.notna(row[self.col_long])) else None
                    self.lookups["Admin1_State"][norm] = {
                        "pcode": pcode,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }
            self.unique_names["Admin1_State"] = list(self.lookups["Admin1_State"].keys())


class SpatialCascadeMatcher:
    """Executes the hierarchical spatial fallback cascade matching algorithm."""

    def __init__(
        self,
        ref_index: PCodeReferenceIndex,
        similarity_threshold: float = 80.0
    ):
        self.index = ref_index
        self.similarity_threshold = similarity_threshold
        # Cache for memoizing fuzzy queries: (level, query_norm) -> (match_dict, score)
        self.fuzzy_cache: Dict[Tuple[str, str], Tuple[Optional[Dict[str, Any]], float]] = {}

    def _match_single_level(
        self,
        raw_name: Any,
        level: str
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """Matches a raw place name at a specific administrative level."""
        if pd.isna(raw_name) or raw_name is None:
            return None, 0.0

        norm = normalize_spatial_name(raw_name)
        if not norm:
            return None, 0.0

        cache_key = (level, norm)
        if cache_key in self.fuzzy_cache:
            return self.fuzzy_cache[cache_key]

        level_lookup = self.index.lookups.get(level, {})
        candidates = self.index.unique_names.get(level, [])

        if not candidates:
            self.fuzzy_cache[cache_key] = (None, 0.0)
            return None, 0.0

        # 1. Exact match
        if norm in level_lookup:
            res = (level_lookup[norm], 100.0)
            self.fuzzy_cache[cache_key] = res
            return res

        # 2. Fuzzy match
        # Compute best match using token_sort_ratio
        best_match = process.extractOne(
            norm,
            candidates,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=self.similarity_threshold
        )

        if best_match:
            matched_norm, score, _ = best_match
            res = (level_lookup[matched_norm], float(score))
            self.fuzzy_cache[cache_key] = res
            return res

        # Try partial ratio fallback for compound names
        best_match_partial = process.extractOne(
            norm,
            candidates,
            scorer=fuzz.partial_ratio,
            score_cutoff=max(self.similarity_threshold, 85.0)
        )
        if best_match_partial:
            matched_norm, score, _ = best_match_partial
            res = (level_lookup[matched_norm], float(score))
            self.fuzzy_cache[cache_key] = res
            return res

        self.fuzzy_cache[cache_key] = (None, 0.0)
        return None, 0.0

    def match_row(
        self,
        locality_val: Any = None,
        admin3_val: Any = None,
        admin2_val: Any = None,
        admin1_val: Any = None
    ) -> Dict[str, Any]:
        """
        Runs the 5-step spatial fallback cascade:
        Step 1: Locality / Village
        Step 2: Admin 3 / Ward (Fallback 1)
        Step 3: Admin 2 / LGA (Fallback 2)
        Step 4: Admin 1 / State (Fallback 3)
        Step 5: Unmatched
        """
        # Step 1: Locality
        if locality_val is not None and str(locality_val).strip():
            match_data, score = self._match_single_level(locality_val, "Locality")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Locality",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        # Step 2: Admin 3 / Ward
        if admin3_val is not None and str(admin3_val).strip():
            match_data, score = self._match_single_level(admin3_val, "Admin3_Ward")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Admin3_Ward",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        # Step 3: Admin 2 / LGA
        if admin2_val is not None and str(admin2_val).strip():
            match_data, score = self._match_single_level(admin2_val, "Admin2_LGA")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Admin2_LGA",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        # Step 4: Admin 1 / State
        if admin1_val is not None and str(admin1_val).strip():
            match_data, score = self._match_single_level(admin1_val, "Admin1_State")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Admin1_State",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        # Step 5: Unmatched
        return {
            "PCODE_ASSIGNED": None,
            "MATCH_LEVEL": "Unmatched",
            "MATCH_SCORE": 0.0,
            "MATCHED_NAME": None,
            "LATITUDE": None,
            "LONGITUDE": None
        }

    def process_dataframe(
        self,
        df: pd.DataFrame,
        col_locality: Optional[str] = None,
        col_admin3: Optional[str] = None,
        col_admin2: Optional[str] = None,
        col_admin1: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Applies cascade matching across the entire DataFrame and appends enriched columns.
        Returns: (enriched_df, stats_summary)
        """
        df_out = df.copy()

        pcodes = []
        match_levels = []
        match_scores = []
        matched_names = []
        latitudes = []
        longitudes = []

        level_counts: Dict[str, int] = {
            "Locality": 0,
            "Admin3_Ward": 0,
            "Admin2_LGA": 0,
            "Admin1_State": 0,
            "Unmatched": 0
        }

        for idx, row in df.iterrows():
            loc_val = row[col_locality] if (col_locality and col_locality in df.columns) else None
            adm3_val = row[col_admin3] if (col_admin3 and col_admin3 in df.columns) else None
            adm2_val = row[col_admin2] if (col_admin2 and col_admin2 in df.columns) else None
            adm1_val = row[col_admin1] if (col_admin1 and col_admin1 in df.columns) else None

            res = self.match_row(loc_val, adm3_val, adm2_val, adm1_val)

            pcodes.append(res["PCODE_ASSIGNED"])
            match_levels.append(res["MATCH_LEVEL"])
            match_scores.append(res["MATCH_SCORE"])
            matched_names.append(res["MATCHED_NAME"])
            latitudes.append(res["LATITUDE"])
            longitudes.append(res["LONGITUDE"])

            level_counts[res["MATCH_LEVEL"]] += 1

        df_out["PCODE_ASSIGNED"] = pcodes
        df_out["MATCH_LEVEL"] = match_levels
        df_out["MATCH_SCORE"] = match_scores
        df_out["MATCHED_NAME"] = matched_names
        df_out["LATITUDE"] = latitudes
        df_out["LONGITUDE"] = longitudes

        total_records = len(df)
        geocoded_count = total_records - level_counts["Unmatched"]
        geocoded_rate = round((geocoded_count / total_records) * 100, 1) if total_records > 0 else 0.0

        scores_valid = [s for s in match_scores if s > 0]
        avg_score = round(float(np.mean(scores_valid)), 1) if scores_valid else 0.0

        stats = {
            "total_records": total_records,
            "geocoded_count": geocoded_count,
            "geocoded_rate_pct": geocoded_rate,
            "average_match_score": avg_score,
            "level_distribution": level_counts,
            "level_percentages": {
                lvl: round((cnt / total_records) * 100, 1) if total_records > 0 else 0.0
                for lvl, cnt in level_counts.items()
            }
        }

        return df_out, stats
