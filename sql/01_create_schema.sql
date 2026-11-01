-- Star schema for the Superstore e-commerce dataset.
-- One fact table (transactional grain = one row per order line item)
-- and three dimension tables, consistent with Kimball-style star schema design:
-- facts are additive numeric measures, dimensions are the "who/what/where/when"
-- you slice those measures by.

DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_customers (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT,
    segment         TEXT,      -- Consumer / Corporate / Home Office
    city            TEXT,
    state           TEXT,
    region          TEXT,
    country         TEXT
);

CREATE TABLE dim_products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT,
    category        TEXT,
    sub_category    TEXT
);

CREATE TABLE dim_date (
    date_key        TEXT PRIMARY KEY,   -- ISO 'YYYY-MM-DD'
    year            INTEGER,
    quarter         INTEGER,
    month           INTEGER,
    month_name      TEXT,
    week            INTEGER,
    day_of_week     TEXT
);

CREATE TABLE fact_orders (
    order_line_id   INTEGER PRIMARY KEY,   -- surrogate key (Row ID in source)
    order_id        TEXT,
    order_date      TEXT,                  -- FK -> dim_date.date_key
    ship_date       TEXT,
    ship_mode       TEXT,
    customer_id     TEXT,                  -- FK -> dim_customers.customer_id
    product_id      TEXT,                  -- FK -> dim_products.product_id
    sales           REAL,
    quantity        INTEGER,
    discount        REAL,
    profit          REAL,
    FOREIGN KEY (order_date)  REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES dim_products(product_id)
);

CREATE INDEX idx_fact_order_date  ON fact_orders(order_date);
CREATE INDEX idx_fact_customer    ON fact_orders(customer_id);
CREATE INDEX idx_fact_product     ON fact_orders(product_id);
