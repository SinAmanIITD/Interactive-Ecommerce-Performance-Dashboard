"""Shared SQLite connection helper for the dashboard pages."""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "superstore.db"
SQL_DIR = ROOT / "sql"


@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def query(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_connection())


@st.cache_data
def query_file(filename: str) -> pd.DataFrame:
    return query((SQL_DIR / filename).read_text())
