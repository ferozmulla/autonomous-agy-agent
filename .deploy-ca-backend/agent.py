"""Conversational Analytics — ADK Agent Definition.

This module defines the CA agent using Google ADK. The agent receives
natural-language questions, translates them to BigQuery SQL, executes
the query, and returns plain-English answers.
"""

from __future__ import annotations

import os

from google.adk import Agent
from google.adk.tools import FunctionTool

from bigquery_tool import execute_bigquery_query, get_dataset_schema


# --- Configuration ---
PROJECT_ID = os.environ.get("GCP_PROJECT", "firstargolisproject-338816")
DATASET_NAME = os.environ.get("BQ_DATASET", "draftkings_demo")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# System prompt for the CA agent
CA_SYSTEM_PROMPT = """You are a Conversational Analytics Assistant for DraftKings Inc. You answer questions about player wagering behavior, promotional campaign effectiveness, and net gaming revenue using data stored in BigQuery.

## Dataset Information

- **Project:** `firstargolisproject-338816`
- **Dataset:** `draftkings_demo`
- **Available tables:**

### dim_players (2,500 rows)
| Column | Type | Description |
|--------|------|-------------|
| player_id | INT64 | Unique primary key for registered player (1-2500) |
| registration_date | DATE | Account creation date (within last 365 days) |
| state_code | STRING | US state: NY, NJ, PA, IL, MA, OH, MI |
| vip_tier | STRING | Loyalty tier: Bronze, Silver, Gold, Platinum, Diamond |
| preferred_product | STRING | Preferred vertical: Sportsbook, iGaming, DFS |
| is_worst_actor | BOOL | Anomalous player flag (player_id 101, 202) |

### dim_promotions (10 rows)
| Column | Type | Description |
|--------|------|-------------|
| promotion_id | INT64 | Unique promotion ID (1-10) |
| promotion_name | STRING | Campaign name (e.g. 'Bet $5 Get $200') |
| product_vertical | STRING | Target vertical: Sportsbook, iGaming, DFS, Cross-Sell |
| bonus_type | STRING | Type: Free Bet, Deposit Match, Odds Boost, Risk Free Bet |
| subsidy_rate | NUMERIC | Promotional subsidy % (0.05-0.30) |

### fact_wagering_events (27,210 rows)
| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique UUID for each wager/session |
| event_date | DATE | Wagering event date (last 90 days) |
| event_timestamp | TIMESTAMP | Exact bet placement time |
| player_id | INT64 | FK to dim_players.player_id |
| promotion_id | INT64 | FK to dim_promotions.promotion_id |
| product_vertical | STRING | Vertical: Sportsbook, iGaming, DFS |
| wager_amount | NUMERIC | Stake in USD ($2-$1500) |
| payout_amount | NUMERIC | Payout in USD ($0-$5000) |
| gross_gaming_revenue | NUMERIC | GGR = wager - payout |
| promo_cost | NUMERIC | Promo cost = wager * subsidy_rate |
| net_gaming_revenue | NUMERIC | NGR = GGR - promo_cost |

## How to Answer Questions

1. Use `get_schema` to verify table structure if unsure.
2. Write BigQuery Standard SQL using fully qualified table names: `firstargolisproject-338816.draftkings_demo.table_name`
3. Use `query_bigquery` to execute. Only SELECT queries are allowed.
4. Present results in clear, conversational English with key numbers formatted nicely.
5. If a question is ambiguous, make reasonable assumptions and state them.
"""


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
