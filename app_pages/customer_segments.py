import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px
import streamlit as st
from db import query_file

st.title("👥 Customer Segments — RFM Analysis")
st.caption("Recency / Frequency / Monetary segmentation, computed entirely in SQL")

rfm = query_file("02_rfm_segmentation.sql")

seg_counts = rfm["segment"].value_counts().reset_index()
seg_counts.columns = ["segment", "count"]
seg_rev = rfm.groupby("segment", as_index=False)["monetary"].sum()

c1, c2, c3 = st.columns(3)
champions_pct = (rfm["segment"] == "Champions").mean() * 100
loyal_pct = (rfm["segment"] == "Loyal Customers").mean() * 100
at_risk_pct = (rfm["segment"] == "At Risk").mean() * 100
c1.metric("% Champions", f"{champions_pct:.1f}%")
c2.metric("% Loyal Customers", f"{loyal_pct:.1f}%")
c3.metric("% At Risk", f"{at_risk_pct:.1f}%")

c1, c2 = st.columns(2)
with c1:
    fig = px.pie(seg_counts, names="segment", values="count", title="Customer Count by Segment", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig2 = px.bar(seg_rev.sort_values("monetary", ascending=False), x="segment", y="monetary",
                   title="Total Monetary Value by Segment", color="segment")
    st.plotly_chart(fig2, use_container_width=True)

fig3 = px.scatter(rfm, x="frequency", y="monetary", color="segment",
                   title="Frequency vs. Monetary Value by Segment",
                   hover_data=["customer_id", "recency_days"])
st.plotly_chart(fig3, use_container_width=True)

st.subheader("At-risk customers (highest monetary value first) — retention priority list")
at_risk = rfm[rfm["segment"] == "At Risk"].sort_values("monetary", ascending=False).head(20)
st.dataframe(at_risk, use_container_width=True, hide_index=True)
