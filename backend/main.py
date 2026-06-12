import os
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from backend.db import db_session
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user
from backend.pricing import calculate_optimized_price, get_simulated_metrics

app = FastAPI(title="Dynamic Pricing SaaS Engine")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Request schemas
class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "Manager"  # Manager or Admin

class UserLogin(BaseModel):
    username: str
    password: str

class PriceUpdateRequest(BaseModel):
    new_price: float
    strategy_applied: str

# ----------------- AUTH ENDPOINTS -----------------

@app.post("/api/auth/register")
def register(user: UserRegister):
    hashed_pwd = get_password_hash(user.password)
    try:
        with db_session() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (user.username, hashed_pwd, user.role)
            )
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username already exists or database error: {e}"
        )

@app.post("/api/auth/login")
def login(user: UserLogin, response: Response):
    with db_session() as cursor:
        cursor.execute("SELECT user_id, username, password_hash, role FROM users WHERE username = %s", (user.username,))
        db_user = cursor.fetchone()
        
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
        
    token = create_access_token(data={
        "sub": db_user["username"],
        "user_id": db_user["user_id"],
        "role": db_user["role"]
    })
    
    # Set HTTP-only cookie for vanilla JS authentication ease
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=False,  # Allow reading token from JS to set auth headers easily
        max_age=86400,
        samesite="lax"
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user["username"],
            "role": db_user["role"]
        }
    }

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
def me(current_user = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user["role"]
    }

# ----------------- BUSINESS ENDPOINTS -----------------

@app.get("/api/products")
def list_products(current_user = Depends(get_current_user)):
    with db_session() as cursor:
        cursor.execute("SELECT product_id, product_name, base_cost, current_price, current_stock FROM products")
        products = cursor.fetchall()
        
    results = []
    for p in products:
        opt_price, strategy = calculate_optimized_price(p["product_id"])
        p_dict = dict(p)
        p_dict["base_cost"] = float(p["base_cost"])
        p_dict["current_price"] = float(p["current_price"])
        p_dict["optimized_price"] = opt_price
        p_dict["recommended_strategy"] = strategy
        results.append(p_dict)
        
    return results

@app.post("/api/products/{product_id}/update-price")
def update_product_price(product_id: int, req: PriceUpdateRequest, current_user = Depends(get_current_user)):
    with db_session() as cursor:
        # Get original price
        cursor.execute("SELECT current_price FROM products WHERE product_id = %s", (product_id,))
        p = cursor.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Product not found")
        
        orig_price = float(p["current_price"])
        
        # Update product price
        cursor.execute(
            "UPDATE products SET current_price = %s WHERE product_id = %s",
            (req.new_price, product_id)
        )
        
        # Write to audit logs
        cursor.execute(
            "INSERT INTO audit_logs (product_id, user_id, action, original_price, new_price, strategy_applied) VALUES (%s, %s, %s, %s, %s, %s)",
            (product_id, current_user["user_id"], "Price Optimized", orig_price, req.new_price, req.strategy_applied)
        )
        
    return {"message": "Price updated and logged successfully"}

@app.get("/api/products/{product_id}/simulate")
def simulate_pricing(product_id: int, simulated_price: float, current_user = Depends(get_current_user)):
    qty, rev, profit = get_simulated_metrics(product_id, simulated_price)
    return {
        "product_id": product_id,
        "simulated_price": simulated_price,
        "predicted_quantity": qty,
        "predicted_revenue": rev,
        "predicted_profit": profit
    }

@app.get("/api/products/{product_id}/analytics")
def get_analytics(product_id: int, current_user = Depends(get_current_user)):
    with db_session() as cursor:
        cursor.execute(
            "SELECT competitor_price, rolling_7d_avg_sales, capture_timestamp FROM market_analytics WHERE product_id = %s ORDER BY capture_timestamp DESC LIMIT 15",
            (product_id,)
        )
        competitor_history = cursor.fetchall()
        
        cursor.execute(
            "SELECT price_charged, quantity_sold, sale_date FROM historical_sales WHERE product_id = %s ORDER BY sale_date DESC LIMIT 30",
            (product_id,)
        )
        sales_history = cursor.fetchall()
        
    # Formatting datetime fields
    comp_formatted = []
    for ch in competitor_history:
        c = dict(ch)
        c["competitor_price"] = float(ch["competitor_price"])
        c["capture_timestamp"] = ch["capture_timestamp"].strftime("%Y-%m-%d %H:%M")
        comp_formatted.append(c)
        
    sales_formatted = []
    for sh in sales_history:
        s = dict(sh)
        s["price_charged"] = float(sh["price_charged"])
        s["sale_date"] = sh["sale_date"].strftime("%Y-%m-%d")
        sales_formatted.append(s)
        
    return {
        "competitor_logs": comp_formatted,
        "sales_logs": sales_formatted
    }

@app.get("/api/logs")
def get_audit_logs(current_user = Depends(get_current_user)):
    with db_session() as cursor:
        cursor.execute("""
            SELECT l.log_id, l.original_price, l.new_price, l.strategy_applied, l.timestamp, p.product_name, u.username
            FROM audit_logs l
            JOIN products p ON l.product_id = p.product_id
            LEFT JOIN users u ON l.user_id = u.user_id
            ORDER BY l.timestamp DESC LIMIT 50
        """)
        logs = cursor.fetchall()
        
    formatted = []
    for log in logs:
        l = dict(log)
        l["original_price"] = float(log["original_price"])
        l["new_price"] = float(log["new_price"])
        l["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        formatted.append(l)
        
    return formatted

# ----------------- STATIC PAGE ROUTING -----------------

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/dashboard")
def read_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/history")
def read_history():
    return FileResponse("static/history.html")

# Serve stylesheets and scripts
app.mount("/static", StaticFiles(directory="static"), name="static")
