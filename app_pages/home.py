import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px
import streamlit as st
from db import query, query_file

st.title("📈 Executive Summary")
st.caption("Superstore E-commerce — Revenue, Profit, Orders & Customer KPIs (2014-2017)")

kpi = query("""
    SELECT ROUND(SUM(sales),2) AS revenue, ROUND(SUM(profit),2) AS profit,
           COUNT(DISTINCT order_id) AS orders,
           ROUND(SUM(sales)/COUNT(DISTINCT order_id),2) AS aov,
           ROUND(SUM(profit)/SUM(sales)*100,2) AS margin,
           COUNT(DISTINCT customer_id) AS customers
    FROM fact_orders
""").iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"${kpi.revenue:,.0f}")
c2.metric("Total Profit", f"${kpi.profit:,.0f}")
c3.metric("Orders", f"{int(kpi.orders):,}")
c4.metric("Avg Order Value", f"${kpi.aov:,.2f}")
c5.metric("Profit Margin", f"{kpi.margin:.1f}%")

st.divider()

trend = query_file("03_revenue_trends.sql")
fig = px.line(trend, x="month", y=["revenue", "profit"], title="Monthly Revenue & Profit Trend",
              labels={"value": "$", "month": "Month", "variable": "Metric"})
st.plotly_chart(fig, use_container_width=True)

seg_rev = query("""
    SELECT c.segment, ROUND(SUM(f.sales),2) revenue
    FROM fact_orders f JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.segment ORDER BY revenue DESC
""")
fig2 = px.bar(seg_rev, x="segment", y="revenue", title="Revenue by Customer Segment",
              color="segment", text_auto=".2s")
st.plotly_chart(fig2, use_container_width=True)
