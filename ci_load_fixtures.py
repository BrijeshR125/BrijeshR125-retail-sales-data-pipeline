"""
Loads the CSV fixtures in /data into a Postgres database.
Used both by CI (GitHub Actions spins up a fresh Postgres each run) and
optionally locally if you want to reset your warehouse from clean fixtures.

Connection details are read from environment variables so the same script
works locally and in CI without code changes.
"""
import os
import csv
import psycopg2
from psycopg2.extras import execute_values

PG_CONFIG = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=os.environ.get("PGPORT", "5432"),
    dbname=os.environ.get("PGDATABASE", "postgres"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ.get("PGPASSWORD", "admin12345"),
)

TABLE_COLUMNS = {
    "dim_product": ["product_id", "product_name", "category", "unit_price"],
    "dim_customer": ["customer_id", "city", "state"],
    "dim_date": ["date_id", "day", "month", "year"],
    "fact_sales": ["date_id", "product_id", "customer_id", "quantity", "revenue"],
}


def load_csv(cur, table, path):
    columns = TABLE_COLUMNS[table]
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [tuple(row[c] for c in columns) for row in reader]

    col_list = ", ".join(columns)
    if table == "fact_sales":
        execute_values(cur, f"INSERT INTO {table} ({col_list}) VALUES %s", rows)
    else:
        pk = columns[0]
        execute_values(
            cur,
            f"INSERT INTO {table} ({col_list}) VALUES %s ON CONFLICT ({pk}) DO NOTHING",
            rows,
        )
    print(f"Loaded {len(rows)} rows into {table}")


def main():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    for table in ["dim_product", "dim_customer", "dim_date", "fact_sales"]:
        load_csv(cur, table, f"data/{table}.csv")

    conn.commit()
    cur.close()
    conn.close()
    print("CI data load complete.")


if __name__ == "__main__":
    main()
