import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px
import streamlit as st
from db import query

st.title("📦 Product Analysis")
st.caption("Category & sub-category revenue, margin, and the high-sales/low-profit problem")

cat = query("""
    SELECT p.category, ROUND(SUM(f.sales),2) revenue, ROUND(SUM(f.profit),2) profit,
           ROUND(SUM(f.profit)/SUM(f.sales)*100,2) margin_pct
    FROM fact_orders f JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.category ORDER BY revenue DESC
""")
c1, c2 = st.columns(2)
with c1:
    fig = px.bar(cat, x="category", y="revenue", color="margin_pct",
                 title="Revenue by Category (colored by margin %)", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.dataframe(cat, use_container_width=True, hide_index=True)

st.divider()

subcat = query("""
    SELECT p.sub_category, ROUND(SUM(f.sales),2) revenue, ROUND(SUM(f.profit),2) profit
    FROM fact_orders f JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.sub_category
""")
subcat["status"] = subcat["profit"].apply(lambda x: "Loss-making" if x < 0 else "Profitable")
fig2 = px.scatter(subcat, x="revenue", y="profit", color="status", text="sub_category",
                   title="Sales vs. Profit by Sub-Category — spot the high-sales, low-profit traps",
                   color_discrete_map={"Loss-making": "#e74c3c", "Profitable": "#2ecc71"})
fig2.update_traces(textposition="top center")
fig2.add_hline(y=0, line_dash="dash", line_color="grey")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top 10 sub-categories by revenue")
top10 = subcat.sort_values("revenue", ascending=False).head(10)
st.dataframe(top10, use_container_width=True, hide_index=True)

loss = subcat[subcat["profit"] < 0].sort_values("profit")
if len(loss):
    st.warning(f"**{len(loss)} sub-categories are losing money despite generating revenue:** "
               + ", ".join(f"{r.sub_category} (${r.profit:,.0f})" for r in loss.itertuples()))
