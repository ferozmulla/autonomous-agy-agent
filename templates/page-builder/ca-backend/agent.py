"""Conversational Analytics — ADK Agent Definition.

This module defines the CA agent using Google ADK. The agent receives
natural-language questions, translates them to BigQuery SQL, executes
the query, and returns plain-English answers.

The Page Builder agent customizes this file at runtime by replacing
the {{CA_SYSTEM_PROMPT}} placeholder with a company-specific prompt.
"""

from __future__ import annotations

import os

from google.adk import Agent
from google.adk.tools import FunctionTool

from bigquery_tool import execute_bigquery_query, get_dataset_schema


# --- Configuration (set by the Page Builder agent) ---
PROJECT_ID = os.environ.get("GCP_PROJECT", "firstargolisproject-338816")
DATASET_NAME = os.environ.get("BQ_DATASET", "{{DATASET_NAME}}")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# System prompt — replaced by the Page Builder agent at build time.
CA_SYSTEM_PROMPT = """{{CA_SYSTEM_PROMPT}}"""


def query_bigquery(sql: str) -> dict:
    """Execute a SQL query against the company's BigQuery dataset.

    Use this tool to answer questions about the company's data. Write
    standard BigQuery SQL. Only query tables in the allowed dataset.

    Args:
        sql: A BigQuery Standard SQL query string.

    Returns:
        A dict with 'results' (list of row dicts) and 'row_count' (int),
        or an 'error' key if the query failed.
    """
    return execute_bigquery_query(
        sql=sql,
        project=PROJECT_ID,
        dataset=DATASET_NAME,
    )


def get_schema() -> dict:
    """Retrieve the schema of all tables in the dataset.

    Use this tool to understand what tables and columns are available
    before writing SQL queries. Each column includes its description,
    data type, and relationships.

    Returns:
        A dict with 'schema' (formatted schema string) and 'tables' (list).
    """
    schema_info = get_dataset_schema(
        project=PROJECT_ID,
        dataset=DATASET_NAME,
    )
    return {"schema": schema_info, "tables": schema_info.split("\n\n")}


# --- Build the ADK Agent ---
bq_query_tool = FunctionTool(func=query_bigquery)
schema_tool = FunctionTool(func=get_schema)

agent = Agent(
    model=GEMINI_MODEL,
    name="conversational_analytics_agent",
    description="Answers natural-language questions about company data using BigQuery.",
    instruction=CA_SYSTEM_PROMPT,
    tools=[bq_query_tool, schema_tool],
)
