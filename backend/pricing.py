import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from backend.db import db_session

def train_elasticity_model(product_id: int):
    """
    Fetches historical sales for the product and fits a simple linear regression
    representing quantity_sold = intercept + slope * price_charged.
    """
    with db_session() as cursor:
        cursor.execute(
            "SELECT price_charged, quantity_sold FROM historical_sales WHERE product_id = %s",
            (product_id,)
        )
        rows = cursor.fetchall()
        
    if len(rows) < 5:
        # Fallback if insufficient data
        return None, 10, -0.05
        
    df = pd.DataFrame(rows)
    X = df[['price_charged']].values
    y = df['quantity_sold'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    return model, intercept, slope

def get_simulated_metrics(product_id: int, simulated_price: float):
    """
    Predicts sales quantity, revenue, and profit for a simulated price.
    """
    with db_session() as cursor:
        cursor.execute("SELECT base_cost, current_price FROM products WHERE product_id = %s", (product_id,))
        prod = cursor.fetchone()
        
    if not prod:
        return 0, 0.0, 0.0

    base_cost = float(prod['base_cost'])
    
    # Train model
    model, intercept, slope = train_elasticity_model(product_id)
    
    if model:
        predicted_qty = max(0, int(round(model.predict([[simulated_price]])[0])))
    else:
        # Simple rule-of-thumb demand calculation if model training failed
        price_diff = simulated_price - float(prod['current_price'])
        predicted_qty = max(0, int(round(10 - price_diff * 0.1)))

    revenue = round(predicted_qty * simulated_price, 2)
    profit = round(predicted_qty * (simulated_price - base_cost), 2)
    
    return predicted_qty, revenue, profit

def calculate_optimized_price(product_id: int):
    """
    Determines an algorithmic recommendation price for a product based on rules:
    - Scarcity Surge (+25% price) if stock <= 5
    - Competitor Match if competitor price is lower, down to floor of base_cost * 1.15
    - Liquidation (-15% discount) if stock >= 40 and rolling sales < 5
    - Absolute Floor of base_cost * 1.05
    """
    with db_session() as cursor:
        # Get product base stats
        cursor.execute(
            "SELECT product_id, product_name, base_cost, current_price, current_stock FROM products WHERE product_id = %s",
            (product_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None, "Product Not Found"
            
        # Get latest competitor intelligence
        cursor.execute(
            "SELECT competitor_price, rolling_7d_avg_sales FROM market_analytics WHERE product_id = %s ORDER BY capture_timestamp DESC LIMIT 1",
            (product_id,)
        )
        latest = cursor.fetchone()

    p_id = row['product_id']
    b_cost = float(row['base_cost'])
    c_price = float(row['current_price'])
    stock = row['current_stock']
    
    if latest:
        comp_price = float(latest['competitor_price'])
        rolling_sales = latest['rolling_7d_avg_sales']
    else:
        comp_price = c_price
        rolling_sales = 5

    proposed_price = c_price
    strategy = "Maintain Base Price"
    icon = "⚙️"
    
    if stock <= 5:
        proposed_price = c_price * 1.25
        strategy = "Scarcity Surge Pricing (+25%)"
        icon = "🚨"
    elif comp_price < c_price:
        floor_price = b_cost * 1.15
        proposed_price = max(comp_price - 0.99, floor_price)
        strategy = "Competitor Match Pricing"
        icon = "⚔️"
    elif stock >= 40 and rolling_sales < 5:
        proposed_price = c_price * 0.85
        strategy = "Inventory Liquidation Discount (-15%)"
        icon = "📦"
        
    proposed_price = max(proposed_price, b_cost * 1.05)
    return round(proposed_price, 2), f"{icon} {strategy}"
