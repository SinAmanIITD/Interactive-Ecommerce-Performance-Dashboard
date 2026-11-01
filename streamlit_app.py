import streamlit as st

st.set_page_config(page_title="E-commerce Performance Dashboard", layout="wide", page_icon="📊")

pages = {
    "Dashboard": [
        st.Page("app_pages/home.py", title="Executive Summary", icon="📈"),
        st.Page("app_pages/product_analysis.py", title="Product Analysis", icon="📦"),
        st.Page("app_pages/geographic.py", title="Geographic Analysis", icon="🗺️"),
        st.Page("app_pages/customer_segments.py", title="Customer Segments (RFM)", icon="👥"),
    ]
}
pg = st.navigation(pages)
pg.run()
