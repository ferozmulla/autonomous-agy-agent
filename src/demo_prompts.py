"""Demo prompt generator for Conversational Analytics.

Queries the BigQuery dataset's schema (INFORMATION_SCHEMA.COLUMNS) after data
generation and produces 3 natural-language demo prompts guaranteed to work
against the actual tables and columns.
"""

from __future__ import annotations

import re
from typing import Any


def generate_demo_prompts(
    project: str,
    dataset: str,
    company: str,
) -> list[str]:
    """Generate 3 demo prompts based on the actual BigQuery dataset schema.

    Queries INFORMATION_SCHEMA.COLUMNS to discover tables and columns,
    then constructs prompts that are guaranteed to be answerable against
    the real data.

    Args:
        project: GCP project ID.
        dataset: BigQuery dataset name (e.g., "exxon_demo").
        company: Human-readable company name.

    Returns:
        A list of 3 prompt strings, or an empty list on failure.
    """
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=project)

        # Get all tables and their columns
        query = f"""
        SELECT table_name, column_name, data_type
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        ORDER BY table_name, ordinal_position
        """
        rows = list(client.query(query, location="us-central1").result())

        if not rows:
            return []

        # Organize schema: {table_name: [{column, type, desc}, ...]}
        schema: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            table = row.table_name
            if table not in schema:
                schema[table] = []
            schema[table].append({
                "column": row.column_name,
                "type": row.data_type,
                "desc": "",
            })

        return _build_prompts(schema, company)

    except Exception:
        return []


def _build_prompts(
    schema: dict[str, list[dict[str, str]]],
    company: str,
) -> list[str]:
    """Build 3 demo prompts from a parsed schema.

    Strategy:
    1. Prompt 1: Aggregation on a dimension table (counts/breakdowns)
    2. Prompt 2: Join between dim + fact for a revenue/metric analysis
    3. Prompt 3: Find "worst actors" or anomalies

    Args:
        schema: Dict of table_name -> list of column dicts.
        company: Human-readable company name.

    Returns:
        A list of 3 prompt strings.
    """
    dim_tables = {t: cols for t, cols in schema.items() if t.startswith("dim_")}
    fact_tables = {t: cols for t, cols in schema.items() if t.startswith("fact_")}

    prompts: list[str] = []

    # --- Prompt 1: Breakdown by a categorical dimension ---
    if dim_tables:
        # Pick the first dim table and find a good categorical column
        dim_name = list(dim_tables.keys())[0]
        dim_cols = dim_tables[dim_name]
        cat_col = _find_categorical_column(dim_cols)
        entity = _table_to_entity(dim_name)

        if cat_col:
            prompts.append(
                f"How many {entity} are in each {_col_to_label(cat_col)}? "
                f"Show a breakdown."
            )
        else:
            prompts.append(f"How many total {entity} are in the dataset?")

    # --- Prompt 2: Revenue/metric analysis joining dim + fact ---
    if fact_tables and dim_tables:
        fact_name = list(fact_tables.keys())[0]
        fact_cols = fact_tables[fact_name]
        dim_name = list(dim_tables.keys())[0]
        dim_cols = dim_tables[dim_name]

        metric_col = _find_metric_column(fact_cols)
        cat_col = _find_categorical_column(dim_cols)

        if metric_col and cat_col:
            prompts.append(
                f"Which {_col_to_label(cat_col)} generates the highest "
                f"total {_col_to_label(metric_col)}?"
            )
        elif metric_col:
            prompts.append(
                f"What is the total {_col_to_label(metric_col)} over the "
                f"last 30 days?"
            )
        else:
            prompts.append(
                f"Show the top 10 records from the {_table_to_label(fact_name)} table."
            )
    elif fact_tables:
        fact_name = list(fact_tables.keys())[0]
        prompts.append(
            f"How many events are recorded in {_table_to_label(fact_name)}?"
        )

    # --- Prompt 3: Worst actors / anomalies ---
    worst_actor_col = None
    worst_actor_table = None
    for tname, cols in schema.items():
        for col in cols:
            if "worst_actor" in col["column"] or "is_worst" in col["column"]:
                worst_actor_col = col["column"]
                worst_actor_table = tname
                break
        if worst_actor_col:
            break

    if worst_actor_col and fact_tables:
        fact_name = list(fact_tables.keys())[0]
        metric_col = _find_metric_column(fact_tables[fact_name])
        entity = _table_to_entity(worst_actor_table or "")
        if metric_col:
            prompts.append(
                f"Identify {entity} flagged as worst actors and compare their "
                f"{_col_to_label(metric_col)} against the rest."
            )
        else:
            prompts.append(
                f"Identify {entity} flagged as worst actors and analyze their behavior."
            )
    else:
        # Fallback: time-series prompt
        if fact_tables:
            fact_name = list(fact_tables.keys())[0]
            metric_col = _find_metric_column(fact_tables[fact_name])
            if metric_col:
                prompts.append(
                    f"Show the daily trend of {_col_to_label(metric_col)} "
                    f"over the last 2 weeks."
                )
            else:
                prompts.append(
                    f"Show the daily event count for the last 2 weeks."
                )

    # Ensure we always return exactly 3
    while len(prompts) < 3:
        prompts.append(f"What insights can you find in the {company} dataset?")

    return prompts[:3]


def _find_categorical_column(cols: list[dict[str, str]]) -> str | None:
    """Find a good categorical column for grouping.

    Prefers columns with names like 'tier', 'segment', 'category', 'type',
    'status', 'region'. Skips ID and date columns.
    """
    preferred = ["tier", "segment", "category", "type", "status", "region", "level", "plan"]
    for keyword in preferred:
        for col in cols:
            name = col["column"].lower()
            if keyword in name and "_id" not in name:
                return col["column"]
    # Fallback: any STRING column that's not an ID or date
    for col in cols:
        name = col["column"].lower()
        if col["type"] == "STRING" and "_id" not in name and "date" not in name and "name" not in name:
            return col["column"]
    return None


def _find_metric_column(cols: list[dict[str, str]]) -> str | None:
    """Find a numeric metric column suitable for SUM/AVG aggregations.

    Prefers revenue, amount, cost, margin columns.
    """
    preferred = ["revenue", "amount", "cost", "margin", "profit", "spend", "value", "price"]
    for keyword in preferred:
        for col in cols:
            name = col["column"].lower()
            if keyword in name and col["type"] in ("FLOAT64", "NUMERIC", "INT64", "BIGNUMERIC"):
                return col["column"]
    return None


def _table_to_entity(table_name: str) -> str:
    """Convert table name like 'dim_players' to 'players'."""
    name = re.sub(r"^(dim_|fact_)", "", table_name)
    return name.replace("_", " ")


def _table_to_label(table_name: str) -> str:
    """Convert table name to a readable label."""
    name = re.sub(r"^(dim_|fact_)", "", table_name)
    return name.replace("_", " ").title()


def _col_to_label(column_name: str) -> str:
    """Convert column_name to a readable label (e.g., 'vip_tier' -> 'VIP tier')."""
    label = column_name.replace("_", " ")
    # Capitalize common abbreviations
    for abbr in ["vip", "roi", "ngr", "ggr", "eps", "ltv", "arpu"]:
        label = re.sub(rf"\b{abbr}\b", abbr.upper(), label, flags=re.IGNORECASE)
    return label
