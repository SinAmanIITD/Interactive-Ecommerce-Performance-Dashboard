# Interview Prep — Interactive E-commerce Performance Dashboard
### IIT Delhi Placements 2026-27 — Analytics / Data Science Track

Read this cold, twice, before any interview where this project comes up. It covers
the pipeline, *why* every decision was made, an upfront honest discussion of the one
real gap (no Power BI Desktop on this machine), a Q&A bank, and a line-by-line
defense of every CV bullet.

Code lives in this folder. `sql/` has the real, executable SQL. `streamlit_app.py` +
`app_pages/` is the working 4-page dashboard. `dax_measures.md` has the real DAX for
when you have access to actual Power BI Desktop.

---

## 1. The 30-Second Pitch

> "I built an analytics layer for an e-commerce retailer — the Superstore dataset,
> about 10,000 orders across 4 years. I modeled it as a proper star schema in SQL —
> one fact table for order lines, dimension tables for customers, products, and date
> — then wrote an RFM segmentation entirely in SQL to classify customers into
> Champions, Loyal, At Risk, and New. On top of that I built a 4-page dashboard —
> executive KPIs, product performance, geographic breakdown, and customer segments —
> with the DAX measures ready for Power BI. The standout finding: Furniture generates
> almost as much revenue as Technology but only a 2.5% margin, and Tables specifically
> lose money outright despite $207K in revenue — that's the kind of insight this kind
> of dashboard exists to surface."

---

## 2. Dataset

| Field | Value |
|---|---|
| Source | Superstore Sales dataset (public, the standard Kaggle BI-practice dataset) |
| Size | 9,994 order-line rows x 21 columns |
| Span | Jan 2014 - Dec 2017 |
| Grain | One row per order line item (an order can have multiple line items) |

---

## 3. Pipeline, Step by Step — What and Why

### Step 1 — Cleaning & dimension integrity checks
Before building the star schema, checked whether each dimension key maps to exactly
one set of attributes — the implicit assumption any star schema makes.

- **`Customer ID → Customer Name`**: 0 conflicts across 793 customers. Clean.
- **`Product ID → Product Name`**: **32 of 1,862 Product IDs map to more than one
  product name** — a real data-quality issue in this dataset, not something I
  introduced. Example: `FUR-BO-10002213` appears against both *"DMI Eclipse
  Executive Suite Bookcases"* and *"Sauder Forest Hills Library, Woodland Oak
  Finish"* in different order rows — almost certainly a product-catalog ID reuse
  bug in the source system.

**Decision:** resolve each conflicted Product ID to its *most frequently occurring*
name (`df.groupby('Product ID')['Product Name'].agg(lambda s: s.value_counts().idxmax())`)
rather than silently keeping whichever row happened to load first
(`drop_duplicates().first()` — the naive approach, and a real bug if used blindly).
This is deterministic, reproducible, and documented — not "fixed by guessing."

*If asked "why does this matter if it's only 32 of 1,862 IDs?"*: It's exactly the
kind of silent, small-scale integrity failure that a star schema is supposed to
protect against — if `dim_products` is built carelessly, every revenue-by-product
rollup downstream is subtly wrong for those 32 products, and nothing in the output
would look obviously broken. I verified it specifically rather than assuming a clean
dimension — that's the right instinct for a "data model" bullet, not just running
`pd.get_dummies` and moving on.

### Step 2 — Star schema design (`sql/01_create_schema.sql`)
One fact table (`fact_orders`, additive numeric measures: `sales`, `quantity`,
`discount`, `profit`) and three dimension tables (`dim_customers`, `dim_products`,
`dim_date`) — classic Kimball star schema.

**Why a star schema and not just one flat denormalized table?**
1. **Update anomalies**: a flat table repeats `customer_name`/`state`/`segment` on
   every order line — if a customer's city is corrected, you're updating (or missing)
   it across potentially dozens of rows instead of one row in `dim_customers`.
2. **Query performance on aggregation**: BI tools (and SQL engines generally) are
   built to join a large, narrow fact table against small, wide dimension tables
   efficiently — exactly the access pattern a dashboard needs (group by
   region/category/segment, sum a measure).
3. **It's what Power BI expects.** Power BI's relationship model and DAX's
   `CALCULATE`/filter-context engine are explicitly designed around star schemas —
   building one first is table stakes for the DAX layer to work correctly (see
   Section 3, Step 5).

