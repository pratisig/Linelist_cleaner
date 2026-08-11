"""
Master Orchestrator Pipeline for Epidemiological Linelist Cleaning and Spatial Cascade Geocoding.
"""

import io
import time
from typing import Dict, List, Optional, Tuple, Any, Union, Set
import pandas as pd
import numpy as np

from linelist_cleaner.schemas.config import CleaningConfig
from linelist_cleaner.schemas.models import (
    CleaningReport,
    CleaningLogEntry,
    ValidationIssue,
    DuplicateGroup,
    DataQualityScores,
    ColumnProfile,
    SpatialCascadeSummary,
)
from linelist_cleaner.schemas.epi_dictionary import CANONICAL_TAGS
from linelist_cleaner.core.column_standardizer import (
    standardize_dataframe_columns,
    map_linelist_columns,
)
from linelist_cleaner.core.categorical_cleaner import (
    clean_missing_sentinels_df,
    standardize_sex_value,
    standardize_case_definition_value,
    standardize_outcome_value,
    standardize_binary_value,
    harmonize_facility_names,
)
from linelist_cleaner.core.date_cleaner import DateCleaner, parse_single_date
from linelist_cleaner.core.age_cleaner import AgeCleaner
from linelist_cleaner.core.epi_week import EpiWeekProcessor
from linelist_cleaner.core.spatial_cascade import PCodeReferenceIndex, SpatialCascadeMatcher
from linelist_cleaner.core.logic_validator import LogicValidator
from linelist_cleaner.core.deduplicator import Deduplicator
from linelist_cleaner.core.anonymizer import Anonymizer
from linelist_cleaner.core.auditor import DataQualityAuditor
from linelist_cleaner.core.epi_analytics import EpiAnalytics
from linelist_cleaner.datasets import get_sample_dataset


def load_dataset(source: Union[str, bytes, io.BytesIO, pd.DataFrame]) -> pd.DataFrame:
    """Loads dataframe from filepath, bytes, buffer, or DataFrame."""
    if isinstance(source, pd.DataFrame):
        return source.copy()

    if isinstance(source, bytes):
        source = io.BytesIO(source)

    if isinstance(source, io.BytesIO):
        try:
            return pd.read_excel(source)
        except Exception:
            source.seek(0)
            return pd.read_csv(source)

    if isinstance(source, str):
        if source.endswith((".xlsx", ".xls")):
            return pd.read_excel(source)
        elif source.endswith(".tsv"):
            return pd.read_csv(source, sep="\t")
        elif source.endswith(".json"):
            return pd.read_json(source)
        else:
            return pd.read_csv(source)

    raise ValueError("Unsupported data source format.")


