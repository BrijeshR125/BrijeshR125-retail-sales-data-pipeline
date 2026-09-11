-- ============================================
-- Stored Procedures / Functions for Sales Warehouse
-- Run against the 'postgres' database (where your tables live)
-- ============================================

-- 1. Function: running total revenue per customer, ordered by date
CREATE OR REPLACE FUNCTION get_customer_running_total(p_customer_id VARCHAR)
RETURNS TABLE (
    date_id VARCHAR,
    revenue NUMERIC,
    running_total NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.date_id,
        f.revenue,
        SUM(f.revenue) OVER (ORDER BY f.date_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
    FROM fact_sales f
    WHERE f.customer_id = p_customer_id
    ORDER BY f.date_id;
END;
$$ LANGUAGE plpgsql;

-- Usage: SELECT * FROM get_customer_running_total('C1');


-- 2. Function: category-level performance summary for a given month
CREATE OR REPLACE FUNCTION get_category_performance(p_year INT, p_month INT)
RETURNS TABLE (
    category VARCHAR,
    total_quantity BIGINT,
    total_revenue NUMERIC,
    avg_order_value NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.category,
        SUM(f.quantity) AS total_quantity,
        SUM(f.revenue) AS total_revenue,
        ROUND(AVG(f.revenue), 2) AS avg_order_value
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE d.year = p_year AND d.month = p_month
    GROUP BY p.category
    ORDER BY total_revenue DESC;
END;
$$ LANGUAGE plpgsql;

-- Usage: SELECT * FROM get_category_performance(2026, 6);


-- 3. Procedure: customer segmentation (High/Medium/Low value) as a materialized-style update
CREATE TABLE IF NOT EXISTS customer_segments (
    customer_id VARCHAR(10) PRIMARY KEY,
    total_revenue NUMERIC,
    segment VARCHAR(20)
);

CREATE OR REPLACE PROCEDURE refresh_customer_segments()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE customer_segments;

    INSERT INTO customer_segments (customer_id, total_revenue, segment)
    SELECT
        customer_id,
        SUM(revenue) AS total_revenue,
        CASE
            WHEN SUM(revenue) >= 20000 THEN 'High'
            WHEN SUM(revenue) >= 8000 THEN 'Medium'
            ELSE 'Low'
        END AS segment
    FROM fact_sales
    GROUP BY customer_id;

    RAISE NOTICE 'Customer segments refreshed.';
END;
$$;

-- Usage: CALL refresh_customer_segments();
--        SELECT * FROM customer_segments ORDER BY total_revenue DESC;
