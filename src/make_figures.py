"""Generates the static figures referenced in the README."""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns

sns.set_style("whitegrid")
ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "reports" / "figures"
conn = sqlite3.connect(ROOT / "data" / "superstore.db")


def savefig(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=150)
    plt.close()


# 1. Monthly revenue trend
trend = pd.read_sql_query(open(ROOT / "sql/03_revenue_trends.sql").read(), conn)
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(trend["month"], trend["revenue"], color="#2980b9", linewidth=2)
ax.fill_between(trend["month"], trend["revenue"], alpha=0.15, color="#2980b9")
ax.set_xticks(trend["month"][::4])
ax.set_xticklabels(trend["month"][::4], rotation=45, ha="right")
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))
ax.set_title("Monthly Revenue Trend (2014-2017)")
savefig("01_revenue_trend.png")

# 2. Category / sub-category performance (sales vs profit)
cat = pd.read_csv(ROOT / "reports" / "category_performance.csv")
fig, ax = plt.subplots(figsize=(8, 4.5))
x = range(len(cat))
ax.bar(x, cat["revenue"], color="#3498db", label="Revenue")
ax2 = ax.twinx()
ax2.plot(x, cat["margin_pct"], color="#e74c3c", marker="o", linewidth=2, label="Profit Margin %")
ax.set_xticks(list(x)); ax.set_xticklabels(cat["category"])
ax.set_ylabel("Revenue ($)"); ax2.set_ylabel("Profit Margin (%)")
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v/1000:.0f}K"))
ax.set_title("Revenue by Category vs. Profit Margin")
lines1, labels1 = ax.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1+lines2, labels1+labels2, loc="upper right")
savefig("02_category_performance.png")

# 3. Sales vs Profit scatter per sub-category (high-sales/low-profit finder)
subcat_full = pd.read_sql_query("""
    SELECT p.sub_category, ROUND(SUM(f.sales),2) revenue, ROUND(SUM(f.profit),2) profit
    FROM fact_orders f JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.sub_category
""", conn)
fig, ax = plt.subplots(figsize=(8, 6))
colors = ["#e74c3c" if p < 0 else "#2ecc71" for p in subcat_full["profit"]]
ax.scatter(subcat_full["revenue"], subcat_full["profit"], c=colors, s=90, edgecolor="black", linewidth=0.5)
for _, row in subcat_full.iterrows():
    ax.annotate(row["sub_category"], (row["revenue"], row["profit"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
ax.axhline(0, color="grey", linestyle="--", linewidth=1)
ax.set_xlabel("Revenue ($)"); ax.set_ylabel("Profit ($)")
ax.set_title("Sales vs. Profit by Sub-Category\n(red = loss-making despite revenue)")
savefig("03_sales_vs_profit_scatter.png")

# 4. Geographic: top 10 states by revenue
geo = pd.read_csv(ROOT / "reports" / "geo.csv").head(10)
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(geo["state"][::-1], geo["revenue"][::-1], color="#9b59b6")
ax.set_xlabel("Revenue ($)")
ax.set_title("Top 10 States by Revenue")
savefig("04_top_states.png")

# 5. RFM segment breakdown
rfm = pd.read_csv(ROOT / "reports" / "rfm.csv")
seg_counts = rfm["segment"].value_counts()
seg_rev = rfm.groupby("segment")["monetary"].sum()
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].pie(seg_counts.values, labels=seg_counts.index, autopct="%1.0f%%", startangle=90,
            colors=sns.color_palette("Set2", len(seg_counts)))
axes[0].set_title("Customer Count by RFM Segment")
order = seg_counts.index
axes[1].bar(order, seg_rev.reindex(order), color=sns.color_palette("Set2", len(order)))
axes[1].set_title("Total Monetary Value by Segment")
axes[1].set_ylabel("Total Sales ($)")
plt.xticks(rotation=20)
savefig("05_rfm_segments.png")

# 6. RFM scatter: Frequency vs Monetary colored by segment
fig, ax = plt.subplots(figsize=(8, 6))
palette = dict(zip(rfm["segment"].unique(), sns.color_palette("Set2", rfm["segment"].nunique())))
for seg, grp in rfm.groupby("segment"):
    ax.scatter(grp["frequency"], grp["monetary"], label=seg, alpha=0.7, color=palette[seg])
ax.set_xlabel("Frequency (distinct orders)"); ax.set_ylabel("Monetary ($)")
ax.set_title("RFM: Frequency vs. Monetary Value by Segment")
ax.legend()
savefig("06_rfm_scatter.png")

print("Figures saved to", FIG_DIR)
conn.close()
