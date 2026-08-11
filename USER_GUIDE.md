# 📖 Linelist Cleaner & Spatial Cascade Geocoding — User Guide

Please refer to the complete User Manual in French: **[MANUEL_UTILISATEUR.md](MANUEL_UTILISATEUR.md)**.

## Quick Summary (English)

### 1. Launch Options
- **Windows Executable (.exe)**: Double-click `Linelist_Cleaner.exe`. Your default web browser will automatically open at `http://127.0.0.1:8000`.
- **Python / CLI**: Run `linelist-cleaner serve --port 8000`.
- **Docker**: Run `cd deploy && docker compose up -d`.

### 2. Main Workflow
1. **Upload Line List**: Click the blue upload box to load raw CSV or Excel (.xlsx) line lists.
2. **P-Code Reference Dataset**: Built-in OCHA COD-AB reference is loaded by default. Upload a custom reference via the green box if needed.
3. **Adjust Fuzzy Matching Threshold**: Use the slider on top (default: **80%**) to balance strict vs. tolerant string matching.
4. **Column Mapping**: Review the **"Spatial & Column Mapping"** tab to map your raw columns (`Locality`, `Admin 3 / Ward`, `Admin 2 / LGA`, `Admin 1 / State`, `Admission Date`, `Age`, `Sex`, etc.).
5. **Execute Cleaning**: Click **"Exécuter Nettoyage & Cascade"** to run the 5-step spatial fallback cascade and WHO EpiWeek calculations.
6. **Analyze & Export**:
   - **Dashboard**: View overall geocoding rate (%) and precision breakdown.
   - **Leaflet Map**: View geocoded cases plotted with color-coded precision markers.
   - **EpiCurve**: Incidence aggregated by WHO EpiWeek (`YYYY-Www`).
   - **Export**: Download the 3-tab Excel file (`KPI_Dashboard`, `LineList_Nettoyee`, `Referentiel_PCode`).
