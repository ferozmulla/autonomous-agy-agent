"""BigQuery query execution and schema discovery tools for the CA agent.

Provides safe query execution (restricted to the allowed dataset) and
schema introspection via INFORMATION_SCHEMA.
"""

from __future__ import annotations

import re
from decimal import Decimal
from datetime import date, datetime, time
from typing import Any


def _serialize_row(row: dict) -> dict:
    """Convert non-JSON-serializable values in a BigQuery row dict.

    Converts Decimal → float, date/datetime/time → ISO string.

    Args:
        row: A dict of column_name → value from BigQuery.

    Returns:
        A dict with all values JSON-serializable.
    """
    out = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            out[key] = float(value)
        elif isinstance(value, (datetime, date, time)):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out

from google.cloud import bigquery


def execute_bigquery_query(
    sql: str,
    project: str,
    dataset: str,
) -> dict[str, Any]:
    """Execute a SQL query against BigQuery with dataset restriction.

    Validates that the query only references tables in the allowed dataset,
    executes it, and returns results as a list of dicts.

    Args:
        sql: The BigQuery Standard SQL query string.
        project: GCP project ID.
        dataset: Allowed BigQuery dataset name.

    Returns:
        A dict with:
        - ``results``: List of row dicts (max 100 rows).
        - ``row_count``: Total number of rows returned.
        - ``columns``: List of column names.
        Or a dict with ``error`` key if validation or execution fails.
    """
    # --- Safety check: only allow queries against the specified dataset ---
    if not _is_query_safe(sql, project, dataset):
        return {
            "error": (
                f"Query rejected: you may only query tables in "
                f"`{project}.{dataset}`. Modify your query to use "
                f"fully qualified table names like "
                f"`{project}.{dataset}.table_name`."
            )
        }

    # --- Reject any data modification statements ---
    sql_upper = sql.strip().upper()
    if any(
        sql_upper.startswith(kw)
        for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "MERGE")
    ):
        return {"error": "Query rejected: only SELECT statements are allowed."}

    try:
        client = bigquery.Client(project=project)
        query_job = client.query(sql)
        results = query_job.result()

        rows = []
        columns = [field.name for field in results.schema]

        for row in results:
            if len(rows) >= 100:
                break
            rows.append(_serialize_row(dict(row)))

        return {
            "results": rows,
            "row_count": results.total_rows,
            "columns": columns,
        }

    except Exception as exc:
        return {"error": f"Query execution failed: {exc!s:.500}"}


def _is_query_safe(sql: str, project: str, dataset: str) -> bool:
    """Check if a SQL query only references tables in the allowed dataset.

    Uses simple pattern matching — not a full SQL parser. Checks that any
    backtick-quoted table references point to the allowed project.dataset.

    Args:
        sql: The SQL query string.
        project: Allowed GCP project ID.
        dataset: Allowed BigQuery dataset name.

    Returns:
        True if the query appears safe, False otherwise.
    """
    # Remove single-line comments and strings to avoid false positives
    cleaned = re.sub(r"--[^\n]*", "", sql)
    cleaned = re.sub(r"'[^']*'", "''", cleaned)

    # Find all backtick-quoted table references
    table_refs = re.findall(r"`([^`]+)`", cleaned)

    for ref in table_refs:
        parts = ref.split(".")
        if len(parts) == 3:
            # Fully qualified: project.dataset.table
            ref_project, ref_dataset, _ = parts
            if ref_project != project or ref_dataset != dataset:
                return False
        elif len(parts) == 2:
            # dataset.table — must match our dataset
            ref_dataset, _ = parts
            if ref_dataset != dataset:
                return False
        # Single part (just a table name) is assumed safe — resolved in context

    return True


def get_dataset_schema(project: str, dataset: str) -> str:
    """Retrieve the full schema of a BigQuery dataset, formatted for LLM consumption.

    Queries INFORMATION_SCHEMA.COLUMN_FIELD_PATHS to get table names, column names,
    data types, and descriptions.

    Args:
        project: GCP project ID.
        dataset: BigQuery dataset name.

    Returns:
        A formatted string describing all tables and columns, suitable for
        including in an LLM prompt.
    """
    client = bigquery.Client(project=project)

    query = f"""
        SELECT
            table_name,
            column_name,
            data_type,
            description
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
        ORDER BY table_name, ordinal_position
    """

    try:
        rows = list(client.query(query).result())
    except Exception as exc:
        return f"Error retrieving schema: {exc}"

    if not rows:
        return f"No tables found in dataset {project}.{dataset}"

    # Group by table
    tables: dict[str, list] = {}
    for row in rows:
        table = row.table_name
        if table not in tables:
            tables[table] = []
        tables[table].append(row)

    # Format output
    output_parts = []
    for table_name, columns in tables.items():
        lines = [f"Table: `{project}.{dataset}.{table_name}`"]
        lines.append("Columns:")
        for col in columns:
            desc = col.description or "No description"
            lines.append(f"  - {col.column_name} ({col.data_type}): {desc}")
        output_parts.append("\n".join(lines))

    return "\n\n".join(output_parts)
