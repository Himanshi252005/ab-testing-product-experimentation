SELECT variant, COUNT(*) AS assigned_users,
       SUM(support_ticket_14d) AS support_tickets,
       ROUND(1.0 * SUM(support_ticket_14d) / COUNT(*), 4) AS support_ticket_rate,
       SUM(app_crash_14d) AS users_with_crash,
       ROUND(1.0 * SUM(app_crash_14d) / COUNT(*), 4) AS app_crash_rate
FROM experiment_users
GROUP BY variant
ORDER BY variant;
