-- RFM (Recency, Frequency, Monetary) customer segmentation, entirely in SQL.
-- "Today" is anchored to one day after the last order in the dataset
-- (the Superstore data ends in 2017; using the real current date would make
-- every customer's recency score meaningless since the data is years old).

WITH anchor AS (
    SELECT DATE(MAX(order_date), '+1 day') AS today FROM fact_orders
),
rfm_raw AS (
    SELECT
        f.customer_id,
        MAX(f.order_date)                      AS last_order_date,
        CAST(JULIANDAY((SELECT today FROM anchor)) - JULIANDAY(MAX(f.order_date)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT f.order_id)              AS frequency,
        ROUND(SUM(f.sales), 2)                  AS monetary
    FROM fact_orders f
    GROUP BY f.customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        -- Quintiles (1-5). Recency: LOWER days-since-last-order = BETTER,
        -- so order ASC and the most recent customers land in bucket 5.
        NTILE(5) OVER (ORDER BY recency_days DESC) AS R,
        NTILE(5) OVER (ORDER BY frequency ASC)     AS F,
        NTILE(5) OVER (ORDER BY monetary ASC)      AS M
    FROM rfm_raw
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    R, F, M,
    (R + F + M) AS rfm_score,
    CASE
        WHEN R >= 4 AND F >= 4 AND M >= 4 THEN 'Champions'
        WHEN R >= 3 AND F >= 3 AND M >= 3 THEN 'Loyal Customers'
        WHEN R >= 4 AND F <= 2                THEN 'New Customers'
        WHEN R <= 2 AND F >= 3                THEN 'At Risk'
        ELSE 'Others'
    END AS segment
FROM rfm_scores
ORDER BY rfm_score DESC;
