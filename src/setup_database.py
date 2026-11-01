"""
Loads the raw Superstore CSV, builds a star schema (1 fact + 3 dims) and
writes it into a SQLite database at data/superstore.db.
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "Sample-Superstore.csv"
SCHEMA_SQL = ROOT / "sql" / "01_create_schema.sql"
DB_PATH = ROOT / "data" / "superstore.db"


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, encoding="latin1")
    # Source file has a UTF-8 BOM on the first header, misdecoded as latin1
    # into the literal 3-byte sequence "ï»¿" prefixing "Row ID".
    df = df.rename(columns={"ï»¿Row ID": "Row ID"})
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d/%m/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d/%m/%Y")
    return df


def check_dimension_integrity(df: pd.DataFrame) -> None:
    """
    A star schema assumes each dimension key maps to exactly one set of
    attributes. Verify that before building dim tables -- if a customer_id
    or product_id maps to more than one name/category, naive de-duplication
    (e.g. drop_duplicates().first()) silently picks an arbitrary version.
    """
    cust_conflicts = df.groupby("Customer ID")["Customer Name"].nunique()
    prod_conflicts = df.groupby("Product ID")["Product Name"].nunique()
    n_cust_conflicts = (cust_conflicts > 1).sum()
    n_prod_conflicts = (prod_conflicts > 1).sum()
    print(f"Customer IDs mapping to >1 name: {n_cust_conflicts} / {len(cust_conflicts)}")
    print(f"Product IDs mapping to >1 name:  {n_prod_conflicts} / {len(prod_conflicts)}")
    # Known, documented quirk of this dataset: a handful of Product IDs are
    # reused across different product names (data entry inconsistency in the
    # source Superstore export). We resolve it deterministically below by
    # taking the most frequent name per ID, rather than silently dropping it.


def build_dim_customers(df: pd.DataFrame) -> pd.DataFrame:
    dim = (
        df.sort_values("Order Date")
        .drop_duplicates(subset=["Customer ID"], keep="last")[
            ["Customer ID", "Customer Name", "Segment", "City", "State", "Region", "Country"]
        ]
        .rename(columns={
            "Customer ID": "customer_id", "Customer Name": "customer_name",
            "Segment": "segment", "City": "city", "State": "state",
            "Region": "region", "Country": "country",
        })
    )
    return dim


def build_dim_products(df: pd.DataFrame) -> pd.DataFrame:
    # Resolve Product ID -> Product Name conflicts by taking the most
    # frequently occurring name for that ID (documented in the report).
    most_common_name = (
        df.groupby("Product ID")["Product Name"]
        .agg(lambda s: s.value_counts().idxmax())
    )
    dim = df.drop_duplicates(subset=["Product ID"])[
        ["Product ID", "Category", "Sub-Category"]
    ].rename(columns={"Product ID": "product_id", "Category": "category", "Sub-Category": "sub_category"})
    dim["product_name"] = dim["product_id"].map(most_common_name)
    return dim[["product_id", "product_name", "category", "sub_category"]]


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    all_dates = pd.concat([df["Order Date"], df["Ship Date"]]).drop_duplicates().sort_values()
    dim = pd.DataFrame({"date_key": all_dates.dt.strftime("%Y-%m-%d")})
    dim["year"] = all_dates.dt.year.values
    dim["quarter"] = all_dates.dt.quarter.values
    dim["month"] = all_dates.dt.month.values
    dim["month_name"] = all_dates.dt.strftime("%B").values
    dim["week"] = all_dates.dt.isocalendar().week.values
    dim["day_of_week"] = all_dates.dt.strftime("%A").values
    return dim.drop_duplicates(subset=["date_key"])


def build_fact_orders(df: pd.DataFrame) -> pd.DataFrame:
    fact = df[[
        "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
        "Customer ID", "Product ID", "Sales", "Quantity", "Discount", "Profit",
    ]].rename(columns={
        "Row ID": "order_line_id", "Order ID": "order_id", "Ship Mode": "ship_mode",
        "Customer ID": "customer_id", "Product ID": "product_id", "Sales": "sales",
        "Quantity": "quantity", "Discount": "discount", "Profit": "profit",
    })
    fact["order_date"] = df["Order Date"].dt.strftime("%Y-%m-%d")
    fact["ship_date"] = df["Ship Date"].dt.strftime("%Y-%m-%d")
    return fact[[
        "order_line_id", "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "product_id", "sales", "quantity", "discount", "profit",
    ]]


def main():
    df = load_raw()
    print(f"Loaded {len(df):,} order-line rows from Superstore CSV")
    check_dimension_integrity(df)

    dim_customers = build_dim_customers(df)
    dim_products = build_dim_products(df)
    dim_date = build_dim_date(df)
    fact_orders = build_fact_orders(df)

    print(f"dim_customers: {len(dim_customers):,} rows")
    print(f"dim_products:  {len(dim_products):,} rows")
    print(f"dim_date:      {len(dim_date):,} rows")
    print(f"fact_orders:   {len(fact_orders):,} rows")

    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL.read_text())

    dim_customers.to_sql("dim_customers", conn, if_exists="append", index=False)
    dim_products.to_sql("dim_products", conn, if_exists="append", index=False)
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    fact_orders.to_sql("fact_orders", conn, if_exists="append", index=False)

    # Referential integrity check -- every FK in fact_orders should resolve.
    orphan_customers = conn.execute(
        "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_customers d "
        "ON f.customer_id = d.customer_id WHERE d.customer_id IS NULL"
    ).fetchone()[0]
    orphan_products = conn.execute(
        "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_products d "
        "ON f.product_id = d.product_id WHERE d.product_id IS NULL"
    ).fetchone()[0]
    orphan_dates = conn.execute(
        "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_date d "
        "ON f.order_date = d.date_key WHERE d.date_key IS NULL"
    ).fetchone()[0]
    print(f"\nReferential integrity check (should all be 0):")
    print(f"  orphan customer FKs: {orphan_customers}")
    print(f"  orphan product FKs:  {orphan_products}")
    print(f"  orphan date FKs:     {orphan_dates}")

    conn.commit()
    conn.close()
    print(f"\nSaved star schema to {DB_PATH}")


if __name__ == "__main__":
    main()
