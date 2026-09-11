# Run these cells in your Databricks notebook, one at a time (or all together).
# df is already loaded from the previous step.

# 1. Basic data quality checks -- flag nulls/negatives before trusting the data
from pyspark.sql.functions import col, when, sum as spark_sum, countDistinct

null_check = df.select([
    spark_sum(col(c).isNull().cast("int")).alias(c) for c in df.columns
])
display(null_check)  # should show 0 for every column if the data is clean

negative_check = df.filter((col("quantity") <= 0) | (col("revenue") <= 0))
print(f"Rows with invalid quantity/revenue: {negative_check.count()}")

# 2. Daily revenue by product and category
daily_product_revenue = (
    df.groupBy("date_id", "product_id", "product_name", "category")
      .agg(
          spark_sum("quantity").alias("total_quantity"),
          spark_sum("revenue").alias("total_revenue")
      )
      .orderBy("date_id")
)
display(daily_product_revenue)

# 3. Running total revenue per customer (using a window function)
from pyspark.sql.window import Window
from pyspark.sql.functions import sum as _sum

customer_window = Window.partitionBy("customer_id").orderBy("date_id") \
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)

customer_running_total = (
    df.withColumn("running_total_revenue", _sum("revenue").over(customer_window))
      .select("customer_id", "date_id", "revenue", "running_total_revenue")
      .orderBy("customer_id", "date_id")
)
display(customer_running_total)

# 4. Write curated output as a Delta table
daily_product_revenue.write.format("delta").mode("overwrite").saveAsTable("sales_curated_daily")
print("Saved sales_curated_daily as a Delta table.")

# Optional: also save the full cleaned fact table for downstream use
df.write.format("delta").mode("overwrite").saveAsTable("sales_fact_curated")
print("Saved sales_fact_curated as a Delta table.")
