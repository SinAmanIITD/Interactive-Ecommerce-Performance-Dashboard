import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px
import streamlit as st
from db import query_file

st.title("🗺️ Geographic Analysis")
st.caption("Revenue, profit, and order share by U.S. state and region")

geo = query_file("04_geographic_analysis.sql")

US_STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}
geo["state_abbr"] = geo["state"].map(US_STATE_ABBR)

fig = px.choropleth(
    geo, locations="state_abbr", locationmode="USA-states", color="revenue",
    scope="usa", color_continuous_scale="Blues", hover_name="state",
    hover_data={"revenue": ":$,.0f", "profit": ":$,.0f", "state_abbr": False},
    title="Revenue by State",
)
st.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    top10 = geo.head(10)
    fig2 = px.bar(top10.sort_values("revenue"), x="revenue", y="state", orientation="h",
                   title="Top 10 States by Revenue")
    st.plotly_chart(fig2, use_container_width=True)
with c2:
    region = geo.groupby("region")[["revenue", "profit"]].sum().reset_index()
    fig3 = px.pie(region, names="region", values="revenue", title="Revenue Share by Region")
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("State performance table")
st.dataframe(geo, use_container_width=True, hide_index=True)

top3_share = geo.head(3)["pct_of_total_revenue"].sum()
st.info(f"**California, New York, and Texas together drive {top3_share:.1f}% of total revenue** "
        "— the top 3 states by a wide margin over the rest of the country.")
