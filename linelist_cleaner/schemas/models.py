"""
Data Models for Linelist Cleaner.
Includes models for validation issues, spatial cascade summary, audit entries, and cleaning reports.
"""

from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Represents a single data quality or epidemiological rule violation."""
    row_idx: int = Field(..., description="1-based row number in dataset")
    case_id: Optional[str] = Field(None, description="Case identifier if available")
    column: Optional[str] = Field(None, description="Column name with issue")
    issue_type: str = Field(..., description="Category of issue (e.g., DATE_CHRONOLOGY, INVALID_AGE)")
    severity: str = Field("WARNING", description="Severity level: ERROR, WARNING, INFO")
    message: str = Field(..., description="Human-readable explanation of the issue")
    raw_value: Optional[Any] = Field(None, description="Raw value that triggered the issue")
    suggested_action: Optional[str] = Field(None, description="Action recommended or taken to fix issue")


class CleaningLogEntry(BaseModel):
    """Log entry for an action taken during the cleaning pipeline."""
    step: str = Field(..., description="Cleaning stage name")
    action: str = Field(..., description="Short description of action")
    affected_rows: int = Field(0, description="Count of affected rows")
    affected_columns: List[str] = Field(default_factory=list, description="List of columns modified")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context/metadata")


class ColumnProfile(BaseModel):
    """Profiling metrics for a single column."""
    column_name: str
    inferred_type: str
    mapped_tag: Optional[str] = None
    total_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    top_values: Dict[str, int] = Field(default_factory=dict)
    sample_values: List[str] = Field(default_factory=list)
    issue_count: int = 0


class DataQualityScores(BaseModel):
    """Decomposed data quality index scores (0-100%)."""
    overall_score: float = Field(..., description="Overall weighted quality score (0-100)")
    grade: str = Field("A", description="Letter grade: A (>=90), B (>=80), C (>=70), D (>=60), F (<60)")
    completeness_score: float = Field(..., description="Completeness score based on missingness")
    chronology_score: float = Field(..., description="Chronological and logic consistency score")
    validity_score: float = Field(..., description="Data type and format validity score")
    uniqueness_score: float = Field(..., description="Duplicate-free score")


class DuplicateGroup(BaseModel):
    """Group of detected duplicate records."""
    group_id: int
    duplicate_type: str = Field("fuzzy", description="'exact' or 'fuzzy'")
    match_score: float = 1.0
    matching_keys: Dict[str, Any] = Field(default_factory=dict)
    row_indices: List[int] = Field(default_factory=list)
    case_ids: List[str] = Field(default_factory=list)
    recommended_keep_idx: int


class SpatialCascadeSummary(BaseModel):
    """Metrics and distribution for hierarchical spatial cascade geocoding."""
    total_records: int = 0
    geocoded_count: int = 0
    geocoded_rate_pct: float = 0.0
    average_match_score: float = 0.0
    level_distribution: Dict[str, int] = Field(default_factory=lambda: {
        "Locality": 0, "Admin3_Ward": 0, "Admin2_LGA": 0, "Admin1_State": 0, "Unmatched": 0
    })
    level_percentages: Dict[str, float] = Field(default_factory=dict)


class CleaningReport(BaseModel):
    """Comprehensive report returned after linelist cleaning pipeline execution."""
    original_shape: Tuple[int, int]
    cleaned_shape: Tuple[int, int]
    quality_scores_before: DataQualityScores
    quality_scores_after: DataQualityScores
    columns_mapped: Dict[str, str] = Field(default_factory=dict)
    columns_renamed: Dict[str, str] = Field(default_factory=dict)
    dates_standardized: Dict[str, int] = Field(default_factory=dict)
    epi_weeks_computed: int = 0
    spatial_summary: Optional[SpatialCascadeSummary] = None
    ages_standardized: int = 0
    missing_values_converted: int = 0
    duplicates_detected: int = 0
    duplicates_resolved: int = 0
    duplicate_groups: List[DuplicateGroup] = Field(default_factory=list)
    validation_issues: List[ValidationIssue] = Field(default_factory=list)
    issues_by_severity: Dict[str, int] = Field(default_factory=lambda: {"ERROR": 0, "WARNING": 0, "INFO": 0})
    issues_by_type: Dict[str, int] = Field(default_factory=dict)
    column_profiles: Dict[str, ColumnProfile] = Field(default_factory=dict)
    cleaning_logs: List[CleaningLogEntry] = Field(default_factory=list)
    execution_time_ms: float = 0.0
