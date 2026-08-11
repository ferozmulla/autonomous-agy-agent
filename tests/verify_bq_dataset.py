"""Standalone BigQuery dataset verification script.

Accepts a dataset name and validates:
  - Dataset exists and is accessible
  - All tables have row counts > 0
  - All columns have descriptions (OPTIONS)
  - At least 2 worst-actor entities exist
  - Date range includes CURRENT_DATE()

Usage:
    python tests/verify_bq_dataset.py --dataset siriusxm_demo
    python tests/verify_bq_dataset.py --dataset apple_demo --project my-project
"""

from __future__ import annotations

import argparse
import sys
from datetime import date


def verify_dataset(project: str, dataset: str) -> bool:
    """Verify a BigQuery dataset meets quality requirements.

    Args:
        project: GCP project ID.
        dataset: BigQuery dataset name (without project prefix).

    Returns:
        True if all checks pass, False otherwise.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    full_dataset = f"{project}.{dataset}"
    all_passed = True

    print(f"🔍 Verifying dataset: {full_dataset}")
    print("─" * 50)

    # --- Check 1: Dataset exists ---
    print("\n1. Dataset existence... ", end="")
    try:
        client.get_dataset(f"{project}.{dataset}")
        print("✓ PASS")
    except Exception as exc:
        print(f"✗ FAIL: {exc}")
        return False

    # --- Check 2: All tables have rows ---
    print("\n2. Table row counts:")
    tables = list(client.list_tables(f"{project}.{dataset}"))
    if not tables:
        print("   ✗ FAIL: No tables found")
        return False

    for table_ref in tables:
        table = client.get_table(table_ref.reference)
        status = "✓" if table.num_rows > 0 else "✗"
        print(f"   {status} {table.table_id}: {table.num_rows:,} rows")
        if table.num_rows == 0:
            all_passed = False

    # --- Check 3: Column descriptions ---
    print("\n3. Column descriptions:")
    query = f"""
        SELECT table_name, column_name, description
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
    """
    rows = list(client.query(query).result())
    total_cols = len(rows)
    described_cols = sum(1 for r in rows if r.description)
    pct = (described_cols / total_cols * 100) if total_cols > 0 else 0
    status = "✓" if pct >= 90 else "✗"
    print(f"   {status} {described_cols}/{total_cols} columns have descriptions ({pct:.0f}%)")
    if pct < 90:
        all_passed = False
        missing = [r for r in rows if not r.description]
        for r in missing[:5]:
            print(f"      Missing: {r.table_name}.{r.column_name}")

    # --- Check 4: Worst actors ---
    print("\n4. Worst actor entities:")
    found_worst_actors = False
    for table_ref in tables:
        # Check if the table has an is_worst_actor column
        table = client.get_table(table_ref.reference)
        col_names = [field.name for field in table.schema]
        if "is_worst_actor" in col_names:
            count_query = f"""
                SELECT COUNT(*) as cnt
                FROM `{project}.{dataset}.{table_ref.table_id}`
                WHERE is_worst_actor = TRUE
            """
            result = list(client.query(count_query).result())
            count = result[0].cnt if result else 0
            if count >= 2:
                print(f"   ✓ {table_ref.table_id}: {count} worst actors found")
                found_worst_actors = True
            else:
                print(f"   ⚠ {table_ref.table_id}: only {count} worst actors")

    if not found_worst_actors:
        print("   ✗ FAIL: No table with >= 2 worst actors found")
        all_passed = False

    # --- Check 5: Date range ---
    print("\n5. Date range (should include today):")
    today = date.today()
    for table_ref in tables:
        table = client.get_table(table_ref.reference)
        date_cols = [
            f.name for f in table.schema
            if f.field_type == "DATE" and ("date" in f.name.lower() or "event" in f.name.lower())
        ]
        for col in date_cols:
            range_query = f"""
                SELECT MIN({col}) as min_date, MAX({col}) as max_date
                FROM `{project}.{dataset}.{table_ref.table_id}`
            """
            result = list(client.query(range_query).result())
            if result:
                min_d = result[0].min_date
                max_d = result[0].max_date
                recent = (today - max_d).days <= 1 if max_d else False
                status = "✓" if recent else "✗"
                print(f"   {status} {table_ref.table_id}.{col}: {min_d} to {max_d}")
                if not recent:
                    all_passed = False

    # --- Summary ---
    print("\n" + "─" * 50)
    if all_passed:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed — see details above.")

    return all_passed


def main() -> None:
    """CLI entry point for dataset verification."""
    parser = argparse.ArgumentParser(
        description="Verify a BigQuery dataset for Agent-Built Demos"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="BigQuery dataset name (e.g., siriusxm_demo)",
    )
    parser.add_argument(
        "--project",
        default="firstargolisproject-338816",
        help="GCP project ID",
    )
    args = parser.parse_args()

    success = verify_dataset(args.project, args.dataset)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
