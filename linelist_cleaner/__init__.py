"""
Linelist Cleaner: Comprehensive Epidemiological Data Cleaning, Logic Validation, and Profiling Engine.
"""

from linelist_cleaner.schemas.config import CleaningConfig
from linelist_cleaner.schemas.models import (
    ValidationIssue,
    CleaningLogEntry,
    ColumnProfile,
    DataQualityScores,
    DuplicateGroup,
    CleaningReport,
    OutbreakAlert,
    IncidenceTrend,
)
from linelist_cleaner.schemas.epi_dictionary import CANONICAL_TAGS
from linelist_cleaner.core.pipeline import LinelistCleaner, load_dataset
from linelist_cleaner.core.column_standardizer import (
    clean_string_identifier,
    standardize_dataframe_columns,
    map_linelist_columns,
)
from linelist_cleaner.core.date_cleaner import DateCleaner, parse_single_date
from linelist_cleaner.core.age_cleaner import AgeCleaner, parse_age_string, categorize_age
from linelist_cleaner.core.categorical_cleaner import (
    standardize_sex_value,
    standardize_case_definition_value,
    standardize_outcome_value,
    standardize_binary_value,
    harmonize_facility_names,
)
from linelist_cleaner.core.logic_validator import LogicValidator
from linelist_cleaner.core.deduplicator import Deduplicator
from linelist_cleaner.core.anonymizer import Anonymizer
from linelist_cleaner.core.epi_analytics import EpiAnalytics
from linelist_cleaner.core.auditor import DataQualityAuditor
from linelist_cleaner.datasets import get_sample_dataset

__version__ = "2.0.0"
__version_v2__ = "2.0.0"

__all__ = [
    "LinelistCleaner",
    "CleaningConfig",
    "CleaningReport",
    "ValidationIssue",
    "CleaningLogEntry",
    "ColumnProfile",
    "DataQualityScores",
    "DuplicateGroup",
    "OutbreakAlert",
    "IncidenceTrend",
    "CANONICAL_TAGS",
    "DateCleaner",
    "AgeCleaner",
    "LogicValidator",
    "Deduplicator",
    "Anonymizer",
    "EpiAnalytics",
    "DataQualityAuditor",
    "clean_string_identifier",
    "standardize_dataframe_columns",
    "map_linelist_columns",
    "parse_single_date",
    "parse_age_string",
    "categorize_age",
    "standardize_sex_value",
    "standardize_case_definition_value",
    "standardize_outcome_value",
    "standardize_binary_value",
    "harmonize_facility_names",
    "load_dataset",
    "get_sample_dataset",
]
