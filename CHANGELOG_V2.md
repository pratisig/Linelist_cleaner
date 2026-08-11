# Changelog V2.0.0 — Linelist Cleaner

**Date:** 2026-08-11  
**Version:** 2.0.0 (majeur) — *Field-Ready Intelligence*  
**Auteur:** Youssoupha MBODJI — PratiSIG Consulting Services, Dakar

## 🚀 Résumé

V2 transforme Linelist Cleaner en **plateforme de veille épidémique terrain** : workbook 6 onglets + GeoJSON, nettoyage téléphones/coordonnées, détection automatique d'alertes, presets maladies, dark mode, i18n, stepper UX, et 4 nouveaux endpoints API + 3 commandes CLI.

---

## ✨ Nouvelles Fonctionnalités

### Core Pipeline
- **CoordinateCleaner** (`coordinate_cleaner.py`): parsing DMS, virgules → WGS84, validation bornes, détection & correction **swap lat/lon**.
- **PhoneCleaner** (`phone_cleaner.py`): normalisation vers **E.164** (`+221`, `+234`…), gestion `0`, `00`, `+`, indicatif pays paramétrable.
- **OutbreakDetector** (`outbreak_detector.py`): alertes EpiWeek (`> μ×1.5` ou `> μ+2σ`), tendance (`increasing/stable/decreasing`), `% croissance`, **pic**, **doubling time**.
- **EpiAnalytics V2**: `get_advanced_metrics()` → CFR par sexe/âge, weekly growth, doubling.
- **Presets maladies**: `cholera`, `measles`, `ebola`, `covid19`, `generic` (ajuste `age_group_breaks` & seuil fuzzy).
- **Pipeline**: applique preset au démarrage, logs V2, rapport enrichi `coordinates_cleaned`, `phones_standardized`, `outbreak_alerts`, `incidence_trend`, `version`.

### Workbook Excel (6 onglets)
- `KPI_Dashboard` V2 : 10 KPIs (coords, téléphones, alertes, tendance) + table alertes rose + légende.
- `Anomalies_Qualite` : 2000 lignes max, ERR/WARN/INFO colorés.
- `Doublons` : groupes avec type, score, lignes, IDs, idx recommandé.
- `Dictionnaire_Donnees` : profil colonnes + légende catégories tags.
- Mise en forme : freeze, filtres auto, paysage A3, fitToPage.

### Export SIG
- `export_geojson()` → FeatureCollection `Point` WGS84 avec `PCODE_ASSIGNED`, `MATCH_LEVEL`, toutes props.
- API `GET /export/geojson/{sid}` + CLI `--geojson`.

### API V2
- `GET /health` → version, name.
- `GET /config/presets` → dico presets.
- `POST /validate` → qualité sans nettoyage.
- `POST /preview_diff/{sid}` → colonnes ajoutées + previews brut/nettoyé.
- `GET /analytics/advanced/{sid}` → advanced + alerts sans re-nettoyage.
- `GET /export/geojson/{sid}`.

### Frontend V2
- **Header** : badge V2.0.0, `preset-select`, toggle dark (D) + langue FR/EN, stepper 5 étapes.
- **Slider** : + raccourcis `Ctrl+K` (focus recherche) & `D`.
- **Banner alertes** : ambré, auto-affiché si `alerts.length>0`.
- **Dashboard** : 9 KPIs V2 (grid 5+4), donut cascade, epi curve + doubling/CFR, délais, pyramide + advanced, quality badge.
- **Carte** : filtre `map-filter-level` + `getFilteredMapPoints()`.
- **Données** : modes `cleaned/raw/diff`, filtre MATCH_LEVEL, recherche.
- **Courbe épi** : KPIs CFR/croissance/doubling + cartes CFR par âge.
- **Qualité** : résumé, table anomalies + dups + profils.
- **Export** : 4 cartes (XLSX 6 onglets, CSV, GeoJSON, PY).
- **Style** : design tokens, dark mode, glass, kpi-card gradients, stepper dots, animations.
- **JS** : `AppState` étendu (advancedMetrics, qualityDelta, outbreakAlerts, incidenceTrend), `renderV2Kpis()`, `downloadGeoJSON()`, `getFilteredMapPoints()`, `updateStepper()`, `Ctrl+K` & `D` handlers, i18n mini.

### CLI V2
- `clean` : `--reference`, `--preset`, `--similarity`, `--phone-code`, `--geojson`, 10 KPIs affichés.
- `audit` : `--preset`, affiche Δ qualité + alertes.
- `validate` : rapide sans nettoyage.
- `geocode` : géocodage seul + geojson.
- `profile` : profil détaillé colonnes.
- `--version` : 2.0.0.
- Bannière V2 : `La pratique des SIG, notre métier — V2.0.0`.

### Config & Modèles
- `CleaningConfig` : + `clean_coordinates`, `clean_phone_numbers`, `default_phone_country_code`, `detect_outbreak_signals`, `outbreak_alert_threshold_multiplier`, `preset` + `apply_preset()`.
- `CleaningReport` : + `coordinates_cleaned`, `phones_standardized`, `outbreak_alerts`, `incidence_trend`, `version`.
- Nouveaux modèles : `OutbreakAlert`, `IncidenceTrend`.

### Build & Deploy
- `Linelist_Cleaner.spec` : `name='Linelist_Cleaner_V2'`, hiddenimports V2.
- `manifest.json` PWA.
- `pyproject.toml` & `setup.py` → 2.0.0.

### Docs
- `README.md` refondu V2 (table comparatif, features, API table, CLI/Python snippets).
- `USER_GUIDE.md` & `MANUEL_UTILISATEUR.md` à mettre à jour (renvoi README V2).
- `CHANGELOG_V2.md` (ce fichier).

---

## 🔄 Breaking Changes

- `CleaningReport` ajoute champs requis (compat ascendant, `version` défaut `2.0.0`).
- `export_excel` génère désormais **6 onglets** (tests attendent au moins 3 → OK).
- Nom exe : `Linelist_Cleaner` → `Linelist_Cleaner_V2.exe` (compat : ancien nom toujours documenté).
- CLI `clean` change nom sortie défaut `*_cleaned_V2.xlsx` (si `--output` non fourni).

## 🧪 Tests

- 44/44 pass (pytest 9). Nouveaux endpoints testés manuellement (`health`, `validate`, `geojson`, `preview_diff`, `advanced`).
- Vérifié : coords swap, phones, alertes avec EpiWeeks artificielles.

## 📦 Migration V1 → V2

1. `pip install -U linelist-cleaner` (ou `pip install -e .`).
2. Aucune config requise — `CleaningConfig()` active V2 par défaut (désactivable via `clean_coordinates=False`, etc.).
3. Pour reproduire comportement V1 strict : `config=CleaningConfig(clean_coordinates=False, clean_phone_numbers=False, detect_outbreak_signals=False, preset=None)`.
4. Re-générer workbook : `LinelistCleaner.export_excel(...)` → 6 onglets auto.

## 👥 Crédits

PratiSIG Consulting Services — Dakar.  
Auteur : Youssoupha MBODJI — pratisig.consulting@gmail.com — *La pratique des SIG, notre métier*

---

*V2.0.0 — prête pour missions terrain offline, intégration QGIS directe & veille épidémique en temps réel.*
