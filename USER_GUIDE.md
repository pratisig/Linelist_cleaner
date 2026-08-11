# 📖 Linelist Cleaner & Spatial Cascade Geocoding : User Guide

**Linelist Cleaner & GIS**
*Epidemiological Line List Cleaning & Hierarchical Spatial Fallback Cascade (OCHA COD-AB)*

---
> **🆕 V2.0.0 (2026-08-11) disponible !** Voir [README V2](README.md) & [CHANGELOG_V2.md](CHANGELOG_V2.md) : workbook 6 onglets + GeoJSON, veille épidémique, téléphones/coordonnées, presets, dark mode. Workbook 3→6 onglets, nouveaux endpoints & CLI.



### 🏛️ Information & Copyright

- **Organization** : PratiSIG Consulting Services
- **Motto / Slogan** : *La pratique des SIG, notre métier*
- **Location** : Dakar, Senegal
- **Lead Author** : **Youssoupha MBODJI**
- **Contact** : [pratisig.consulting@gmail.com](mailto:pratisig.consulting@gmail.com)
- **License & Rights** : © PratiSIG Consulting Services - Dakar, Senegal. Free tool for the GIS and humanitarian community (MIT Open Source License).

---

Please refer to the full, detailed French manual: **[MANUEL_UTILISATEUR.md](MANUEL_UTILISATEUR.md)**.

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
5. **Execute Cleaning**: Click **"Nettoyer & Géocoder"** to run the 5-step spatial fallback cascade and WHO EpiWeek calculations.
6. **Analyze & Export**:
   - **Dashboard**: View overall geocoding rate (%) and precision breakdown.
   - **Leaflet Map**: View geocoded cases plotted with color-coded precision markers.
   - **EpiCurve**: Incidence aggregated by WHO EpiWeek (`YYYY-Www`).
   - **Export**: Download the 3-tab Excel file (`KPI_Dashboard`, `LineList_Nettoyee`, `Referentiel_PCode`).

---

© PratiSIG Consulting Services - Dakar, Senegal.
*Author: Youssoupha MBODJI (pratisig.consulting@gmail.com)*
