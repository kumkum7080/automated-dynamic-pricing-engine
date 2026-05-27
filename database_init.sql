-- Database Initialization Script
CREATE DATABASE IF NOT EXISTS pricing_system;
USE pricing_system;

-- 1. Base Products Infrastructure
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    base_cost DECIMAL(10,2),
    current_price DECIMAL(10,2),
    current_stock INT
);

-- 2. Competitor and Market Analytics Logs
CREATE TABLE IF NOT EXISTS market_analytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    competitor_price DECIMAL(10,2),
    rolling_7d_avg_sales INT,
    capture_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 3. Historical Sales Ledger for ML Demand Profiling
CREATE TABLE IF NOT EXISTS historical_sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    price_charged DECIMAL(10,2),
    quantity_sold INT,
    sale_date DATE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 4. Analytical Feature Engineering View
CREATE OR REPLACE VIEW v_pricing_metrics AS
SELECT 
    p.product_id,
    p.product_name,
    m.competitor_price,
    m.rolling_7d_avg_sales,
    m.capture_timestamp AS date
FROM products p
JOIN market_analytics m ON p.product_id = m.product_id;
