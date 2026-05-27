import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ==========================================
# 1. SYSTEM CONFIGURATION & DI
# ==========================================
st.set_page_config(page_title="Enterprise Pricing Engine", layout="wide")

# Replace with environment variables or external configuration paths in production
DATABASE_URI = 'mysql+pymysql://root:root@localhost/pricing_system'
engine = create_engine(DATABASE_URI)

# ==========================================
# 2. DATA ACCESS LAYER
# ==========================================
@st.cache_data(ttl=10)
def fetch_system_data():
    products = pd.read_sql_query("SELECT * FROM products", engine)
    metrics = pd.read_sql_query("SELECT * FROM v_pricing_metrics", engine)
    historical = pd.read_sql_query("SELECT * FROM historical_sales", engine)
    return products, metrics, historical

# ==========================================
# 3. CORE ANALYTICS & ML SERVICE
# ==========================================
def train_elasticity_model(historical_df, product_id):
    prod_hist = historical_df[historical_df['product_id'] == product_id]
    X = prod_hist[['price_charged']].values
    y = prod_hist['quantity_sold'].values
    
    model = LinearRegression()
    model.fit(X, y)
    return model, prod_hist, X

def compute_algorithmic_price(row, metrics_df):
    p_id = row['product_id']
    b_cost = row['base_cost']
    c_price = row['current_price']
    stock = row['current_stock']
    
    latest = metrics_df[metrics_df['product_id'] == p_id].sort_values(by='date', ascending=False).iloc[0]
    comp_price = latest['competitor_price']
    rolling_sales = latest['rolling_7d_avg_sales']
    
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

# ==========================================
# 4. STREAMLIT USER INTERFACE (FUTURE UPGRADE LAYER)
# ==========================================
st.title("🚀 Enterprise Dynamic Pricing & ML Demand Predictor")
st.markdown("Powered by a live **MySQL** backend and embedded **Scikit-Learn** predictive models.")

try:
    products_df, metrics_df, historical_df = fetch_system_data()
    
    # --- SIDEBAR CONTROL PANEL ---
    st.sidebar.header("🤖 ML Predictive Simulator")
    selected_prod_name = st.sidebar.selectbox("Select Product to Optimize", products_df['product_name'].unique())
    
    prod_row = products_df[products_df['product_name'] == selected_prod_name].iloc[0]
    model, prod_hist, X = train_elasticity_model(historical_df, prod_row['product_id'])
    
    simulated_price = st.sidebar.slider(
        f"Simulate New Price for {selected_prod_name}",
        float(round(prod_row['base_cost'] * 1.05, 2)),
        float(round(prod_row['current_price'] * 2.0, 2)),
        float(round(prod_row['current_price'], 2))
    )
    
    # ML Inference Execution
    predicted_qty = max(0, int(model.predict([[simulated_price]])[0]))
    predicted_revenue = predicted_qty * simulated_price
    predicted_profit = predicted_qty * (simulated_price - prod_row['base_cost'])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔮 ML Forecasted Metrics")
    st.sidebar.metric("Predicted Units Sold", f"{predicted_qty} units")
    st.sidebar.metric("Projected Total Revenue", f"${predicted_revenue:,.2f}")
    st.sidebar.metric("Projected Net Profit", f"${predicted_profit:,.2f}")

    # --- MAIN CONTROLS PANEL ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Managed Products", len(products_df))
    col2.metric("Critical Low-Stock Items", len(products_df[products_df['current_stock'] <= 5]))
    col3.metric("Overstocked Items", len(products_df[products_df['current_stock'] >= 40]))
    
    st.subheader("📋 Operational Control Board")
    recommendations = []
    for idx, row in products_df.iterrows():
        opt_price, strategy = compute_algorithmic_price(row, metrics_df)
        recommendations.append({
            'Product ID': row['product_id'],
            'Product Name': row['product_name'],
            'Stock': row['current_stock'],
            'Cost ($)': row['base_cost'],
            'Current Price ($)': round(row['current_price'], 2),
            'Optimized Price ($)': opt_price,
            'Strategy Applied': strategy
        })
    st.dataframe(pd.DataFrame(recommendations), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader(f"📈 Analytics Deep-Dive: {selected_prod_name}")
    left_chart, right_chart = st.columns(2)
    
    with left_chart:
        fig_scatter = px.scatter(prod_hist, x="price_charged", y="quantity_sold", title="Historical Sales vs Price")
        x_range = np.linspace(X.min(), X.max(), 100).reshape(-1, 1)
        fig_scatter.add_scatter(x=x_range.flatten(), y=model.predict(x_range), mode='lines', name='ML Demand Model', line=dict(color='red'))
        fig_scatter.add_scatter(x=[simulated_price], y=[predicted_qty], mode='markers', marker=dict(color='gold', size=15, symbol='star'), name='Your Simulation')
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with right_chart:
        sim_prices = np.linspace(prod_row['base_cost'], prod_row['current_price'] * 2, 50)
        pred_profits = [max(0, int(model.predict([[p]])[0])) * (p - prod_row['base_cost']) for p in sim_prices]
        fig_curve = px.line(x=sim_prices, y=pred_profits, title="Profit Optimization Frontier", labels={'x':'Price ($)', 'y':'Projected Profit ($)'})
        fig_curve.add_scatter(x=[simulated_price], y=[predicted_profit], mode='markers', marker=dict(color='gold', size=12), name='Simulated Target')
        st.plotly_chart(fig_curve, use_container_width=True)

except Exception as e:
    st.error(f"System Connection Wait state: Connecting to backend pipeline... ({e})")
