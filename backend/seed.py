import os
import pymysql
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "pricing_system")

def init_db():
    print("[SEED] Connecting to MySQL server to check/create database...")
    # Connect without database first
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()

    # Connect to the target database
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )
    cursor = conn.cursor()

    print("[SEED] Creating tables...")
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL
    )""")

    # 2. Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INT PRIMARY KEY,
        product_name VARCHAR(100) NOT NULL,
        base_cost DECIMAL(10,2) NOT NULL,
        current_price DECIMAL(10,2) NOT NULL,
        current_stock INT NOT NULL
    )""")

    # 3. Market Analytics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_analytics (
        analytics_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        competitor_price DECIMAL(10,2) NOT NULL,
        rolling_7d_avg_sales INT NOT NULL,
        capture_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    )""")

    # 4. Historical Sales table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historical_sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        price_charged DECIMAL(10,2) NOT NULL,
        quantity_sold INT NOT NULL,
        sale_date DATE NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    )""")

    # 5. Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        user_id INT NULL,
        action VARCHAR(100) NOT NULL,
        original_price DECIMAL(10,2) NOT NULL,
        new_price DECIMAL(10,2) NOT NULL,
        strategy_applied VARCHAR(255) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    )""")

    # Seeding Data
    cursor.execute("SELECT COUNT(*) AS count FROM products")
    if cursor.fetchone()[0] == 0:
        print("[SEED] Database is empty. Seeding mock data...")
        
        # Seed mock products
        products = [
            (101, "Titanium Smartwatch", 120.00, 199.99, 25),
            (102, "Wireless Noise-Canceling Headphones", 80.00, 149.99, 50),
            (103, "Premium Leather Messenger Bag", 45.00, 89.99, 4),  # Critical stock
            (104, "Ergonomic Office Chair", 110.00, 249.99, 3),    # Critical stock
            (105, "Mechanical Gaming Keyboard", 35.00, 79.99, 45)  # Overstocked
        ]
        cursor.executemany(
            "INSERT INTO products (product_id, product_name, base_cost, current_price, current_stock) VALUES (%s, %s, %s, %s, %s)",
            products
        )

        # Seed mock users (admin with password 'admin123', manager with password 'manager123')
        # We'll hash these inside auth later, but seed plain hashes (using bcrypt hash of 'admin123' and 'manager123')
        # Password 'admin123' hashed: $2b$12$R.S2uU6J/6m7z9/w6s8o.eeh.2/rS.H42o6O0107O.cTz0WJ5Fv12 (mock bcrypt)
        # We can just generate them programmatically for security, let's do it below using passlib or standard bcrypt
        import bcrypt
        admin_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        manager_hash = bcrypt.hashpw("manager123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("admin", admin_hash, "Admin"))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", ("manager", manager_hash, "Manager"))


        # Seed historical sales to construct demand curves
        # Product 101: Titanium Smartwatch (Base: 120, Current: 199.99)
        # Price range: 140 to 240. Sales follow negative slope.
        print("[SEED] Seeding historical sales logs...")
        sales_data = []
        analytics_data = []
        today = datetime.now().date()

        for prod_id, name, base_cost, cur_price, stock in products:
            # Let's create 30 days of sales
            for i in range(45):
                date_offset = today - timedelta(days=i)
                # Randomize price charged around base cost * 1.5
                price = round(random.uniform(base_cost * 1.1, base_cost * 2.2), 2)
                # Linear demand logic: quantity = Max_Qty - slope * price + noise
                # Max qty at cost: 15. Quantity decreases as price increases.
                optimal_markup = price / base_cost
                if optimal_markup <= 1.2:
                    qty = random.randint(12, 20)
                elif optimal_markup <= 1.5:
                    qty = random.randint(6, 12)
                elif optimal_markup <= 1.8:
                    qty = random.randint(2, 7)
                else:
                    qty = random.randint(0, 3)

                sales_data.append((prod_id, price, qty, date_offset))
            
            # Seed competitor analytics logs
            # Product competitor price fluctuates around our current price
            for i in range(10):
                timestamp = datetime.now() - timedelta(days=i, hours=random.randint(0, 23))
                comp_price = round(cur_price * random.uniform(0.85, 1.15), 2)
                rolling_sales = random.randint(3, 15)
                analytics_data.append((prod_id, comp_price, rolling_sales, timestamp))

        cursor.executemany(
            "INSERT INTO historical_sales (product_id, price_charged, quantity_sold, sale_date) VALUES (%s, %s, %s, %s)",
            sales_data
        )
        cursor.executemany(
            "INSERT INTO market_analytics (product_id, competitor_price, rolling_7d_avg_sales, capture_timestamp) VALUES (%s, %s, %s, %s)",
            analytics_data
        )

        print("[SEED] Seeding complete.")
    else:
        print("[SEED] Products already exist in database. Skipping seed.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()
