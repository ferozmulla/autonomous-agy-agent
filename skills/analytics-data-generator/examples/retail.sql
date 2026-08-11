-- =============================================================================
-- EXAMPLE: Retail — Seasonal Campaign Lift Analysis
-- =============================================================================
-- USE-CASE: Seasonal campaign lift analysis by product category
-- INDUSTRY: Retail
-- COMPANY: Target
--
-- This example demonstrates the complete Generation Blueprint output for a
-- retail campaign effectiveness use-case. It creates dimension tables for
-- customers and products, plus a fact table for daily transactions with
-- worst-actor patterns (underperforming stores/regions).
--
-- NOTE: This is a documentation reference, not meant to be executed directly.
--       The Data Generator agent produces scripts like this at runtime.
-- =============================================================================

-- Step 1: Variable Declaration & Configuration
DECLARE start_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
DECLARE end_date DATE DEFAULT CURRENT_DATE();
DECLARE outlier_prob FLOAT64 DEFAULT 0.02;
DECLARE current_batch_date DATE;

-- Create dataset (idempotent)
CREATE SCHEMA IF NOT EXISTS `firstargolisproject-338816.target_demo`
OPTIONS(location = 'us-central1');

-- Step 2: Define Stable Entities — Customers
DROP TABLE IF EXISTS `firstargolisproject-338816.target_demo.dim_customers`;
CREATE OR REPLACE TABLE `firstargolisproject-338816.target_demo.dim_customers` (
  customer_id INT64 OPTIONS(description="Unique customer identifier. Integer, range 1-5000."),
  customer_name STRING OPTIONS(description="Full name of the customer. Generated deterministically from customer_id."),
  loyalty_segment STRING OPTIONS(description="Customer loyalty tier. One of: 'Red', 'Silver', 'Gold', 'Platinum'. Determines discount eligibility and promotion targeting."),
  region STRING OPTIONS(description="Customer home region. One of: 'Northeast', 'Southeast', 'Midwest', 'Southwest', 'Pacific'. Influences product preferences and seasonal patterns."),
  signup_year INT64 OPTIONS(description="Year the customer joined the loyalty program. Range: 2018-2025."),
  is_worst_actor BOOL OPTIONS(description="Flag indicating underperforming customer segment. TRUE for customers 77, 234, 888, 1500, 3333. These customers show declining purchase frequency and high return rates."),
  preferred_category STRING OPTIONS(description="Customer's most-purchased product category. One of: 'Grocery', 'Apparel', 'Electronics', 'Home', 'Beauty', 'Toys'. Derived deterministically from customer_id."),
  avg_basket_size FLOAT64 OPTIONS(description="Historical average transaction value in USD. Range: 15.00-250.00. Gold/Platinum tiers tend toward higher values.")
) AS
SELECT
  id AS customer_id,
  CONCAT(
    (SELECT name FROM UNNEST(['Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'James', 'Sophia', 'William', 'Isabella', 'Oliver']) AS name WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id AS STRING))), 10)),
    ' ',
    (SELECT name FROM UNNEST(['Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Moore', 'Allen', 'Young']) AS name WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 11 AS STRING))), 10))
  ) AS customer_name,
  CASE MOD(ABS(FARM_FINGERPRINT(CAST(id * 2 AS STRING))), 10)
    WHEN 0 THEN 'Platinum'
    WHEN 1 THEN 'Gold'
    WHEN 2 THEN 'Gold'
    WHEN 3 THEN 'Silver'
    WHEN 4 THEN 'Silver'
    WHEN 5 THEN 'Silver'
    ELSE 'Red'
  END AS loyalty_segment,
  (SELECT region FROM UNNEST(['Northeast', 'Southeast', 'Midwest', 'Southwest', 'Pacific']) AS region WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 13 AS STRING))), 5)) AS region,
  2018 + MOD(ABS(FARM_FINGERPRINT(CAST(id * 19 AS STRING))), 8) AS signup_year,
  id IN (77, 234, 888, 1500, 3333) AS is_worst_actor,
  (SELECT cat FROM UNNEST(['Grocery', 'Apparel', 'Electronics', 'Home', 'Beauty', 'Toys']) AS cat WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 23 AS STRING))), 6)) AS preferred_category,
  ROUND(
    CASE MOD(ABS(FARM_FINGERPRINT(CAST(id * 2 AS STRING))), 10)
      WHEN 0 THEN 120.0 + RAND() * 130.0  -- Platinum: 120-250
      WHEN 1 THEN 80.0 + RAND() * 100.0   -- Gold: 80-180
      WHEN 2 THEN 80.0 + RAND() * 100.0   -- Gold
      ELSE 15.0 + RAND() * 85.0           -- Silver/Red: 15-100
    END, 2
  ) AS avg_basket_size
FROM UNNEST(GENERATE_ARRAY(1, 5000)) AS id;

