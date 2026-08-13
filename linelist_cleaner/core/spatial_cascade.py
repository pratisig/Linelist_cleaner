"""
Hierarchical Spatial Fallback Cascade Geocoding Engine (P-Code Matching).
Implements OCHA COD-AB and humanitarian spatial standard matching with multi-level fallbacks.
PratiSIG Consulting Services - Dakar, Sénégal.
Auteur : Youssoupha MBODJI (pratisig.consulting@gmail.com)
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
    - Strips leading/trailing whitespace
    - Normalizes accents/diacritics ('Béni' -> 'beni', 'Équateur' -> 'equateur', 'Thiès' -> 'thies')
    - Converts to lowercase
    - Normalizes punctuation and separators to single spaces
    """
    if pd.isna(name) or name is None:
        return ""
    s = str(name).strip().lower()
    if s in ["", "nan", "none", "null", "n/a", "inconnu", "unknown", "-", "0", "aucun", "sans", "non precise", "non renseigne", "nd"]:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\'\"_,\.\-\/\\:;]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def auto_detect_reference_mapping(ref_df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Automatically detects column roles in an uploaded P-Code reference dataset (Excel or CSV).
    Supports English, French, Spanish, OCHA COD-AB and standard humanitarian GIS headers.
    """
    cols = list(ref_df.columns)
    mapping: Dict[str, Optional[str]] = {
        "admin1_name": None,
        "admin1_pcode": None,
        "admin2_name": None,
        "admin2_pcode": None,
        "admin3_name": None,
        "admin3_pcode": None,
        "locality_name": None,
        "locality_pcode": None,
        "lat": None,
        "long": None
    }

    role_synonyms = {
        "admin1_name": [
            "admin1_name", "adm1_name", "adm1_fr", "adm1_en", "state", "province", "region",
            "nom_region", "nom_province", "nom_state", "departement", "admin1", "adm1", "state_name", "province_name", "region_name"
        ],
        "admin1_pcode": [
            "admin1_pcode", "adm1_pcode", "pcode_adm1", "code_adm1", "code_region", "code_province", "code_state",
            "pcode1", "adm1_code", "admin1_code", "pcode_admin1", "adm1_pcode_code"
        ],
        "admin2_name": [
            "admin2_name", "adm2_name", "adm2_fr", "adm2_en", "lga", "district", "zone_sante",
            "zone_de_sante", "nom_district", "nom_lga", "cercle", "commune", "admin2", "adm2", "district_name", "lga_name", "county"
        ],
        "admin2_pcode": [
            "admin2_pcode", "adm2_pcode", "pcode_adm2", "code_adm2", "code_district", "code_lga",
            "pcode2", "adm2_code", "admin2_code", "pcode_admin2", "pcode_lga"
        ],
        "admin3_name": [
            "admin3_name", "adm3_name", "adm3_fr", "adm3_en", "ward", "subdistrict", "sub_district",
            "aire_sante", "aire_de_sante", "nom_ward", "nom_commune", "admin3", "adm3", "ward_name", "subcounty"
        ],
        "admin3_pcode": [
            "admin3_pcode", "adm3_pcode", "pcode_adm3", "code_adm3", "code_ward", "pcode3",
            "adm3_code", "admin3_code", "pcode_admin3", "pcode_ward"
        ],
        "locality_name": [
            "locality_name", "loc_name", "loc_nr", "village", "village_name", "settlement", "localite",
            "nom_localite", "nom_village", "nom_loc", "rue_quartier", "rq_norm", "ville_village", "site", "camp",
            "center", "centre", "structure", "point_name", "nom_site", "locality"
        ],
        "locality_pcode": [
            "pcode", "locality_pcode", "loc_pcode", "pcode_loc", "pcode_vil", "pcode_rue", "pcode_village",
            "pcode_localite", "code_localite", "code_village", "pcode_site", "pcode_locality", "locality_code",
            "loc_code", "code_pcode", "id_pcode", "code_loc", "pcode_final", "p_code", "code"
        ],
        "lat": [
            "latitude", "lat", "lat_y", "y", "y_coord", "coord_y", "latitude_y", "lat_dd"
        ],
        "long": [
            "longitude", "long", "lon", "long_x", "lng", "x", "x_coord", "coord_x", "longitude_x", "long_dd"
        ]
    }

    used_cols: Set[str] = set()

    # Pass 1: Exact matches
    for role, syn_list in role_synonyms.items():
        for col in cols:
            if col in used_cols:
                continue
            clean_col = normalize_spatial_name(col)
            if clean_col in [normalize_spatial_name(s) for s in syn_list]:
                mapping[role] = col
                used_cols.add(col)
                break

    # Pass 2: Substring matches
    for role, syn_list in role_synonyms.items():
        if mapping[role] is not None:
            continue
        for col in cols:
            if col in used_cols:
                continue
            clean_col = normalize_spatial_name(col)
            if any(normalize_spatial_name(s) in clean_col for s in syn_list):
                mapping[role] = col
                used_cols.add(col)
                break

    return mapping


class PCodeReferenceIndex:
    """Indexed reference hierarchy for fast exact and fuzzy lookup."""

    def __init__(self, ref_df: pd.DataFrame, mapping: Optional[Dict[str, str]] = None):
        self.ref_df = ref_df.copy()
        
        auto_map = auto_detect_reference_mapping(ref_df)
        if mapping:
            auto_map.update({k: v for k, v in mapping.items() if v})
        self.mapping = auto_map

        def get_col(*roles: str) -> Optional[str]:
            for role in roles:
                col = self.mapping.get(role)
                if col and col in ref_df.columns:
                    return col
            return None

        self.col_adm1_name = get_col("admin1_name", "ref_a1", "nom_adm1", "nom_region")
        self.col_adm1_pcode = get_col("admin1_pcode", "ref_a1_pcode", "pcode_adm1", "code_adm1")
        self.col_adm2_name = get_col("admin2_name", "ref_a2", "nom_adm2", "nom_district")
        self.col_adm2_pcode = get_col("admin2_pcode", "ref_a2_pcode", "pcode_adm2", "code_adm2")
        self.col_adm3_name = get_col("admin3_name", "ref_a3", "nom_adm3", "nom_ward")
        self.col_adm3_pcode = get_col("admin3_pcode", "ref_a3_pcode", "pcode_adm3", "code_adm3")
        self.col_loc_name = get_col("locality_name", "ref_loc", "nom_loc", "nom_village")
        self.col_loc_pcode = get_col("locality_pcode", "ref_loc_pcode", "pcode_loc", "pcode")
        self.col_lat = get_col("lat", "ref_lat", "latitude")
        self.col_long = get_col("long", "ref_long", "longitude", "lon", "lng")

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

    def _extract_row_pcodes(self, row: pd.Series, idx: int) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        def get_val(col_name: Optional[str]) -> Optional[str]:
            if col_name and col_name in row and pd.notna(row[col_name]):
                val = str(row[col_name]).strip()
                if val and val.lower() not in ["", "nan", "none", "null", "n/a", "-"]:
                    return val
            return None

        p_loc = get_val(self.col_loc_pcode)
        p_a3 = get_val(self.col_adm3_pcode)
        p_a2 = get_val(self.col_adm2_pcode)
        p_a1 = get_val(self.col_adm1_pcode)

        p_general = p_loc or p_a3 or p_a2 or p_a1
        if not p_general:
            for c in row.index:
                cl = str(c).lower()
                if "pcode" in cl or cl == "code":
                    v = get_val(c)
                    if v:
                        p_general = v
                        break

        return p_loc, p_a3, p_a2, p_a1, p_general

    def _build_indices(self):
        for idx, row in self.ref_df.iterrows():
            p_loc, p_a3, p_a2, p_a1, p_gen = self._extract_row_pcodes(row, idx)

            lat = None
            lon = None
            if self.col_lat and pd.notna(row.get(self.col_lat)):
                try:
                    lat = float(row[self.col_lat])
                except (ValueError, TypeError):
                    lat = None
            if self.col_long and pd.notna(row.get(self.col_long)):
                try:
                    lon = float(row[self.col_long])
                except (ValueError, TypeError):
                    lon = None

            # 1. Locality
            if self.col_loc_name and pd.notna(row.get(self.col_loc_name)):
                raw_name = str(row[self.col_loc_name]).strip()
                norm = normalize_spatial_name(raw_name)
                if norm and norm not in self.lookups["Locality"]:
                    best_p = p_loc or p_a3 or p_a2 or p_a1 or p_gen
                    self.lookups["Locality"][norm] = {
                        "pcode": best_p,
                        "pcode_loc": p_loc,
                        "pcode_adm3": p_a3,
                        "pcode_adm2": p_a2,
                        "pcode_adm1": p_a1,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }

            # 2. Admin 3
            if self.col_adm3_name and pd.notna(row.get(self.col_adm3_name)):
                raw_name = str(row[self.col_adm3_name]).strip()
                norm = normalize_spatial_name(raw_name)
                if norm and norm not in self.lookups["Admin3_Ward"]:
                    best_p = p_a3 or p_loc or p_a2 or p_a1 or p_gen
                    self.lookups["Admin3_Ward"][norm] = {
                        "pcode": best_p,
                        "pcode_loc": p_loc,
                        "pcode_adm3": p_a3,
                        "pcode_adm2": p_a2,
                        "pcode_adm1": p_a1,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }

            # 3. Admin 2
            if self.col_adm2_name and pd.notna(row.get(self.col_adm2_name)):
                raw_name = str(row[self.col_adm2_name]).strip()
                norm = normalize_spatial_name(raw_name)
                if norm and norm not in self.lookups["Admin2_LGA"]:
                    best_p = p_a2 or p_a3 or p_loc or p_a1 or p_gen
                    self.lookups["Admin2_LGA"][norm] = {
                        "pcode": best_p,
                        "pcode_loc": p_loc,
                        "pcode_adm3": p_a3,
                        "pcode_adm2": p_a2,
                        "pcode_adm1": p_a1,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }

            # 4. Admin 1
            if self.col_adm1_name and pd.notna(row.get(self.col_adm1_name)):
                raw_name = str(row[self.col_adm1_name]).strip()
                norm = normalize_spatial_name(raw_name)
                if norm and norm not in self.lookups["Admin1_State"]:
                    best_p = p_a1 or p_a2 or p_a3 or p_loc or p_gen
                    self.lookups["Admin1_State"][norm] = {
                        "pcode": best_p,
                        "pcode_loc": p_loc,
                        "pcode_adm3": p_a3,
                        "pcode_adm2": p_a2,
                        "pcode_adm1": p_a1,
                        "name": raw_name,
                        "lat": lat,
                        "long": lon
                    }

        self.unique_names["Locality"] = list(self.lookups["Locality"].keys())
        self.unique_names["Admin3_Ward"] = list(self.lookups["Admin3_Ward"].keys())
        self.unique_names["Admin2_LGA"] = list(self.lookups["Admin2_LGA"].keys())
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

        # 1. Exact lookup
        if norm in level_lookup:
            res = (level_lookup[norm], 100.0)
            self.fuzzy_cache[cache_key] = res
            return res

        # 2. WRatio matcher (handles token reordering, partial matches, case/diacritics, and length weighting)
        best_match = process.extractOne(
            norm,
            candidates,
            scorer=fuzz.WRatio,
            score_cutoff=self.similarity_threshold
        )

        if best_match:
            matched_norm, score, _ = best_match
            res = (level_lookup[matched_norm], float(score))
            self.fuzzy_cache[cache_key] = res
            return res

        # 3. Token Set Ratio fallback (handles subset names e.g. "Bolori I Ward" vs "Bolori I")
        best_match_set = process.extractOne(
            norm,
            candidates,
            scorer=fuzz.token_set_ratio,
            score_cutoff=max(self.similarity_threshold, 80.0)
        )
        if best_match_set:
            matched_norm, score, _ = best_match_set
            res = (level_lookup[matched_norm], float(score))
            self.fuzzy_cache[cache_key] = res
            return res

        # 4. Partial Ratio fallback
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
        if locality_val is not None and str(locality_val).strip():
            match_data, score = self._match_single_level(locality_val, "Locality")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Locality",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "PCODE_LOCALITY": match_data.get("pcode_loc"),
                    "PCODE_ADMIN3": match_data.get("pcode_adm3"),
                    "PCODE_ADMIN2": match_data.get("pcode_adm2"),
                    "PCODE_ADMIN1": match_data.get("pcode_adm1"),
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        if admin3_val is not None and str(admin3_val).strip():
            match_data, score = self._match_single_level(admin3_val, "Admin3_Ward")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Admin3_Ward",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "PCODE_LOCALITY": None,
                    "PCODE_ADMIN3": match_data.get("pcode_adm3"),
                    "PCODE_ADMIN2": match_data.get("pcode_adm2"),
                    "PCODE_ADMIN1": match_data.get("pcode_adm1"),
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        if admin2_val is not None and str(admin2_val).strip():
            match_data, score = self._match_single_level(admin2_val, "Admin2_LGA")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Admin2_LGA",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "PCODE_LOCALITY": None,
                    "PCODE_ADMIN3": None,
                    "PCODE_ADMIN2": match_data.get("pcode_adm2"),
                    "PCODE_ADMIN1": match_data.get("pcode_adm1"),
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        if admin1_val is not None and str(admin1_val).strip():
            match_data, score = self._match_single_level(admin1_val, "Admin1_State")
            if match_data:
                return {
                    "PCODE_ASSIGNED": match_data["pcode"],
                    "MATCH_LEVEL": "Admin1_State",
                    "MATCH_SCORE": score,
                    "MATCHED_NAME": match_data["name"],
                    "PCODE_LOCALITY": None,
                    "PCODE_ADMIN3": None,
                    "PCODE_ADMIN2": None,
                    "PCODE_ADMIN1": match_data.get("pcode_adm1"),
                    "LATITUDE": match_data["lat"],
                    "LONGITUDE": match_data["long"]
                }

        return {
            "PCODE_ASSIGNED": None,
            "MATCH_LEVEL": "Unmatched",
            "MATCH_SCORE": 0.0,
            "MATCHED_NAME": None,
            "PCODE_LOCALITY": None,
            "PCODE_ADMIN3": None,
            "PCODE_ADMIN2": None,
            "PCODE_ADMIN1": None,
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
        df_out = df.copy()

        pcodes = []
        match_levels = []
        match_scores = []
        matched_names = []
        pcodes_loc = []
        pcodes_a3 = []
        pcodes_a2 = []
        pcodes_a1 = []
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
            pcodes_loc.append(res["PCODE_LOCALITY"])
            pcodes_a3.append(res["PCODE_ADMIN3"])
            pcodes_a2.append(res["PCODE_ADMIN2"])
            pcodes_a1.append(res["PCODE_ADMIN1"])
            latitudes.append(res["LATITUDE"])
            longitudes.append(res["LONGITUDE"])

            level_counts[res["MATCH_LEVEL"]] += 1

        df_out["PCODE_ASSIGNED"] = pcodes
        df_out["MATCH_LEVEL"] = match_levels
        df_out["MATCH_SCORE"] = match_scores
        df_out["MATCHED_NAME"] = matched_names

        # Add granular level P-Codes if mapped in reference
        if self.index.col_loc_pcode and any(p is not None for p in pcodes_loc):
            df_out["PCODE_LOCALITY"] = pcodes_loc
        if self.index.col_adm3_pcode and any(p is not None for p in pcodes_a3):
            df_out["PCODE_ADMIN3"] = pcodes_a3
        if self.index.col_adm2_pcode and any(p is not None for p in pcodes_a2):
            df_out["PCODE_ADMIN2"] = pcodes_a2
        if self.index.col_adm1_pcode and any(p is not None for p in pcodes_a1):
            df_out["PCODE_ADMIN1"] = pcodes_a1

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
