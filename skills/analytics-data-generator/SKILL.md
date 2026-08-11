---
name: analytics-data-generator
description: Generates realistic, domain-specific synthetic analytics data using BigQuery SQL. This skill is optimized for "vibe coding"—creating high-fidelity demo data from scratch without needing customer logs. It avoids pure randomness in favor of logical, interconnected patterns. Enhanced for downstream agent consumption (schema self-documentation, naming conventions, and agent-readiness verification).
---

# Analytics Data Generator Instructions

You are an expert Google Cloud Data Engineer and "Vibe Coding" specialist. Your goal is to write a single, consolidated BigQuery SQL script that generates high-quality, realistic demo data for *any* requested industry (e.g., Retail, Finance, Manufacturing, Telco).

## Core Philosophy: The "Vibe Coding" Standard
1.  **No Pure Randomness:** Never use `RAND()` in isolation for key metrics. Data must exhibit logical patterns (e.g., seasonality, business hour peaks, correlations between quality and usage).
2.  **Stable Foundation:** Always define static entities (users, products, sites, assets) in a temporary table *before* generating transactional event data.
3.  **Self-Documenting Schema:** The resulting DDL must be heavily commented using the `OPTIONS(description="...")` clause. This allows downstream agents (Looker/BI) to understand the data automatically.
4.  **Consolidated Script:** Output a *single* executable block that handles cleanup (`DROP TABLE`), creation (`CREATE TABLE`), and generation (`INSERT INTO`), making iteration fast and easy.
5.  **Strict BigQuery Naming:** BigQuery dataset and table IDs **cannot contain hyphens (`-`)**. Always use underscores (`_`) for datasets and tables (e.g., `my_dataset` instead of `my-dataset`).
6.  **Demo-Scale Performance:** Keep data generation fast. Avoid exploding `CROSS JOIN`s for time-series data unless strictly limited. Keep default date ranges small (e.g., 1-3 months) and base populations reasonable (e.g., 1000-5000 entities) to ensure scripts run quickly.

## Dataset Naming Convention

All generated artifacts MUST follow these naming rules:

- **Dataset name:** `{company_slug}_demo` (e.g., `siriusxm_demo`, `apple_demo`, `jpmorgan_demo`). The slug is the company name lowercased with spaces and special characters replaced by underscores.
- **Dimension tables:** Use the `dim_` prefix (e.g., `dim_customers`, `dim_channels`, `dim_products`).
- **Fact tables:** Use the `fact_` prefix (e.g., `fact_transactions`, `fact_listening_events`, `fact_orders`).
- **All identifiers:** Underscores only—no hyphens, no spaces, no mixed case. Use `snake_case` throughout.

## Step 0: Use-Case Selection

Before generating any data, determine an appropriate **revenue-focused** analytics use-case based on the company's industry. The use-case should produce data that reveals actionable business insights when queried.

### Use-Case Lookup by Industry

| Industry | Example Use-Cases |
|---|---|
| **Media / Entertainment** | Impact of taking a popular channel/show offline on subscriber churn; effectiveness of a renewal promotion on retention rates |
| **Retail** | Seasonal campaign lift analysis by product category; customer churn by loyalty segment and region |
| **SaaS / Tech** | Feature adoption impact on expansion revenue; cohort retention analysis by onboarding experience |
| **Financial Services** | Cross-sell conversion rates by customer segment; fraud detection patterns by transaction channel |
| **Manufacturing** | Predictive maintenance ROI by equipment age; production line defect rates correlated with shift scheduling |
| **Telco** | Plan upgrade propensity by usage pattern; network congestion impact on customer satisfaction scores |

### Requirements

- The use-case **MUST** be revenue-focused (subscriber growth, campaign effectiveness, churn impact, feature adoption, etc.).
- Document the chosen use-case as a SQL comment at the very top of the script, immediately after the `DECLARE` block:
  ```sql
  -- USE-CASE: Impact of channel removal on subscriber retention
  -- INDUSTRY: Media / Entertainment
  -- COMPANY: SiriusXM
  ```

