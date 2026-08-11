"""
Command-Line Interface (CLI) for Linelist Cleaner.
PratiSIG Consulting Services - Dakar, Sénégal.
Auteur : Youssoupha MBODJI (pratisig.consulting@gmail.com)
"""

import sys
import os
import argparse
import json
from typing import Optional
import pandas as pd
from tabulate import tabulate

# Configuration sécurisée de l'encodage console
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
   La pratique des SIG, notre metier
-------------------------------------------------------------------
   Linelist Cleaner & Geocodage Spatial en Cascade (P-Codes OCHA)
   Auteur  : Youssoupha MBODJI
   Contact : pratisig.consulting@gmail.com
===================================================================
"""
    print(banner)


def cmd_clean(args):
    """Clean a linelist dataset and output results."""
    print_banner()
    print(f"[*] Lecture de la line list : {args.input}")
    
    config = CleaningConfig()
    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as f:
            config = CleaningConfig(**json.load(f))

    if args.anonymize:
        config.anonymize = True
    if args.dedup_action:
        config.dedup_action = args.dedup_action

    cleaner = LinelistCleaner(config=config)
    df_clean, report = cleaner.clean(args.input)

    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_cleaned.xlsx" if args.excel else f"{base}_cleaned.csv"

    if output_path.endswith((".xlsx", ".xls")) or args.excel:
        if not output_path.endswith(".xlsx"):
            output_path += ".xlsx"
        print(f"[*] Export du classeur Excel 3 onglets vers : {output_path}")
        cleaner.export_excel(df_clean, report, output_path)
    else:
        print(f"[*] Export du fichier nettoye vers : {output_path}")
        cleaner.export_csv(df_clean, output_path)

    qs = report.quality_scores_after
    print("\n" + "=" * 60)
    print(" SYNTHESE DU TRAITEMENT")
    print("=" * 60)
    print(f" Lignes : {report.original_shape[0]} brutes -> {report.cleaned_shape[0]} nettoyees ({report.cleaned_shape[1]} colonnes)")
    print(f" Score Qualite Global : {qs.overall_score}% [Grade: {qs.grade}]")
    if report.spatial_summary:
        sp = report.spatial_summary
        print(f" Taux de Geocodage (P-Codes) : {sp.geocoded_rate_pct}% ({sp.geocoded_count}/{sp.total_records})")
        print(f" Score Moyen de Similarite : {sp.average_match_score}%")
    print(f" Semaines Epi OMS Calculees : {report.epi_weeks_computed}")
    print(f" Anomalies Detectees : {len(report.validation_issues)}")
    print(f" Temps d'Execution : {report.execution_time_ms} ms")
    print("=" * 60)
    print("(c) PratiSIG Consulting Services - Dakar, Senegal")


def cmd_audit(args):
    """Audit dataset data quality and output report."""
    print_banner()
    print(f"[*] Audit qualite de la line list : {args.input}")
    
    cleaner = LinelistCleaner()
    df_clean, report = cleaner.clean(args.input)
    
    output_path = args.output or "linelist_quality_audit.xlsx"
    cleaner.export_excel(df_clean, report, output_path)
    print(f"[+] Rapport d'audit genere : {output_path}")

    qs = report.quality_scores_after
    score_table = [
        ["Score Qualite Global", f"{qs.overall_score}%", f"Grade {qs.grade}"],
        ["Completude", f"{qs.completeness_score}%", "Variables cles renseignees"],
        ["Sequence Chronologique", f"{qs.chronology_score}%", "Coherence temporelle des dates"],
        ["Validite & Conformite", f"{qs.validity_score}%", "Codes valides et plages plausibles"],
        ["Unicite", f"{qs.uniqueness_score}%", "Absence de doublons"],
    ]
    print("\n" + tabulate(score_table, headers=["Indicateur", "Score", "Description"], tablefmt="grid"))


def cmd_inspect(args):
    """Inspect columns, types, missingness, and detected epi tags in terminal."""
    print_banner()
    df = load_dataset(args.input)
    print(f"[*] Dimensions du jeu de donnees : {df.shape[0]} lignes x {df.shape[1]} colonnes\n")

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

    print(tabulate(
        table_data,
        headers=["Colonne", "Tag Epidemio / Spatial", "Categorie", "Completude", "Valeurs Uniques", "Exemple"],
        tablefmt="grid"
    ))


def cmd_sample(args):
    """Generate sample dataset."""
    disease = args.type or "borno"
    out_file = args.output or f"{disease}_sample_linelist.csv"
    df = get_sample_dataset(disease)
    df.to_csv(out_file, index=False)
    print(f"[+] Line list exemple [{disease.upper()}] generee : {out_file} ({len(df)} lignes)")


def cmd_serve(args):
    """Start interactive web dashboard."""
    import uvicorn
    from linelist_cleaner.web.app import app
    print_banner()
    print(f"[*] Demarrage du serveur web PratiSIG sur http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="Linelist Cleaner & Geocodage Spatial (PratiSIG Consulting Services - Dakar, Senegal)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    p_clean = subparsers.add_parser("clean", help="Nettoyer et geocoder une line list")
    p_clean.add_argument("input", help="Fichier d'entree (.csv, .xlsx, .json, .tsv)")
    p_clean.add_argument("-o", "--output", help="Chemin du fichier de sortie")
    p_clean.add_argument("--excel", action="store_true", help="Generer le classeur Excel 3 onglets (.xlsx)")
    p_clean.add_argument("--config", help="Fichier de configuration JSON")
    p_clean.add_argument("--anonymize", action="store_true", help="Activer l'anonymisation RGPD")
    p_clean.add_argument("--dedup-action", choices=["flag", "keep_first", "keep_most_complete", "merge"], help="Action sur les doublons")

    p_audit = subparsers.add_parser("audit", help="Auditer la qualite d'une line list")
    p_audit.add_argument("input", help="Fichier d'entree")
    p_audit.add_argument("-o", "--output", help="Chemin du rapport Excel")

    p_inspect = subparsers.add_parser("inspect", help="Inspecter les colonnes et tags dans le terminal")
    p_inspect.add_argument("input", help="Fichier d'entree")

    p_sample = subparsers.add_parser("sample", help="Generer un jeu de donnees d'exemple")
    p_sample.add_argument("-t", "--type", choices=["borno", "cholera", "covid19", "ebola", "measles", "pcode_reference"], default="borno", help="Type d'epidemie")
    p_sample.add_argument("-o", "--output", help="Fichier de sortie")

    p_serve = subparsers.add_parser("serve", help="Lancer l'application web interactive")
    p_serve.add_argument("--host", default="0.0.0.0", help="Adresse IP hote (defaut 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port TCP (defaut 8000)")

    args = parser.parse_args()

    if args.command == "clean":
        cmd_clean(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "sample":
        cmd_sample(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
