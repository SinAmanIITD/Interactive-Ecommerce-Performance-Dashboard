# Interactive E-commerce Performance Dashboard

**Interactive E-commerce Performance Dashboard | SQL, Star Schema, RFM Segmentation, Power BI / DAX**

> Built a 4-page dashboard (SQL-modeled data: revenue, profit, orders, product performance, customer metrics) · Star-schema data model in SQL + Python · RFM segmentation in SQL identifying Champions / Loyal / New / At-Risk customers · Power BI-ready with real DAX measures, geographic insights, and time-series trends.

**Honest note up front:** this was built on a Mac with no Power BI Desktop available
(it's Windows-only). The SQL star schema and RFM segmentation — the actual data
engineering work — are built for real. The 4-page dashboard is delivered as a working
Streamlit/Plotly app instead of a `.pbix`, and every DAX measure a real Power BI build
would need is written out, correct, and ready to paste in `dax_measures.md`. Full
explanation and how to talk about this in an interview: `INTERVIEW_PREP.md`.

---

## Project Structure

```
Interactive_Ecommerce_Performance_Dashboard/
├── data/
│   ├── raw/Sample-Superstore.csv   # Kaggle Superstore dataset, 9,994 rows x 21 cols
│   └── superstore.db                # SQLite star schema (built by src/setup_database.py)
├── sql/
│   ├── 01_create_schema.sql         # Star schema DDL (1 fact + 3 dims)
│   ├── 02_rfm_segmentation.sql      # RFM scoring + segment classification
│   ├── 03_revenue_trends.sql        # Monthly revenue/profit/MoM growth
│   └── 04_geographic_analysis.sql   # Revenue/profit by state & region
├── src/
│   ├── setup_database.py            # CSV -> cleaned star schema -> SQLite
│   ├── db.py                        # Shared DB connection helper for the dashboard
│   └── make_figures.py              # Generates reports/figures/*.png
├── app_pages/
│   ├── home.py                      # Page 1: Executive Summary
│   ├── product_analysis.py          # Page 2: Product Analysis
│   ├── geographic.py                # Page 3: Geographic Analysis
│   └── customer_segments.py         # Page 4: Customer Segments (RFM)
├── streamlit_app.py                 # Dashboard entry point
├── reports/
│   ├── figures/                     # Static chart exports
│   ├── rfm.csv, geo.csv, revenue_trends.csv, kpi_summary.json, ...
├── dax_measures.md                  # Real DAX, ready for an actual Power BI build
├── requirements.txt
├── README.md
└── INTERVIEW_PREP.md                # Full interview-prep report — read before the interview
```

---

## Quick Start

```bash
cd Interactive_Ecommerce_Performance_Dashboard
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Build the star schema SQLite database from the raw CSV
python3 src/setup_database.py

# Regenerate report figures
python3 src/make_figures.py

# Launch the 4-page dashboard
streamlit run streamlit_app.py
```

---

## Dataset

| Field | Value |
|---|---|
| Name | Superstore Sales Dataset |
| Size | 9,994 order-line rows x 21 columns |
| Coverage | Jan 2014 - Dec 2017, 793 customers, 1,862 products, 49 states |
| Source | Public Kaggle dataset ("vivek468/superstore-dataset-final"), mirrored from a public GitHub copy the same way the churn project downloaded its Telco CSV |

## Star Schema

`fact_orders` (9,994 rows, one per order line) joins to `dim_customers` (793 rows),
`dim_products` (1,862 rows), and `dim_date` (1,434 rows) — all foreign keys verified
with zero orphan rows after load (`src/setup_database.py` prints this check).

## RFM Segmentation (SQL, `sql/02_rfm_segmentation.sql`)

Recency/Frequency/Monetary quintile-scored per customer, classified by per-axis
thresholds (not a single summed cutoff — see `INTERVIEW_PREP.md` for why):

| Segment | Customers | % of customers | Total monetary value | % of value |
|---|---|---|---|---|
| Loyal Customers | 159 | 20.1% | — | 26.4% |
| Champions | 109 | 13.7% | — | 24.9% |
| At Risk | 143 | 18.0% | — | 23.2% |
| New Customers | 86 | 10.8% | — | 6.0% |
| Others | 296 | 37.3% | — | 19.6% |

**Champions + Loyal Customers = 33.8% of customers, driving 51.3% of total revenue.**

## Key KPIs (real, computed from the SQL layer)

| KPI | Value |
|---|---|
| Total Revenue | $2,297,200.86 |
| Total Profit | $286,397.02 |
| Total Orders | 5,009 |
| Avg Order Value | $458.61 |
| Profit Margin | 12.47% |
| Top 3 states by revenue | California (20.7%), New York (12.4%), Texas (7.6%) |
| Loss-making sub-categories | Tables (-$17,725), Machines near-breakeven ($3,385 on $189K revenue) |

Full write-up, every design decision justified, and the honest Power BI discussion:
[`INTERVIEW_PREP.md`](INTERVIEW_PREP.md).