class LinelistCleaner:
    """Production-grade Linelist Cleaning and Spatial Cascade Geocoding Engine."""

    def __init__(self, config: Optional[CleaningConfig] = None):
        self.config = config or CleaningConfig()

    def clean(
        self,
        source: Union[str, bytes, io.BytesIO, pd.DataFrame],
        custom_mapping: Optional[Dict[str, str]] = None,
        reference_pcode_df: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Executes the end-to-end linelist cleaning and spatial cascade pipeline.
        Returns: (cleaned_df, CleaningReport)
        """
        start_time = time.time()
        df_raw = load_dataset(source)
        original_shape = df_raw.shape
        logs: List[CleaningLogEntry] = []

        df_curr = df_raw.copy()

        # Step 1: Standardize Column Headers
        renamed_cols_map: Dict[str, str] = {}
        if self.config.standardize_headers:
            df_curr, renamed_cols_map = standardize_dataframe_columns(df_curr)
            logs.append(CleaningLogEntry(
                step="Standardize Headers",
                action="Converted column names to snake_case and removed special characters",
                affected_rows=0,
                affected_columns=list(renamed_cols_map.values()),
                details=renamed_cols_map
            ))

        # Step 2: Clean Missing Sentinels
        missing_count = 0
        if self.config.standardize_missing_values:
            df_curr, missing_count = clean_missing_sentinels_df(
                df_curr,
                custom_sentinels=self.config.custom_missing_sentinels
            )
            logs.append(CleaningLogEntry(
                step="Handle Missing Values",
                action="Standardized missing tokens ('NA', '-99', '999', 'unknown') to null",
                affected_rows=missing_count,
                affected_columns=list(df_curr.columns),
                details={"sentinels_cleaned": missing_count}
            ))

        # Step 3: Semantic Column Mapping
        mapping_res = map_linelist_columns(
            df_curr,
            similarity_threshold=0.78,
            custom_mapping=custom_mapping or self.config.column_mapping
        )
        tag_to_col: Dict[str, str] = {}
        mapped_summary: Dict[str, str] = {}

        for col, meta in mapping_res.items():
            if meta["is_mapped"] and meta["mapped_tag"]:
                tag = meta["mapped_tag"]
                tag_to_col[tag] = col
                mapped_summary[col] = tag

        logs.append(CleaningLogEntry(
            step="Semantic Column Mapping",
            action="Mapped raw columns to standard epidemiological and geographic variables",
            affected_rows=0,
            affected_columns=list(mapped_summary.keys()),
            details=mapped_summary
        ))

        # Initial quality baseline assessment
        validator = LogicValidator(
            min_date=self.config.outbreak_start_date,
            max_date=self.config.outbreak_end_date
        )
        initial_issues = validator.validate(df_curr, tag_to_col)
        deduper = Deduplicator(
            fuzzy_threshold=self.config.fuzzy_similarity_threshold,
            method=self.config.dedup_method,
            action=self.config.dedup_action
        )
        initial_dups = deduper.find_duplicates(df_curr, tag_to_col)
        qs_before = DataQualityAuditor.calculate_quality_scores(
            df_curr, initial_issues, initial_dups, tag_to_col
        )

        # Step 4: Date Standardization & WHO EpiWeek Computation
        dates_cleaned_count: Dict[str, int] = {}
        epi_weeks_count = 0
        if self.config.standardize_dates:
            date_cleaner = DateCleaner(
                output_format=self.config.date_output_format,
                day_first_preference=self.config.date_order_preference
            )

            date_cols_to_clean: Set[str] = set()
            for tag, col in tag_to_col.items():
                if CANONICAL_TAGS.get(tag, {}).get("type") == "date" and col in df_curr.columns:
                    date_cols_to_clean.add(col)

            for col in df_curr.columns:
                if any(kw in col.lower() for kw in ["date", "dt_", "_dt", "fecha", "jour"]):
                    date_cols_to_clean.add(col)

            for d_col in date_cols_to_clean:
                clean_s, d_stats = date_cleaner.clean_column(df_curr[d_col], col_name=d_col)
                df_curr[d_col] = clean_s
                dates_cleaned_count[d_col] = d_stats["successfully_parsed"]

            # Compute WHO EpiWeeks on primary admission/onset date
            if self.config.compute_epi_weeks:
                primary_date_col = tag_to_col.get("date_admission") or tag_to_col.get("date_onset") or tag_to_col.get("date_consultation")
                if not primary_date_col and date_cols_to_clean:
                    primary_date_col = list(date_cols_to_clean)[0]

                if primary_date_col and primary_date_col in df_curr.columns:
                    day_first_pref = (self.config.date_order_preference != "MDY")
                    processor = EpiWeekProcessor(day_first=day_first_pref)
                    clean_d, epi_w, epi_wn, epi_y = processor.process_series(df_curr[primary_date_col])

                    df_curr["DATE_ADMISSION_CLEAN"] = clean_d
                    df_curr["EPI_WEEK"] = epi_w
                    df_curr["EPI_WEEK_NUM"] = epi_wn
                    df_curr["EPI_YEAR"] = epi_y
                    epi_weeks_count = int(epi_w.notna().sum())

            logs.append(CleaningLogEntry(
                step="Date & EpiWeek Processing",
                action="Standardized dates to ISO and computed WHO EpiWeeks (EPI_WEEK, EPI_WEEK_NUM)",
                affected_rows=sum(dates_cleaned_count.values()),
                affected_columns=list(date_cols_to_clean) + (["EPI_WEEK", "EPI_WEEK_NUM", "DATE_ADMISSION_CLEAN"] if self.config.compute_epi_weeks else []),
                details=dates_cleaned_count
            ))

        # Step 5: Spatial Fallback Cascade Geocoding (P-Code Matching)
        spatial_summary: Optional[SpatialCascadeSummary] = None
        if self.config.enable_spatial_cascade:
            ref_df = reference_pcode_df
            if ref_df is None:
                # Load default OCHA COD-AB reference
                ref_df = get_sample_dataset("pcode_reference")

            if ref_df is not None and not ref_df.empty:
                ref_index = PCodeReferenceIndex(ref_df, self.config.spatial_reference_mapping)
                matcher = SpatialCascadeMatcher(
                    ref_index,
                    similarity_threshold=self.config.spatial_similarity_threshold
                )

                col_loc = tag_to_col.get("admin3") or tag_to_col.get("health_facility")
                col_a3 = tag_to_col.get("admin3")
                col_a2 = tag_to_col.get("admin2")
                col_a1 = tag_to_col.get("admin1")

                # Fallback to column name scanning if not mapped
                for c in df_curr.columns:
                    c_low = c.lower()
                    if not col_loc and any(k in c_low for k in ["localit", "village", "site", "camp", "settlement"]):
                        col_loc = c
                    if not col_a3 and any(k in c_low for k in ["ward", "subdistrict", "aire"]):
                        col_a3 = c
                    if not col_a2 and any(k in c_low for k in ["lga", "district", "zone"]):
                        col_a2 = c
                    if not col_a1 and any(k in c_low for k in ["state", "province", "region"]):
                        col_a1 = c

                df_curr, sp_stats = matcher.process_dataframe(
                    df_curr,
                    col_locality=col_loc,
                    col_admin3=col_a3,
                    col_admin2=col_a2,
                    col_admin1=col_a1
                )

                spatial_summary = SpatialCascadeSummary(**sp_stats)
                logs.append(CleaningLogEntry(
                    step="Spatial Fallback Cascade",
                    action=f"Executed 5-level cascade geocoding (Geocoded Rate: {sp_stats['geocoded_rate_pct']}%)",
                    affected_rows=sp_stats["geocoded_count"],
                    affected_columns=["PCODE_ASSIGNED", "MATCH_LEVEL", "MATCH_SCORE", "MATCHED_NAME", "LATITUDE", "LONGITUDE"],
                    details=sp_stats
                ))

        # Step 6: Demographic & Categorical Standardization
        # Sex
        if self.config.standardize_sex and "sex" in tag_to_col:
            sex_col = tag_to_col["sex"]
            if sex_col in df_curr.columns:
                df_curr[sex_col] = df_curr[sex_col].apply(standardize_sex_value)

        # Age & Age Groups
        ages_cleaned_count = 0
        if self.config.standardize_ages and "age" in tag_to_col:
            age_col = tag_to_col["age"]
            unit_col = tag_to_col.get("age_unit")
            unit_s = df_curr[unit_col] if unit_col and unit_col in df_curr.columns else None

            if age_col in df_curr.columns:
                age_cleaner = AgeCleaner(
                    breaks=self.config.age_group_breaks,
                    labels=self.config.age_group_labels
                )
                clean_ages, age_groups, age_stats = age_cleaner.clean_age_column(
                    df_curr[age_col], unit_series=unit_s
                )
                df_curr[age_col] = clean_ages
                ages_cleaned_count = age_stats["parsed_count"]

                if self.config.create_age_groups:
                    age_idx = df_curr.columns.get_loc(age_col)
                    df_curr.insert(age_idx + 1, "age_group", age_groups)

        # Case Classification
        if self.config.standardize_case_definitions and "case_definition" in tag_to_col:
            cdef_col = tag_to_col["case_definition"]
            if cdef_col in df_curr.columns:
                df_curr[cdef_col] = df_curr[cdef_col].apply(standardize_case_definition_value)

        # Outcome
        if self.config.standardize_outcomes and "outcome" in tag_to_col:
            out_col = tag_to_col["outcome"]
            if out_col in df_curr.columns:
                df_curr[out_col] = df_curr[out_col].apply(standardize_outcome_value)

        # Binary Symptoms
        if self.config.standardize_binary_fields:
            binary_tags = ["hospitalized", "vaccinated", "pregnant", "fever", "cough", "diarrhea", "vomiting", "bleeding", "rash"]
            for b_tag in binary_tags:
                col = tag_to_col.get(b_tag)
                if col and col in df_curr.columns:
                    df_curr[col] = df_curr[col].apply(standardize_binary_value)

        # Facility Harmonization
        if "health_facility" in tag_to_col:
            fac_col = tag_to_col["health_facility"]
            if fac_col in df_curr.columns:
                harmonized_fac, fac_map = harmonize_facility_names(df_curr[fac_col])
                df_curr[fac_col] = harmonized_fac

        # Step 7: Epidemiological Logic Validation
        final_issues = validator.validate(df_curr, tag_to_col)
        issues_by_sev = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        issues_by_type = {}
        for iss in final_issues:
            issues_by_sev[iss.severity] = issues_by_sev.get(iss.severity, 0) + 1
            issues_by_type[iss.issue_type] = issues_by_type.get(iss.issue_type, 0) + 1

        # Step 8: Deduplication
        dup_groups: List[DuplicateGroup] = []
        dups_removed = 0
        if self.config.detect_duplicates:
            dup_groups = deduper.find_duplicates(df_curr, tag_to_col)
            df_curr, dups_removed = deduper.resolve_duplicates(df_curr, dup_groups)

        # Step 9: Anonymization
        if self.config.anonymize:
            anonymizer = Anonymizer(
                method=self.config.anonymize_method,
                fields_to_anonymize=self.config.anonymize_fields
            )
            df_curr, anon_cols = anonymizer.anonymize_dataframe(df_curr, tag_to_col)

        # Step 10: Final Quality Assessment & Column Profiling
        qs_after = DataQualityAuditor.calculate_quality_scores(
            df_curr, final_issues, dup_groups, tag_to_col
        )
        col_profiles = DataQualityAuditor.profile_columns(
            df_curr, tag_to_col, final_issues
        )

        exec_time = round((time.time() - start_time) * 1000, 2)

        report = CleaningReport(
            original_shape=original_shape,
            cleaned_shape=df_curr.shape,
            quality_scores_before=qs_before,
            quality_scores_after=qs_after,
            columns_mapped=mapped_summary,
            columns_renamed=renamed_cols_map,
            dates_standardized=dates_cleaned_count,
            epi_weeks_computed=epi_weeks_count,
            spatial_summary=spatial_summary,
            ages_standardized=ages_cleaned_count,
            missing_values_converted=missing_count,
            duplicates_detected=len(dup_groups),
            duplicates_resolved=dups_removed,
            duplicate_groups=dup_groups,
            validation_issues=final_issues,
            issues_by_severity=issues_by_sev,
            issues_by_type=issues_by_type,
            column_profiles=col_profiles,
            cleaning_logs=logs,
            execution_time_ms=exec_time
        )

        return df_curr, report

    @staticmethod
    def export_excel(
        df_clean: pd.DataFrame,
        report: CleaningReport,
        output_path_or_buffer: Any,
        reference_df: Optional[pd.DataFrame] = None
    ) -> None:
        """Exports the 3-tab Excel report workbook (KPI_Dashboard, LineList_Nettoyee, Referentiel_PCode)."""
        DataQualityAuditor.export_excel_audit_workbook(df_clean, report, output_path_or_buffer, ref_df=reference_df)

    @staticmethod
    def export_csv(df_clean: pd.DataFrame, output_path_or_buffer: Any) -> None:
        """Exports cleaned linelist as CSV."""
        df_clean.to_csv(output_path_or_buffer, index=False)

    @staticmethod
    def generate_reproducible_python_script(config: CleaningConfig) -> str:
        """Generates reproducible Python script for spatial cascade geocoding."""
        return f'''"""
Reproducible Linelist Cleaning & Spatial Fallback Cascade Pipeline
Generated automatically by Linelist Cleaner.
"""

import pandas as pd
from linelist_cleaner import LinelistCleaner, CleaningConfig
from linelist_cleaner.datasets import get_sample_dataset

# 1. Configuration with Spatial Fallback Cascade
config = CleaningConfig(
    standardize_headers={config.standardize_headers},
    auto_map_epi_tags={config.auto_map_epi_tags},
    standardize_dates={config.standardize_dates},
    compute_epi_weeks={config.compute_epi_weeks},
    enable_spatial_cascade={config.enable_spatial_cascade},
    spatial_similarity_threshold={config.spatial_similarity_threshold},
    standardize_sex={config.standardize_sex},
    standardize_ages={config.standardize_ages},
    create_age_groups={config.create_age_groups},
    validate_chronology={config.validate_chronology},
    detect_duplicates={config.detect_duplicates},
    dedup_action="{config.dedup_action}"
)

# 2. Load Raw Line List and P-Code Reference Dataset
print("Loading raw line list and spatial reference...")
raw_linelist = pd.read_csv("cholera_borno_field_linelist.csv")
pcode_reference = pd.read_csv("ocha_pcode_reference_nigeria.csv")

# 3. Initialize Cleaner and Execute Pipeline
cleaner = LinelistCleaner(config=config)
cleaned_df, report = cleaner.clean(raw_linelist, reference_pcode_df=pcode_reference)

# 4. Save 3-Tab Excel Workbook
output_excel = "Linelist_Nettoyee_PCode_Report.xlsx"
cleaner.export_excel(cleaned_df, report, output_excel, reference_df=pcode_reference)

print(f"Pipeline executed successfully!")
print(f"Geocoding Rate: {{report.spatial_summary.geocoded_rate_pct}}%")
print(f"Cleaned shape: {{report.cleaned_shape}}")
print(f"Output saved to: {{output_excel}}")
'''
