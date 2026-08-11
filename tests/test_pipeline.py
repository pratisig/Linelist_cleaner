import pandas as pd
import pytest
from linelist_cleaner.core.pipeline import LinelistCleaner
from linelist_cleaner.schemas.config import CleaningConfig
from linelist_cleaner.datasets import get_sample_dataset


def test_linelist_cleaner_pipeline_cholera():
    raw_df = get_sample_dataset("cholera")
    cleaner = LinelistCleaner()
    df_clean, report = cleaner.clean(raw_df)

    assert len(df_clean) > 0
    assert report.quality_scores_after.grade in ["A", "B", "C"]
    assert "age_group" in df_clean.columns
    assert len(report.cleaning_logs) > 0
    assert report.original_shape[0] == len(raw_df)


def test_linelist_cleaner_pipeline_borno_pcode():
    raw_df = get_sample_dataset("borno")
    ref_df = get_sample_dataset("pcode_reference")
    cleaner = LinelistCleaner()
    df_clean, report = cleaner.clean(raw_df, reference_pcode_df=ref_df)

    assert len(df_clean) > 0
    assert "PCODE_ASSIGNED" in df_clean.columns
    assert "MATCH_LEVEL" in df_clean.columns
    assert "EPI_WEEK" in df_clean.columns
    assert report.spatial_summary is not None
    assert report.spatial_summary.geocoded_rate_pct >= 70.0


def test_linelist_cleaner_pipeline_covid():
    raw_df = get_sample_dataset("covid19")
    cleaner = LinelistCleaner()
    df_clean, report = cleaner.clean(raw_df)

    assert len(df_clean) > 0
    assert report.quality_scores_after.grade in ["A", "B", "C"]


def test_generate_reproducible_script():
    config = CleaningConfig()
    script = LinelistCleaner.generate_reproducible_python_script(config)
    assert "LinelistCleaner" in script
    assert "config" in script
