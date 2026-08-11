"""
Command-Line Interface (CLI) V2 for Linelist Cleaner.
PratiSIG Consulting Services - Dakar, Sénégal.
Auteur : Youssoupha MBODJI (pratisig.consulting@gmail.com)
Version: 2.0.0
"""

import sys
import os
import argparse
import json
from typing import Optional
import pandas as pd
from tabulate import tabulate

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from linelist_cleaner.schemas.config import CleaningConfig
from linelist_cleaner.core.pipeline import LinelistCleaner, load_dataset
from linelist_cleaner.core.column_standardizer import map_linelist_columns
from linelist_cleaner.datasets import get_sample_dataset


def print_banner():
    banner = """
===================================================================
   PRATISIG CONSULTING SERVICES - DAKAR, SENEGAL
   La pratique des SIG, notre metier — Linelist Cleaner V2.0.0
-------------------------------------------------------------------
   Nettoyage, Geocodage en Cascade (P-Codes OCHA) & Veille Epi
   Auteur  : Youssoupha MBODJI
   Contact : pratisig.consulting@gmail.com
   Docs    : /docs (FastAPI) | V2 Workbook 6 onglets + GeoJSON
===================================================================
"""
    print(banner)


def cmd_clean(args):
    """Clean a linelist dataset and output results V2."""
    print_banner()
    print(f"[*] Lecture de la line list : {args.input}")
    config = CleaningConfig()
    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as f:
            config = CleaningConfig(**json.load(f))
    if getattr(args, "preset", None):
        config.preset = args.preset
    if args.anonymize:
        config.anonymize = True
    if args.dedup_action:
        config.dedup_action = args.dedup_action
    if getattr(args, "similarity", None) is not None:
        config.spatial_similarity_threshold = float(args.similarity)
    if getattr(args, "phone_code", None):
        config.default_phone_country_code = args.phone_code

    cleaner = LinelistCleaner(config=config)
    # reference loading if provided
    ref_df = None
    if getattr(args, "reference", None) and os.path.exists(args.reference):
        ref_df = load_dataset(args.reference)
        print(f"[*] Référentiel P-Code chargé : {args.reference} ({ref_df.shape[0]} lignes)")

    df_clean, report = cleaner.clean(args.input, reference_pcode_df=ref_df)

    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_cleaned_V2.xlsx" if args.excel else f"{base}_cleaned_V2.csv"

    if output_path.endswith((".xlsx", ".xls")) or args.excel:
        if not output_path.endswith(".xlsx"):
            output_path += ".xlsx"
        print(f"[*] Export V2 classeur Excel 6 onglets vers : {output_path}")
        cleaner.export_excel(df_clean, report, output_path, reference_df=ref_df)
    else:
        print(f"[*] Export du fichier nettoyé vers : {output_path}")
        cleaner.export_csv(df_clean, output_path)

    if getattr(args, "geojson", None):
        gj_path = args.geojson if args.geojson != "auto" else os.path.splitext(output_path)[0] + ".geojson"
        LinelistCleaner.export_geojson(df_clean, gj_path)
        print(f"[*] Export GeoJSON V2 : {gj_path}")

    qs = report.quality_scores_after
    print("\n" + "=" * 60)
    print(" SYNTHESE V2 DU TRAITEMENT")
    print("=" * 60)
    print(f" Lignes : {report.original_shape[0]} brutes -> {report.cleaned_shape[0]} nettoyées ({report.cleaned_shape[1]} colonnes)")
    print(f" Score Qualité Global : {qs.overall_score}% [Grade: {qs.grade}]Δ {round(qs.overall_score - report.quality_scores_before.overall_score,1):+}%")
    if report.spatial_summary:
        sp = report.spatial_summary
        print(f" Taux Géocodage (P-Codes) : {sp.geocoded_rate_pct}% ({sp.geocoded_count}/{sp.total_records})")
        print(f" Score Moyen Similarité : {sp.average_match_score}%")
    print(f" Semaines Epi OMS Calculées : {report.epi_weeks_computed}")
    print(f" Coords WGS84 Validées   : {getattr(report,'coordinates_cleaned',0)}")
    print(f" Téléphones Normalisés   : {getattr(report,'phones_standardized',0)}")
    if getattr(report, "incidence_trend", None):
        tr = report.incidence_trend
        # handle BaseModel or dict
        trend = getattr(tr, "trend", None) or (tr.get("trend") if isinstance(tr, dict) else None)
        growth = getattr(tr, "weekly_growth_pct", None) or (tr.get("weekly_growth_pct") if isinstance(tr, dict) else None)
        peak = getattr(tr, "peak_week", None) or (tr.get("peak_week") if isinstance(tr, dict) else None)
        print(f" Tendance Incidence      : {trend} ({growth}%) pic {peak}")
    if getattr(report, "outbreak_alerts", None):
        print(f" Alertes Épidémiques     : {len(report.outbreak_alerts)} semaine(s) > seuil")
    print(f" Anomalies Détectées     : {len(report.validation_issues)} (ERR {report.issues_by_severity.get('ERROR',0)})")
    print(f" Temps d'Exécution       : {report.execution_time_ms} ms")
    print("=" * 60)
    print("© PratiSIG Consulting Services - Dakar, Sénégal - V2.0.0")


