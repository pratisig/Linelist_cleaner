"""
Configuration settings for the Linelist Cleaner pipeline.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CleaningConfig(BaseModel):
    """Configurable rules and preferences for cleaning epidemiological linelists and spatial cascade geocoding."""

    # Column standardization
    standardize_headers: bool = Field(
        True,
        description="Convert header names to snake_case, strip whitespace, remove special symbols and accents."
    )
    auto_map_epi_tags: bool = Field(
        True,
        description="Automatically detect and map standard epidemiological columns (case_id, onset_date, etc.)."
    )
    column_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Explicit user-supplied column mapping dictionary: {'raw_col': 'canonical_tag'}."
    )

    # Missing value handling
    standardize_missing_values: bool = Field(
        True,
        description="Replace sentinel missing tokens ('NA', '-99', '999', 'unknown') with NaN/None."
    )
    custom_missing_sentinels: List[str] = Field(
        default_factory=list,
        description="Additional user-defined tokens to treat as missing values."
    )

    # Date parsing & WHO EpiWeek standardization
    standardize_dates: bool = Field(
        True,
        description="Parse and standardize all detected date columns into ISO YYYY-MM-DD format and compute WHO EpiWeeks."
    )
    date_output_format: str = Field(
        "%Y-%m-%d",
        description="Output date format string (default '%Y-%m-%d')."
    )
    date_order_preference: str = Field(
        "auto",
        description="Preferred order when ambiguous (e.g. 05/06/2023): 'auto', 'DMY', 'MDY', 'YMD'."
    )
    compute_epi_weeks: bool = Field(
        True,
        description="Automatically calculate WHO Epidemiological Year and Week (EPI_WEEK, EPI_WEEK_NUM)."
    )

    # Spatial Fallback Cascade (P-Code Matching)
    enable_spatial_cascade: bool = Field(
        True,
        description="Enable hierarchical spatial cascade geocoding (Locality -> Admin3 -> Admin2 -> Admin1 -> Unmatched)."
    )
    spatial_similarity_threshold: float = Field(
        80.0,
        description="Minimum fuzzy matching similarity score threshold (0-100%) for spatial cascade."
    )
    spatial_reference_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
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
        },
        description="Column mapping for the P-Code reference dataset."
    )

    # Demographic & Categorical Standardization
    standardize_sex: bool = Field(
        True,
        description="Standardize sex/gender column values to 'Male', 'Female', 'Other', 'Unknown'."
    )
    standardize_outcomes: bool = Field(
        True,
        description="Standardize outcome column values to 'Alive', 'Dead', 'Recovered', 'Discharged', 'Transferred', 'LAMA', 'Unknown'."
    )
    standardize_case_definitions: bool = Field(
        True,
        description="Standardize case classification to 'Confirmed', 'Probable', 'Suspect', 'Discarded', 'Unknown'."
    )
    standardize_binary_fields: bool = Field(
        True,
        description="Standardize symptom/boolean columns to 'Yes', 'No', 'Unknown'."
    )
    standardize_ages: bool = Field(
        True,
        description="Parse string age expressions (e.g. '6m', '18 mos', '45yo', '2 weeks') to standardized decimal years."
    )
    create_age_groups: bool = Field(
        True,
        description="Automatically generate age group categories (e.g., '<5', '5-14', '15-29', '30-49', '50-64', '65+')."
    )
    age_group_breaks: List[int] = Field(
        default_factory=lambda: [0, 5, 15, 30, 50, 65, 80],
        description="Cut-off points for creating age groups."
    )
    age_group_labels: Optional[List[str]] = Field(
        None,
        description="Optional custom labels for age groups."
    )

    # Logic & Chronology Validation
    validate_chronology: bool = Field(
        True,
        description="Validate logical sequence of epidemiological dates."
    )
    validate_demographics: bool = Field(
        True,
        description="Validate plausible ages (0-120) and pregnancy rules."
    )
    validate_clinical_logic: bool = Field(
        True,
        description="Validate clinical consistency."
    )
    outbreak_start_date: Optional[str] = None
    outbreak_end_date: Optional[str] = None

    # Deduplication
    detect_duplicates: bool = Field(
        True,
        description="Detect exact and fuzzy duplicate patient records."
    )
    dedup_method: str = Field(
        "both",
        description="Method for duplicate detection: 'exact', 'fuzzy', 'both', 'none'."
    )
    dedup_action: str = Field(
        "flag",
        description="Action on duplicates: 'flag', 'keep_first', 'keep_most_complete', 'merge'."
    )
    fuzzy_similarity_threshold: float = Field(
        0.80,
        description="Similarity threshold (0.0 - 1.0) for fuzzy duplicate matching."
    )

    # Anonymization / De-identification
    anonymize: bool = Field(
        False,
        description="Anonymize or strip personally identifiable information."
    )
    anonymize_method: str = Field(
        "pseudonymize",
        description="Anonymization strategy: 'pseudonymize', 'mask', 'hash', 'drop'."
    )
    anonymize_fields: List[str] = Field(
        default_factory=lambda: ["full_name", "first_name", "last_name", "phone", "address", "national_id"],
        description="Column tags to anonymize."
    )

    # V2: Extended Cleaning & Intelligence
    clean_coordinates: bool = Field(
        True,
        description="V2: Validate and standardize GPS coordinates (lat/lon) and detect swapped coords."
    )
    clean_phone_numbers: bool = Field(
        True,
        description="V2: Standardize phone numbers to international format."
    )
    default_phone_country_code: str = Field(
        "+221",
        description="Default country code for phone normalization (e.g., +221 Senegal, +234 Nigeria)."
    )
    detect_outbreak_signals: bool = Field(
        True,
        description="V2: Enable outbreak alert detection based on EpiWeek anomaly thresholds."
    )
    outbreak_alert_threshold_multiplier: float = Field(
        1.5,
        description="Multiplier over baseline mean for outbreak alert."
    )
    preset: Optional[str] = Field(
        None,
        description="V2: Preset configuration ('cholera', 'measles', 'ebola', 'covid19', 'generic')."
    )

    @property
    def resolved_preset(self) -> Optional[str]:
        return self.preset.lower().strip() if self.preset else None

    def apply_preset(self) -> "CleaningConfig":
        """Apply disease-specific presets (mutates and returns self)."""
        p = self.resolved_preset
        if not p:
            return self
        presets = {
            "cholera": {"age_group_breaks": [0, 5, 15, 30, 50, 65, 80], "spatial_similarity_threshold": 78.0},
            "measles": {"age_group_breaks": [0, 1, 5, 10, 15, 30, 50], "spatial_similarity_threshold": 80.0},
            "ebola": {"age_group_breaks": [0, 5, 15, 30, 50, 65, 80], "spatial_similarity_threshold": 85.0, "validate_clinical_logic": True},
            "covid19": {"age_group_breaks": [0, 10, 20, 30, 40, 50, 60, 70, 80], "spatial_similarity_threshold": 80.0},
            "covid": {"age_group_breaks": [0, 10, 20, 30, 40, 50, 60, 70, 80], "spatial_similarity_threshold": 80.0},
        }
        if p in presets:
            for k, v in presets[p].items():
                setattr(self, k, v)
        return self
