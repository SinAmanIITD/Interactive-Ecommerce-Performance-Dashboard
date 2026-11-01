# DAX Measures — Ready to Paste Into Power BI Desktop

These are **real, correct DAX** written against the same star schema built in this
project (`fact_orders`, `dim_customers`, `dim_products`, `dim_date`). They are not
executed here (no Power BI Desktop on this machine — see `INTERVIEW_PREP.md` for the
honest explanation of that gap) but are syntactically correct and ready to paste into
a real `.pbix` file the moment one is available.

## How to build the real .pbix (if you get access to Power BI Desktop)

1. **Get Data → SQLite** (or export each table from `data/superstore.db` to CSV via
   `sqlite3 data/superstore.db ".mode csv" ".output dim_customers.csv" "SELECT * FROM dim_customers;"`
   and repeat per table, then **Get Data → Text/CSV** for each).
2. Import all 4 tables: `fact_orders`, `dim_customers`, `dim_products`, `dim_date`.
3. **Model view** → draw relationships: `fact_orders[customer_id] → dim_customers[customer_id]`,
   `fact_orders[product_id] → dim_products[product_id]`, `fact_orders[order_date] → dim_date[date_key]`
   (all one-to-many, single direction — standard star schema).
4. Mark `dim_date` as a **Date Table** (Table tools → Mark as Date Table) — required
   for the time-intelligence measures (`SAMEPERIODLASTYEAR`, etc.) to work.
5. Paste each measure below into a new measure (Modeling → New Measure) on `fact_orders`.
6. Build the 4 pages per the layout in `README.md` / `INTERVIEW_PREP.md`, using these
   measures as the KPI cards and chart values.

Total build time for someone who already has the data modeled (which this project
hands you): **30-60 minutes**, almost all of it visual layout, not logic.

---

## Core measures

```dax
Total Revenue = SUM(fact_orders[sales])

Total Profit = SUM(fact_orders[profit])

Total Orders = DISTINCTCOUNT(fact_orders[order_id])

Avg Order Value = DIVIDE([Total Revenue], [Total Orders], 0)

Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0)
```

## Time intelligence (requires dim_date marked as a Date Table)

```dax
Revenue LY =
    CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[date_key]))

YoY Revenue Growth % =
    DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY], 0)

Revenue PM =  -- previous month
    CALCULATE([Total Revenue], DATEADD(dim_date[date_key], -1, MONTH))

MoM Revenue Growth % =
    DIVIDE([Total Revenue] - [Revenue PM], [Revenue PM], 0)

Revenue MTD =
    TOTALMTD([Total Revenue], dim_date[date_key])
```

## Customer / RFM measures

```dax
Customer Count = DISTINCTCOUNT(fact_orders[customer_id])

Revenue per Customer = DIVIDE([Total Revenue], [Customer Count], 0)

-- RFM segment % measures (assumes an rfm_segments table imported from
-- `reports/rfm.csv`, joined 1:1 to dim_customers on customer_id)
Champions % =
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(rfm_segments[customer_id]), rfm_segments[segment] = "Champions"),
        DISTINCTCOUNT(rfm_segments[customer_id]),
        0
    )

At Risk Customer Count =
    CALCULATE(DISTINCTCOUNT(rfm_segments[customer_id]), rfm_segments[segment] = "At Risk")

At Risk Revenue at Stake =
    CALCULATE([Total Revenue], TREATAS(VALUES(rfm_segments[customer_id]), fact_orders[customer_id]), rfm_segments[segment] = "At Risk")
```

## Product measures

```dax
Loss-Making Sub-Categories =
    CALCULATE(
        DISTINCTCOUNT(dim_products[sub_category]),
        FILTER(
            SUMMARIZE(fact_orders, dim_products[sub_category], "p", [Total Profit]),
            [p] < 0
        )
    )

High-Revenue Low-Margin Flag =
    IF([Total Revenue] > 100000 && [Profit Margin %] < 0.05, "Investigate", "OK")
```

## Measures mapped to this project's real, computed numbers (for sanity-checking a Power BI build)

| Measure | Value computed here (SQL, `reports/kpi_summary.json`) |
|---|---|
| Total Revenue | $2,297,200.86 |
| Total Profit | $286,397.02 |
| Total Orders | 5,009 |
| Avg Order Value | $458.61 |
| Profit Margin % | 12.47% |
| Customer Count | 793 |

If a real `.pbix` build of these same measures against the same tables produces
different totals, the model relationships are wrong (most likely: a many-to-many
join from an un-deduplicated dimension table) — the SQL numbers above are the ground
truth to debug against.