def cmd_audit(args):
    """Audit dataset data quality and output report V2."""
    print_banner()
    print(f"[*] Audit qualité V2 : {args.input}")
    cleaner = LinelistCleaner(CleaningConfig(preset=getattr(args, "preset", None)))
    df_clean, report = cleaner.clean(args.input)
    output_path = args.output or "linelist_quality_audit_V2.xlsx"
    cleaner.export_excel(df_clean, report, output_path)
    print(f"[+] Rapport d'audit V2 généré : {output_path} (6 onglets)")
    qs = report.quality_scores_after
    score_table = [
        ["Score Global", f"{qs.overall_score}%", f"Grade {qs.grade} (Δ {round(qs.overall_score - report.quality_scores_after.overall_score if False else qs.overall_score - report.quality_scores_before.overall_score,1):+}%)"],
        ["Complétude", f"{qs.completeness_score}%", "Variables clés renseignées"],
        ["Chronologie", f"{qs.chronology_score}%", "Cohérence temporelle"],
        ["Validité", f"{qs.validity_score}%", "Codes valides"],
        ["Unicité", f"{qs.uniqueness_score}%", "Absence doublons"],
    ]
    print("\n" + tabulate(score_table, headers=["Indicateur", "Score V2", "Description"], tablefmt="grid"))
    if report.outbreak_alerts:
        print("\n[!] Alertes épidémiques :")
        for al in report.outbreak_alerts[:5]:
            # handle both dict and model
            wk = al.get("epi_week") if isinstance(al, dict) else al.epi_week
            cs = al.get("cases") if isinstance(al, dict) else al.cases
            msg = al.get("message") if isinstance(al, dict) else al.message
            print(f"  - {wk}: {cs} cas — {msg}")


def cmd_validate(args):
    """V2 quick validate without full cleaning."""
    print_banner()
    df = load_dataset(args.input)
    from linelist_cleaner.core.logic_validator import LogicValidator
    from linelist_cleaner.core.deduplicator import Deduplicator
    from linelist_cleaner.core.auditor import DataQualityAuditor
    mapping = map_linelist_columns(df)
    tag_to_col = {v["mapped_tag"]: k for k, v in mapping.items() if v["mapped_tag"]}
    validator = LogicValidator()
    issues = validator.validate(df, tag_to_col)
    dups = Deduplicator().find_duplicates(df, tag_to_col)
    qs = DataQualityAuditor.calculate_quality_scores(df, issues, dups, tag_to_col)
    print(f"[*] Fichier : {args.input} — {len(df)} lignes x {len(df.columns)} colonnes")
    print(f" Qualité : {qs.overall_score}% Grade {qs.grade}")
    print(f" Anomalies : {len(issues)} (ERR {sum(1 for i in issues if i.severity=='ERROR')}, WARN {sum(1 for i in issues if i.severity=='WARNING')})")
    print(f" Doublons : {len(dups)} groupes")
    if issues:
        print("\nTop anomalies :")
        for iss in issues[:10]:
            print(f"  L{iss.row_idx} [{iss.severity}] {iss.issue_type} @ {iss.column}: {iss.message}")

