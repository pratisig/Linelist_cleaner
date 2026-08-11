"""Datasets module with sample outbreak datasets and OCHA COD-AB reference."""
import os
import pandas as pd
from linelist_cleaner.utils import get_resource_path
from linelist_cleaner.datasets.generator import (
    generate_cholera_linelist,
    generate_cholera_borno_linelist,
    generate_covid19_linelist,
    generate_ebola_linelist,
    generate_measles_linelist,
    generate_ocha_pcode_reference_nigeria,
    save_all_sample_datasets,
)

DATASET_DIR = get_resource_path(os.path.join("linelist_cleaner", "datasets"))
if not os.path.exists(DATASET_DIR):
    DATASET_DIR = os.path.dirname(os.path.abspath(__file__))


def get_sample_dataset(name: str = "cholera") -> pd.DataFrame:
    """Returns sample dataframe by disease type."""
    name_clean = name.lower().strip()
    path_map = {
        "cholera": os.path.join(DATASET_DIR, "cholera_outbreak_messy.csv"),
        "cholera_borno": os.path.join(DATASET_DIR, "cholera_borno_field_linelist.csv"),
        "borno": os.path.join(DATASET_DIR, "cholera_borno_field_linelist.csv"),
        "covid19": os.path.join(DATASET_DIR, "covid19_surveillance_messy.csv"),
        "covid": os.path.join(DATASET_DIR, "covid19_surveillance_messy.csv"),
        "ebola": os.path.join(DATASET_DIR, "ebola_evd_messy.csv"),
        "measles": os.path.join(DATASET_DIR, "measles_outbreak_messy.csv"),
        "pcode_reference": os.path.join(DATASET_DIR, "ocha_pcode_reference_nigeria.csv"),
        "pcode_nigeria": os.path.join(DATASET_DIR, "ocha_pcode_reference_nigeria.csv"),
    }

    if name_clean in path_map and os.path.exists(path_map[name_clean]):
        return pd.read_csv(path_map[name_clean])

    if "borno" in name_clean:
        return generate_cholera_borno_linelist()
    elif "pcode" in name_clean:
        return generate_ocha_pcode_reference_nigeria()
    elif "cholera" in name_clean:
        return generate_cholera_linelist()
    elif "covid" in name_clean:
        return generate_covid19_linelist()
    elif "ebola" in name_clean:
        return generate_ebola_linelist()
    elif "measles" in name_clean:
        return generate_measles_linelist()

    return generate_cholera_borno_linelist()


__all__ = [
    "get_sample_dataset",
    "generate_cholera_linelist",
    "generate_cholera_borno_linelist",
    "generate_covid19_linelist",
    "generate_ebola_linelist",
    "generate_measles_linelist",
    "generate_ocha_pcode_reference_nigeria",
    "save_all_sample_datasets",
]
