#!/usr/bin/env python3
"""Preprocess gaf-eco-mapping.txt into koza-compatible TSV using DuckDB.

This script runs the SQL transformation to convert the GAF-ECO mapping file
into a format suitable for koza's map lookup system.
"""

import os
import sys
from pathlib import Path

import duckdb


def main():
    """Run the preprocessing SQL script with DuckDB."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    sql_file = script_dir / "preprocess_gaf_eco_map.sql"
    if not sql_file.exists():
        print(f"Error: SQL file not found: {sql_file}", file=sys.stderr)
        sys.exit(1)

    input_file = project_root / "data" / "gaf-eco-mapping.txt"
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        print("Run 'just download' first to download the source files.", file=sys.stderr)
        sys.exit(1)

    sql_content = sql_file.read_text()

    # Execute from project root so relative paths in SQL work
    original_dir = os.getcwd()
    try:
        os.chdir(project_root)
        con = duckdb.connect(":memory:")
        con.execute(sql_content)

        # Report results
        count = con.execute("SELECT COUNT(*) FROM gaf_eco_map").fetchone()[0]
        print(f"Preprocessed {count} GAF-ECO mappings to data/gaf-eco-map.tsv")

        con.close()
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()
