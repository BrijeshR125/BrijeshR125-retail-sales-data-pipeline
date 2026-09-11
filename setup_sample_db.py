"""
Creates a small demo SQLite database with a star-schema-style sales dataset.
This stands in for your real Redshift/Databricks warehouse so you can build
and test the NL query agent right away. Swap the connection layer later.
"""
import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "sales_demo.db"

PRODUCTS = [
    ("P1", "Wireless Mouse", "Electronics", 799),
    ("P2", "Office Chair", "Furniture", 5499),
    ("P3", "Notebook Pack", "Stationery", 199),
    ("P4", "LED Desk Lamp", "Electronics", 1299),
    ("P5", "Water Bottle", "Accessories", 349),
]

CUSTOMERS = [
    ("C1", "Ahmedabad", "Gujarat"),
    ("C2", "Bengaluru", "Karnataka"),
    ("C3", "Pune", "Maharashtra"),
    ("C4", "Delhi", "Delhi"),
    ("C5", "Hyderabad", "Telangana"),
]

def build():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS fact_sales;
    DROP TABLE IF EXISTS dim_product;
    DROP TABLE IF EXISTS dim_customer;
    DROP TABLE IF EXISTS dim_date;

    CREATE TABLE dim_product (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        unit_price INTEGER
    );

    CREATE TABLE dim_customer (
        customer_id TEXT PRIMARY KEY,
        city TEXT,
        state TEXT
    );

    CREATE TABLE dim_date (
        date_id TEXT PRIMARY KEY,
        day INTEGER,
        month INTEGER,
        year INTEGER
    );

    CREATE TABLE fact_sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_id TEXT,
        product_id TEXT,
        customer_id TEXT,
        quantity INTEGER,
        revenue INTEGER,
        FOREIGN KEY(date_id) REFERENCES dim_date(date_id),
        FOREIGN KEY(product_id) REFERENCES dim_product(product_id),
        FOREIGN KEY(customer_id) REFERENCES dim_customer(customer_id)
    );
    """)

    cur.executemany("INSERT INTO dim_product VALUES (?,?,?,?)", PRODUCTS)
    cur.executemany("INSERT INTO dim_customer VALUES (?,?,?)", CUSTOMERS)

    start = date(2026, 6, 1)
    dates = [start + timedelta(days=i) for i in range(90)]
    for d in dates:
        date_id = d.strftime("%Y%m%d")
        cur.execute("INSERT OR IGNORE INTO dim_date VALUES (?,?,?,?)",
                    (date_id, d.day, d.month, d.year))

    random.seed(42)
    for d in dates:
        date_id = d.strftime("%Y%m%d")
        for _ in range(random.randint(3, 8)):
            product = random.choice(PRODUCTS)
            customer = random.choice(CUSTOMERS)
            qty = random.randint(1, 5)
            revenue = qty * product[3]
            cur.execute(
                "INSERT INTO fact_sales (date_id, product_id, customer_id, quantity, revenue) "
                "VALUES (?,?,?,?,?)",
                (date_id, product[0], customer[0], qty, revenue)
            )

    conn.commit()
    conn.close()
    print(f"Demo database created at {DB_PATH}")

if __name__ == "__main__":
    build()