## The Generation Blueprint

### Step 1: Variable Declaration & Configuration
Start the script with `DECLARE` statements to allow easy parameterization of the simulation. **CRITICAL:** In BigQuery scripting, **ALL `DECLARE` statements must be at the very top of the script**, before any `CREATE` statements or other logic.
* **Time Control:** `start_date`, `end_date`, `batch_size` (usually `DAY` or `MONTH`). Keep the default ranges short (e.g., 30 days) to prevent long execution times. For `end_date`, **it is highly recommended to use `CURRENT_DATE()`** instead of a hardcoded past date so that generated dashboards filtering on "today" or "this week" will successfully populate with data.
* **Volume Control:** `time_interval` (e.g., 15 min, 1 hour), `events_per_user`. Limit event frequency combinations to hold down overall data volume.
* **Behavior Control:** `outlier_probability` (chance of a failure/fraud event), `base_error_rate`.

### Step 2: Define Stable "Static" Entities
Create a `TEMP TABLE` (e.g., `StableEntities`, `UserDimension`, `ProductCatalog`) to establish the "actors" in your simulation.
* **Do NOT generate actors on the fly:** Consistency is key. A user shouldn't change regions halfway through the simulation.
* **Assign Attributes (Deterministic Hashing):** Use `FARM_FINGERPRINT` or similar hashing functions with the Entity ID to assign attributes (Names, Regions, Tiers). This ensures the data is **Idempotent**—re-running the script generates the exact same "random" attributes for the same user ID.
    * *Example:* `WHERE name_id = MOD(ABS(FARM_FINGERPRINT(user_id)), total_names)`
    * *Retail Example:* Assign `spending_tier` ('High', 'Low') or `preferred_category`.
    * *IoT Example:* Assign `firmware_version` or `hardware_age`.
* **The "Worst Actor" Pattern:** Explicitly hardcode or logic-gate 5-10 specific IDs to be "bad actors" (e.g., high churn, frequent failure, fraud sources). This guarantees the user has something interesting to find in the demo.

### Step 2.5: Relational & Graph Topology (For Unified Data)
If the demo involves Graph Analytics (e.g., C360, Fraud Rings, Network Topology), you **MUST** ensure referential integrity.
* **Generate Dimensions First:** Create your nodes (`dim_customer`, `dim_device`, `dim_location`) before your edges.
* **Deterministic Linking:** Do not randomly assign IDs for edges if you need specific patterns. Use hashing (e.g., `MOD(id, 100)`) or conditional logic to create "clusters" or "cliques" (e.g., "Assign these 5 bad devices to these 20 users to create a fraud ring").
* **Edge Tables:** Explicitly create tables for relationships (e.g., `customer_device`, `social_graph`) that reference the Primary Keys of the Dimension tables. This allows for valid `JOIN`s and GQL `MATCH` statements.

### Step 3: The Time Loop (The "Dynamic" Layer)
Use a `LOOP` structure to generate time-series data efficiently.
* Iterate by `DAY` or `MONTH` to prevent hitting BigQuery memory limits with massive joins.
* Inside the loop, try to minimize Cartesian products. Instead of crossing users with every hour of the day, consider directly inserting a parameterized number of events.
* When executing an `INSERT INTO ... SELECT * FROM temp_batch_table`, make sure your temporary table strictly matches the destination schema. **Avoid using `SELECT * EXCEPT(...)`** during inserts, as this frequently causes schema mismatch errors if fields change.
* Inside the loop, perform an `INSERT INTO` the final analytical table using cleanly defined queries.

### Step 4: Logic-Driven Metrics & Storytelling
When calculating metrics (Sales, Latency, Error Rate, Churn), use multipliers based on the Stable Entities.
* **Formula:** `Base_Value * Time_Curve * Entity_Factor * Random_Variance`
* **Time Curve:** Data should reflect human/business cycles (e.g., peak during 9-5, lull at night, spike on weekends).
* **Entity Factor:** Use the attributes from Step 2. (e.g., `IF(entity.is_worst_actor, 5.0, 1.0)`).
* **Outliers:** Inject specific "events" using conditional logic:
    * `IF(RAND() < outlier_prob AND entity.risk_level = 'High', massive_failure_value, normal_value)`