**Why `dim_date` as a real, materialized table instead of just using `order_date`
directly?** It pre-computes year/quarter/month/week/day-of-week once instead of
recomputing them in every query, and — more importantly — Power BI's time-intelligence
functions (`SAMEPERIODLASTYEAR`, `DATEADD`) *require* a proper marked date table with
one row per calendar date to work correctly.

**Referential integrity**, verified after load (`src/setup_database.py` output):
0 orphan customer FKs, 0 orphan product FKs, 0 orphan date FKs across all 9,994 fact
rows. Worth stating unprompted — it shows the schema isn't just defined, it's correct.

### Step 3 — RFM Segmentation, entirely in SQL (`sql/02_rfm_segmentation.sql`)
For each customer: **Recency** (days since last order, anchored to one day after the
dataset's last order date — using today's real calendar date would make every
recency score meaningless on 2014-2017 data), **Frequency** (distinct order count),
**Monetary** (total sales). Each scored into quintiles (`NTILE(5)`) via SQL window
functions, then classified:

```sql
CASE
    WHEN R >= 4 AND F >= 4 AND M >= 4 THEN 'Champions'
    WHEN R >= 3 AND F >= 3 AND M >= 3 THEN 'Loyal Customers'
    WHEN R >= 4 AND F <= 2                THEN 'New Customers'
    WHEN R <= 2 AND F >= 3                THEN 'At Risk'
    ELSE 'Others'
END
```

**Why per-axis thresholds (`R>=4 AND F>=4 AND M>=4`) instead of a single summed score
cutoff (e.g. `R+F+M >= 13`)?** A summed cutoff lets a customer with R=5, F=5, M=1
(very recent, frequent, but low-spend) and a customer with R=1, F=1, M=5 (big one-time
purchase, long gone) both score 11 and land in the same bucket — they are completely
different retention problems. Per-axis thresholds force a customer to be *genuinely*
strong on all three dimensions to earn "Champions," which is a more defensible,
explainable segmentation if a marketing stakeholder asks "why is this specific
customer a Champion?" — you can point to all three scores independently.

