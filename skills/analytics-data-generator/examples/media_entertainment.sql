-- =============================================================================
-- EXAMPLE: Media / Entertainment — SiriusXM Subscriber Churn Analysis
-- =============================================================================
-- USE-CASE: Impact of channel removal on subscriber retention
-- INDUSTRY: Media / Entertainment
-- COMPANY: SiriusXM
--
-- This example demonstrates the complete Generation Blueprint output for a
-- subscriber churn use-case. It creates dimension tables for subscribers and
-- channels, plus a fact table for daily listening events with worst-actor
-- patterns baked in.
--
-- NOTE: This is a documentation reference, not meant to be executed directly.
--       The Data Generator agent produces scripts like this at runtime.
-- =============================================================================

-- Step 1: Variable Declaration & Configuration
DECLARE start_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
DECLARE end_date DATE DEFAULT CURRENT_DATE();
DECLARE outlier_prob FLOAT64 DEFAULT 0.03;
DECLARE current_batch_date DATE;
DECLARE project_id STRING DEFAULT 'firstargolisproject-338816';
DECLARE dataset_name STRING DEFAULT 'siriusxm_demo';

-- Create dataset (idempotent)
CREATE SCHEMA IF NOT EXISTS `firstargolisproject-338816.siriusxm_demo`
OPTIONS(location = 'us-central1');

-- Step 2: Define Stable "Static" Entities — Subscribers
DROP TABLE IF EXISTS `firstargolisproject-338816.siriusxm_demo.dim_subscribers`;
CREATE OR REPLACE TABLE `firstargolisproject-338816.siriusxm_demo.dim_subscribers` (
  subscriber_id INT64 OPTIONS(description="Unique subscriber identifier. Integer, range 1-3000."),
  subscriber_name STRING OPTIONS(description="Full name of the subscriber. Generated deterministically from subscriber_id."),
  plan_tier STRING OPTIONS(description="Subscription plan tier. One of: 'Basic', 'Premium', 'Platinum'. Determines access to premium channels."),
  signup_date DATE OPTIONS(description="Date the subscriber first signed up. Range: 2020-01-01 to 2025-12-31."),
  region STRING OPTIONS(description="Geographic region of the subscriber. One of: 'Northeast', 'Southeast', 'Midwest', 'Southwest', 'West'."),
  is_worst_actor BOOL OPTIONS(description="Flag indicating high churn-risk subscriber. TRUE for subscribers 42, 187, 501, 1337, 2999. These subscribers show declining engagement and high skip rates."),
  preferred_genre STRING OPTIONS(description="Subscriber's most-listened genre. One of: 'Pop', 'Rock', 'Country', 'Hip-Hop', 'Talk', 'News', 'Comedy'. Derived deterministically from subscriber_id."),
  monthly_fee FLOAT64 OPTIONS(description="Monthly subscription fee in USD. Basic: 8.99, Premium: 14.99, Platinum: 24.99.")
) AS
SELECT
  id AS subscriber_id,
  CONCAT(
    (SELECT name FROM UNNEST(['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Drew', 'Quinn', 'Avery', 'Blake']) AS name WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id AS STRING))), 10)),
    ' ',
    (SELECT name FROM UNNEST(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Martinez', 'Wilson']) AS name WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 7 AS STRING))), 10))
  ) AS subscriber_name,
  CASE MOD(ABS(FARM_FINGERPRINT(CAST(id AS STRING))), 10)
    WHEN 0 THEN 'Platinum'
    WHEN 1 THEN 'Platinum'
    WHEN 2 THEN 'Premium'
    WHEN 3 THEN 'Premium'
    WHEN 4 THEN 'Premium'
    ELSE 'Basic'
  END AS plan_tier,
  DATE_ADD('2020-01-01', INTERVAL MOD(ABS(FARM_FINGERPRINT(CAST(id * 3 AS STRING))), 2000) DAY) AS signup_date,
  (SELECT region FROM UNNEST(['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West']) AS region WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 13 AS STRING))), 5)) AS region,
  id IN (42, 187, 501, 1337, 2999) AS is_worst_actor,
  (SELECT genre FROM UNNEST(['Pop', 'Rock', 'Country', 'Hip-Hop', 'Talk', 'News', 'Comedy']) AS genre WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 17 AS STRING))), 7)) AS preferred_genre,
  CASE MOD(ABS(FARM_FINGERPRINT(CAST(id AS STRING))), 10)
    WHEN 0 THEN 24.99
    WHEN 1 THEN 24.99
    WHEN 2 THEN 14.99
    WHEN 3 THEN 14.99
    WHEN 4 THEN 14.99
    ELSE 8.99
  END AS monthly_fee
FROM UNNEST(GENERATE_ARRAY(1, 3000)) AS id;

