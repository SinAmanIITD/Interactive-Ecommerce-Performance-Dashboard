-- Monthly revenue / profit / order trend with month-over-month growth.
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        SUM(sales)                    AS revenue,
        SUM(profit)                   AS profit,
        COUNT(DISTINCT order_id)      AS orders
    FROM fact_orders
    GROUP BY 1
)
SELECT
    month,
    revenue,
    profit,
    orders,
    ROUND(profit / NULLIF(revenue, 0) * 100, 2) AS profit_margin_pct,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2
    ) AS mom_growth_pct
FROM monthly
ORDER BY month;
