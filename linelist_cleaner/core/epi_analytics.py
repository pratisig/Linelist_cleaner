"""
Epidemiological Analytics, EpiCurve Generator, and Key Indicator Calculator.
"""

import datetime
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np


class EpiAnalytics:
    """Computes epidemiological summary statistics, epi curves, delay distributions, and demographic pyramids."""

    def __init__(self, df: pd.DataFrame, tag_to_col: Dict[str, str]):
        self.df = df
        self.tag_to_col = tag_to_col

    def _get_series(self, tag: str) -> Optional[pd.Series]:
        col = self.tag_to_col.get(tag)
        if col and col in self.df.columns:
            return self.df[col]
        return None

    def get_summary_indicators(self) -> Dict[str, Any]:
        """Calculates key public health indicators: CFR, Hospitalization Rate, Sex Ratio, Median Age."""
        n_total = len(self.df)
        if n_total == 0:
            return {}

        outcome_s = self._get_series("outcome")
        case_def_s = self._get_series("case_definition")
        sex_s = self._get_series("sex")
        age_s = self._get_series("age")
        hosp_s = self._get_series("hospitalized")

        # Deaths & CFR
        deaths = 0
        recovered = 0
        if outcome_s is not None:
            deaths = int((outcome_s.str.lower() == "dead").sum())
            recovered = int((outcome_s.str.lower() == "recovered").sum())

        cfr_total = round((deaths / n_total) * 100, 2) if n_total > 0 else 0.0
        closed_cases = deaths + recovered
        cfr_closed = round((deaths / closed_cases) * 100, 2) if closed_cases > 0 else cfr_total

        # Hospitalization
        hosp_count = 0
        if hosp_s is not None:
            hosp_count = int((hosp_s.str.lower() == "yes").sum())
        elif self._get_series("date_admission") is not None:
            hosp_count = int(self._get_series("date_admission").notna().sum())
        hosp_rate = round((hosp_count / n_total) * 100, 2) if n_total > 0 else 0.0

        # Classification counts
        conf_count = 0
        prob_count = 0
        susp_count = 0
        if case_def_s is not None:
            s_lower = case_def_s.str.lower()
            conf_count = int((s_lower == "confirmed").sum())
            prob_count = int((s_lower == "probable").sum())
            susp_count = int((s_lower == "suspect").sum())

        # Demographics
        m_count = 0
        f_count = 0
        sex_ratio = 1.0
        if sex_s is not None:
            m_count = int((sex_s.str.lower() == "male").sum())
            f_count = int((sex_s.str.lower() == "female").sum())
            sex_ratio = round(m_count / f_count, 2) if f_count > 0 else (m_count if m_count > 0 else 1.0)

        # Age stats
        median_age = None
        mean_age = None
        q25_age = None
        q75_age = None
        min_age = None
        max_age = None
        if age_s is not None:
            numeric_ages = pd.to_numeric(age_s, errors="coerce").dropna()
            if not numeric_ages.empty:
                median_age = round(float(numeric_ages.median()), 1)
                mean_age = round(float(numeric_ages.mean()), 1)
                q25_age = round(float(numeric_ages.quantile(0.25)), 1)
                q75_age = round(float(numeric_ages.quantile(0.75)), 1)
                min_age = round(float(numeric_ages.min()), 1)
                max_age = round(float(numeric_ages.max()), 1)

        return {
            "total_cases": n_total,
            "confirmed_cases": conf_count,
            "probable_cases": prob_count,
            "suspect_cases": susp_count,
            "deaths": deaths,
            "recovered": recovered,
            "case_fatality_ratio_pct": cfr_total,
            "closed_case_cfr_pct": cfr_closed,
            "hospitalized_count": hosp_count,
            "hospitalization_rate_pct": hosp_rate,
            "male_count": m_count,
            "female_count": f_count,
            "sex_ratio_m_f": sex_ratio,
            "age_stats": {
                "median": median_age,
                "mean": mean_age,
                "q25": q25_age,
                "q75": q75_age,
                "min": min_age,
                "max": max_age
            }
        }

    def get_epi_curve(
        self,
        time_unit: str = "day",  # "day", "week", "month"
        stratify_by: str = "case_definition"  # "case_definition", "outcome", "sex", "none"
    ) -> Dict[str, Any]:
        """
        Generates epidemic curve aggregated by Day, ISO EpiWeek, or Month.
        Robust fallback searches all candidate date columns and precomputed EPI_WEEK.
        """
        # Strategy A: If weekly curve requested and EPI_WEEK column is available and populated
        if time_unit == "week" and "EPI_WEEK" in self.df.columns:
            epi_s = self.df["EPI_WEEK"].astype(str)
            valid_mask = (epi_s.str.strip().ne("") & epi_s.ne("nan") & epi_s.ne("None") & self.df["EPI_WEEK"].notna()).to_numpy()
            if valid_mask.any():
                df_valid = self.df[valid_mask].copy()
                df_valid["_period"] = df_valid["EPI_WEEK"].astype(str)
                all_periods = sorted(df_valid["_period"].unique().tolist())

                strat_col = None
                if stratify_by != "none":
                    strat_s = self._get_series(stratify_by)
                    if strat_s is not None and strat_s.notna().any():
                        strat_col = strat_s.name

                if strat_col and strat_col in df_valid.columns:
                    df_valid["_strat"] = df_valid[strat_col].fillna("Unknown").astype(str)
                    categories = sorted(df_valid["_strat"].unique().tolist())
                    series_data: Dict[str, List[int]] = {cat: [] for cat in categories}
                    totals: Dict[str, int] = {}

                    grouped = df_valid.groupby(["_period", "_strat"]).size().unstack(fill_value=0)
                    for p in all_periods:
                        p_sum = 0
                        for cat in categories:
                            cnt = int(grouped.at[p, cat]) if (p in grouped.index and cat in grouped.columns) else 0
                            series_data[cat].append(cnt)
                            p_sum += cnt
                        totals[p] = p_sum

                    return {
                        "time_unit": "week",
                        "stratified_by": stratify_by,
                        "periods": all_periods,
                        "series": series_data,
                        "total_by_period": totals
                    }
                else:
                    counts = df_valid["_period"].value_counts().to_dict()
                    total_counts = [int(counts.get(p, 0)) for p in all_periods]
                    return {
                        "time_unit": "week",
                        "stratified_by": "none",
                        "periods": all_periods,
                        "series": {"Total Cas": total_counts},
                        "total_by_period": {p: int(counts.get(p, 0)) for p in all_periods}
                    }

        # Strategy B: Find best date column from mapped tags or column names
        onset_s = self._get_series("date_onset")
        if onset_s is None or onset_s.dropna().empty:
            for d_tag in ["date_admission", "date_consultation", "date_notification", "date_report", "date_sample_collected", "date_discharge", "date_death"]:
                cand = self._get_series(d_tag)
                if cand is not None and not cand.dropna().empty:
                    onset_s = cand
                    break

        if onset_s is None or onset_s.dropna().empty:
            if "DATE_ADMISSION_CLEAN" in self.df.columns and self.df["DATE_ADMISSION_CLEAN"].notna().any():
                onset_s = self.df["DATE_ADMISSION_CLEAN"]

        # Strategy C: Search any column containing date keywords
        if onset_s is None or onset_s.dropna().empty:
            for c in self.df.columns:
                c_low = c.lower()
                if any(kw in c_low for kw in ["date", "dt_", "_dt", "fecha", "jour", "admission", "onset", "consult"]):
                    s = self.df[c]
                    if s.notna().any():
                        onset_s = s
                        break

        # Strategy D: Search any datetime64 column
        if onset_s is None or onset_s.dropna().empty:
            for c in self.df.columns:
                if pd.api.types.is_datetime64_any_dtype(self.df[c]):
                    onset_s = self.df[c]
                    break

        if onset_s is None or onset_s.dropna().empty:
            return {"dates": [], "periods": [], "series": {}, "total_by_period": {}}

        # Parse dates safely
        valid_dates = pd.to_datetime(onset_s, errors="coerce")
        valid_mask = valid_dates.notna().to_numpy()
        if not valid_mask.any():
            return {"dates": [], "periods": [], "series": {}, "total_by_period": {}}

        df_valid = self.df.iloc[valid_mask].copy()
        df_valid["_dt"] = valid_dates[valid_mask].values

        if time_unit == "week":
            df_valid["_period"] = df_valid["_dt"].dt.strftime("%G-W%V")
        elif time_unit == "month":
            df_valid["_period"] = df_valid["_dt"].dt.strftime("%Y-%m")
        else:
            df_valid["_period"] = df_valid["_dt"].dt.strftime("%Y-%m-%d")

        all_periods = sorted(df_valid["_period"].unique().tolist())

        # Check stratification series
        strat_col = None
        if stratify_by != "none":
            strat_s = self._get_series(stratify_by)
            if strat_s is not None and strat_s.notna().any():
                strat_col = strat_s.name

        if strat_col and strat_col in df_valid.columns:
            df_valid["_strat"] = df_valid[strat_col].fillna("Unknown").astype(str)
            categories = sorted(df_valid["_strat"].unique().tolist())
            series_data: Dict[str, List[int]] = {cat: [] for cat in categories}
            totals: Dict[str, int] = {}

            grouped = df_valid.groupby(["_period", "_strat"]).size().unstack(fill_value=0)
            for p in all_periods:
                p_sum = 0
                for cat in categories:
                    cnt = int(grouped.at[p, cat]) if (p in grouped.index and cat in grouped.columns) else 0
                    series_data[cat].append(cnt)
                    p_sum += cnt
                totals[p] = p_sum

            return {
                "time_unit": time_unit,
                "stratified_by": stratify_by,
                "periods": all_periods,
                "series": series_data,
                "total_by_period": totals
            }
        else:
            counts = df_valid["_period"].value_counts().to_dict()
            total_counts = [int(counts.get(p, 0)) for p in all_periods]
            return {
                "time_unit": time_unit,
                "stratified_by": "none",
                "periods": all_periods,
                "series": {"Total Cas": total_counts},
                "total_by_period": {p: int(counts.get(p, 0)) for p in all_periods}
            }

    def get_delay_distributions(self) -> Dict[str, Any]:
        """Calculates onset-to-consult, onset-to-admit, length of stay, and onset-to-death delay statistics."""
        def calc_delay(start_tag: str, end_tag: str, name: str) -> Optional[Dict[str, Any]]:
            s_start = self._get_series(start_tag)
            s_end = self._get_series(end_tag)
            if s_start is None or s_end is None:
                return None

            dt_start = pd.to_datetime(s_start, errors="coerce")
            dt_end = pd.to_datetime(s_end, errors="coerce")

            valid_mask = dt_start.notna() & dt_end.notna()
            if not valid_mask.any():
                return None

            delays = (dt_end[valid_mask] - dt_start[valid_mask]).dt.days
            # Filter non-negative plausible delays
            valid_delays = delays[(delays >= 0) & (delays <= 180)]
            if valid_delays.empty:
                return None

            return {
                "name": name,
                "count": int(len(valid_delays)),
                "mean_days": round(float(valid_delays.mean()), 1),
                "median_days": round(float(valid_delays.median()), 1),
                "iqr_25_75": [round(float(valid_delays.quantile(0.25)), 1), round(float(valid_delays.quantile(0.75)), 1)],
                "min_days": int(valid_delays.min()),
                "max_days": int(valid_delays.max()),
                "distribution_histogram": {
                    "0-2 days": int(((valid_delays >= 0) & (valid_delays <= 2)).sum()),
                    "3-5 days": int(((valid_delays >= 3) & (valid_delays <= 5)).sum()),
                    "6-10 days": int(((valid_delays >= 6) & (valid_delays <= 10)).sum()),
                    "11-20 days": int(((valid_delays >= 11) & (valid_delays <= 20)).sum()),
                    ">20 days": int((valid_delays > 20).sum())
                }
            }

        return {
            "onset_to_consultation": calc_delay("date_onset", "date_consultation", "Onset to Consultation Delay"),
            "onset_to_admission": calc_delay("date_onset", "date_admission", "Onset to Hospital Admission Delay"),
            "hospital_length_of_stay": calc_delay("date_admission", "date_discharge", "Hospital Length of Stay"),
            "onset_to_death": calc_delay("date_onset", "date_death", "Onset to Death Delay"),
        }

    def get_advanced_metrics(self) -> Dict[str, Any]:
        """V2: Attack rates, CFR by strata, weekly incidence, growth rate stub."""
        # Attack-rate-like weekly incidence per 10k (pseudo denominator = total)
        n_total = len(self.df)
        # CFR by age_group / sex if available
        cfr_by_age = {}
        cfr_by_sex = {}
        outcome_s = self._get_series("outcome")
        if outcome_s is not None and n_total > 0:
            # by sex
            sex_s = self._get_series("sex")
            if sex_s is not None:
                for sex_val in ["Male", "Female"]:
                    mask = sex_s.str.lower() == sex_val.lower()
                    total = int(mask.sum())
                    deaths = int(((sex_s.str.lower() == sex_val.lower()) & (outcome_s.str.lower() == "dead")).sum())
                    if total > 0:
                        cfr_by_sex[sex_val] = round(deaths/total*100, 2)
            # by age_group
            if "age_group" in self.df.columns:
                ag = self.df["age_group"]
                for grp in sorted(ag.dropna().unique().tolist()):
                    mask = ag == grp
                    total = int(mask.sum())
                    deaths = int((mask & (outcome_s.str.lower() == "dead")).sum())
                    if total > 0:
                        cfr_by_age[str(grp)] = round(deaths/total*100, 2)
        # Weekly incidence & doubling
        weekly = self.get_epi_curve(time_unit="week", stratify_by="none")
        weekly_counts = list(weekly.get("total_by_period", {}).values())
        growth = 0.0
        doubling = None
        if len(weekly_counts) >= 2 and weekly_counts[-2] > 0:
            growth = round((weekly_counts[-1] - weekly_counts[-2]) / weekly_counts[-2] * 100, 1)
            if growth > 0:
                try:
                    import math
                    # simple doubling time: ln2 / ln(1 + r) where r = growth/100 weekly
                    r = growth/100
                    doubling = round(math.log(2)/math.log(1+r), 1) if r>0 else None
                except:
                    doubling = None
        return {
            "cfr_by_sex_pct": cfr_by_sex,
            "cfr_by_age_group_pct": cfr_by_age,
            "weekly_growth_pct": growth,
            "estimated_doubling_time_weeks": doubling,
            "total_cases": n_total,
        }

    def get_demographic_pyramid(self) -> Dict[str, Any]:
        """Calculates age-sex demographic breakdown."""
        age_group_s = None
        if "age_group" in self.df.columns:
            age_group_s = self.df["age_group"]
        elif self.tag_to_col.get("age") in self.df.columns:
            age_s = pd.to_numeric(self.df[self.tag_to_col["age"]], errors="coerce")
            bins = [0, 5, 15, 30, 50, 65, 80, 120]
            labels = ["<5", "5-14", "15-29", "30-49", "50-64", "65-79", "80+"]
            age_group_s = pd.cut(age_s, bins=bins, labels=labels, right=False)

        sex_s = self._get_series("sex")

        if age_group_s is None or sex_s is None:
            return {"age_groups": [], "male": [], "female": [], "unknown": []}

        df_demo = pd.DataFrame({"age_group": age_group_s, "sex": sex_s}).dropna(subset=["age_group"])
        if df_demo.empty:
            return {"age_groups": [], "male": [], "female": [], "unknown": []}

        ordered_groups = ["<5", "5-14", "15-29", "30-49", "50-64", "65-79", "80+"]
        present_groups = [g for g in ordered_groups if g in df_demo["age_group"].values] or sorted(list(df_demo["age_group"].dropna().unique()))

        m_counts = []
        f_counts = []
        u_counts = []

        for g in present_groups:
            sub = df_demo[df_demo["age_group"] == g]
            m = int((sub["sex"].str.lower() == "male").sum())
            f = int((sub["sex"].str.lower() == "female").sum())
            u = int((~sub["sex"].str.lower().isin(["male", "female"])).sum())
            m_counts.append(m)
            f_counts.append(f)
            u_counts.append(u)

        return {
            "age_groups": present_groups,
            "male": m_counts,
            "female": f_counts,
            "unknown": u_counts
        }
