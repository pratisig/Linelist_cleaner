# 📖 Manuel de l'Utilisateur : Linelist Cleaner & Géocodage en Cascade (P-Codes OCHA)

**Linelist Cleaner & SIG**
*Application de Nettoyage de Données Épidémiologiques et de Rapprochement Spatial Hiérarchique*

---
> **🆕 V2.0.0 (2026-08-11) disponible !** Voir [README V2](README.md) & [CHANGELOG_V2.md](CHANGELOG_V2.md) : workbook 6 onglets + GeoJSON, veille épidémique, téléphones/coordonnées, presets, dark mode. Workbook 3→6 onglets, nouveaux endpoints & CLI.



### 🏛️ Informations & Droits d'Auteur

- **Organisation** : PratiSIG Consulting Services
- **Devise / Slogan** : *La pratique des SIG, notre métier*
- **Siège** : Dakar, Sénégal
- **Auteur Principal** : **Youssoupha MBODJI**
- **Contact** : [pratisig.consulting@gmail.com](mailto:pratisig.consulting@gmail.com)
- **Droits & Licence** : © PratiSIG Consulting Services - Dakar, Sénégal. Outil à usage libre pour la communauté SIG et humanitaire (Licence Open Source MIT).

---

## 📑 Table des Matières

1. [Introduction & Contexte Métier](#1-introduction--contexte-métier)
2. [Lancement de l'Application](#2-lancement-de-lapplication)
   - [Version Portable Windows (.exe) sans installation](#a-version-portable-windows-exe)
   - [Mode Serveur Web Local / Docker](#b-mode-serveur-web-local--docker)
3. [Guide Étape par Étape d'Utilisation](#3-guide-étape-par-étape-dutilisation)
   - [Étape 1 : Charger votre Line List de Terrain](#étape-1--charger-votre-line-list-de-terrain)
   - [Étape 2 : Ignorer les Lignes d'En-tête de Titre (Skip Rows) & Choisir la Feuille Excel](#étape-2--ignorer-les-lignes-den-tête-de-titre-skip-rows--choisir-la-feuille-excel)
   - [Étape 3 : Charger votre Référentiel P-Code OCHA](#étape-3--charger-votre-référentiel-p-code-ocha)
   - [Étape 4 : Vérifier et Ajuster le Mapping des Colonnes](#étape-4--vérifier-et-ajuster-le-mapping-des-colonnes)
   - [Étape 5 : Régler le Seuil de Similarité Floue (Fuzzy Threshold)](#étape-5--régler-le-seuil-de-similarité-floue)
   - [Étape 6 : Lancer le Traitement et Analyser les Résultats](#étape-6--lancer-le-traitement-et-analyser-les-résultats)
4. [Description Détaillée des Onglets](#4-description-détaillée-des-onglets)
   - [📊 Onglet 1 : Tableau de Bord KPI & Précision](#-onglet-1--tableau-de-bord-kpi--précision)
   - [🗺️ Onglet 2 : Carte Interactive SIG (Leaflet)](#️-onglet-2--carte-interactive-sig-leaflet)
   - [📋 Onglet 3 : Données Nettoyées & P-Codes](#-onglet-3--données-nettoyées--p-codes)
   - [🔗 Onglet 4 : Mapping Spatial & Colonnes](#-onglet-4--mapping-spatial--colonnes)
   - [📈 Onglet 5 : Courbe Épidémique (EPI_WEEK OMS)](#-onglet-5--courbe-épidémique-epi_week-oms)
   - [⚠️ Onglet 6 : Anomalies & Contrôle Qualité](#️-onglet-6--anomalies--contrôle-qualité)
   - [📥 Onglet 7 : Exportation des Données & Classeur 3 Onglets](#-onglet-7--exportation-des-données--classeur-3-onglets)
5. [Structure Recommandée du Référentiel P-Code OCHA](#5-structure-recommandée-du-référentiel-p-code-ocha)
6. [Foire Aux Questions & Résolution des Problèmes (FAQ)](#6-foire-aux-questions--résolution-des-problèmes-faq)

---

## 1. Introduction & Contexte Métier

Lors des épidémies et urgences sanitaires (ex. choléra, rougeole, fièvres hémorragiques), les données individuelles des patients (*Line Lists*) recueillies dans les structures de soins ou camps de déplacés souffrent fréquemment :
- D'erreurs d'orthographe sur les noms de localités (`"Bollori"` au lieu de `"Bolori I"`, `"Muna Garage Camp"` au lieu de `"Muna Garage IDP Camp"`).
- De dates hétérogènes (`04/09/2023`, `2023-09-04`, `4 sept 2023`, entiers Excel `45173`).
- De lignes d'en-tête de titre ou de métadonnées superflues en haut de fichier (ex: *Ministère de la Santé / Rapport hebdomadaire*).
- D'incohérences chronologiques (date de sortie antérieure à l'admission, âge négatif).

Ces erreurs bloquent le rapprochement avec les référentiels géographiques standards (P-Codes OCHA COD-AB) et la production cartographique rapide.

**Linelist Cleaner résout ce problème** grâce à son **moteur de cascade spatiale hiérarchique** qui tente d'abord de localiser chaque patient au niveau le plus fin possible (Localité), et rétrograde automatiquement vers le niveau supérieur (Admin 3, Admin 2, Admin 1) si la localité est introuvable.

---

## 2. Lancement de l'Application

### A. Version Portable Windows (.exe)

1. Téléchargez `Linelist_Cleaner.exe` depuis la section **Releases** du dépôt GitHub.
2. **Double-cliquez sur `Linelist_Cleaner.exe`**.
3. Une console s'ouvre pour initialiser l'application.
4. **Votre navigateur web s'ouvre automatiquement** sur `http://127.0.0.1:8000`.
5. *Conseil : Laissez la fenêtre de console ouverte pendant l'utilisation.*

### B. Mode Serveur Web Local / Docker

- **En ligne de commande Python** :
  ```bash
  linelist-cleaner serve --port 8000
