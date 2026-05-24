-- ============================================================
-- BusinessVerse Database Schema
-- Creates tables for customers, products, and orders
-- ============================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS businessverse;
USE businessverse;

-- ─── Customers Table ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id       VARCHAR(10)    PRIMARY KEY,
    name              VARCHAR(100)   NOT NULL,
    email             VARCHAR(150)   UNIQUE NOT NULL,
    age               INT            CHECK (age BETWEEN 18 AND 100),
    region            VARCHAR(50)    NOT NULL,
    registration_date DATE           NOT NULL,
    purchase_frequency INT           DEFAULT 0,
    avg_order_value   DECIMAL(10,2)  DEFAULT 0.00,
    last_purchase_days_ago INT       DEFAULT 0,
    support_tickets   INT            DEFAULT 0,
    satisfaction_score INT           CHECK (satisfaction_score BETWEEN 1 AND 10),
    total_spent       DECIMAL(12,2)  DEFAULT 0.00,
    churn             TINYINT(1)     DEFAULT 0,
    created_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- ─── Products Table ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id       VARCHAR(10)    PRIMARY KEY,
    product_name     VARCHAR(150)   NOT NULL,
    category         VARCHAR(100)   NOT NULL,
    price            DECIMAL(10,2)  NOT NULL,
    cost             DECIMAL(10,2)  NOT NULL,
    profit_margin    DECIMAL(5,2)   NOT NULL,
    stock_quantity   INT            DEFAULT 0,
    supplier         VARCHAR(100),
    rating           DECIMAL(3,1)   CHECK (rating BETWEEN 0 AND 5),
    created_at       TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- ─── Orders Table ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id         VARCHAR(10)    PRIMARY KEY,
    customer_id      VARCHAR(10)    NOT NULL,
    product_id       VARCHAR(10)    NOT NULL,
    product_name     VARCHAR(150),
    category         VARCHAR(100),
    region           VARCHAR(50),
    order_date       DATE           NOT NULL,
    quantity         INT            NOT NULL DEFAULT 1,
    unit_price       DECIMAL(10,2)  NOT NULL,
    discount_pct     DECIMAL(5,2)   DEFAULT 0.00,
    total_amount     DECIMAL(12,2)  NOT NULL,
    cost             DECIMAL(12,2),
    profit           DECIMAL(12,2),
    payment_method   VARCHAR(50),
    status           VARCHAR(50)    DEFAULT 'Processing',
    created_at       TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)  REFERENCES products(product_id)   ON DELETE CASCADE
);

-- ─── Indexes for Performance ──────────────────────────────────────────────────
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_product  ON orders(product_id);
CREATE INDEX idx_orders_region   ON orders(region);
CREATE INDEX idx_orders_category ON orders(category);
CREATE INDEX idx_customers_region ON customers(region);

-- ============================================================
-- ANALYTICS VIEWS
-- ============================================================

-- Monthly Revenue View
CREATE OR REPLACE VIEW monthly_revenue AS
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    SUM(total_amount)                AS revenue,
    SUM(profit)                      AS profit,
    COUNT(*)                         AS order_count
FROM orders
WHERE status != 'Cancelled'
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;

-- Top Products View
CREATE OR REPLACE VIEW top_products AS
SELECT
    p.product_name,
    p.category,
    COUNT(o.order_id)     AS total_orders,
    SUM(o.quantity)       AS units_sold,
    SUM(o.total_amount)   AS revenue,
    SUM(o.profit)         AS profit,
    AVG(o.unit_price)     AS avg_price
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status != 'Cancelled'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC;

-- Region Sales View
CREATE OR REPLACE VIEW region_sales AS
SELECT
    region,
    COUNT(*)             AS total_orders,
    SUM(total_amount)    AS revenue,
    SUM(profit)          AS profit,
    AVG(total_amount)    AS avg_order_value
FROM orders
WHERE status != 'Cancelled'
GROUP BY region
ORDER BY revenue DESC;

-- Category Performance View
CREATE OR REPLACE VIEW category_performance AS
SELECT
    category,
    COUNT(*)             AS total_orders,
    SUM(total_amount)    AS revenue,
    SUM(profit)          AS profit,
    SUM(quantity)        AS units_sold,
    AVG(profit_margin_calc) AS avg_margin
FROM (
    SELECT
        o.category,
        o.order_id,
        o.total_amount,
        o.profit,
        o.quantity,
        CASE WHEN o.total_amount > 0 THEN (o.profit / o.total_amount * 100) ELSE 0 END AS profit_margin_calc
    FROM orders o
    WHERE o.status != 'Cancelled'
) sub
GROUP BY category
ORDER BY revenue DESC;

-- Customer Purchase Frequency
CREATE OR REPLACE VIEW customer_purchase_summary AS
SELECT
    c.customer_id,
    c.name,
    c.region,
    COUNT(o.order_id)   AS total_orders,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount) AS avg_order_value,
    MAX(o.order_date)   AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.region
ORDER BY total_spent DESC;

-- ============================================================
-- SAMPLE ANALYTICS QUERIES
-- ============================================================

-- 1. Top 10 Best Selling Products by Revenue
-- SELECT product_name, category, revenue, units_sold FROM top_products LIMIT 10;

-- 2. Monthly Revenue Trend
-- SELECT * FROM monthly_revenue ORDER BY month;

-- 3. Region-wise Sales Comparison
-- SELECT * FROM region_sales;

-- 4. Best Performing Category
-- SELECT * FROM category_performance;

-- 5. Customer Purchase Frequency
-- SELECT * FROM customer_purchase_summary LIMIT 20;

-- 6. Average Order Value by Payment Method
-- SELECT payment_method, AVG(total_amount) AS avg_order, COUNT(*) AS total_orders
-- FROM orders GROUP BY payment_method ORDER BY avg_order DESC;

-- 7. Year-over-Year Growth
-- SELECT YEAR(order_date) AS year, SUM(total_amount) AS revenue
-- FROM orders WHERE status != 'Cancelled' GROUP BY YEAR(order_date);
