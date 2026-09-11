"""
Connects to the local MinIO server using boto3 (the same library used for
real AWS S3) and uploads the sample sales data as a landing-zone file.

Run setup_sample_db.py first if you haven't, or generate a CSV export from
your sales_demo.db to use here.
"""
import boto3
import sqlite3
import pandas as pd
from io import StringIO

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin12345"
BUCKET_NAME = "sales-raw-data"

# Connect to MinIO using the same boto3 client used for real AWS S3 --
# only the endpoint_url differs.
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)


def create_bucket():
    existing = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if BUCKET_NAME not in existing:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")
    else:
        print(f"Bucket already exists: {BUCKET_NAME}")


def export_sales_to_csv():
    """Pull data out of the demo SQLite DB and turn it into a raw CSV,
    simulating a source system export landing in your data lake."""
    conn = sqlite3.connect("sales_demo.db")
    df = pd.read_sql_query("""
        SELECT f.sale_id, f.date_id, f.product_id, p.product_name, p.category,
               f.customer_id, c.city, c.state, f.quantity, f.revenue
        FROM fact_sales f
        JOIN dim_product p ON f.product_id = p.product_id
        JOIN dim_customer c ON f.customer_id = c.customer_id
    """, conn)
    conn.close()
    return df


def upload_csv(df, key="raw/sales_transactions.csv"):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=csv_buffer.getvalue())
    print(f"Uploaded {len(df)} rows to s3://{BUCKET_NAME}/{key}")


def list_bucket_contents():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    print("\nCurrent bucket contents:")
    for obj in response.get("Contents", []):
        print(f"  - {obj['Key']} ({obj['Size']} bytes)")


if __name__ == "__main__":
    create_bucket()
    df = export_sales_to_csv()
    upload_csv(df)
    list_bucket_contents()
