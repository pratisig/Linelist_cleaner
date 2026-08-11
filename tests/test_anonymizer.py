import pandas as pd
import pytest
from linelist_cleaner.core.anonymizer import Anonymizer, mask_string, hash_string


def test_mask_string():
    assert mask_string("John Doe") == "J**n D*e"
    assert mask_string("A") == "A"


def test_hash_string():
    h1 = hash_string("John Doe")
    h2 = hash_string("john doe")
    assert h1.startswith("HASH_")
    assert h1 == h2  # Case insensitive determinism


def test_anonymizer_pipeline():
    df = pd.DataFrame({
        "case_id": ["C1", "C2"],
        "name": ["Alice Wonderland", "Bob Builder"],
        "phone": ["+1234567890", "+1987654321"],
        "age": [25, 40]
    })
    tag_to_col = {"case_id": "case_id", "full_name": "name", "phone": "phone"}

    anon = Anonymizer(method="pseudonymize")
    df_anon, modified = anon.anonymize_dataframe(df, tag_to_col)

    assert "name" in modified
    assert df_anon["name"].iloc[0].startswith("PATIENT_")
    assert df_anon["age"].iloc[0] == 25