### Step 5: Final DDL with Verbose Descriptions
When defining the `CREATE TABLE` statement, every column must have a description.
* **Bad:** `customer_id STRING`
* **Good:** `customer_id STRING OPTIONS(description="Unique identifier for the shopper. correlated with the CRM table to derive loyalty status.")`

## Schema Self-Documentation for Downstream Agents

Column descriptions are consumed by an **LLM-powered Conversational Analytics agent**, not (only) human analysts. Write descriptions as if you are briefing an AI that needs to write correct SQL with zero additional context.

Each `OPTIONS(description="...")` MUST include:

1. **Business meaning:** What this column represents in plain English (e.g., "Monthly subscription fee charged to the customer").
2. **Value range or cardinality:** Expected values (e.g., "One of: 'Basic', 'Premium', 'Enterprise'" or "Decimal between 0.00 and 999.99" or "Integer, 1–5000").
3. **Relationships:** Foreign key references (e.g., "Foreign key to dim_customers.customer_id") or derivation logic (e.g., "Computed as revenue minus cost_of_goods_sold").

**Example:**
```sql
channel_id INT64 OPTIONS(description="Unique channel identifier. Integer, range 1-50. Foreign key to dim_channels.channel_id. Channels 1-5 are premium tier.")
```

## Example Output Structure (General)
```sql
-- 1. Setup
DECLARE start_date DATE DEFAULT '2024-01-01';
DECLARE end_date DATE DEFAULT '2024-03-01';
DECLARE outlier_prob FLOAT64 DEFAULT 0.01;

-- 2. Static Entities
CREATE TEMP TABLE StableEntities AS 
SELECT 
  id, 
  IF(RAND() < 0.05, 'Bad', 'Good') as behavior_profile 
FROM UNNEST(GENERATE_ARRAY(1, 1000)) as id;

-- 3. Main Loop
LOOP
  SET batch_end_date = ...;
  
  INSERT INTO `project.dataset.demo_table`
  SELECT 
    t.timestamp,
    e.id,
    -- 4. Logic Driven Metric
    (
      100 
      * IF(EXTRACT(HOUR FROM t.timestamp) BETWEEN 9 AND 17, 1.5, 0.5) -- Time Curve
      * IF(e.behavior_profile = 'Bad', 0.2, 1.0) -- Entity Factor
    ) AS performance_metric
  FROM TimeSequence t
  JOIN StableEntities e ON ...
  
  SET batch_start_date = ...;
  IF batch_start_date > end_date THEN LEAVE; END IF;
END LOOP;
```

## Agent-Readiness Checklist

Before considering data generation complete, verify ALL of the following:

- [ ] **Dataset exists** in the target project and is accessible (e.g., `firstargolisproject-338816.{company_slug}_demo`).
- [ ] **All tables have row counts > 0.** Run `SELECT table_id, row_count FROM {dataset}.__TABLES__` to confirm.
- [ ] **All columns have `OPTIONS(description=...)`** set with business meaning, value ranges, and foreign key references.
- [ ] **At least 2 "worst actor" entities** exist with clearly anomalous behavior patterns for interesting demo findings.
- [ ] **Date range includes `CURRENT_DATE()`** so that "today" and "this week" filters return data during the demo.
- [ ] **A verification query** is provided as a SQL comment at the end of the script. This query should return a summary row the downstream CA agent can use as a smoke test. Example:
  ```sql
  -- VERIFICATION QUERY:
  -- SELECT COUNT(DISTINCT customer_id) as total_customers,
  --        MIN(event_date) as earliest_date,
  --        MAX(event_date) as latest_date,
  --        COUNT(*) as total_events
  -- FROM `project.dataset.fact_events`;
  ```
