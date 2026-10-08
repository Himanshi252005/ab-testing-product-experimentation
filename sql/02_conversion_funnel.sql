-- Intent-to-treat rates: denominator is every assigned user in each arm.
SELECT variant,
       COUNT(*) AS assigned_users,
       SUM(activated_7d) AS activated_users,
       ROUND(1.0 * SUM(activated_7d) / COUNT(*), 4) AS activation_rate_7d,
       SUM(paid_14d) AS paid_users,
       ROUND(1.0 * SUM(paid_14d) / COUNT(*), 4) AS paid_conversion_rate_14d,
       ROUND(SUM(revenue_usd_14d) / COUNT(*), 2) AS revenue_per_assigned_user_usd,
       ROUND(SUM(revenue_usd_14d) / NULLIF(SUM(paid_14d), 0), 2) AS revenue_per_payer_usd
FROM experiment_users
GROUP BY variant
ORDER BY variant;
