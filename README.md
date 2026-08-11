# Linelist Cleaner & Géocodage Spatial en Cascade (P-Codes OCHA COD-AB)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![Windows Executable](https://img.shields.io/badge/Windows-Standalone%20.exe-brightgreen.svg)](https://github.com/pratisig/Linelist_cleaner/releases)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-orange.svg)](.github/workflows/build_windows_exe.yml)
[![Tests](https://img.shields.io/badge/tests-45%20passed-brightgreen.svg)]()

> **Linelist Cleaner** est une application complète de nettoyage de line lists épidémiologiques, de calcul des semaines épidémiologiques OMS et de **géocodage spatial hiérarchique en cascade (P-Codes OCHA COD-AB)**. Conçue pour les épidémiologistes de terrain (FETP), les gestionnaires de données humanitaires et les équipes d'intervention d'urgence sanitaire (ex. choléra, rougeole, fièvres hémorragiques).

---

## 🌟 Fonctionnalités Clés

### 1. 📍 Algorithme de Matching Spatial en Cascade (5 Niveaux de Fallback)
- Curseur de similarité floue (Fuzzy Matching) réglable de 50% à 100% (défaut : **80%**).
- Cascade hiérarchique avec arrêt dès qu'une correspondance est trouvée :
  1. **Étape 1 : Localité / Village / Camp IDP** → Attribution du P-code Localité (`MATCH_LEVEL = 'Locality'`)
  2. **Étape 2 (Fallback 1) : Admin 3 / Ward / Aire de santé** → Attribution du P-code Admin 3 (`MATCH_LEVEL = 'Admin3_Ward'`)
  3. **Étape 3 (Fallback 2) : Admin 2 / LGA / Zone de santé** → Attribution du P-code Admin 2 (`MATCH_LEVEL = 'Admin2_LGA'`)
  4. **Étape 4 (Fallback 3) : Admin 1 / État / Province** → Attribution du P-code Admin 1 (`MATCH_LEVEL = 'Admin1_State'`)
  5. **Étape 5 : Non localisé** → Attribution null (`MATCH_LEVEL = 'Unmatched'`)
- Ajout automatique des colonnes : `PCODE_ASSIGNED`, `MATCH_LEVEL`, `MATCH_SCORE`, `MATCHED_NAME`, `LATITUDE`, `LONGITUDE`.

### 2. 📅 Normalisation Temporelle & Semaines Épidémiologiques OMS
- Parsing multi-formats de dates (`DD/MM/YYYY`, `YYYY-MM-DD`, `DD-Mon-YYYY`, mois français/espagnols, entiers Excel serials).
- Calcul automatique de la semaine épi selon la norme OMS / ISO 8601 :
  - `EPI_WEEK` (ex. `2023-W33`)
  - `EPI_WEEK_NUM` (ex. `33`)
  - `EPI_YEAR` (ex. `2023`)
  - `DATE_ADMISSION_CLEAN` (format ISO `YYYY-MM-DD`)

### 3. 🗺️ Visualisation Cartographique SIG (Leaflet.js)
- Carte interactive intégrée affichant chaque cas géocodé avec des pastilles colorées par niveau de précision :
  - 🟢 **Vert** : Localité
  - 🔵 **Turquoise** : Admin 3 (Ward)
  - 🔷 **Bleu** : Admin 2 (LGA)
  - 🟡 **Ambre** : Admin 1 (State)
- Popups d'informations : ID Patient, Nom de l'entité, P-Code, Score et Semaine Épi.

### 4. 📥 Exportation Excel Multi-Onglets (.xlsx)
- **Onglet 1 : `KPI_Dashboard`** : Synthèse des métriques, taux de géocodage global (%), répartition des cas par niveau de précision et synthèse par semaine épi OMS.
- **Onglet 2 : `LineList_Nettoyee`** : Line list brute enrichie avec mise en forme conditionnelle et couleurs distinctes selon le `MATCH_LEVEL`.
- **Onglet 3 : `Referentiel_PCode`** : Copie conforme du référentiel spatial P-code chargé.

---

## 🪟 Version Exécutable Autonome Windows (.exe)

L'application peut être distribuée sous forme de **fichier exécutable autonome (`Linelist_Cleaner.exe`)** fonctionnant directement sous Windows sans avoir besoin d'installer Python.

### Comment l'utilisateur final l'utilise sous Windows :
1. Télécharger `Linelist_Cleaner_Windows_x64.zip` ou `Linelist_Cleaner.exe` depuis la section **Releases** de votre dépôt GitHub.
2. **Double-cliquer sur `Linelist_Cleaner.exe`**.
3. L'application démarre le serveur local et **ouvre automatiquement votre navigateur web par défaut** à l'adresse `http://127.0.0.1:8000`.
4. Aucune connexion Internet ni installation de Python n'est requise.

---

## ⚡ Automatisation avec GitHub Actions

Le workflow GitHub Actions [`.github/workflows/build_windows_exe.yml`](.github/workflows/build_windows_exe.yml) compile automatiquement l'exécutable Windows à chaque mise à jour.

### Déclencheurs configurés :
- À chaque `push` sur les branches principales.
- À chaque création de tag de version (ex. `git tag v1.0.0 && git push origin v1.0.0`).
- Manuellement via le bouton **Run workflow** dans l'onglet **Actions** de GitHub (*workflow_dispatch*).

### Étapes exécutées sur la machine Windows de GitHub :
1. Provisionnement d'un environnement Windows (`windows-latest`) avec Python 3.11.
2. Installation des dépendances et de PyInstaller.
3. Exécution complète des 45 tests unitaires (`pytest`).
4. Compilation en exécutable unique (`Linelist_Cleaner.spec`).
5. Création de l'archive `Linelist_Cleaner_Windows_x64.zip`.
6. Publication automatique dans les artefacts et en tant que release GitHub.

---

## 🛠️ Compilation Manuelle en Local sous Windows (Optionnel)

Si vous souhaitez générer le `.exe` directement sur votre propre machine Windows :

```powershell
# 1. Cloner le dépôt et installer les dépendances
git clone https://github.com/pratisig/Linelist_cleaner.git
cd Linelist_cleaner
pip install -r requirements.txt
pip install pyinstaller

# 2. Compiler avec le fichier spec inclus
pyinstaller --clean Linelist_Cleaner.spec

# 3. L'exécutable autonome est prêt dans le dossier dist\
dist\Linelist_Cleaner.exe
```

---

## 💻 Démarrage en Mode Serveur / Développeur

```bash
# Lancement de l'interface web (accessible sur http://localhost:8000)
linelist-cleaner serve --host 0.0.0.0 --port 8000

# Nettoyage et géocodage direct en CLI
linelist-cleaner clean linelist_brute.csv -o linelist_nettoyee.xlsx --excel
```

---

## 🧪 Tests Unitaires

```bash
pytest -v
# 45 passed in 11.25s
```

---

## 📄 Licence

Projet open-source sous licence [MIT](LICENSE).
