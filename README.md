# Linelist Cleaner & Géocodage Spatial en Cascade (P-Codes OCHA COD-AB)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Organisation](https://img.shields.io/badge/PratiSIG-Consulting%20Services-emerald.svg)](mailto:pratisig.consulting@gmail.com)
[![Tests](https://img.shields.io/badge/tests-45%20passed-brightgreen.svg)]()

> **Linelist Cleaner** est une application professionnelle de nettoyage de données épidémiologiques, de calcul automatique des semaines épidémiologiques OMS et de **géocodage spatial hiérarchique en cascade avec attribution des P-Codes de référence (OCHA COD-AB)**.
> Développé par **PratiSIG Consulting Services** (Dakar, Sénégal) pour appuyer les épidémiologistes de terrain (FETP), les gestionnaires de données humanitaires et les acteurs de santé publique en situation d'urgence sanitaire.

---

## 🏛️ Informations & Droits d'Auteur

- **Organisation** : PratiSIG Consulting Services
- **Devise / Slogan** : *La pratique des SIG, notre métier*
- **Siège** : Dakar, Sénégal
- **Auteur Principal** : **Youssoupha MBODJI**
- **Contact Électronique** : [pratisig.consulting@gmail.com](mailto:pratisig.consulting@gmail.com)
- **Licence & Droits** : © PratiSIG Consulting Services - Dakar, Sénégal. Outil à usage libre pour la communauté SIG et humanitaire (Licence Open Source MIT).

---

## 🌟 Fonctionnalités Clés

### 1. 📍 Algorithme de Matching Spatial en Cascade (P-Codes OCHA COD-AB)
- Curseur interactif de similarité textuelle floue (Fuzzy Matching) réglable en temps réel de 50% à 100% (valeur par défaut : **80%**).
- Cascade hiérarchique en 5 étapes avec rétrogradation automatique :
  1. **Étape 1 : Localité / Village / Camp IDP** : Rapprochement précis et attribution du P-code Localité (`MATCH_LEVEL = 'Locality'`)
  2. **Étape 2 (Fallback 1) : Admin 3 / Ward / Aire de santé** : Attribution du P-code Admin 3 (`MATCH_LEVEL = 'Admin3_Ward'`)
  3. **Étape 3 (Fallback 2) : Admin 2 / LGA / Zone de santé** : Attribution du P-code Admin 2 (`MATCH_LEVEL = 'Admin2_LGA'`)
  4. **Étape 4 (Fallback 3) : Admin 1 / État / Province** : Attribution du P-code Admin 1 (`MATCH_LEVEL = 'Admin1_State'`)
  5. **Étape 5 : Non Localisé** : Valeur nulle assignée (`MATCH_LEVEL = 'Unmatched'`)
- Colonnes enrichies automatiquement : `PCODE_ASSIGNED`, `MATCH_LEVEL`, `MATCH_SCORE`, `MATCHED_NAME`, `LATITUDE`, `LONGITUDE`.

### 2. 📅 Normalisation Temporelle & Semaines Épidémiologiques OMS
- Conversion automatique des formats de dates hétérogènes (`DD/MM/YYYY`, `YYYY-MM-DD`, `DD-Mon-YYYY`, mois en français/espagnol, entiers de dates Excel) vers le format standard ISO `YYYY-MM-DD` (`DATE_ADMISSION_CLEAN`).
- Calcul de l'année et de la semaine épidémiologique selon le calendrier standard de l'OMS (ISO 8601) :
  - `EPI_WEEK` (ex. `2023-W33`)
  - `EPI_WEEK_NUM` (ex. `33`)
  - `EPI_YEAR` (ex. `2023`)

### 3. 🗺️ Visualisation Cartographique SIG Interactive (Leaflet.js)
- Visualisation instantanée de chaque patient géocodé sur fond cartographique OpenStreetMap.
- Pastilles colorées par niveau de résolution géographique :
  - 🟢 **Vert** : Localité / Village
  - 🔵 **Turquoise** : Admin 3 (Ward)
  - 🔷 **Bleu** : Admin 2 (LGA)
  - 🟡 **Ambre** : Admin 1 (State)
- Popups interactives détaillées avec identifiant patient, P-Code OCHA, nom officiel, score de similarité et semaine épi.

### 4. 📥 Exportation Excel Multi-Onglets Formatée (.xlsx)
Génération d'un classeur Excel prêt pour la diffusion et la prise de décision :
- **Onglet 1 : `KPI_Dashboard`** : Synthèse des indicateurs, taux global de géocodage (%), tableau de décomposition de la cascade spatiale et distribution des cas par semaine épi OMS.
- **Onglet 2 : `LineList_Nettoyee`** : Données brutes de terrain enrichies avec mise en forme conditionnelle et couleurs distinctes selon le niveau de matching (`MATCH_LEVEL`).
- **Onglet 3 : `Referentiel_PCode`** : Copie intégrale du référentiel géographique P-Code utilisé.

---

## 🪟 Version Exécutable Portable Windows (.exe)

L'outil est disponible sous la forme d'un **exécutable autonome portable (`Linelist_Cleaner.exe`)** pour Windows :
- **Aucune installation de Python requise**.
- Double-cliquez sur `Linelist_Cleaner.exe` : le serveur démarre et ouvre automatiquement votre navigateur web sur `http://127.0.0.1:8000`.
- Fonctionnement 100% hors-ligne (idéal pour les missions de terrain sans connexion internet).

### Compilation locale sous Windows :
```powershell
pip install -r requirements.txt pyinstaller
pyinstaller --clean Linelist_Cleaner.spec
```
Le binaire est généré dans `dist\Linelist_Cleaner.exe`.

---

## 🚀 Démarrage Rapide

### Mode Application Web
```bash
linelist-cleaner serve --host 0.0.0.0 --port 8000
```
Ouvrez votre navigateur sur `http://localhost:8000`.

### Mode Ligne de Commande (CLI)
```bash
# Nettoyage d'une line list et export du classeur Excel 3 onglets
linelist-cleaner clean linelist_brute.csv -o linelist_nettoyee.xlsx --excel

# Audit qualité rapide dans le terminal
linelist-cleaner audit linelist_brute.csv
```

### Exemple en Python
```python
import pandas as pd
from linelist_cleaner import LinelistCleaner, CleaningConfig
from linelist_cleaner.datasets import get_sample_dataset

# 1. Chargement de la line list et du référentiel P-Code OCHA
linelist_raw = get_sample_dataset("borno")
pcode_ref = get_sample_dataset("pcode_reference")

# 2. Configuration du moteur
config = CleaningConfig(
    enable_spatial_cascade=True,
    spatial_similarity_threshold=80.0,
    compute_epi_weeks=True
)

# 3. Exécution du nettoyage et du géocodage en cascade
cleaner = LinelistCleaner(config=config)
cleaned_df, report = cleaner.clean(linelist_raw, reference_pcode_df=pcode_ref)

print(f"Taux de géocodage : {report.spatial_summary.geocoded_rate_pct}%")

# 4. Export du classeur Excel à 3 onglets
cleaner.export_excel(cleaned_df, report, "Linelist_Nettoyee_PCode.xlsx", reference_df=pcode_ref)
```

---

## 🧪 Tests & Qualité Logicielle

```bash
pytest -v
# 45 passed in 11.25s
```

---

## 📄 Licence

© PratiSIG Consulting Services - Dakar, Sénégal. Outil à usage libre pour la communauté SIG et humanitaire sous licence [MIT](LICENSE).