def cmd_inspect(args):
    print_banner()
    df = load_dataset(args.input)
    print(f"[*] Dimensions : {df.shape[0]} lignes x {df.shape[1]} colonnes\n")
    mapping = map_linelist_columns(df)
    table_data = []
    for col in df.columns:
        meta = mapping.get(col, {})
        tag = meta.get("mapped_tag") or "N/A"
        cat = meta.get("category") or "N/A"
        missing_count = int(df[col].isna().sum())
        missing_pct = round((missing_count / len(df)) * 100, 1) if len(df) > 0 else 0.0
        unique_cnt = int(df[col].nunique())
        sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "N/A"
        table_data.append([col, tag, cat, f"{100 - missing_pct:.1f}%", unique_cnt, sample_val[:25]])
    print(tabulate(table_data, headers=["Colonne", "Tag", "Catégorie", "Complétude", "Uniques", "Exemple"], tablefmt="grid"))

def cmd_geocode(args):
    """V2 geocode-only mode."""
    print_banner()
    print(f"[*] Géocodage seul : {args.input}")
    ref_df = load_dataset(args.reference) if args.reference and os.path.exists(args.reference) else get_sample_dataset("pcode_reference")
    config = CleaningConfig(spatial_similarity_threshold=float(args.similarity) if args.similarity else 80.0)
    cleaner = LinelistCleaner(config=config)
    df_clean, report = cleaner.clean(args.input, reference_pcode_df=ref_df)
    out = args.output or "geocoded_output.xlsx"
    cleaner.export_excel(df_clean, report, out, reference_df=ref_df)
    print(f"[+] Géocodage terminé : {report.spatial_summary.geocoded_rate_pct}% géocodés —> {out}")
    if getattr(args, "geojson", None):
        gj = args.geojson if args.geojson != "auto" else out.replace(".xlsx",".geojson")
        LinelistCleaner.export_geojson(df_clean, gj)
        print(f"[+] GeoJSON : {gj}")

def cmd_profile(args):
    """V2 profile columns detailed."""
    print_banner()
    df = load_dataset(args.input)
    mapping = map_linelist_columns(df)
    from linelist_cleaner.core.auditor import DataQualityAuditor
    from linelist_cleaner.core.logic_validator import LogicValidator
    tag_to_col = {v["mapped_tag"]: k for k, v in mapping.items() if v["mapped_tag"]}
    issues = LogicValidator().validate(df, tag_to_col)
    profiles = DataQualityAuditor.profile_columns(df, tag_to_col, issues)
    rows = []
    for col, p in profiles.items():
        rows.append([p.column_name, p.mapped_tag or "-", p.inferred_type, f"{p.missing_percentage}%", p.unique_count, str(p.top_values)[:40]])
    print(tabulate(rows, headers=["Colonne", "Tag", "Type", "% manquant", "Uniques", "Top valeurs"], tablefmt="grid"))

def cmd_sample(args):
    disease = args.type or "borno"
    out_file = args.output or f"{disease}_sample_linelist.csv"
    df = get_sample_dataset(disease)
    df.to_csv(out_file, index=False)
    print(f"[+] Linelist exemple [{disease.upper()}] V2 générée : {out_file} ({len(df)} lignes)")

def cmd_serve(args):
    import uvicorn
    from linelist_cleaner.web.app import app
    print_banner()
    print(f"[*] Serveur PratiSIG V2 démarré : http://{args.host}:{args.port} (docs: http://{args.host}:{args.port}/docs )")
    uvicorn.run(app, host=args.host, port=args.port)

