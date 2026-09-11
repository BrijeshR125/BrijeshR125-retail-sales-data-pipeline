# Natural-Language Sales Query Agent

Part of the end-to-end retail sales data pipeline project. This module lets a
user ask plain-English questions about the sales data and get back a SQL
query, the raw results, and a natural-language answer — powered by the
Claude API.

Currently wired to a local SQLite demo database so you can build and test
the agent immediately, without waiting on the full AWS/Databricks/Redshift
pipeline. Swap `run_sql()` in `agent.py` to point at Redshift or Postgres
once that part of the pipeline is ready — the prompting and safety logic
stay the same.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a Claude API key from https://console.anthropic.com and set it as an
   environment variable (never commit this to Git):
   ```
   export ANTHROPIC_API_KEY="your-key-here"
   ```

3. Build the demo database:
   ```
   python setup_sample_db.py
   ```

4. Run the CLI version to test quickly:
   ```
   python agent.py
   ```

5. Or run the full UI:
   ```
   streamlit run app.py
   ```

## How it works

1. `generate_sql()` sends the database schema + the user's question to
   Claude, asking for a SQL query only.
2. `is_safe_sql()` checks the returned query is a read-only `SELECT` —
   blocks `INSERT`/`UPDATE`/`DELETE`/`DROP`/etc. before anything runs.
3. `run_sql()` executes the query and returns a DataFrame.
4. `summarize_result()` sends the results back to Claude and asks for a
   short plain-English answer.

## Next steps (once your AWS/Databricks pipeline is built)

- Replace the SQLite connection in `run_sql()` with a Redshift connector
  (`redshift_connector` or `psycopg2` via the Redshift endpoint).
- Update `SCHEMA_DESCRIPTION` in `agent.py` to match your real star schema
  (fact_sales, dim_customer, dim_product, dim_date, dim_store).
- Add a few-shot example query or two to the prompt if generated SQL needs
  tuning for your actual schema's naming conventions.
