# 📖 Manuel de l'Utilisateur : Linelist Cleaner V2 & Géocodage en Cascade

**Linelist Cleaner V2 — Plateforme de Nettoyage Épidémiologique, Géocodage Spatial & Veille Sanitaire**  
*PratiSIG Consulting Services — Dakar, Sénégal*  
*Auteur : **Youssoupha MBODJI** (pratisig.consulting@gmail.com)*  
*Slogan : « La pratique des SIG, notre métier »*  
*Licence : MIT (Usage libre pour les acteurs de santé publique et humanitaires)*

---

## 📑 Table des Matières

1. [Principes Généraux & Architecture du Moteur](#1-principes-généraux--architecture-du-moteur)
2. [Comment Fonctionne le Géocodage Spatial en Cascade (P-Codes OCHA)](#2-comment-fonctionne-le-géocodage-spatial-en-cascade-p-codes-ocha)
   - [Le modèle de jointure en cascade (similaire à Power Query / R / Python)](#a-le-modèle-de-jointure-en-cascade)
   - [Comment mapper votre Line List avec votre Référentiel](#b-comment-mapper-votre-line-list-avec-votre-référentiel)
   - [Extraction des vrais P-Codes du Référentiel](#c-extraction-des-vrais-p-codes-du-référentiel)
   - [Comprendre le Taux de Géocodage (%)](#d-comprendre-le-taux-de-géocodage-)
3. [Calcul des Semaines Épidémiologiques OMS (`EPI_WEEK`)](#3-calcul-des-semaines-épidémiologiques-oms-epi_week)
   - [Quelle colonne date est utilisée ?](#a-quelle-colonne-date-est-utilisée-)
   - [Norme épidémiologique internationale](#b-norme-épidémiologique-internationale)
4. [Indicateurs Épidémiologiques & Courbe Épi](#4-indicateurs-épidémiologiques--courbe-épi)
   - [Semaine Pic & Période de l'Épidémie](#a-semaine-pic--période-de-lépidémie)
   - [Moyenne Hebdomadaire & Minimum/Maximum](#b-moyenne-hebdomadaire--minimummaximum)
   - [Taux de Létalité Global (CFR)](#c-taux-de-létalité-global-cfr)
   - [Tendance d'Incidence & Temps de Doublement](#d-tendance-dincidence--temps-de-doublement)
5. [Contrôle Qualité, Calcul du Score (ex. 80%) & Doublons](#5-contrôle-qualité-calcul-du-score-ex-80--doublons)
   - [Comment est calculé le Score Global de Qualité ?](#a-comment-est-calculé-le-score-global-de-qualité-)
   - [Comment fonctionnent les Groupes de Duplicatas (Doublons) ?](#b-comment-fonctionnent-les-groupes-de-duplicatas-doublons-)
6. [Différence entre les Boutons d'Action](#6-différence-entre-les-boutons-daction)
7. [Guide d'Utilisation Étape par Étape](#7-guide-dutilisation-étape-par-étape)
8. [Foire Aux Questions (FAQ)](#8-foire-aux-questions-faq)

---

## 1. Principes Généraux & Architecture du Moteur

Sur le terrain (missions MSF, OMS, Ministères de la Santé, ONG humanitaires), les bases de données de surveillance (*Line Lists*) proviennent de multiples structures de soins et présentent des hétérogénéités :
- Noms de colonnes variables selon les pays (`rq_norm`, `rue_quartier`, `village_village`, `district`, `zone_sante`, `adm3`).
- Orthographe approximative des localités (`Bollori`, `Custom House IDP`, `Muna Garage`).
- Formats de dates hétérogènes (Excel, ISO, texte).

Linelist Cleaner V2 normalise ces données, applique les jointures floues en cascade contre vos référentiels administratifs et génère des classeurs Excel 6 onglets ainsi que des fichiers GeoJSON prêts pour QGIS et ArcGIS.

---

## 2. Comment Fonctionne le Géocodage Spatial en Cascade (P-Codes OCHA)

### A. Le modèle de jointure en cascade

Le moteur applique une cascade hiérarchique en 4 étapes successives (*similaire aux jointures conditionnelles imbriquées dans Power Query ou R*) :

```
[ Ligne Patient ]
       │
       ▼
1. Match Localité (Village / Rue / Quartier) ?
       ├── OUI ──► Assigne PCODE_LOCALITY & Coordonnées GPS Village
       └── NON
            │
            ▼
2. Match Admin 3 (Ward / Sous-district / Aire de Santé) ?
       ├── OUI ──► Assigne PCODE_ADMIN3 & Coordonnées Admin 3
       └── NON
            │
            ▼
3. Match Admin 2 (District / LGA / Cercle / Département) ?
       ├── OUI ──► Assigne PCODE_ADMIN2 & Coordonnées Admin 2
       └── NON
            │
            ▼
4. Match Admin 1 (Région / Province / État) ?
       ├── OUI ──► Assigne PCODE_ADMIN1 & Coordonnées Admin 1
       └── NON ──► Marqué comme 'Unmatched' (Non localisé)
```

### B. Comment mapper votre Line List avec votre Référentiel

Dans l'onglet **« Mapping »**, chaque niveau géographique est paramétré avec 3 sélecteurs :

| Champ dans l'Interface | Description | Exemple Linelist | Exemple Référentiel |
| :--- | :--- | :--- | :--- |
| **📊 1. Colonne Line List** | La colonne de votre base patient à géocoder | `rue_quartier` ou `rq_norm` | — |
| **🗺️ 2. Colonne Nom Référentiel** | La colonne du référentiel contenant les noms de lieux à comparer | — | `loc_nr` ou `Locality_Name` |
| **🏷️ 3. Colonne P-Code Référentiel** | La colonne du référentiel contenant le code officiel à extraire | — | `pcode` ou `Locality_Pcode` |

### C. Extraction des vrais P-Codes du Référentiel

- Le moteur extrait **exclusivement les vrais P-Codes** présents dans votre fichier de référentiel (`pcode`, `code`, `pcode_adm3`, `pcode_adm2`, `pcode_adm1`).
- **Aucun code artificiel ou inventé (comme `LOC_...`) n'est généré** : si une ligne n'a pas de correspondance dans le référentiel, la colonne P-Code reste vide (`null`) et le statut est `Unmatched`.
- Les colonnes extraites dans le fichier de sortie sont :
  - `PCODE_ASSIGNED` : Meilleur P-Code trouvé (Localité > Admin 3 > Admin 2 > Admin 1).
  - `MATCH_LEVEL` : Niveau auquel le match a abouti (`Locality`, `Admin3_Ward`, `Admin2_LGA`, `Admin1_State`, ou `Unmatched`).
  - `MATCH_SCORE` : Score de similarité textuelle floue (0 à 100%).
  - `MATCHED_NAME` : Nom officiel correspondant dans le référentiel.
  - `PCODE_LOCALITY`, `PCODE_ADMIN3`, `PCODE_ADMIN2`, `PCODE_ADMIN1`.
  - `LATITUDE`, `LONGITUDE` : Coordonnées GPS WGS84.

### D. Comprendre le Taux de Géocodage (%)

$$\text{Taux de Géocodage (\%)} = \frac{\text{Nombre de cas avec un vrai P-Code trouvé}}{\text{Nombre total de cas dans la Line List}} \times 100$$

*Exemple* : Sur 180 cas, si 77 cas sont localisés (32 au niveau village, 25 au niveau Ward, 15 au niveau LGA, 5 au niveau Région) et 103 cas sont `Unmatched`, le taux est de **43.1% (77/180)**.

---

## 3. Calcul des Semaines Épidémiologiques OMS (`EPI_WEEK`)

### A. Quelle colonne date est utilisée ?

Le moteur recherche automatiquement la date épidémiologique selon l'ordre de priorité clinique suivant :
1. **Date de début des symptômes** (`date_onset`, `date_debut`)
2. **Date d'admission hospitalière / CTC** (`date_admission`, `date_entree`)
3. **Date de consultation / visite** (`date_consultation`, `date_visite`)
4. **Date de notification / déclaration** (`date_notification`, `date_declaration`)
5. **Date de prélèvement biologique** (`date_sample`, `date_prelevement`)
6. Toute colonne de date personnalisée sélectionnée dans l'onglet **Mapping** sous *« 📅 Date Principale »*.

### B. Norme épidémiologique internationale

- Les semaines OMS suivent le standard international **ISO 8601 / OMS** (semaine commençant le lundi et se terminant le dimanche).
- Le format généré est :
  - `EPI_WEEK` : ex. `2026-W06` (Année - Semaine).
  - `EPI_WEEK_NUM` : Numéro entier de 1 à 53.
  - `EPI_YEAR` : Année épidémiologique.

---

## 4. Indicateurs Épidémiologiques & Courbe Épi

Linelist Cleaner V2 calcule automatiquement des indicateurs épidémiologiques clés de santé publique :

### A. Semaine Pic & Période de l'Épidémie
- **Semaine Pic (`Peak Week`)** : La semaine épidémiologique ayant enregistré le plus grand nombre de cas (ex. `2026-W08` avec 45 cas).
- **Période de l'épidémie** : Première semaine enregistrée $\rightarrow$ dernière semaine enregistrée (ex. `2026-W01 → 2026-W12` : durée de 12 semaines).

### B. Moyenne Hebdomadaire & Minimum/Maximum
- **Moyenne hebdomadaire** : Nombre moyen de nouveaux cas par semaine ($\bar{x} = \frac{\sum \text{cas}}{\text{nombre de semaines}}$).
- **Minimum et Maximum** : Permettent d'observer l'amplitude de l'onde épidémique.

### C. Taux de Létalité Global (CFR)

$$\text{CFR (\%)} = \frac{\text{Nombre total de décès}}{\text{Nombre total de cas}} \times 100$$

- Si votre Line List ne contient pas de colonne d'issue clinique (`outcome` / `statut_patient`) ou si aucun décès n'est enregistré, le CFR affiche `0 décès documenté (CFR 0.0%)`.
- Dès qu'une colonne avec des issues (`Dead`, `Décédé`, `DCD`, `Mort`) est présente, le CFR exact et le nombre de décès s'actualisent instantanément.

### D. Tendance d'Incidence & Temps de Doublement
- **Tendance** : Comparaison de la dynamique des deux dernières semaines épidémiologiques :
  - $\nearrow$ **En hausse** : Croissance hebdomadaire positive ($> 0\%$).
  - $\searrow$ **En baisse** : Décroissance hebdomadaire ($< 0\%$).
  - $\rightarrow$ **Stable** : Variation nulle ou négligeable.
- **Temps de doublement (*Doubling Time*)** : Estimation en semaines du temps nécessaire pour que le nombre de cas double si la vitesse de transmission actuelle se maintient ($T_d = \frac{\ln(2)}{\ln(1+r)}$).

---

## 5. Contrôle Qualité, Calcul du Score (ex. 80%) & Doublons

### A. Comment est calculé le Score Global de Qualité ?

Le score qualité (sur 100%) est une note composite pondérée calculée par le module d'audit épidémiologique :

1. **Complétude (Completeness - 30%)** : Taux de remplissage des variables indispensables (Identifiant, Âge, Sexe, Date, Localité).
2. **Validité Clinique & Démographique (Validity - 30%)** : Absence d'âges invraisemblables ($<0$ ou $>120$), absence de dates futures ou antérieures à 1900.
3. **Cohérence Chronologique (Chronology - 20%)** : Respect de la chronologie logique ($\text{Date début} \le \text{Date consultation} \le \text{Date admission} \le \text{Date sortie/décès}$).
4. **Unicité des Patients (Uniqueness - 20%)** : Absence de fiches doublons.

*Échelle des Grades Qualité* :
- **Grade A** : $\ge 90\%$ (Excellente qualité)
- **Grade B** : $80 - 89\%$ (Bonne qualité, anomalies mineures)
- **Grade C** : $70 - 79\%$ (Qualité moyenne, corrections recommandées)
- **Grade D / F** : $< 70\%$ (Données incomplètes ou incohérentes)

### B. Comment fonctionnent les Groupes de Duplicatas (Doublons) ?

- Le moteur compare les fiches patients sur un vecteur d'identité : Nom + Prénom + Sexe + Âge + Date d'apparition + Localité.
- Lorsque deux ou plusieurs lignes présentent une similarité élevée ($\ge 80\%$), elles sont regroupées dans un **Groupe de doublons** (ex. `Groupe #1`).
- L'onglet **Qualité** vous liste les numéros de lignes et les identifiants patients concernés pour vous permettre de vérifier s'il s'agit d'une double notification ou d'une ré-admission.

---

## 6. Différence entre les Boutons d'Action

| Bouton | Emplacement | Fonction |
| :--- | :--- | :--- |
| **« Nettoyer V2 »** | En haut à droite (Barre principale) | Lance le nettoyage global avec les détections automatiques et les paramètres généraux. |
| **« ⚡ Appliquer & Recalculer »** | Dans l'onglet **Mapping** | Applique immédiatement vos correspondances manuelles personnalisées entre les colonnes de votre Line List et celles de votre Référentiel, puis recalcule la cascade spatiale. |

---

## 7. Guide d'Utilisation Étape par Étape

1. **Charger la Line List** : Glissez-déposez ou cliquez sur le bouton bleu « Parcourir » pour charger votre fichier Excel (`.xlsx`, `.xls`) ou CSV.
2. **Charger le Référentiel P-Code** : Glissez-déposez votre référentiel de localités / COD-AB dans la zone verte.
3. **Ajuster le Mapping (Onglet Mapping)** :
   - Vérifiez que la colonne de localité de votre linelist (ex: `rue_quartier` ou `village`) est bien associée à la colonne nom du référentiel (ex: `loc_nr`) et à la colonne P-Code (ex: `pcode`).
   - Cliquez sur **« ⚡ Appliquer & Recalculer le Nettoyage »**.
4. **Consulter la Carte SIG (Onglet Carte SIG)** : Visualisez les marqueurs géocodés sur le plan CartoDB ou l'image satellite Esri.
5. **Consulter la Courbe Épi (Onglet Courbe épi)** : Observez la dynamique hebdomadaire OMS et le pic épidémique.
6. **Exporter (Onglet Export V2)** : Téléchargez votre classeur Excel 6 onglets, votre fichier CSV assaini, votre GeoJSON pour QGIS ou votre script Python reproductible.

---

## 8. Foire Aux Questions (FAQ)

### Pourquoi les boutons de téléchargement semblaient ne pas réagir ?
Dans les environnements avec iframe (comme les previews sécurisées), l'ouverture d'onglets externes (`window.open`) peut être bloquée par la politique du navigateur. Les boutons utilisent désormais un déclencheur direct par flux binaire (`Blob Download`) qui fonctionne de manière 100% transparente dans tous les navigateurs.

### Que faire si mon référentiel ne contient que des villages et pas de codes Admin ?
Aucun problème : le moteur prend en charge les référentiels de localités simples. Il suffit de mapper la colonne des villages de votre linelist avec celle de votre référentiel.

### Comment intégrer le résultat dans QGIS ou ArcGIS ?
Rendez-vous dans l'onglet **Export V2** et téléchargez le fichier **GeoJSON**. Glissez-le directement dans QGIS ou ArcGIS : tous les points, P-Codes, semaines épidémiologiques et variables patients sont déjà géoréférencés en WGS84 (EPSG:4326).
