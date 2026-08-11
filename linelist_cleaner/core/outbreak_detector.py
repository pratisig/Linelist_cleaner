"""
Outbreak Detection & Alert Engine V2.
Simple threshold + EpiWeek anomaly detection (CUSUM-like).
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def detect_outbreak_alerts(
    df: pd.DataFrame,
    epi_week_col: str = "EPI_WEEK",
    threshold_multiplier: float = 1.5,
    min_cases: int = 5
) -> List[Dict[str, Any]]:
    alerts = []
    if epi_week_col not in df.columns or df.empty:
        return alerts
    epi_counts = df[epi_week_col].value_counts().sort_index()
    if len(epi_counts) < 3:
        return alerts
    # Moving average baseline (3 weeks)
    values = epi_counts.values
    weeks = epi_counts.index.tolist()
    # Simple mean
    mean = float(np.mean(values))
    std = float(np.std(values))
    baseline = mean
    # Detect weeks > baseline * multiplier or > mean+2sd
    for wk, cnt in epi_counts.items():
        if cnt >= min_cases and (cnt > baseline * threshold_multiplier or (std > 0 and cnt > mean + 2*std)):
            alerts.append({
                "epi_week": str(wk),
                "cases": int(cnt),
                "baseline_mean": round(mean, 1),
                "severity": "HIGH" if cnt > mean + 2*std else "MEDIUM",
                "message": f"Alerte: {cnt} cas en {wk} dépasse le seuil attendu ({round(baseline*threshold_multiplier,1)})"
            })
    return alerts


def compute_incidence_trend(df: pd.DataFrame, epi_week_col: str = "EPI_WEEK") -> Dict[str, Any]:
    if epi_week_col not in df.columns or df.empty:
        return {"trend": "stable", "weekly_growth_pct": 0.0, "peak_week": None}
    epi_counts = df[epi_week_col].value_counts().sort_index()
    if len(epi_counts) < 2:
        return {"trend": "stable", "weekly_growth_pct": 0.0, "peak_week": str(epi_counts.index[0]) if len(epi_counts)==1 else None}
    vals = epi_counts.values
    # Growth last 2 weeks
    last = vals[-1]
    prev = vals[-2] if len(vals) >=2 else last
    growth = round(((last - prev)/prev*100) if prev>0 else 0.0, 1)
    if growth > 20:
        trend = "increasing"
    elif growth < -20:
        trend = "decreasing"
    else:
        trend = "stable"
    peak_week = str(epi_counts.idxmax())
    return {"trend": trend, "weekly_growth_pct": growth, "peak_week": peak_week, "last_week_cases": int(last), "previous_week_cases": int(prev)}
