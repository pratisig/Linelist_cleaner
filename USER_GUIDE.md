# 📖 Linelist Cleaner V2 & Spatial Cascade Geocoding : User Guide

**Linelist Cleaner V2 — Epidemiological Cleaning, Spatial Fallback Cascade & Outbreak Intelligence**  
*PratiSIG Consulting Services — Dakar, Senegal*  
*Lead Author: **Youssoupha MBODJI** (pratisig.consulting@gmail.com)*  
*Motto: « La pratique des SIG, notre métier » (GIS in practice, our expertise)*  
*License: MIT Open Source*

---

For the comprehensive French documentation with in-depth methodological explanations, see: **[MANUEL_UTILISATEUR.md](MANUEL_UTILISATEUR.md)**.

---

## 📑 Key Features & Workflow Summary

### 1. Spatial Fallback Cascade (OCHA COD-AB / Custom Reference)
- **Multi-Level Matching**: Tries highest precision level first (Locality / Village / Street), then falls back to Admin 3 (Ward), Admin 2 (District / LGA), Admin 1 (Province / State).
- **Authentic P-Codes**: Directly extracts real P-Codes from your reference dataset (`pcode`, `code`, `pcode_adm3`, `pcode_adm2`, `pcode_adm1`). Never invents synthetic IDs.
- **Output Columns**: Adds `PCODE_ASSIGNED`, `MATCH_LEVEL`, `MATCH_SCORE`, `MATCHED_NAME`, `PCODE_LOCALITY`, `PCODE_ADMIN3`, `PCODE_ADMIN2`, `PCODE_ADMIN1`, `LATITUDE`, and `LONGITUDE`.

### 2. WHO EpiWeek Computation (`EPI_WEEK`)
- Standard **WHO / ISO 8601** epidemiological week calculation (starts Monday, ends Sunday).
- Automatic detection of date columns: Symptom Onset $\rightarrow$ Admission $\rightarrow$ Consultation $\rightarrow$ Notification $\rightarrow$ Sample collection.
- Generates `EPI_WEEK` (e.g. `2026-W06`), `EPI_WEEK_NUM` (1-53), and `EPI_YEAR`.

### 3. Epidemiological Outbreak Analytics
- **Peak Week (`peak_week`)**: Epidemiological week with the maximum number of cases.
- **Weekly Mean & Range**: Mean weekly incidence, minimum and maximum weekly counts.
- **Outbreak Duration**: Start week $\rightarrow$ End week and total weeks count.
- **Case Fatality Ratio (CFR)**: Calculated as $(\text{Deaths} / \text{Total Cases}) \times 100$. Displays `0 documented deaths` if outcome data is missing.
- **Dynamic Trend & Doubling Time**: Detects increasing ($\nearrow$), decreasing ($\searrow$), or stable ($\rightarrow$) trajectory.

### 4. Quality Audit & Duplicate Groups
- **Quality Score (0-100%)**: Weighted composite score based on Completeness, Validity, Chronology, and Uniqueness.
- **Duplicate Groups**: Exact and fuzzy identity clustering (Name + Age + Sex + Date + Locality).

### 5. Multi-Format Direct Exports
- **Excel V2 Workbook (6 Sheets)**: `KPI_Dashboard`, `LineList_Nettoyee`, `Referentiel_PCode`, `Anomalies_Qualite`, `Doublons`, `Dictionnaire_Donnees`.
- **Cleaned CSV**: Sanitized against CSV formula injection (DDE).
- **GeoJSON V2**: EPSG:4326 Point FeatureCollection ready for instant drag-and-drop into QGIS or ArcGIS.
- **Reproducible Python Script (.py)**: Offline batch pipeline.

---

© PratiSIG Consulting Services — Dakar, Senegal.  
*Contact: pratisig.consulting@gmail.com*