def main():
    parser = argparse.ArgumentParser(description="Linelist Cleaner V2 & Géocodage Spatial (PratiSIG - Dakar, Sénégal)", prog="linelist-cleaner")
    parser.add_argument("--version", action="store_true", help="Afficher version V2")
    subparsers = parser.add_subparsers(dest="command", help="Commandes V2 disponibles")
    p_clean = subparsers.add_parser("clean", help="Nettoyer & géocoder (V2: + coords, phones, alertes)")
    p_clean.add_argument("input", help="Fichier d'entrée (.csv, .xlsx, .json, .tsv)")
    p_clean.add_argument("-o", "--output", help="Chemin sortie")
    p_clean.add_argument("--excel", action="store_true", help="Générer classeur Excel 6 onglets V2 (.xlsx)")
    p_clean.add_argument("--config", help="Fichier config JSON")
    p_clean.add_argument("--reference", help="Référentiel P-Code externe (csv/xlsx)")
    p_clean.add_argument("--preset", choices=["cholera","measles","ebola","covid19","covid","generic"], help="Preset maladie V2")
    p_clean.add_argument("--similarity", type=float, help="Seuil similarité fuzzy 50-100")
    p_clean.add_argument("--phone-code", help="Indicatif téléphonique par défaut (ex +221, +234)")
    p_clean.add_argument("--geojson", nargs="?", const="auto", help="Exporter GeoJSON (chemin ou auto)")
    p_clean.add_argument("--anonymize", action="store_true", help="Activer anonymisation RGPD")
    p_clean.add_argument("--dedup-action", choices=["flag", "keep_first", "keep_most_complete", "merge"], help="Action doublons")

    p_audit = subparsers.add_parser("audit", help="Auditer qualité V2")
    p_audit.add_argument("input", help="Fichier d'entrée"); p_audit.add_argument("-o", "--output", help="Rapport Excel")
    p_audit.add_argument("--preset", choices=["cholera","measles","ebola","covid19","generic"], help="Preset")

    p_validate = subparsers.add_parser("validate", help="Validation rapide sans nettoyage (V2)")
    p_validate.add_argument("input", help="Fichier d'entrée")

    p_geocode = subparsers.add_parser("geocode", help="Géocodage seul (V2)")
    p_geocode.add_argument("input", help="Fichier linelist"); p_geocode.add_argument("-r","--reference", help="Référentiel"); p_geocode.add_argument("-o","--output", help="Sortie"); p_geocode.add_argument("--similarity", help="Seuil"); p_geocode.add_argument("--geojson", nargs="?", const="auto", help="Export GeoJSON")

    p_inspect = subparsers.add_parser("inspect", help="Inspecter colonnes & tags")
    p_inspect.add_argument("input", help="Fichier")

    p_profile = subparsers.add_parser("profile", help="Profil détaillé des colonnes (V2)")
    p_profile.add_argument("input", help="Fichier")

    p_sample = subparsers.add_parser("sample", help="Générer jeu exemple")
    p_sample.add_argument("-t", "--type", choices=["borno", "cholera", "covid19", "ebola", "measles", "pcode_reference"], default="borno", help="Type")
    p_sample.add_argument("-o", "--output", help="Fichier sortie")

    p_serve = subparsers.add_parser("serve", help="Lancer app web interactive V2")
    p_serve.add_argument("--host", default="0.0.0.0", help="Adresse IP"); p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    if getattr(args, "version", False):
        print("Linelist Cleaner V2.0.0 — PratiSIG Consulting Services")
        return
    if args.command == "clean": cmd_clean(args)
    elif args.command == "audit": cmd_audit(args)
    elif args.command == "validate": cmd_validate(args)
    elif args.command == "geocode": cmd_geocode(args)
    elif args.command == "inspect": cmd_inspect(args)
    elif args.command == "profile": cmd_profile(args)
    elif args.command == "sample": cmd_sample(args)
    elif args.command == "serve": cmd_serve(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
