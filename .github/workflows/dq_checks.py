"""
Data quality checks against the warehouse. Run manually or as part of CI.
Exits with a non-zero status code if any check fails, so GitHub Actions
correctly reports the build as failed.
"""
import os
import sys
import psycopg2

PG_CONFIG = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=os.environ.get("PGPORT", "5432"),
    dbname=os.environ.get("PGDATABASE", "postgres"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ.get("PGPASSWORD", "admin12345"),
)

failures = []


def check(cur, description, query, expect_zero=True):
    cur.execute(query)
    result = cur.fetchone()[0]
    passed = (result == 0) if expect_zero else (result > 0)
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {description} -> {result}")
    if not passed:
        failures.append(description)


def main():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # 1. Row count sanity -- tables shouldn't be empty
    check(cur, "fact_sales has rows",
          "SELECT COUNT(*) FROM fact_sales", expect_zero=False)

    # 2. Null checks on critical columns
    check(cur, "No null product_id in fact_sales",
          "SELECT COUNT(*) FROM fact_sales WHERE product_id IS NULL")
    check(cur, "No null customer_id in fact_sales",
          "SELECT COUNT(*) FROM fact_sales WHERE customer_id IS NULL")

    # 3. Referential integrity -- every fact row should match a real dimension row
    check(cur, "No orphaned product_id in fact_sales",
          """SELECT COUNT(*) FROM fact_sales f
             LEFT JOIN dim_product p ON f.product_id = p.product_id
             WHERE p.product_id IS NULL""")
    check(cur, "No orphaned customer_id in fact_sales",
          """SELECT COUNT(*) FROM fact_sales f
             LEFT JOIN dim_customer c ON f.customer_id = c.customer_id
             WHERE c.customer_id IS NULL""")

    # 4. Business rule checks
    check(cur, "No negative or zero revenue",
          "SELECT COUNT(*) FROM fact_sales WHERE revenue <= 0")
    check(cur, "No negative or zero quantity",
          "SELECT COUNT(*) FROM fact_sales WHERE quantity <= 0")

    # 5. Duplicate check on dimension primary keys (shouldn't be possible with PK
    #    constraints, but useful as an explicit documented check)
    check(cur, "No duplicate product_id in dim_product",
          """SELECT COUNT(*) FROM (
                SELECT product_id FROM dim_product GROUP BY product_id HAVING COUNT(*) > 1
             ) t""")

    cur.close()
    conn.close()

    print(f"\n{len(failures)} check(s) failed out of {7}.")
    if failures:
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All data quality checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
