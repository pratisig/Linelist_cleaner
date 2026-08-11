# Linelist Cleaner V2 — Géocodage Spatial en Cascade & Veille Épidémique (P-Codes OCHA COD-AB)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.0.0-emerald.svg)](https://github.com/pratisig/Linelist_cleaner)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Organisation](https://img.shields.io/badge/PratiSIG-Consulting%20Services-emerald.svg)](mailto:pratisig.consulting@gmail.com)
[![Tests](https://img.shields.io/badge/tests-44%20passed-brightgreen.svg)]()
[![Workbook](https://img.shields.io/badge/workbook-6%20onglets%20%2B%20GeoJSON-blue.svg)]()

> **Linelist Cleaner V2** — Nettoyage épidémiologique intelligent, calcul automatique des semaines OMS, **géocodage spatial hiérarchique en cascade (P-Codes OCHA COD-AB)** + **veille épidémique (alertes & tendances)**, validation GPS/téléphones, dark mode, presets maladies et exports SIG directs.
> Développé par **PratiSIG Consulting Services** (Dakar, Sénégal) pour la communauté FETP, Epi-terrain et humanitaire.

**V1 → V2 highlights:** workbook 3 → **6 onglets** + GeoJSON, presets choléra/rougeole/Ebola/COVID, normalisation **téléphones E.164** & **coordonnées WGS84** (swap auto), détection **alertes EpiWeek** (anomalie), tendance & doubling time, dark mode/i18n, stepper UX, API `/health`, `/config/presets`, `/export/geojson`, `/analytics/advanced`, `/validate`, CLI `validate|geocode|profile`.

---

## 🏛️ Informations & Droits d'Auteur

- **Organisation** : PratiSIG Consulting Services — *La pratique des SIG, notre métier*
- **Siège** : Dakar, Sénégal
- **Auteur Principal** : **Youssoupha MBODJI** — [pratisig.consulting@gmail.com](mailto:pratisig.consulting@gmail.com)
- **Licence** : © PratiSIG — MIT (usage libre communauté SIG/humanitaire)
- **Version** : **2.0.0** (2026-08-11) — [CHANGELOG_V2.md](CHANGELOG_V2.md)

---

## ✨ Nouveautés V2 (2026-08)

| Domaine | V1 | **V2** |
|---|---|---|
| **Workbook Excel** | 3 onglets | **6 onglets** : `KPI_Dashboard (V2)` + `LineList_Nettoyee` + `Referentiel_PCode` + `Anomalies_Qualite` + `Doublons` + `Dictionnaire_Donnees` |
| **Export SIG** | Excel/CSV | **+ GeoJSON** FeatureCollection `Point` WGS84 prêt pour QGIS/ArcGIS |
| **Nettoyage** | dates, âges, sexe, outcomes | **+ téléphones E.164** (`+221`, `+234`…), **+ coordonnées** WGS84 (swap lat/lon auto, DMS) |
| **Veille épi** | EpiWeeks | **+ alertes EpiWeek** (seuil μ×1.5 & 2σ), **+ tendance** (↗↘→), **pic**, **croissance %**, **doubling time** |
| **Analytics** | CFR, epi curve, délais, pyramide | **+ CFR par sexe/âge**, **weekly growth**, **attack-rate-like** |
| **UX** | Tailwind + Leaflet | **Dark mode** (D), **i18n FR/EN**, **stepper 1→5**, **command palette Ctrl+K**, presets maladie |
| **API** | 4 endpoints | **8 endpoints** : `health`, `config/presets`, `validate`, `preview_diff`, `analytics/advanced`, `export/geojson` |
| **CLI** | clean/audit/inspect/sample/serve | **+ validate**, **+ geocode**, **+ profile**, **+ preset**, **+ geojson**, **+ phone-code** |
| **Config** | basique | **presets** (`cholera`, `measles`, `ebola`, `covid19`, `generic`) + seuils V2 |

---

## 🌟 Fonctionnalités Clés V2

### 1. 📍 Cascade Spatiale 5 Niveaux (P-Codes OCHA COD-AB)
- Slider fuzzy 50→100% (défaut **80%**, presets ajustent : choléra 78, Ebola 85).
- Cascade : **Localité** → **Admin3 Ward** → **Admin2 LGA** → **Admin1 State** → **Unmatched**.
- Colonnes enrichies : `PCODE_ASSIGNED`, `MATCH_LEVEL`, `MATCH_SCORE`, `MATCHED_NAME`, `LATITUDE`, `LONGITUDE` (validées WGS84).

### 2. 📅 Temporalité & EpiWeeks OMS (ISO 8601)
- Normalisation dates hétérogènes (`DD/MM/YYYY`, `YYYY-MM-DD`, `DD-Mon-YYYY`, FR/ES, entiers Excel) → ISO `YYYY-MM-DD`.
- Calcul `EPI_WEEK` (`2023-W33`), `EPI_WEEK_NUM`, `EPI_YEAR`.

### 3. 📞📍 Nettoyage V2 — Téléphones & GPS
- **Téléphones** : détection `0`, `00`, `+`, formats locaux → **E.164** (`+221771234567`), paramétrable par pays (`--phone-code`).
- **Coordonnées** : parsing DMS/virgules, validation `-90→90 / -180→180`, **correction swap lat/lon** auto.

### 4. 🚨 Veille Épidémique V2
- **Alertes** : semaines où `cas > μ×1.5` **ou** `cas > μ+2σ` (min 5 cas).
- **Tendance** : `increasing / stable / decreasing`, **% croissance hebdo**, **semaine pic**, **doubling time** (semaines).

### 5. 🗺️ SIG Interactive V2 (Leaflet.js)
- Pastilles couleur par `MATCH_LEVEL` (🟢 Localité, 🔵 Admin3, 🔷 Admin2, 🟡 Admin1, 🔴 Unmatched).
- **Filtre par niveau** rapide, popups P-Code + score + EpiWeek, fond OSM.
- Export **GeoJSON** direct.

### 6. 📊 Dashboard V2
- **9 KPIs** : total, géocodés, qualité (+Δ), EpiWeeks, coords validées, téléphones, alertes, tendance, doubling.
- **Donut cascade**, **epi curve stacked** + KPI doubling/CFR, **délais**, **pyramide âge-sexe**, **CFR par sexe/âge**.

### 7. 📥 Workbook Excel V2 — 6 Onglets Formatés
- **KPI_Dashboard** : KPIs V2, cascade, EpiWeeks, **alertes** (table rose), tendance.
- **LineList_Nettoyee** : données enrichies, couleur par `MATCH_LEVEL`, filtres & freeze.
- **Referentiel_PCode** : copie référentiel utilisé.
- **Anomalies_Qualite** : `validation_issues` (ERR/WARN/INFO) + colonne, message, action, valeur brute — cap 2000 lignes.
- **Doublons** : `DuplicateGroup` (type, score, lignes, IDs, idx recommandé).
- **Dictionnaire_Donnees** : profil colonnes (manquants %, uniques, top valeurs) + légende tags.

---

## 🪟 Exécutable Portable Windows (.exe V2)

- **Aucun Python requis**. Double-clic sur `Linelist_Cleaner_V2.exe` → serveur `http://127.0.0.1:8000` (navigateur auto).
- **100% offline** (idéal terrain sans internet, PWA manifest inclus).
```powershell
pip install -r requirements.txt pyinstaller
pyinstaller --clean Linelist_Cleaner.spec   # → dist\Linelist_Cleaner_V2.exe
```

---

## 🚀 Démarrage Rapide V2

### Web
```bash
linelist-cleaner serve --host 0.0.0.0 --port 8000
# → http://localhost:8000  (docs: /docs )
```

### CLI V2
```bash
# Nettoyage + workbook 6 onglets + GeoJSON + preset choléra
linelist-cleaner clean linelist_brute.csv -o linelist_nettoyee_V2.xlsx --excel --preset cholera --geojson --phone-code +221 --similarity 78

# Audit qualité V2 (6 onglets)
linelist-cleaner audit linelist_brute.csv -o audit_V2.xlsx --preset measles

# Validation rapide sans nettoyage
linelist-cleaner validate linelist_brute.csv

# Géocodage seul + GeoJSON
linelist-cleaner geocode linelist.csv -r referentiel.xlsx -o geocoded.xlsx --geojson --similarity 80

# Profil colonnes
linelist-cleaner profile linelist_brute.csv

# Inspect mapping
linelist-cleaner inspect linelist_brute.csv

# Exemple dataset
linelist-cleaner sample --type borno -o borno_sample.csv
```

### Python V2
```python
import pandas as pd
from linelist_cleaner import LinelistCleaner, CleaningConfig
from linelist_cleaner.datasets import get_sample_dataset

linelist_raw = get_sample_dataset("borno")
pcode_ref = get_sample_dataset("pcode_reference")

config = CleaningConfig(
    preset="cholera",  # V2 preset
    enable_spatial_cascade=True,
    spatial_similarity_threshold=78.0,
    compute_epi_weeks=True,
    clean_coordinates=True,        # V2
    clean_phone_numbers=True,      # V2
    default_phone_country_code="+221",
    detect_outbreak_signals=True   # V2
)

cleaner = LinelistCleaner(config=config)
cleaned_df, report = cleaner.clean(linelist_raw, reference_pcode_df=pcode_ref)

print(report.version, report.spatial_summary.geocoded_rate_pct, report.outbreak_alerts)
print(f"Δ qualité: {report.quality_scores_after.overall_score - report.quality_scores_before.overall_score}%")

cleaner.export_excel(cleaned_df, report, "Linelist_V2_6onglets.xlsx", reference_df=pcode_ref)
LinelistCleaner.export_geojson(cleaned_df, "Linelist_V2.geojson")  # V2 SIG
```

---

## 🔌 API V2

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health & version 2.0.0 |
| `GET` | `/api/dictionary` | Dictionnaire tags épidémiologiques |
| `GET` | `/api/config/presets` | Presets maladies |
| `POST` | `/api/upload` | Upload linelist (skiprows, sheet) |
| `POST` | `/api/upload_reference` | Upload référentiel P-Code |
| `POST` | `/api/clean` | Pipeline complet V2 |
| `GET` | `/api/analytics/advanced/{sid}` | Métriques avancées V2 |
| `POST` | `/api/validate` | Validation rapide |
| `POST` | `/api/preview_diff/{sid}` | Diff brut vs nettoyé |
| `GET` | `/api/export/excel/{sid}` | Workbook 6 onglets V2 |
| `GET` | `/api/export/csv/{sid}` | CSV nettoyé |
| `GET` | `/api/export/geojson/{sid}` | GeoJSON V2 |
| `GET` | `/api/export/script/{sid}` | Script Python reproductible V2 |

---

## 🧪 Tests & Qualité V2

```bash
pip install -r requirements.txt
pytest -v  # 44 passed
```

- Pipeline : dates, âges, sexe, outcomes, cascade spatiale, coords/phones, alertes.
- Web : upload Excel/CSV, référence, clean, exports (excel, csv, geojson).
- CLI : help, sample, inspect.

---

## 📄 Licence

© PratiSIG Consulting Services - Dakar, Sénégal. Outil libre communauté SIG & humanitaire sous [MIT](LICENSE).

---

*V2.0.0 — 2026-08-11 — PratiSIG : La pratique des SIG, notre métier — Contact: pratisig.consulting@gmail.com*
