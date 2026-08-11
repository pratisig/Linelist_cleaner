"""
Command-Line Interface (CLI) for Linelist Cleaner.
"""

import sys
import os
import argparse
import json
from typing import Optional
import pandas as pd
from tabulate import tabulate

from linelist_cleaner.schemas.config import CleaningConfig
from linelist_cleaner.core.pipeline import LinelistCleaner, load_dataset
from linelist_cleaner.core.column_standardizer import map_linelist_columns
from linelist_cleaner.datasets import get_sample_dataset


def print_banner():
    banner = """
===================================================================
     _     _            _ _     _      ____ _                              
    | |   (_)_ __   ___| (_)___| |_   / ___| | ___  __ _ _ __   ___ _ __ 
    | |   | | '_ \ / _ \ | / __| __| | |   | |/ _ \/ _` | '_ \ / _ \ '__|
    | |___| | | | |  __/ | \__ \ |_  | |___| |  __/ (_| | | | |  __/ |   
    |_____|_|_| |_|\___|_|_|___/\__|  \____|_|\___|\__,_|_| |_|\___|_|   
    Epidemiological Data Cleaning, Validation & Profiling Engine
===================================================================
"""
    print(banner)


def cmd_clean(args):
    """Clean a linelist dataset and output results."""
    print_banner()
    print(f"[*] Reading linelist from: {args.input}")
    
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
        print(f"[*] Exporting multi-sheet audit Excel workbook to: {output_path}")
        cleaner.export_excel(df_clean, report, output_path)
    else:
        print(f"[*] Exporting cleaned dataset to: {output_path}")
        cleaner.export_csv(df_clean, output_path)

    # Print summary
    qs = report.quality_scores_after
    print("\n" + "=" * 60)
    print(f" CLEANING SUMMARY")
    print("=" * 60)
    print(f" Records: {report.original_shape[0]} rows -> {report.cleaned_shape[0]} rows ({report.cleaned_shape[1]} columns)")
    print(f" Data Quality Score: {qs.overall_score}% [Grade: {qs.grade}]")
    print(f"   • Completeness: {qs.completeness_score}%")
    print(f"   • Chronological Consistency: {qs.chronology_score}%")
    print(f"   • Format & Value Validity: {qs.validity_score}%")
    print(f"   • Uniqueness: {qs.uniqueness_score}%")
    print(f" Issues Detected: {len(report.validation_issues)} (Errors: {report.issues_by_severity.get('ERROR', 0)}, Warnings: {report.issues_by_severity.get('WARNING', 0)})")
    print(f" Duplicates Detected: {report.duplicates_detected} (Resolved: {report.duplicates_resolved})")
    print(f" Execution Time: {report.execution_time_ms} ms")
    print("=" * 60)


def cmd_audit(args):
    """Audit dataset data quality and output report."""
    print_banner()
    print(f"[*] Auditing linelist data quality: {args.input}")
    
    cleaner = LinelistCleaner()
    df_clean, report = cleaner.clean(args.input)
    
    output_path = args.output or "linelist_quality_audit.xlsx"
    cleaner.export_excel(df_clean, report, output_path)
    print(f"[+] Audit report generated successfully: {output_path}")

    # Display console scorecard
    qs = report.quality_scores_after
    score_table = [
        ["Overall Quality Score", f"{qs.overall_score}%", f"Grade {qs.grade}"],
        ["Completeness", f"{qs.completeness_score}%", "Non-missingness across key variables"],
        ["Chronological Sequence", f"{qs.chronology_score}%", "Timeline order & logic rules"],
        ["Validity & Conformity", f"{qs.validity_score}%", "Valid standard codes & plausible ranges"],
        ["Uniqueness", f"{qs.uniqueness_score}%", "Absence of duplicate records"],
    ]
    print("\n" + tabulate(score_table, headers=["Metric", "Score", "Description"], tablefmt="fancy_grid"))


def cmd_inspect(args):
    """Inspect columns, types, missingness, and detected epi tags in terminal."""
    print_banner()
    df = load_dataset(args.input)
    print(f"[*] Dataset Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    mapping = map_linelist_columns(df)
    table_data = []

    for col in df.columns:
        meta = mapping.get(col, {})
        tag = meta.get("mapped_tag") or "—"
        cat = meta.get("category") or "—"
        missing_count = int(df[col].isna().sum())
        missing_pct = round((missing_count / len(df)) * 100, 1) if len(df) > 0 else 0.0
        unique_cnt = int(df[col].nunique())
        sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "—"

        table_data.append([col, tag, cat, f"{100 - missing_pct:.1f}%", unique_cnt, sample_val[:25]])

    print(tabulate(
        table_data,
        headers=["Column", "Mapped Epi Tag", "Category", "Completeness", "Unique", "Sample Value"],
        tablefmt="fancy_grid"
    ))


def cmd_sample(args):
    """Generate sample dataset."""
    disease = args.type or "cholera"
    out_file = args.output or f"{disease}_sample_linelist.csv"
    df = get_sample_dataset(disease)
    df.to_csv(out_file, index=False)
    print(f"[+] Sample {disease.upper()} linelist created: {out_file} ({len(df)} rows)")


def cmd_serve(args):
    """Start interactive web dashboard."""
    import uvicorn
    from linelist_cleaner.web.app import app
    print_banner()
    print(f"[*] Starting Linelist Cleaner Web Dashboard on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="Linelist Cleaner: Epidemiological Data Cleaning, Validation, and Profiling Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Clean command
    p_clean = subparsers.add_parser("clean", help="Clean and standardize a linelist dataset")
    p_clean.add_argument("input", help="Input dataset path (.csv, .xlsx, .json, .tsv)")
    p_clean.add_argument("-o", "--output", help="Output path")
    p_clean.add_argument("--excel", action="store_true", help="Output as full Excel audit workbook (.xlsx)")
    p_clean.add_argument("--config", help="Path to JSON config file")
    p_clean.add_argument("--anonymize", action="store_true", help="Enable PII anonymization")
    p_clean.add_argument("--dedup-action", choices=["flag", "keep_first", "keep_most_complete", "merge"], help="Deduplication action")

    # Audit command
    p_audit = subparsers.add_parser("audit", help="Audit dataset quality without modifying records")
    p_audit.add_argument("input", help="Input dataset path")
    p_audit.add_argument("-o", "--output", help="Output path for Excel quality audit report")

    # Inspect command
    p_inspect = subparsers.add_parser("inspect", help="Quick terminal inspection of columns and mapped tags")
    p_inspect.add_argument("input", help="Input dataset path")

    # Sample command
    p_sample = subparsers.add_parser("sample", help="Generate realistic outbreak sample dataset")
    p_sample.add_argument("-t", "--type", choices=["cholera", "covid19", "ebola", "measles"], default="cholera", help="Disease type")
    p_sample.add_argument("-o", "--output", help="Output file path")

    # Serve command
    p_serve = subparsers.add_parser("serve", help="Launch interactive web application and API")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host address (default 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default 8000)")

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
