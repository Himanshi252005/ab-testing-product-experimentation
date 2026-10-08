-- SQLite compatible. Import data/experiment_users.csv as experiment_users.
-- One row per randomized user and no missing 14-day outcomes are required.
SELECT COUNT(*) AS assigned_users,
       COUNT(DISTINCT user_id) AS unique_users,
       SUM(CASE WHEN variant = 'control' THEN 1 ELSE 0 END) AS control_users,
       SUM(CASE WHEN variant = 'treatment' THEN 1 ELSE 0 END) AS treatment_users,
       SUM(CASE WHEN paid_14d IS NULL OR revenue_usd_14d IS NULL THEN 1 ELSE 0 END) AS missing_primary_outcomes
FROM experiment_users;

-- Assignment by day, useful for spotting allocation drift.
SELECT assigned_at, variant, COUNT(*) AS users
FROM experiment_users
GROUP BY assigned_at, variant
ORDER BY assigned_at, variant;
