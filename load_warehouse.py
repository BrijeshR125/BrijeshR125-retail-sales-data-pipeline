"""
Loads dimension and fact data from the local sales_demo.db (SQLite) into
the PostgreSQL warehouse (star schema created via warehouse_schema.sql).

In a real pipeline this step would instead read from your curated Databricks
Delta tables -- here we read from SQLite directly since that's the easiest
consistent source across both local demo layers.
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

SQLITE_DB = "sales_demo.db"

PG_CONFIG = dict(
    host="localhost",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="admin12345",
)


def fetch_sqlite_table(cur, table, columns):
    cur.execute(f"SELECT {', '.join(columns)} FROM {table}")
    return cur.fetchall()


def main():
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cur = pg_conn.cursor()

    # --- dim_product ---
    rows = fetch_sqlite_table(sqlite_cur, "dim_product",
                               ["product_id", "product_name", "category", "unit_price"])
    execute_values(pg_cur,
        "INSERT INTO dim_product (product_id, product_name, category, unit_price) VALUES %s "
        "ON CONFLICT (product_id) DO NOTHING", rows)
    print(f"Loaded {len(rows)} rows into dim_product")

    # --- dim_customer ---
    rows = fetch_sqlite_table(sqlite_cur, "dim_customer",
                               ["customer_id", "city", "state"])
    execute_values(pg_cur,
        "INSERT INTO dim_customer (customer_id, city, state) VALUES %s "
        "ON CONFLICT (customer_id) DO NOTHING", rows)
    print(f"Loaded {len(rows)} rows into dim_customer")

    # --- dim_date ---
    rows = fetch_sqlite_table(sqlite_cur, "dim_date",
                               ["date_id", "day", "month", "year"])
    execute_values(pg_cur,
        "INSERT INTO dim_date (date_id, day, month, year) VALUES %s "
        "ON CONFLICT (date_id) DO NOTHING", rows)
    print(f"Loaded {len(rows)} rows into dim_date")

    # --- fact_sales ---
    rows = fetch_sqlite_table(sqlite_cur, "fact_sales",
                               ["date_id", "product_id", "customer_id", "quantity", "revenue"])
    execute_values(pg_cur,
        "INSERT INTO fact_sales (date_id, product_id, customer_id, quantity, revenue) VALUES %s",
        rows)
    print(f"Loaded {len(rows)} rows into fact_sales")

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    sqlite_conn.close()
    print("\nWarehouse load complete.")


if __name__ == "__main__":
    main()