-- Step 2 (cont.): Define Stable Entities — Products
DROP TABLE IF EXISTS `firstargolisproject-338816.target_demo.dim_products`;
CREATE OR REPLACE TABLE `firstargolisproject-338816.target_demo.dim_products` (
  product_id INT64 OPTIONS(description="Unique product identifier. Integer, range 1-200."),
  product_name STRING OPTIONS(description="Display name of the product. E.g., 'Organic Avocados', 'Wireless Earbuds'."),
  category STRING OPTIONS(description="Product category. One of: 'Grocery', 'Apparel', 'Electronics', 'Home', 'Beauty', 'Toys'."),
  unit_price FLOAT64 OPTIONS(description="Retail price per unit in USD. Range: 1.99-499.99. Electronics tend toward higher prices."),
  is_seasonal BOOL OPTIONS(description="Whether the product has seasonal demand spikes. TRUE for ~30% of products."),
  campaign_eligible BOOL OPTIONS(description="Whether the product is included in the current promotional campaign. TRUE for ~40% of products.")
) AS
SELECT
  id AS product_id,
  CONCAT('Product_', CAST(id AS STRING)) AS product_name,
  (SELECT cat FROM UNNEST(['Grocery', 'Apparel', 'Electronics', 'Home', 'Beauty', 'Toys']) AS cat WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 7 AS STRING))), 6)) AS category,
  ROUND(
    CASE MOD(ABS(FARM_FINGERPRINT(CAST(id * 7 AS STRING))), 6)
      WHEN 0 THEN 1.99 + RAND() * 18.0    -- Grocery: 1.99-19.99
      WHEN 1 THEN 9.99 + RAND() * 90.0    -- Apparel: 9.99-99.99
      WHEN 2 THEN 19.99 + RAND() * 480.0  -- Electronics: 19.99-499.99
      WHEN 3 THEN 4.99 + RAND() * 195.0   -- Home: 4.99-199.99
      WHEN 4 THEN 3.99 + RAND() * 76.0    -- Beauty: 3.99-79.99
      ELSE 5.99 + RAND() * 94.0           -- Toys: 5.99-99.99
    END, 2
  ) AS unit_price,
  MOD(ABS(FARM_FINGERPRINT(CAST(id * 31 AS STRING))), 10) < 3 AS is_seasonal,
  MOD(ABS(FARM_FINGERPRINT(CAST(id * 37 AS STRING))), 10) < 4 AS campaign_eligible
FROM UNNEST(GENERATE_ARRAY(1, 200)) AS id;

-- Step 3: Time Loop — Generate Daily Transactions
DROP TABLE IF EXISTS `firstargolisproject-338816.target_demo.fact_transactions`;
CREATE OR REPLACE TABLE `firstargolisproject-338816.target_demo.fact_transactions` (
  transaction_date DATE OPTIONS(description="Date of the transaction. Range: 90 days ending at CURRENT_DATE()."),
  customer_id INT64 OPTIONS(description="Foreign key to dim_customers.customer_id. Integer, range 1-5000."),
  product_id INT64 OPTIONS(description="Foreign key to dim_products.product_id. Integer, range 1-200."),
  quantity INT64 OPTIONS(description="Number of units purchased. Range: 1-10. Campaign items tend toward higher quantities."),
  total_amount FLOAT64 OPTIONS(description="Total transaction value in USD. Computed as unit_price * quantity * (1 - discount). Range: 1.99-4999.90."),
  discount_pct FLOAT64 OPTIONS(description="Discount percentage applied. Range: 0.0-0.30. Campaign items get 10-30% off for Gold/Platinum customers."),
  channel STRING OPTIONS(description="Purchase channel. One of: 'in-store', 'online', 'app'. Distribution: ~50% in-store, ~30% online, ~20% app."),
  is_return BOOL OPTIONS(description="Whether this transaction was a return. TRUE for ~5% of transactions. Worst-actor customers have ~20% return rate.")
);

SET current_batch_date = start_date;

LOOP
  INSERT INTO `firstargolisproject-338816.target_demo.fact_transactions`
  SELECT
    current_batch_date AS transaction_date,
    c.customer_id,
    -- Product selection weighted by customer preference
    MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(c.customer_id AS STRING), CAST(current_batch_date AS STRING)))), 200) + 1 AS product_id,
    -- Quantity: campaign items get higher quantities
    CAST(1 + RAND() * 4 AS INT64) AS quantity,
    -- Total amount placeholder (would be computed with product price in production)
    ROUND(c.avg_basket_size * (0.6 + RAND() * 0.8), 2) AS total_amount,
    -- Discount: loyalty tier and campaign eligibility
    CASE
      WHEN c.loyalty_segment IN ('Gold', 'Platinum') THEN ROUND(0.10 + RAND() * 0.20, 2)
      WHEN c.loyalty_segment = 'Silver' THEN ROUND(0.05 + RAND() * 0.10, 2)
      ELSE 0.0
    END AS discount_pct,
    -- Channel distribution
    (SELECT ch FROM UNNEST(['in-store', 'in-store', 'in-store', 'in-store', 'in-store',
                            'online', 'online', 'online',
                            'app', 'app']) AS ch
     WITH OFFSET AS pos
     WHERE pos = MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(c.customer_id AS STRING), CAST(current_batch_date AS STRING), 'ch'))), 10)
    ) AS channel,
    -- Returns: worst actors have ~20% return rate vs ~5% baseline
    CASE
      WHEN c.is_worst_actor THEN RAND() < 0.20
      ELSE RAND() < 0.05
    END AS is_return
  FROM `firstargolisproject-338816.target_demo.dim_customers` c
  -- Sample ~20% of customers per day
  WHERE MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(c.customer_id AS STRING), CAST(current_batch_date AS STRING)))), 5) = 0;

  SET current_batch_date = DATE_ADD(current_batch_date, INTERVAL 1 DAY);
  IF current_batch_date > end_date THEN LEAVE; END IF;
END LOOP;

-- =============================================================================
-- VERIFICATION QUERY:
-- SELECT
--   COUNT(DISTINCT customer_id) AS total_customers,
--   MIN(transaction_date) AS earliest_date,
--   MAX(transaction_date) AS latest_date,
--   COUNT(*) AS total_transactions,
--   ROUND(SUM(total_amount), 2) AS total_revenue,
--   COUNTIF(is_return) AS total_returns,
--   ROUND(COUNTIF(is_return) / COUNT(*) * 100, 1) AS return_rate_pct
-- FROM `firstargolisproject-338816.target_demo.fact_transactions`;
-- =============================================================================
