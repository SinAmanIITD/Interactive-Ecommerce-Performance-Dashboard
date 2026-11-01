-- Revenue / profit by state, ranked, with each state's share of total revenue.
WITH state_perf AS (
    SELECT
        c.state,
        c.region,
        ROUND(SUM(f.sales), 2)  AS revenue,
        ROUND(SUM(f.profit), 2) AS profit,
        COUNT(DISTINCT f.order_id) AS orders
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.state, c.region
)
SELECT
    state,
    region,
    revenue,
    profit,
    orders,
    ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2) AS pct_of_total_revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM state_perf
ORDER BY revenue DESC;
