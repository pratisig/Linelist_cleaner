# 📖 Manuel de l'Utilisateur — Linelist Cleaner & Géocodage en Cascade (P-Codes OCHA)

Bienvenue dans le manuel d'utilisation de **Linelist Cleaner**, l'application conçue pour le nettoyage, la validation épidémiologique, le calcul des semaines épidémiologiques OMS et le géocodage spatial en cascade avec attribution des P-Codes de référence (OCHA COD-AB).

---

## 📑 Table des Matières

1. [Introduction & Contexte Métier](#1-introduction--contexte-métier)
2. [Modes de Lancement de l'Application](#2-modes-de-lancement-de-lapplication)
   - [Lancement sous Windows via l'Exécutable (.exe)](#a-lancement-sans-python-fichier-exe-windows)
   - [Lancement via Navigateur Web / Serveur](#b-lancement-serveur-web--docker)
3. [Guide Étape par Étape d'Utilisation](#3-guide-étape-par-étape-dutilisation)
   - [Étape 1 : Charger une Line List de Terrain](#étape-1--charger-une-line-list-de-terrain)
   - [Étape 2 : Charger ou Utiliser le Référentiel P-Code OCHA](#étape-2--charger-ou-utiliser-le-référentiel-p-code-ocha)
   - [Étape 3 : Vérifier et Ajuster la Correspondance des Colonnes (Column Mapping)](#étape-3--vérifier-et-ajuster-la-correspondance-des-colonnes)
   - [Étape 4 : Régler le Seuil de Similarité Floue (Fuzzy Threshold)](#étape-4--régler-le-seuil-de-similarité-floue)
   - [Étape 5 : Lancer le Traitement et Analyser les Résultats](#étape-5--lancer-le-traitement-et-analyser-les-résultats)
4. [Comprendre les Onglets de l'Application](#4-comprendre-les-onglets-de-lapplication)
   - [📊 Onglet 1 : Tableau de Bord KPI & Précision](#-onglet-1--tableau-de-bord-kpi--précision)
   - [🗺️ Onglet 2 : Carte Interactive SIG (Leaflet)](#️-onglet-2--carte-interactive-sig-leaflet)
   - [📋 Onglet 3 : Données Nettoyées & P-Codes](#-onglet-3--données-nettoyées--p-codes)
   - [🔗 Onglet 4 : Mapping Spatial & Colonnes](#-onglet-4--mapping-spatial--colonnes)
   - [📈 Onglet 5 : Courbe Épidémique (EPI_WEEK OMS)](#-onglet-5--courbe-épidémique-epi_week-oms)
   - [⚠️ Onglet 6 : Anomalies & Contrôle Qualité](#️-onglet-6--anomalies--contrôle-qualité)
   - [📥 Onglet 7 : Exportation des Données & Classeur 3 Onglets](#-onglet-7--exportation-des-données--classeur-3-onglets)
5. [Spécification du Fichier Référentiel P-Code OCHA](#5-spécification-du-fichier-référentiel-p-code-ocha)
6. [Foire Aux Questions & Résolution des Problèmes (FAQ)](#6-foire-aux-questions--résolution-des-problèmes-faq)

---

## 1. Introduction & Contexte Métier

Lors des épidémies et urgences sanitaires (ex. choléra, rougeole, fièvres hémorragiques virales), les données individuelles des patients (*Line Lists*) recueillies dans les centres de santé ou camps de déplacés souffrent fréquemment :
- D'erreurs d'orthographe sur les noms de localités ou de quartiers (`"Bollori"` au lieu de `"Bolori I"`, `"Muna Garage Camp"` au lieu de `"Muna Garage IDP Camp"`).
- De dates hétérogènes (`04/09/2023`, `2023-09-04`, `4 sept 2023`, entiers Excel `45173`).
- D'incohérences chronologiques (date de sortie antérieure à l'admission, âge négatif).

Ces erreurs empêchent la jointure directe avec les référentiels géographiques standards (P-Codes OCHA COD-AB) et la production cartographique rapide.

**Linelist Cleaner résout ce problème** grâce à un **algorithme de cascade spatiale hiérarchique** qui tente de localiser chaque patient au niveau le plus précis possible, et rétrograde automatiquement vers le niveau supérieur si la localité est introuvable.

---

## 2. Modes de Lancement de l'Application

### A. Lancement sans Python (Fichier .exe Windows)

Si vous utilisez la version exécutable Windows :
1. Téléchargez `Linelist_Cleaner.exe` depuis la section **Releases** de votre dépôt GitHub.
2. **Double-cliquez sur `Linelist_Cleaner.exe`**.
3. Une fenêtre noire s'ouvre pour initialiser l'application en arrière-plan.
4. **Votre navigateur web s'ouvre automatiquement** sur `http://127.0.0.1:8000`.
5. *Conseil : Ne fermez pas la fenêtre noire pendant que vous utilisez l'application.*

### B. Lancement Serveur Web / Docker

- **En ligne de commande Python** :
  ```bash
  linelist-cleaner serve --port 8000
  ```
- **Avec Docker** :
  ```bash
  cd deploy && docker compose up -d
  ```

---

## 3. Guide Étape par Étape d'Utilisation

### Étape 1 : Charger une Line List de Terrain
1. Dans la bannière du haut, cliquez sur la zone bleue **"Charger Line List (.csv / .xlsx)"**.
2. Sélectionnez votre fichier de cas bruts sur votre ordinateur.
3. *Astuce : Vous pouvez aussi cliquer directement sur le bouton d'exemple **"📍 Borno Choléra (P-Codes)"** pour explorer immédiatement avec un jeu de données réel.*

### Étape 2 : Charger ou Utiliser le Référentiel P-Code OCHA
1. Par défaut, le référentiel OCHA COD-AB standard (Borno/Yobe, Nigéria) est préchargé.
2. Pour utiliser votre propre référentiel (ex. RDC Nord-Kivu, Haïti, Cameroun) : cliquez sur la zone verte **"Référentiel P-Code (OCHA COD-AB)"** et sélectionnez votre fichier CSV ou Excel.

### Étape 3 : Vérifier et Ajuster la Correspondance des Colonnes
1. Rendez-vous dans l'onglet **"🔗 Mapping Spatial & Colonnes"**.
2. L'algorithme détecte automatiquement les variables :
   - `Localité / Village`
   - `Admin 3 (Ward / Aire de santé)`
   - `Admin 2 (LGA / District)`
   - `Admin 1 (State / Province)`
   - `Date d'admission / Date de début`
   - `Sexe`, `Âge`, `Issue clinique`, `Classification du cas`
3. Si une colonne n'a pas été reconnue, utilisez le menu déroulant pour lui assigner la variable correspondante.

### Étape 4 : Régler le Seuil de Similarité Floue
1. Dans le bandeau supérieur gris, utilisez le curseur **"Seuil de Similarité Fuzzy"** :
   - **80% (Recommandé)** : Tolère les fautes de frappe courantes tout en évitant les faux positifs.
   - **90% - 100% (Strict)** : Exige une quasi-exactitude orthographique.
   - **60% - 70% (Tolérant)** : Utile si les noms de villages ont des variations phonétiques importantes.

### Étape 5 : Lancer le Traitement et Analyser les Résultats
1. Cliquez sur le bouton vert **"Exécuter Nettoyage & Cascade"** en haut à droite.
2. Le traitement s'exécute en quelques secondes.
3. Consultez les indicateurs du tableau de bord et la carte interactive.

---

## 4. Comprendre les Onglets de l'Application

### 📊 Onglet 1 : Tableau de Bord KPI & Précision
Cet onglet présente la synthèse opérationnelle :
- **Nombre Total de Cas** : Volume de la line list traitée.
- **Taux Global de Géocodage (%)** : Pourcentage de cas ayant reçu un P-Code valide.
- **Score Moyen de Similarité** : Mesure de la qualité du rapprochement textuel.
- **Tableau de Répartition de la Cascade** :
  - **Étape 1 (Localité)** : Cas rattachés au village / camp exact.
  - **Étape 2 (Admin 3)** : Cas rattachés au Ward / Aire de santé.
  - **Étape 3 (Admin 2)** : Cas rattachés au LGA / District.
  - **Étape 4 (Admin 1)** : Cas rattachés à l'État / Province.
  - **Étape 5 (Unmatched)** : Cas non localisés.
- **Graphique Donut** illustrant visuellement la précision géographique.

---

### 🗺️ Onglet 2 : Carte Interactive SIG (Leaflet)
- Affiche une carte dynamique OpenStreetMap avec tous les cas géocodés.
- Les pastilles sont colorées selon le niveau de précision :
  - 🟢 **Vert** : Localité / Village
  - 🔵 **Turquoise** : Admin 3 (Ward)
  - 🔷 **Bleu** : Admin 2 (LGA)
  - 🟡 **Ambre** : Admin 1 (State)
- Cliquez sur un point pour ouvrir la popup avec le **P-Code**, le **Nom du lieu apparié**, le **Score %** et la **Semaine Épi OMS**.

---

### 📋 Onglet 3 : Données Nettoyées & P-Codes
- Tableau complet contenant les données originales enrichies des nouvelles colonnes :
  - `PCODE_ASSIGNED` : Le code standard OCHA attribué.
  - `MATCH_LEVEL` : Le niveau de résolution (`Locality`, `Admin3_Ward`, `Admin2_LGA`, `Admin1_State`, `Unmatched`).
  - `MATCH_SCORE` : Le score de confiance (de 0 à 100%).
  - `MATCHED_NAME` : Le nom officiel du lieu trouvé dans le référentiel.
  - `EPI_WEEK` : La semaine épidémiologique OMS (ex. `2023-W33`).
  - `EPI_WEEK_NUM` : Le numéro de semaine (ex. `33`).
  - `DATE_ADMISSION_CLEAN` : La date normalisée au format ISO `YYYY-MM-DD`.
  - `LATITUDE`, `LONGITUDE` : Les coordonnées géographiques.
- Utilisez le filtre **"Filtrer par niveau"** pour inspecter par exemple uniquement les cas `Unmatched` et identifier les localités manquantes.

---

### 📈 Onglet 5 : Courbe Épidémique (EPI_WEEK OMS)
- Graphique en barres représentant l'incidence hebdomadaire des cas selon le calendrier standard de surveillance de l'OMS (semaine du dimanche au samedi / ISO 8601).
- Permet de suivre l'évolution temporelle de l'épidémie directement sur les données nettoyées.

---

### ⚠️ Onglet 6 : Anomalies & Contrôle Qualité
- Liste détaillée des incohérences détectées dans la line list :
  - Dates chronologiquement impossibles (ex. date de consultation avant la date de début des symptômes).
  - Âges négatifs ou supérieurs à 120 ans.
  - Incohérences de statut (patient décédé sans date de décès).
  - Doublons identifiés sur le même patient avec recommandation de la ligne à conserver.

---

### 📥 Onglet 7 : Exportation des Données & Classeur 3 Onglets

Trois options de téléchargement en 1 clic :

1. **Classeur Excel Multi-Onglets (`.xlsx`)** :
   - **Onglet 1 : `KPI_Dashboard`** : Synthèse complète des indicateurs, taux de géocodage, tableau de cascade et répartition hebdomadaire.
   - **Onglet 2 : `LineList_Nettoyee`** : Données complètes enrichies avec coloration automatique selon le niveau de matching (`MATCH_LEVEL`).
   - **Onglet 3 : `Referentiel_PCode`** : Copie du référentiel spatial utilisé.
2. **Fichier Plat CSV (`.csv`)** : Fichier plat prêt à être importé dans QGIS, ArcGIS, R ou PowerBI.
3. **Script Python Reproductible (`.py`)** : Code Python automatisé permettant de rejouer le même traitement sur de nouveaux fichiers en ligne de commande.

---

## 5. Spécification du Fichier Référentiel P-Code OCHA

Pour que le géocodage fonctionne de manière optimale, votre fichier de référentiel (CSV ou Excel) doit contenir les colonnes suivantes (les noms peuvent varier, ils sont mappés automatiquement) :

| Rôle Spatial | Exemple de Nom de Colonne | Exemple de Valeur |
| :--- | :--- | :--- |
| **Admin 1 Nom** | `Admin1_Name` ou `State` | `Borno` |
| **Admin 1 P-Code** | `Admin1_Pcode` | `NG008` |
| **Admin 2 Nom** | `Admin2_Name` ou `LGA` | `Maiduguri` |
| **Admin 2 P-Code** | `Admin2_Pcode` | `NG008018` |
| **Admin 3 Nom** | `Admin3_Name` ou `Ward` | `Bolori I` |
| **Admin 3 P-Code** | `Admin3_Pcode` | `NG008018001` |
| **Localité Nom** | `Locality_Name` ou `Village` | `Custom House IDP Camp` |
| **Localité P-Code** | `Locality_Pcode` | `NG008018001001` |
| **Latitude** | `Latitude` ou `Lat` | `11.8333` |
| **Longitude** | `Longitude` ou `Long` | `13.1500` |

---

## 6. Foire Aux Questions & Résolution des Problèmes (FAQ)

### Q1 : Que faire si le taux de géocodage est trop faible ?
- Vérifiez dans l'onglet **"🔗 Mapping Spatial"** que les colonnes administratives de votre line list sont bien associées aux bons rôles.
- Baissez légèrement le **Seuil de Similarité** (ex. passez de 80% à 70% ou 65%) si l'orthographe locale sur le terrain est très variable.
- Vérifiez si votre référentiel P-Code couvre bien la zone géographique de l'épidémie.

### Q2 : Comment sont traitées les dates au format Excel serial (ex. 45180) ?
L'application détecte automatiquement les entiers de date d'Excel et les convertit sans erreur vers la date calendrier ISO correspondante (`2023-09-12`).

### Q3 : Pourquoi certains cas sont marqués `Unmatched` ?
Un cas est marqué `Unmatched` si le nom de localité, de Ward, de LGA et d'État indiqués dans la line list ne trouvent aucune correspondance avec un score supérieur au seuil de similarité dans le référentiel P-Code. Vous pouvez filtrer ces lignes dans l'onglet **"📋 Données Nettoyées"** pour enrichir manuellement votre référentiel.

### Q4 : L'application fonctionne-t-elle sans connexion Internet ?
**Oui, à 100%.** Que ce soit via l'exécutable Windows `.exe` ou via le serveur local, tous les algorithmes de nettoyage, de cascade spatiale et les bibliothèques fonctionnent intégralement hors-ligne.
