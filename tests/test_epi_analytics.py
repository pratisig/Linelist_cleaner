import pandas as pd
import pytest
from linelist_cleaner.core.epi_analytics import EpiAnalytics


def test_epi_analytics():
    df = pd.DataFrame({
        "case_id": ["C1", "C2", "C3", "C4"],
        "sex": ["Male", "Female", "Male", "Female"],
        "age": [10, 25, 45, 70],
        "date_onset": ["2023-01-01", "2023-01-01", "2023-01-02", "2023-01-03"],
        "date_admission": ["2023-01-02", "2023-01-03", None, "2023-01-04"],
        "date_discharge": ["2023-01-05", "2023-01-08", None, "2023-01-09"],
        "outcome": ["Recovered", "Dead", "Recovered", "Recovered"],
        "case_definition": ["Confirmed", "Confirmed", "Probable", "Suspect"]
    })
    tag_to_col = {
        "case_id": "case_id",
        "sex": "sex",
        "age": "age",
        "date_onset": "date_onset",
        "date_admission": "date_admission",
        "date_discharge": "date_discharge",
        "outcome": "outcome",
        "case_definition": "case_definition"
    }

    epi = EpiAnalytics(df, tag_to_col)
    ind = epi.get_summary_indicators()

    assert ind["total_cases"] == 4
    assert ind["deaths"] == 1
    assert ind["case_fatality_ratio_pct"] == 25.0
    assert ind["male_count"] == 2
    assert ind["female_count"] == 2

    # EpiCurve
    curve = epi.get_epi_curve(time_unit="day", stratify_by="case_definition")
    assert "2023-01-01" in curve["periods"]

    # Delays
    delays = epi.get_delay_distributions()
    assert delays["hospital_length_of_stay"] is not None
    assert delays["hospital_length_of_stay"]["median_days"] == 5.0
