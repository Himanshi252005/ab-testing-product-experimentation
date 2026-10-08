-- Daily assignment cohorts and 14-day conversion; all cohorts are fully mature.
SELECT assigned_at AS assignment_cohort, variant,
       COUNT(*) AS users, SUM(paid_14d) AS paid_users,
       ROUND(1.0 * SUM(paid_14d) / COUNT(*), 4) AS conversion_rate_14d
FROM experiment_users
GROUP BY assigned_at, variant
ORDER BY assigned_at, variant;

-- Pre-treatment segmentation. Compare treatment and control within each level.
SELECT device, acquisition_channel, customer_tenure, variant,
       COUNT(*) AS users,
       ROUND(1.0 * SUM(paid_14d) / COUNT(*), 4) AS conversion_rate_14d,
       ROUND(SUM(revenue_usd_14d) / COUNT(*), 2) AS revenue_per_user_usd
FROM experiment_users
GROUP BY device, acquisition_channel, customer_tenure, variant
ORDER BY device, acquisition_channel, customer_tenure, variant;