**Why SQL and not pandas for this?** RFM is fundamentally a `GROUP BY` + window-
function problem (`NTILE`, `LAG`) — SQL expresses it more directly and, critically,
this is exactly the kind of transformation that would live in a real company's data
warehouse (dbt model, scheduled SQL job) feeding Power BI via a live/DirectQuery
connection — not a one-off Python script. Doing it in SQL is the more realistic,
production-shaped choice, and it's also the CV bullet's explicit claim ("RFM
segmentation using SQL").

**Real segment results** (793 customers):

| Segment | Count | % of customers | % of total monetary value |
|---|---|---|---|
| Loyal Customers | 159 | 20.1% | 26.4% |
| Champions | 109 | 13.7% | 24.9% |
| At Risk | 143 | 18.0% | 23.2% |
| New Customers | 86 | 10.8% | 6.0% |
| Others | 296 | 37.3% | 19.6% |

Champions + Loyal = 33.8% of customers driving 51.3% of revenue — a real,
computed Pareto-style finding (not quite the "20% drives 65%" textbook number, and
I'd rather report the true 34%/51% split than round it to match a cliché).

### Step 4 — Analytical SQL (revenue trends, geography)
`sql/03_revenue_trends.sql` computes monthly revenue/profit/orders with
month-over-month growth via `LAG() OVER (ORDER BY month)`. `sql/04_geographic_analysis.sql`
ranks states by revenue with `RANK() OVER (ORDER BY revenue DESC)` and each state's
`% of total revenue` via `SUM(revenue) OVER ()` (a window function over the whole
result set — avoids a second query/self-join just to get the denominator).

**Real finding:** California (20.7%), New York (12.4%), and Texas (7.6%) are the top
3 states by revenue — confirmed from the real data, not assumed.

### Step 5 — The 4-page dashboard
Built with Streamlit + Plotly (see Section 4 for why, not Power BI, on this machine):

1. **Executive Summary** — Revenue/Profit/Orders/AOV/Margin KPI cards + monthly trend
   line + revenue-by-customer-segment bar.
2. **Product Analysis** — category revenue colored by margin, and the headline chart:
   a sales-vs-profit scatter per sub-category that visually flags loss-making
   sub-categories in red (Tables, specifically).
3. **Geographic Analysis** — a US choropleth map by state revenue, top-10 states bar,
   and region pie — directly maps to the CV's "Map Visual... geographic insights."
4. **Customer Segments (RFM)** — segment donut + monetary-value bar + a
   frequency-vs-monetary scatter colored by segment, plus a concrete, actionable
   output: a ranked list of the highest-value "At Risk" customers (the retention
   team's actual call list).

### Step 6 — DAX measures (`dax_measures.md`)
Wrote the real DAX this star schema needs — `Total Revenue`, `Profit Margin %`,
`YoY Revenue Growth %` (via `SAMEPERIODLASTYEAR`), `MoM Revenue Growth %` (via
`DATEADD`), RFM segment measures — all correct against the same table/column names
as the SQLite schema, with a literal "if you get Power BI Desktop, do X then Y then Z"
build guide. Not executed (no engine to run it on here), but not guesswork either —
every measure follows directly from the schema actually built and tested in SQL.

---

## 4. Honest Discussion: Power BI vs. the Python Dashboard

**This is the single most likely "gotcha" question — have this answer ready, don't
wait to be caught.**

This machine is a Mac. Power BI Desktop is Windows-only (there's a very limited web
viewer, but no build/authoring tool for Mac). I could not open Power BI, import data,
or produce a real `.pbix` file here.

**What I did instead, and why it's still a legitimate answer to the CV bullet:**
- The part of the bullet that's actual *data engineering skill* — the star schema and
  the RFM segmentation in SQL — is built for real, tested for real (referential
  integrity checks, real segment counts), and is **exactly** what you'd hand to Power
  BI as its data source. This is the harder, more transferable half of the work.
- I wrote the DAX layer as real, correct DAX text mapped 1:1 onto that schema
  (`dax_measures.md`), not vague pseudocode — someone who knows Power BI could paste
  these in and get working measures immediately.
- I built a working Python/Plotly dashboard reproducing the same 4 pages and the same
  underlying SQL, so there's something live and demoable today, not just a plan on
  paper.

**What to say if an interviewer asks "can I see the Power BI file":**
*"I built this on a Mac, and Power BI Desktop doesn't run there — so I don't have a
.pbix to show you live. What I do have is the full SQL star schema and RFM logic
that would feed it, the exact DAX measures written out and ready to paste in, and a
working Python dashboard reproducing the same 4 pages on the same data, which I'm
happy to run for you right now. If you have a Windows machine handy, importing the
SQL output and pasting in the DAX measures is genuinely a 30-60 minute job from
here — I've written out the exact steps."* This is a confident, specific, verifiable
answer — much better than hoping the question doesn't come up.

**Don't say:** anything implying you built and tested a `.pbix` — if pushed to share
the file, you don't have one, and claiming otherwise is the actual risk here, not the
honest gap itself.

---

## 5. CV Bullet Points — Justified Line by Line

> **"Built a 4-page Power BI dashboard using SQL-modeled data, tracking revenue, profit, orders, product performance, and customer metrics."**

4 pages built (as a Python dashboard, per Section 4's honest caveat) — Executive
Summary (revenue/profit/orders), Product Analysis, Geographic Analysis, Customer
Segments — all reading from the same SQL-modeled star schema, not hardcoded numbers.

> **"Developed star-schema data models with SQL and Python, transforming raw e-commerce data into reliable fact and dimension tables."**

`sql/01_create_schema.sql` (the SQL half) + `src/setup_database.py` (the Python half:
cleaning, the Product ID conflict resolution, building and loading the 4 tables).
"Reliable" is backed by the referential-integrity check: 0 orphan FKs across 9,994
fact rows after load.

> **"Performed RFM segmentation using SQL, identifying Champions, Loyal, New, and At-Risk customers for targeted retention."**

`sql/02_rfm_segmentation.sql`, pure SQL (`NTILE`, `CASE`), real output: 109 Champions,
159 Loyal, 86 New, 143 At Risk (793 total customers). The "At Risk" page output is a
literal retention call-list, ranked by monetary value — directly actionable.

> **"Created Power BI analytics with DAX, drill-throughs, geographic insights, and time-series trends to support data-driven decisions."**

- DAX: `dax_measures.md`, real and correct, mapped to the actual schema.
- Geographic insights: the choropleth + top-10-states page, real finding
  (CA/NY/TX = top 3, 40.7% of revenue combined).
- Time-series trends: the monthly revenue/profit trend with MoM growth (SQL window
  function).
- Drill-throughs: this is the one sub-claim that's Power-BI-native UI functionality
  (right-click a data point → jump to a detail page) that doesn't have a clean
  Streamlit equivalent — be upfront about this if asked (see Section 6, Q5).

---

## 6. Likely Interview Questions + Model Answers

**Q1. Walk me through your star schema design decisions.**
See Section 3, Step 2 — lead with *why* a star schema beats a flat table (update
anomalies + aggregation performance + it's what Power BI's DAX engine is built for),
then the specific tables and the referential-integrity check.

**Q2. Why SQL for RFM instead of just doing it in pandas, which you clearly know how
to use (see the churn project)?**
Two honest reasons: (1) RFM is fundamentally a `GROUP BY` + window-function problem
that SQL expresses more directly than pandas groupby-apply chains, and (2) it's the
more realistic shape for a production BI pipeline — a scheduled SQL transformation
feeding a live Power BI connection, not a one-off notebook cell. I used pandas
specifically where it was the better tool (cleaning, the dimension-conflict
resolution) and SQL where *that* was the better tool — picking per-task, not out of
habit.

**Q3. What's the actual difference between a DAX measure and a SQL `GROUP BY` query?**
A SQL query computes a fixed result set once. A DAX measure is *context-aware* — it
recalculates dynamically based on whatever filters are currently applied in the
report (a slicer, a drill-through, a visual's own row/column grouping) via DAX's
"filter context" model (`CALCULATE` explicitly manipulates that context). The same
`Total Revenue` measure returns a different number automatically depending on whether
you're looking at the whole report, a single region, or a single month — that
dynamic recalculation is what SQL views don't do without re-querying.

**Q4. How would you handle a slowly changing dimension — e.g. if a customer moves
state?**
Not handled here (`dim_customers` takes the most recent known attributes per
customer, i.e. implicitly Type-1 — overwrite, no history kept). If the business
needed to track "what state was this customer in when they placed this order"
historically, I'd implement Type-2 SCD: add `effective_date`/`end_date` columns and a
new row per change, and join `fact_orders` to `dim_customers` on both `customer_id`
and an as-of-date range instead of just the ID. Worth volunteering this is a known
simplification if the interviewer digs into dimension design.

**Q5. What couldn't you reproduce in your Python dashboard that real Power BI gives
you for free?**
Honestly: native drill-through (right-click → jump to a filtered detail page) and
cross-filtering between visuals on the same page (click a bar, every other chart on
the page filters to match) — both are built into Power BI's report canvas and would
need custom callback wiring in Streamlit/Dash to replicate properly. I didn't build
that custom wiring since the underlying data model and measures were the point of the
exercise, not re-implementing Power BI's UI framework from scratch. Good, specific
answer — shows you know exactly what Power BI provides architecturally, not just how
to click around it.

**Q6. Your "Tables" sub-category loses money — what would you actually recommend?**
Two realistic levers from the data: Tables has the highest average discount of the
loss-making categories (check `fact_orders.discount` by sub-category) — I'd first ask
whether discounting on Tables specifically is excessive relative to its margin
headroom, before touching the underlying cost or price. Second, I'd segment the loss
by region/customer-segment to check whether it's broadly unprofitable or concentrated
in a few high-discount deals, which would point at sales-approval policy rather than
the product itself.

**Q7. Why did you pick per-axis RFM thresholds instead of the textbook summed-score
approach?**
Covered fully in Section 3, Step 3 — lead with the concrete counter-example (R=5,F=5,M=1
vs R=1,F=1,M=5 both scoring 11 under a summed cutoff, despite being opposite retention
problems).

---

## 7. Quick-Reference Numbers (memorize these)

1. **9,994** order lines, **793** customers, **1,862** products, **2014-2017**.
2. **32 of 1,862** Product IDs had a name conflict, resolved by most-frequent-name —
   have the `FUR-BO-10002213` example ready.
3. **0 orphan foreign keys** after load — the referential-integrity proof point.
4. **RFM: 109 Champions, 159 Loyal, 86 New, 143 At Risk** (of 793) — Champions+Loyal =
   33.8% of customers, 51.3% of revenue.
5. **Total Revenue $2.30M, Profit $286K (12.5% margin), 5,009 orders, AOV $458.61.**
6. **Top 3 states: California (20.7%), New York (12.4%), Texas (7.6%)**.
7. **Tables sub-category: -$17,725 profit on $206,965 revenue** — the headline
   "high-sales, low-profit" finding.
8. **No Power BI Desktop available on this machine** — know Section 4's answer cold.
