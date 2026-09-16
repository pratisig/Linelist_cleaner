# Linelist Cleaner V2 — Géocodage Spatial en Cascade & Veille Épidémique (P-Codes OCHA COD-AB)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.0.0-emerald.svg)](https://github.com/pratisig/Linelist_cleaner)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Organisation](https://img.shields.io/badge/PratiSIG-Consulting%20Services-emerald.svg)](mailto:pratisig.consulting@gmail.com)
[![Tests](https://img.shields.io/badge/tests-59%20passed-brightgreen.svg)]()
[![Workbook](https://img.shields.io/badge/workbook-6%20onglets%20%2B%20GeoJSON-blue.svg)]()

> **Linelist Cleaner V2** — Nettoyage épidémiologique intelligent, calcul automatique des semaines OMS, **géocodage spatial hiérarchique en cascade (P-Codes OCHA COD-AB)** + **veille épidémique (alertes & tendances)**, validation GPS/téléphones, dark mode, presets maladies et exports SIG directs.
> Développé par **PratiSIG Consulting Services** (Dakar, Sénégal) pour la communauté FETP, Epi-terrain et humanitaire.

---

## 🏛️ Informations & Droits d'Auteur

- **Organisation** : PratiSIG Consulting Services — *La pratique des SIG, notre métier*
- **Siège** : Dakar, Sénégal
- **Auteur Principal** : **Youssoupha MBODJI** — [pratisig.consulting@gmail.com](mailto:pratisig.consulting@gmail.com)
- **Licence** : © PratiSIG — MIT (usage libre communauté SIG/humanitaire)
- **Documentation Complète** : [MANUEL_UTILISATEUR.md](MANUEL_UTILISATEUR.md) (Français) | [USER_GUIDE.md](USER_GUIDE.md) (English)

---

## ✨ Points Forts du Moteur V2

1. **Cascade Spatiale Hiérarchique (P-Codes OCHA COD-AB)** :
   - Jointure floue (*Fuzzy Matching*) en 4 étapes : **Localité / Village / Rue** $\rightarrow$ **Admin 3 (Ward)** $\rightarrow$ **Admin 2 (District/LGA)** $\rightarrow$ **Admin 1 (Région/State)** $\rightarrow$ **Unmatched**.
   - Extraction des vrais P-Codes du référentiel (`PCODE_ASSIGNED`, `PCODE_LOCALITY`, `PCODE_ADMIN3`, `PCODE_ADMIN2`, `PCODE_ADMIN1`) et des coordonnées GPS WGS84.
   - Jamais de faux codes synthétiques générés.
2. **Semaines Épidémiologiques OMS (`EPI_WEEK`)** :
   - Calcul automatique de la semaine épidémiologique internationale OMS / ISO 8601 (`YYYY-Www`, `EPI_WEEK_NUM`, `EPI_YEAR`).
3. **Indicateurs Épidémiologiques & Courbe Épi** :
   - Semaine Pic (`Peak Week`), moyenne hebdomadaire, minimum/maximum, étendue temporelle, taux de létalité global (CFR), tendance ($\nearrow \searrow \rightarrow$) et temps de doublement (*Doubling Time*).
4. **Audit Qualité & Détection des Doublons** :
   - Note composite de qualité sur 100% (Complétude, Validité, Cohérence chronologique, Unicité).
   - Détection des anomalies cliniques et regroupement intelligent des doublons patients.
5. **Multi-Formats & Exports Directs** :
   - **Classeur Excel 6 Onglets** : `KPI_Dashboard`, `LineList_Nettoyee`, `Referentiel_PCode`, `Anomalies_Qualite`, `Doublons`, `Dictionnaire_Donnees`.
   - **CSV Assaini** (protection anti-injection de formules DDE).
   - **GeoJSON Point WGS84** prêt à glisser dans QGIS ou ArcGIS.
   - **Script Python reproductible** pour exécution hors-ligne.

---

## 🚀 Démarrage Rapide

### Serveur Web Interactif
```bash
linelist-cleaner serve --host 0.0.0.0 --port 8000
# Ouvrez http://localhost:8000
```

### En Ligne de Commande (CLI)
```bash
# Nettoyage complet + workbook Excel 6 onglets + GeoJSON
linelist-cleaner clean linelist_brute.csv -o linelist_nettoyee.xlsx --excel --geojson

# Audit qualité seul
linelist-cleaner audit linelist_brute.csv -o audit.xlsx

# Validation rapide
linelist-cleaner validate linelist_brute.csv

# Profilage des colonnes
linelist-cleaner profile linelist_brute.csv
```

---

## 🧪 Tests Unitaires & Intégration

```bash
pip install -r requirements.txt
pytest  # 59 passed
```

---

© PratiSIG Consulting Services — Dakar, Sénégal.  
*Contact : pratisig.consulting@gmail.com*