-- Step 2 (cont.): Define Stable "Static" Entities — Channels
DROP TABLE IF EXISTS `firstargolisproject-338816.siriusxm_demo.dim_channels`;
CREATE OR REPLACE TABLE `firstargolisproject-338816.siriusxm_demo.dim_channels` (
  channel_id INT64 OPTIONS(description="Unique channel identifier. Integer, range 1-50. Channels 1-5 are premium tier."),
  channel_name STRING OPTIONS(description="Display name of the channel. E.g., 'Hits 1', 'The Highway', 'Howard 100'."),
  genre STRING OPTIONS(description="Genre category. One of: 'Pop', 'Rock', 'Country', 'Hip-Hop', 'Talk', 'News', 'Comedy'."),
  is_premium BOOL OPTIONS(description="Whether the channel requires Premium or Platinum tier. TRUE for channel_id 1-5."),
  popularity_rank INT64 OPTIONS(description="Popularity ranking. Integer 1-50, where 1 is most popular. Lower rank = more listeners.")
) AS
SELECT
  id AS channel_id,
  CONCAT('Channel_', CAST(id AS STRING)) AS channel_name,
  (SELECT genre FROM UNNEST(['Pop', 'Rock', 'Country', 'Hip-Hop', 'Talk', 'News', 'Comedy']) AS genre WITH OFFSET AS pos WHERE pos = MOD(ABS(FARM_FINGERPRINT(CAST(id * 23 AS STRING))), 7)) AS genre,
  id <= 5 AS is_premium,
  id AS popularity_rank
FROM UNNEST(GENERATE_ARRAY(1, 50)) AS id;

-- Step 3: Time Loop — Generate Daily Listening Events
DROP TABLE IF EXISTS `firstargolisproject-338816.siriusxm_demo.fact_listening_events`;
CREATE OR REPLACE TABLE `firstargolisproject-338816.siriusxm_demo.fact_listening_events` (
  event_date DATE OPTIONS(description="Date of the listening session. Range: 90 days ending at CURRENT_DATE()."),
  subscriber_id INT64 OPTIONS(description="Foreign key to dim_subscribers.subscriber_id. Integer, range 1-3000."),
  channel_id INT64 OPTIONS(description="Foreign key to dim_channels.channel_id. Integer, range 1-50."),
  listen_duration_minutes FLOAT64 OPTIONS(description="Total minutes listened in this session. Range: 1.0-180.0. Worst actors show declining duration over time."),
  skip_count INT64 OPTIONS(description="Number of track/segment skips during the session. Range: 0-50. Worst actors have 3-5x higher skip rates."),
  session_type STRING OPTIONS(description="Type of listening session. One of: 'car', 'home', 'mobile', 'web'. Distribution varies by time of day.")
);

SET current_batch_date = start_date;

LOOP
  INSERT INTO `firstargolisproject-338816.siriusxm_demo.fact_listening_events`
  SELECT
    current_batch_date AS event_date,
    s.subscriber_id,
    -- Step 4: Logic-Driven Metrics
    -- Channel selection weighted by genre preference
    MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(s.subscriber_id AS STRING), CAST(current_batch_date AS STRING)))), 50) + 1 AS channel_id,
    -- Listen duration: Base * Day-of-week curve * Worst-actor decay * Variance
    GREATEST(1.0,
      45.0
      * (CASE EXTRACT(DAYOFWEEK FROM current_batch_date)
           WHEN 1 THEN 1.4  -- Sunday: more listening
           WHEN 7 THEN 1.3  -- Saturday
           ELSE 1.0
         END)
      * (CASE WHEN s.is_worst_actor
           THEN GREATEST(0.1, 1.0 - (DATE_DIFF(current_batch_date, start_date, DAY) * 0.01))
           ELSE 1.0
         END)
      * (0.7 + RAND() * 0.6)
    ) AS listen_duration_minutes,
    -- Skip count: worst actors skip 3-5x more
    CAST(
      CASE WHEN s.is_worst_actor
        THEN 8.0 + RAND() * 15.0
        ELSE 1.0 + RAND() * 4.0
      END AS INT64
    ) AS skip_count,
    -- Session type: time-of-day simulation via random bucket
    (SELECT type FROM UNNEST(['car', 'home', 'mobile', 'web']) AS type
     WITH OFFSET AS pos
     WHERE pos = MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(s.subscriber_id AS STRING), CAST(current_batch_date AS STRING), 'session'))), 4)
    ) AS session_type
  FROM `firstargolisproject-338816.siriusxm_demo.dim_subscribers` s
  -- Sample ~30% of subscribers per day to keep volume reasonable
  WHERE MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(s.subscriber_id AS STRING), CAST(current_batch_date AS STRING)))), 3) = 0;

  SET current_batch_date = DATE_ADD(current_batch_date, INTERVAL 1 DAY);
  IF current_batch_date > end_date THEN LEAVE; END IF;
END LOOP;

-- =============================================================================
-- VERIFICATION QUERY:
-- SELECT
--   COUNT(DISTINCT subscriber_id) AS total_subscribers,
--   MIN(event_date) AS earliest_date,
--   MAX(event_date) AS latest_date,
--   COUNT(*) AS total_events,
--   COUNTIF(s.is_worst_actor) AS worst_actor_events
-- FROM `firstargolisproject-338816.siriusxm_demo.fact_listening_events` e
-- JOIN `firstargolisproject-338816.siriusxm_demo.dim_subscribers` s
--   ON e.subscriber_id = s.subscriber_id;
-- =============================================================================
