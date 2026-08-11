"""
Epidemiological Chronological and Logic Rule Validator.
"""

import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from linelist_cleaner.schemas.models import ValidationIssue


def _to_date_obj(val: Any) -> Optional[datetime.date]:
    """Helper to convert string/date to datetime.date."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, datetime.date):
        return val
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, str):
        try:
            return datetime.date.fromisoformat(val[:10])
        except Exception:
            pass
    return None


class LogicValidator:
    """Validates epidemiological timelines, demographic logic, and clinical consistency."""

    def __init__(
        self,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
    ):
        self.min_date = _to_date_obj(min_date)
        self.max_date = _to_date_obj(max_date) or datetime.date.today()

    def validate(
        self,
        df: pd.DataFrame,
        tag_to_col: Dict[str, str]
    ) -> List[ValidationIssue]:
        """
        Runs all epidemiological validation checks against the DataFrame.
        tag_to_col maps canonical tags (e.g. 'date_onset', 'sex', 'age') to dataframe column names.
        """
        issues: List[ValidationIssue] = []

        # Helper to get series for a tag
        def get_series(tag: str) -> Optional[pd.Series]:
            col = tag_to_col.get(tag)
            if col and col in df.columns:
                return df[col]
            return None

        case_id_s = get_series("case_id")
        dob_s = get_series("date_birth")
        onset_s = get_series("date_onset")
        consult_s = get_series("date_consultation")
        admit_s = get_series("date_admission")
        discharge_s = get_series("date_discharge")
        death_s = get_series("date_death")
        sample_s = get_series("date_sample_collected")
        lab_res_date_s = get_series("date_lab_result")
        lab_result_s = get_series("lab_result")

        age_s = get_series("age")
        sex_s = get_series("sex")
        pregnant_s = get_series("pregnant")
        outcome_s = get_series("outcome")
        hospitalized_s = get_series("hospitalized")
        case_def_s = get_series("case_definition")

        for idx in range(len(df)):
            row_idx = idx + 1  # 1-based index for user reporting
            cid = str(case_id_s.iloc[idx]) if (case_id_s is not None and pd.notna(case_id_s.iloc[idx])) else f"Row {row_idx}"

            # 1. Mandatory ID check
            if case_id_s is not None and (pd.isna(case_id_s.iloc[idx]) or not str(case_id_s.iloc[idx]).strip()):
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=None,
                    column=tag_to_col.get("case_id"),
                    issue_type="MISSING_MANDATORY",
                    severity="ERROR",
                    message="Missing unique case identifier (case_id).",
                    raw_value=None,
                    suggested_action="Assign a unique case identifier."
                ))

            # Dates conversion
            d_dob = _to_date_obj(dob_s.iloc[idx]) if dob_s is not None else None
            d_onset = _to_date_obj(onset_s.iloc[idx]) if onset_s is not None else None
            d_consult = _to_date_obj(consult_s.iloc[idx]) if consult_s is not None else None
            d_admit = _to_date_obj(admit_s.iloc[idx]) if admit_s is not None else None
            d_discharge = _to_date_obj(discharge_s.iloc[idx]) if discharge_s is not None else None
            d_death = _to_date_obj(death_s.iloc[idx]) if death_s is not None else None
            d_sample = _to_date_obj(sample_s.iloc[idx]) if sample_s is not None else None
            d_lab_res = _to_date_obj(lab_res_date_s.iloc[idx]) if lab_res_date_s is not None else None

            # 2. Chronological sequence checks
            # DOB <= Onset
            if d_dob and d_onset and d_dob > d_onset:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_onset"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Date of symptom onset ({d_onset}) is before Date of Birth ({d_dob}).",
                    raw_value=str(d_onset),
                    suggested_action="Verify birth date and onset date."
                ))

            # Onset <= Consultation
            if d_onset and d_consult and d_onset > d_consult:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_consultation"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Date of consultation ({d_consult}) precedes Date of Onset ({d_onset}).",
                    raw_value=str(d_consult),
                    suggested_action="Check for inverted day/month or typos in consultation date."
                ))

            # Onset <= Admission
            if d_onset and d_admit and d_onset > d_admit:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_admission"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Date of admission ({d_admit}) precedes Date of Onset ({d_onset}).",
                    raw_value=str(d_admit),
                    suggested_action="Verify admission date."
                ))

            # Consultation <= Admission
            if d_consult and d_admit and d_consult > d_admit:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_admission"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="WARNING",
                    message=f"Date of hospital admission ({d_admit}) precedes Date of Consultation ({d_consult}).",
                    raw_value=str(d_admit),
                    suggested_action="Verify if patient was admitted directly before initial consult."
                ))

            # Admission <= Discharge
            if d_admit and d_discharge and d_admit > d_discharge:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_discharge"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Date of discharge ({d_discharge}) precedes Date of Admission ({d_admit}).",
                    raw_value=str(d_discharge),
                    suggested_action="Correct discharge date or swap inverted dates."
                ))

            # Onset <= Death
            if d_onset and d_death and d_onset > d_death:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_death"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Date of death ({d_death}) precedes Date of Onset ({d_onset}).",
                    raw_value=str(d_death),
                    suggested_action="Correct date of death."
                ))

            # Admission <= Death
            if d_admit and d_death and d_admit > d_death:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_death"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Date of death ({d_death}) precedes Date of Admission ({d_admit}).",
                    raw_value=str(d_death),
                    suggested_action="Check hospital death timeline."
                ))

            # Sample collection <= Lab result
            if d_sample and d_lab_res and d_sample > d_lab_res:
                issues.append(ValidationIssue(
                    row_idx=row_idx,
                    case_id=cid,
                    column=tag_to_col.get("date_lab_result"),
                    issue_type="DATE_CHRONOLOGY",
                    severity="ERROR",
                    message=f"Lab result date ({d_lab_res}) is prior to specimen collection date ({d_sample}).",
                    raw_value=str(d_lab_res),
                    suggested_action="Verify laboratory test report dates."
                ))

            # Future date check
            for d_val, t_name in [(d_onset, "date_onset"), (d_consult, "date_consultation"), (d_admit, "date_admission"), (d_death, "date_death")]:
                if d_val and self.max_date and d_val > self.max_date:
                    issues.append(ValidationIssue(
                        row_idx=row_idx,
                        case_id=cid,
                        column=tag_to_col.get(t_name),
                        issue_type="DATE_CHRONOLOGY",
                        severity="ERROR",
                        message=f"{t_name} ({d_val}) is in the future (after {self.max_date}).",
                        raw_value=str(d_val),
                        suggested_action="Check for century/year typo."
                    ))

            # 3. Demographic & Physiological checks
            if age_s is not None and pd.notna(age_s.iloc[idx]):
                try:
                    age_val = float(age_s.iloc[idx])
                    if age_val < 0:
                        issues.append(ValidationIssue(
                            row_idx=row_idx,
                            case_id=cid,
                            column=tag_to_col.get("age"),
                            issue_type="INVALID_AGE",
                            severity="ERROR",
                            message=f"Negative age value detected: {age_val}.",
                            raw_value=str(age_val),
                            suggested_action="Set to positive or check birth date."
                        ))
                    elif age_val > 120:
                        issues.append(ValidationIssue(
                            row_idx=row_idx,
                            case_id=cid,
                            column=tag_to_col.get("age"),
                            issue_type="INVALID_AGE",
                            severity="WARNING",
                            message=f"Implausibly high age value detected: {age_val} years.",
                            raw_value=str(age_val),
                            suggested_action="Verify if age was entered in months/days or has typo."
                        ))
                except (ValueError, TypeError):
                    pass

            # Pregnancy logic
            if pregnant_s is not None and sex_s is not None:
                preg_val = str(pregnant_s.iloc[idx]).strip().capitalize() if pd.notna(pregnant_s.iloc[idx]) else ""
                sex_val = str(sex_s.iloc[idx]).strip().capitalize() if pd.notna(sex_s.iloc[idx]) else ""
                if preg_val == "Yes" and sex_val == "Male":
                    issues.append(ValidationIssue(
                        row_idx=row_idx,
                        case_id=cid,
                        column=tag_to_col.get("pregnant"),
                        issue_type="INCONSISTENT_STATUS",
                        severity="ERROR",
                        message="Pregnancy recorded as 'Yes' for a Male patient.",
                        raw_value="Pregnant=Yes, Sex=Male",
                        suggested_action="Check patient sex or pregnancy field."
                    ))

            # 4. Clinical & Outcome consistency
            if outcome_s is not None and pd.notna(outcome_s.iloc[idx]):
                out_val = str(outcome_s.iloc[idx]).strip().capitalize()
                if out_val == "Dead" and d_death is None and death_s is not None:
                    issues.append(ValidationIssue(
                        row_idx=row_idx,
                        case_id=cid,
                        column=tag_to_col.get("date_death"),
                        issue_type="INCONSISTENT_STATUS",
                        severity="WARNING",
                        message="Patient outcome is 'Dead' but Date of Death is missing.",
                        raw_value=out_val,
                        suggested_action="Record date of death if available."
                    ))
                elif out_val in ["Recovered", "Discharged", "Alive"] and d_death is not None:
                    issues.append(ValidationIssue(
                        row_idx=row_idx,
                        case_id=cid,
                        column=tag_to_col.get("outcome"),
                        issue_type="INCONSISTENT_STATUS",
                        severity="ERROR",
                        message=f"Patient outcome is '{out_val}' but Date of Death ({d_death}) is recorded.",
                        raw_value=f"Outcome={out_val}, DateDeath={d_death}",
                        suggested_action="Verify vital status and death date."
                    ))

            # Hospitalized check
            if hospitalized_s is not None and pd.notna(hospitalized_s.iloc[idx]):
                hosp_val = str(hospitalized_s.iloc[idx]).strip().capitalize()
                if hosp_val == "No" and d_admit is not None:
                    issues.append(ValidationIssue(
                        row_idx=row_idx,
                        case_id=cid,
                        column=tag_to_col.get("hospitalized"),
                        issue_type="INCONSISTENT_STATUS",
                        severity="WARNING",
                        message=f"Hospitalized recorded as 'No' but Admission Date ({d_admit}) is present.",
                        raw_value=f"Hospitalized=No, DateAdmission={d_admit}",
                        suggested_action="Update hospitalized flag to 'Yes'."
                    ))

        return issues
