-- ============================================
-- Star Schema DDL for Sales Data Warehouse
-- Run this in DBeaver against sales_warehouse DB
-- ============================================

CREATE TABLE dim_product (
    product_id      VARCHAR(10) PRIMARY KEY,
    product_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL
);

CREATE TABLE dim_customer (
    customer_id     VARCHAR(10) PRIMARY KEY,
    city            VARCHAR(50) NOT NULL,
    state           VARCHAR(50) NOT NULL
);

CREATE TABLE dim_date (
    date_id         VARCHAR(8) PRIMARY KEY,   -- format YYYYMMDD
    day             INT NOT NULL,
    month           INT NOT NULL,
    year            INT NOT NULL
);

CREATE TABLE fact_sales (
    sale_id                 SERIAL PRIMARY KEY,
    date_id                 VARCHAR(8) REFERENCES dim_date(date_id),
    product_id              VARCHAR(10) REFERENCES dim_product(product_id),
    customer_id             VARCHAR(10) REFERENCES dim_customer(customer_id),
    quantity                INT NOT NULL CHECK (quantity > 0),
    revenue                 NUMERIC(12,2) NOT NULL CHECK (revenue >= 0)
);

-- Helpful indexes for query performance (a good keyword/skill to mention too)
CREATE INDEX idx_fact_sales_date ON fact_sales(date_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);
