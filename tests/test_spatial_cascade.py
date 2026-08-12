import pandas as pd
import pytest
from linelist_cleaner.core.spatial_cascade import (
    normalize_spatial_name,
    PCodeReferenceIndex,
    SpatialCascadeMatcher,
)
from linelist_cleaner.datasets import get_sample_dataset


def test_normalize_spatial_name():
    assert normalize_spatial_name("Béni Village") == "beni"
    assert normalize_spatial_name("Ward Bolori I") == "bolori i"
    assert normalize_spatial_name("Maiduguri LGA") == "maiduguri"
    assert normalize_spatial_name("Zone de Sante de Goma") == "de goma"


def test_spatial_cascade_matching():
    # 1. Load OCHA reference
    ref_df = get_sample_dataset("pcode_reference")
    ref_mapping = {
        "admin1_name": "Admin1_Name",
        "admin1_pcode": "Admin1_Pcode",
        "admin2_name": "Admin2_Name",
        "admin2_pcode": "Admin2_Pcode",
        "admin3_name": "Admin3_Name",
        "admin3_pcode": "Admin3_Pcode",
        "locality_name": "Locality_Name",
        "locality_pcode": "Locality_Pcode",
        "lat": "Latitude",
        "long": "Longitude"
    }
    ref_index = PCodeReferenceIndex(ref_df, ref_mapping)
    matcher = SpatialCascadeMatcher(ref_index, similarity_threshold=80.0)

    # Level 1: Exact / Fuzzy Locality match
    res_loc = matcher.match_row(locality_val="Custom House IDP Camp")
    assert res_loc["MATCH_LEVEL"] == "Locality"
    assert res_loc["PCODE_ASSIGNED"] == "NG008018001001"
    assert res_loc["MATCH_SCORE"] == 100.0

    # Level 1 Fuzzy: Typo in locality
    res_loc_fuzz = matcher.match_row(locality_val="Muna Garage Camp")
    assert res_loc_fuzz["MATCH_LEVEL"] == "Locality"
    assert res_loc_fuzz["PCODE_ASSIGNED"] == "NG008013001001"
    assert res_loc_fuzz["MATCH_SCORE"] >= 80.0

    # Level 2: Fallback 1 -> Admin 3 / Ward match when locality is missing
    res_adm3 = matcher.match_row(locality_val="Unknown bush", admin3_val="Bolori II")
    assert res_adm3["MATCH_LEVEL"] == "Admin3_Ward"
    assert res_adm3["PCODE_ASSIGNED"] == "NG008018002"

    # Level 3: Fallback 2 -> Admin 2 / LGA match when locality and ward are missing
    res_adm2 = matcher.match_row(locality_val=None, admin3_val=None, admin2_val="Maiduguri LGA")
    assert res_adm2["MATCH_LEVEL"] == "Admin2_LGA"
    assert res_adm2["PCODE_ASSIGNED"] == "NG008018"

    # Level 4: Fallback 3 -> Admin 1 / State match
    res_adm1 = matcher.match_row(locality_val=None, admin3_val=None, admin2_val=None, admin1_val="Borno State")
    assert res_adm1["MATCH_LEVEL"] == "Admin1_State"
    assert res_adm1["PCODE_ASSIGNED"] == "NG008"

    # Level 5: Unmatched
    res_unmatch = matcher.match_row(locality_val="Outside Continent", admin1_val="Nowhere")
    assert res_unmatch["MATCH_LEVEL"] == "Unmatched"
    assert res_unmatch["PCODE_ASSIGNED"] is None


def test_spatial_cascade_custom_powerquery_like_reference():
    """Test matching with custom column names like in the user's Power Query workflow."""
    # Custom reference dataframe with columns: loc_nr, adm3, adm2, pcode, pcode_adm3, pcode_adm2, lat, long
    ref_data = pd.DataFrame({
        "loc_nr": ["Rue des Fleurs", "Quartier Médina", "Village Camp A"],
        "pcode": ["SEN_DK_001_01", "SEN_DK_001_02", "SEN_TH_002_01"],
        "adm3": ["Médina", "Médina", "Pout"],
        "pcode_adm3": ["SEN_DK_001", "SEN_DK_001", "SEN_TH_002"],
        "adm2": ["Dakar", "Dakar", "Thiès"],
        "pcode_adm2": ["SEN_DK", "SEN_DK", "SEN_TH"],
        "lat": [14.69, 14.70, 14.75],
        "long": [-17.44, -17.45, -16.92]
    })

    # Custom spatial mapping
    mapping = {
        "linelist_locality_col": "rq_norm",
        "locality_name": "loc_nr",
        "locality_pcode": "pcode",
        "linelist_admin3_col": "village",
        "admin3_name": "adm3",
        "admin3_pcode": "pcode_adm3",
        "linelist_admin2_col": "district",
        "admin2_name": "adm2",
        "admin2_pcode": "pcode_adm2",
        "lat": "lat",
        "long": "long"
    }

    ref_index = PCodeReferenceIndex(ref_data, mapping)
    matcher = SpatialCascadeMatcher(ref_index, similarity_threshold=80.0)

    # Linelist row 1: matches locality rq_norm -> Rue des Fleurs
    res1 = matcher.match_row(locality_val="Rue des Fleurs", admin3_val="Médina", admin2_val="Dakar")
    assert res1["MATCH_LEVEL"] == "Locality"
    assert res1["PCODE_ASSIGNED"] == "SEN_DK_001_01"  # Real PCode from reference
    assert res1["PCODE_LOCALITY"] == "SEN_DK_001_01"
    assert res1["PCODE_ADMIN3"] == "SEN_DK_001"
    assert res1["PCODE_ADMIN2"] == "SEN_DK"
    assert not str(res1["PCODE_ASSIGNED"]).startswith("LOC_")  # Never synthetic

    # Linelist row 2: locality is unknown, fallback to admin3 village -> Pout
    res2 = matcher.match_row(locality_val="Inconnu", admin3_val="Pout", admin2_val="Thiès")
    assert res2["MATCH_LEVEL"] == "Admin3_Ward"
    assert res2["PCODE_ASSIGNED"] == "SEN_TH_002"
    assert res2["PCODE_ADMIN3"] == "SEN_TH_002"
    assert not str(res2["PCODE_ASSIGNED"]).startswith("LOC_")

