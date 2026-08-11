"""
Data Quality Profiling, Auditing, and Multi-Sheet Excel/HTML Report Generator with Spatial P-Code Support.
"""

import io
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from linelist_cleaner.schemas.models import (
    ColumnProfile,
    DataQualityScores,
    ValidationIssue,
    DuplicateGroup,
    CleaningReport,
    SpatialCascadeSummary,
)
from linelist_cleaner.schemas.epi_dictionary import CANONICAL_TAGS


class DataQualityAuditor:
    """Calculates comprehensive Linelist Data Quality Index and generates audit reports."""

    @staticmethod
    def calculate_quality_scores(
        df: pd.DataFrame,
        issues: List[ValidationIssue],
        duplicates: List[DuplicateGroup],
        tag_to_col: Dict[str, str]
    ) -> DataQualityScores:
        """
        Computes composite Data Quality Index (0-100%).
        """
        n_rows = len(df)
        if n_rows == 0:
            return DataQualityScores(
                overall_score=100.0,
                grade="A",
                completeness_score=100.0,
                chronology_score=100.0,
                validity_score=100.0,
                uniqueness_score=100.0
            )

        # 1. Completeness Score (30% weight)
        key_tags = ["case_id", "sex", "age", "date_onset", "outcome", "case_definition"]
        key_cols = [tag_to_col[t] for t in key_tags if t in tag_to_col and tag_to_col[t] in df.columns]
        if not key_cols:
            key_cols = df.columns.tolist()

        completeness_pcts = []
        for col in key_cols:
            valid_pct = (df[col].notna() & (df[col].astype(str).str.strip() != "")).mean() * 100
            completeness_pcts.append(valid_pct)

        completeness_score = float(np.mean(completeness_pcts)) if completeness_pcts else 100.0

        # 2. Chronology / Logic Score (25% weight)
        chrono_errors = sum(1 for i in issues if i.issue_type == "DATE_CHRONOLOGY" and i.severity == "ERROR")
        chrono_score = max(0.0, 100.0 - (chrono_errors / n_rows * 100.0 * 2.0))

        # 3. Validity Score (25% weight)
        other_errors = sum(1 for i in issues if i.issue_type != "DATE_CHRONOLOGY" and i.severity == "ERROR")
        warnings = sum(1 for i in issues if i.severity == "WARNING")
        validity_penalty = (other_errors * 2.0 + warnings * 0.5) / n_rows * 100.0
        validity_score = max(0.0, 100.0 - validity_penalty)

        # 4. Uniqueness Score (20% weight)
        dup_row_count = sum(len(g.row_indices) - 1 for g in duplicates)
        uniqueness_score = max(0.0, 100.0 - (dup_row_count / n_rows * 100.0 * 2.5))

        # Weighted overall
        overall = (
            0.30 * completeness_score +
            0.25 * chrono_score +
            0.25 * validity_score +
            0.20 * uniqueness_score
        )
        overall = round(max(0.0, min(100.0, overall)), 1)

        if overall >= 90:
            grade = "A"
        elif overall >= 80:
            grade = "B"
        elif overall >= 70:
            grade = "C"
        elif overall >= 60:
            grade = "D"
        else:
            grade = "F"

        return DataQualityScores(
            overall_score=overall,
            grade=grade,
            completeness_score=round(completeness_score, 1),
            chronology_score=round(chrono_score, 1),
            validity_score=round(validity_score, 1),
            uniqueness_score=round(uniqueness_score, 1)
        )

    @staticmethod
    def profile_columns(
        df: pd.DataFrame,
        tag_to_col: Dict[str, str],
        issues: List[ValidationIssue]
    ) -> Dict[str, ColumnProfile]:
        """Profiles each column in the DataFrame."""
        profiles: Dict[str, ColumnProfile] = {}
        col_to_tag = {v: k for k, v in tag_to_col.items()}

        issue_counts_by_col: Dict[str, int] = {}
        for issue in issues:
            if issue.column:
                issue_counts_by_col[issue.column] = issue_counts_by_col.get(issue.column, 0) + 1

        n_rows = len(df)

        for col in df.columns:
            series = df[col]
            missing_count = int((series.isna() | (series.astype(str).str.strip() == "")).sum())
            missing_pct = round((missing_count / n_rows) * 100, 1) if n_rows > 0 else 0.0

            valid_series = series[series.notna() & (series.astype(str).str.strip() != "")]
            unique_count = int(valid_series.nunique())

            top_vals = {}
            if not valid_series.empty:
                vc = valid_series.astype(str).value_counts().head(5)
                top_vals = {str(k): int(v) for k, v in vc.items()}

            samples = [str(x) for x in valid_series.head(4).tolist()]

            inferred = "string"
            if pd.api.types.is_numeric_dtype(series):
                inferred = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series):
                inferred = "date"
            elif col_to_tag.get(col) in CANONICAL_TAGS:
                inferred = CANONICAL_TAGS[col_to_tag[col]]["type"]

            profiles[col] = ColumnProfile(
                column_name=col,
                inferred_type=inferred,
                mapped_tag=col_to_tag.get(col),
                total_count=n_rows,
                missing_count=missing_count,
                missing_percentage=missing_pct,
                unique_count=unique_count,
                top_values=top_vals,
                sample_values=samples,
                issue_count=issue_counts_by_col.get(col, 0)
            )

        return profiles

    @staticmethod
    def export_excel_audit_workbook(
        df_clean: pd.DataFrame,
        report: CleaningReport,
        output_path_or_buffer: Any,
        ref_df: Optional[pd.DataFrame] = None
    ) -> None:
        """
        Exports the 3-tab Humanitarian & Quality Excel Workbook:
        - Tab 1: KPI_Dashboard (Summary metrics, Geocoding rate, Cascade breakdown, Quality Scorecard)
        - Tab 2: LineList_Nettoyee (Cleaned data colored by MATCH_LEVEL)
        - Tab 3: Referentiel_PCode (P-code reference dataset)
        """
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Palette definition
        navy_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        blue_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        teal_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
        subhead_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        # Match level color fills for LineList_Nettoyee rows
        match_colors = {
            "Locality": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),      # Light Emerald
            "Admin3_Ward": PatternFill(start_color="CCFBF1", end_color="CCFBF1", fill_type="solid"),   # Light Teal
            "Admin2_LGA": PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),    # Light Blue
            "Admin1_State": PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),  # Light Amber
            "Unmatched": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),     # Light Rose
        }

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=15, bold=True, color="0F172A")
        section_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
        bold_font = Font(name="Calibri", size=10, bold=True)
        regular_font = Font(name="Calibri", size=10)

        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        # -------------------------------------------------------------
        # TAB 1: KPI_Dashboard
        # -------------------------------------------------------------
        ws_kpi = wb.create_sheet(title="KPI_Dashboard")
        ws_kpi.views.sheetView[0].showGridLines = True

        ws_kpi["A1"] = "TABLEAU DE BORD QUALITÉ & GÉOCODAGE EN CASCADE"
        ws_kpi["A1"].font = title_font

        # 1. Spatial Cascade Geocoding KPI Box
        ws_kpi["A3"] = "1. Indicateurs Clés de Géocodage Spatial (P-Codes)"
        ws_kpi["A3"].font = section_font
        ws_kpi["A3"].fill = blue_fill
        ws_kpi.merge_cells("A3:E3")

        spatial = report.spatial_summary
        total_rows = report.cleaned_shape[0]

        if spatial:
            geo_rate = f"{spatial.geocoded_rate_pct}%"
            geo_count = f"{spatial.geocoded_count} / {spatial.total_records}"
            avg_score = f"{spatial.average_match_score}%"
        else:
            geo_rate = "—"
            geo_count = f"{total_rows} records"
            avg_score = "—"

        kpi_metrics = [
            ("Nombre Total de Cas (Cleaned Line List)", str(total_rows), "Lignes exploitables après validation"),
            ("Taux Global de Géocodage (%)", geo_rate, "Proportion de cas rattachés à un P-Code valide"),
            ("Cas Géocodés avec Succès", geo_count, "Nombre absolu de cas localisés"),
            ("Score Moyen de Similarité Fuzzy", avg_score, "Précision moyenne du matching textuel"),
            ("Score Global de Qualité des Données", f"{report.quality_scores_after.overall_score}%", f"Grade: {report.quality_scores_after.grade}"),
            ("Semaines Épidémiologiques Calculées", f"{report.epi_weeks_computed} / {total_rows}", "Dates normalisées vers EPI_WEEK OMS")
        ]

        for idx, (label, val, note) in enumerate(kpi_metrics, start=4):
            ws_kpi[f"A{idx}"] = label
            ws_kpi[f"A{idx}"].font = bold_font
            ws_kpi[f"B{idx}"] = val
            ws_kpi[f"B{idx}"].font = bold_font
            ws_kpi[f"B{idx}"].alignment = Alignment(horizontal="center")
            ws_kpi[f"C{idx}"] = note
            ws_kpi[f"C{idx}"].font = regular_font
            for c in ["A", "B", "C", "D", "E"]:
                ws_kpi[f"{c}{idx}"].border = thin_border

        # 2. Precision Breakdown Table
        start_cascade_row = len(kpi_metrics) + 6
        ws_kpi[f"A{start_cascade_row}"] = "2. Répartition par Niveau de Précision Spatiale (Spatial Fallback Cascade)"
        ws_kpi[f"A{start_cascade_row}"].font = section_font
        ws_kpi[f"A{start_cascade_row}"].fill = teal_fill
        ws_kpi.merge_cells(f"A{start_cascade_row}:E{start_cascade_row}")

        casc_headers = ["Niveau de Résolution (MATCH_LEVEL)", "Description", "Nombre de Cas", "Proportion (%)", "Couleur Assignée"]
        h_row = start_cascade_row + 1
        for col_i, h_text in enumerate(casc_headers, start=1):
            cell = ws_kpi.cell(row=h_row, column=col_i, value=h_text)
            cell.font = header_font
            cell.fill = navy_fill

        levels_info = [
            ("Locality", "Village / Localité / Camp IDP (Précision Maximale)", match_colors["Locality"]),
            ("Admin3_Ward", "Admin 3 / Ward / Aire de Santé (Fallback 1)", match_colors["Admin3_Ward"]),
            ("Admin2_LGA", "Admin 2 / LGA / Zone de Santé (Fallback 2)", match_colors["Admin2_LGA"]),
            ("Admin1_State", "Admin 1 / État / Province (Fallback 3)", match_colors["Admin1_State"]),
            ("Unmatched", "Non Localisé (Aucune correspondance trouvée)", match_colors["Unmatched"])
        ]

        curr_r = h_row + 1
        for lvl, desc, fill_style in levels_info:
            cnt = spatial.level_distribution.get(lvl, 0) if spatial else 0
            pct = spatial.level_percentages.get(lvl, 0.0) if spatial else 0.0

            ws_kpi.cell(row=curr_r, column=1, value=lvl).font = bold_font
            ws_kpi.cell(row=curr_r, column=2, value=desc).font = regular_font
            ws_kpi.cell(row=curr_r, column=3, value=cnt).font = bold_font
            ws_kpi.cell(row=curr_r, column=4, value=f"{pct}%").font = bold_font
            
            c_cell = ws_kpi.cell(row=curr_r, column=5, value="■ Accent")
            c_cell.font = bold_font
            c_cell.fill = fill_style
            c_cell.alignment = Alignment(horizontal="center")

            for c in range(1, 6):
                ws_kpi.cell(row=curr_r, column=c).border = thin_border
            curr_r += 1

        # 3. EpiWeek Distribution Table
        if "EPI_WEEK" in df_clean.columns:
            start_epi_row = curr_r + 2
            ws_kpi[f"A{start_epi_row}"] = "3. Synthèse par Semaine Épidémiologique (WHO EpiWeeks)"
            ws_kpi[f"A{start_epi_row}"].font = section_font
            ws_kpi[f"A{start_epi_row}"].fill = blue_fill
            ws_kpi.merge_cells(f"A{start_epi_row}:E{start_epi_row}")

            epi_h_row = start_epi_row + 1
            for col_i, h_text in enumerate(["Semaine Épi (EPI_WEEK)", "Nombre de Cas", "Proportion (%)"], start=1):
                cell = ws_kpi.cell(row=epi_h_row, column=col_i, value=h_text)
                cell.font = header_font
                cell.fill = navy_fill

            epi_counts = df_clean["EPI_WEEK"].dropna().value_counts().sort_index()
            curr_epi_r = epi_h_row + 1
            for wk, c_num in epi_counts.items():
                p_val = round((c_num / total_rows) * 100, 1) if total_rows > 0 else 0.0
                ws_kpi.cell(row=curr_epi_r, column=1, value=str(wk)).font = bold_font
                ws_kpi.cell(row=curr_epi_r, column=2, value=int(c_num)).font = regular_font
                ws_kpi.cell(row=curr_epi_r, column=3, value=f"{p_val}%").font = regular_font
                for c in range(1, 4):
                    ws_kpi.cell(row=curr_epi_r, column=c).border = thin_border
                curr_epi_r += 1

        ws_kpi.column_dimensions["A"].width = 38
        ws_kpi.column_dimensions["B"].width = 25
        ws_kpi.column_dimensions["C"].width = 32
        ws_kpi.column_dimensions["D"].width = 18
        ws_kpi.column_dimensions["E"].width = 18

        # -------------------------------------------------------------
        # TAB 2: LineList_Nettoyee
        # -------------------------------------------------------------
        ws_data = wb.create_sheet(title="LineList_Nettoyee")
        ws_data.views.sheetView[0].showGridLines = True

        headers = list(df_clean.columns)
        for col_idx, col_name in enumerate(headers, start=1):
            cell = ws_data.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = navy_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        match_level_col_idx = headers.index("MATCH_LEVEL") if "MATCH_LEVEL" in headers else None

        for row_idx, row_values in enumerate(df_clean.itertuples(index=False), start=2):
            match_lvl = row_values[match_level_col_idx] if match_level_col_idx is not None else None
            lvl_fill = match_colors.get(str(match_lvl), None)

            for col_idx, val in enumerate(row_values, start=1):
                val_to_write = "" if pd.isna(val) else val
                cell = ws_data.cell(row=row_idx, column=col_idx, value=val_to_write)
                cell.font = regular_font
                cell.border = thin_border
                
                # Apply row highlight or cell highlight for MATCH_LEVEL
                if col_idx - 1 == match_level_col_idx and lvl_fill:
                    cell.fill = lvl_fill
                    cell.font = bold_font
                elif val_to_write == "":
                    cell.fill = PatternFill(start_color="F8FAFC", fill_type="solid")

        # Auto-adjust column widths
        for col in ws_data.columns:
            max_len = max(len(str(cell.value or "")) for cell in col[:40])
            col_letter = get_column_letter(col[0].column)
            ws_data.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # -------------------------------------------------------------
        # TAB 3: Referentiel_PCode
        # -------------------------------------------------------------
        ws_ref = wb.create_sheet(title="Referentiel_PCode")
        ws_ref.views.sheetView[0].showGridLines = True

        if ref_df is not None and not ref_df.empty:
            ref_headers = list(ref_df.columns)
            for c_idx, h_text in enumerate(ref_headers, start=1):
                cell = ws_ref.cell(row=1, column=c_idx, value=h_text)
                cell.font = header_font
                cell.fill = teal_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")

            for r_idx, r_values in enumerate(ref_df.itertuples(index=False), start=2):
                for c_idx, val in enumerate(r_values, start=1):
                    cell = ws_ref.cell(row=r_idx, column=c_idx, value="" if pd.isna(val) else val)
                    cell.font = regular_font
                    cell.border = thin_border

            for col in ws_ref.columns:
                max_len = max(len(str(cell.value or "")) for cell in col[:30])
                col_letter = get_column_letter(col[0].column)
                ws_ref.column_dimensions[col_letter].width = max(max_len + 3, 14)
        else:
            ws_ref["A1"] = "Aucun référentiel P-Code externe chargé."
            ws_ref["A1"].font = regular_font

        wb.save(output_path_or_buffer)
