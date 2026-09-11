"""
Natural-language query agent.

Flow:
  1. Send the DB schema + user's question to Claude, asking for a SQL query only.
  2. Validate the returned SQL is a safe, read-only SELECT.
  3. Execute it against the database.
  4. Send the results back to Claude and ask for a plain-English summary.

Swap `run_sql` and the schema string to point at Redshift/Databricks later —
everything else (prompting, safety checks, summarization) stays the same.
"""
import os
import re
import psycopg2
import pandas as pd
from anthropic import Anthropic

MODEL = "claude-sonnet-4-5"  # swap model name as needed

PG_CONFIG = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=os.environ.get("PGPORT", "5432"),
    dbname=os.environ.get("PGDATABASE", "postgres"),
    user=os.environ.get("PGUSER", "postgres"),
    password=os.environ.get("PGPASSWORD", "admin12345"),
)

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SCHEMA_DESCRIPTION = """
Tables:
- fact_sales(sale_id, date_id, product_id, customer_id, quantity, revenue)
- dim_product(product_id, product_name, category, unit_price)
- dim_customer(customer_id, city, state)
- dim_date(date_id, day, month, year)
- customer_segments(customer_id, total_revenue, segment)

date_id format is YYYYMMDD (text). Join fact_sales to dimension tables on the
matching *_id columns. customer_segments is a derived table with segment
values 'High', 'Medium', or 'Low'.
"""

BLOCKED_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]


def generate_sql(question: str) -> str:
    """Ask Claude to turn a natural-language question into a SQL query."""
    prompt = f"""You are a SQL generator for a PostgreSQL sales database.

{SCHEMA_DESCRIPTION}

Write a single SQL SELECT query that answers this question:
"{question}"

Rules:
- Return ONLY the SQL query, no explanation, no markdown formatting, no backticks.
- Only generate SELECT statements. Never modify data.
- Use standard PostgreSQL syntax.
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    sql = response.content[0].text.strip()
    # strip accidental markdown fences if the model adds them anyway
    sql = re.sub(r"^```sql|```$|^```", "", sql, flags=re.IGNORECASE).strip()
    return sql


def is_safe_sql(sql: str) -> bool:
    """Basic guardrail: block any statement that isn't a read-only SELECT."""
    upper = sql.upper()
    if not upper.strip().startswith("SELECT"):
        return False
    return not any(keyword in upper for keyword in BLOCKED_KEYWORDS)


def run_sql(sql: str) -> pd.DataFrame:
    """Execute SQL against the PostgreSQL warehouse. Swap PG_CONFIG for a
    Redshift connection (e.g. redshift_connector) if you move to Redshift later."""
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df


def summarize_result(question: str, df: pd.DataFrame) -> str:
    """Ask Claude to turn the raw result rows into a plain-English answer."""
    table_text = df.to_string(index=False) if not df.empty else "No rows returned."
    prompt = f"""The user asked: "{question}"

Here are the query results:
{table_text}

Write a short, clear, plain-English answer (2-3 sentences max) summarizing
what these results show. Mention specific numbers where relevant.
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def ask(question: str):
    """End-to-end: question -> SQL -> results -> summary. Returns all three."""
    sql = generate_sql(question)
    if not is_safe_sql(sql):
        return sql, None, "Blocked: generated query was not a safe read-only SELECT."
    df = run_sql(sql)
    summary = summarize_result(question, df)
    return sql, df, summary


if __name__ == "__main__":
    # quick CLI test
    q = input("Ask a question about the sales data: ")
    sql, df, summary = ask(q)
    print("\nGenerated SQL:\n", sql)
    print("\nResults:\n", df)
    print("\nSummary:\n", summary)
