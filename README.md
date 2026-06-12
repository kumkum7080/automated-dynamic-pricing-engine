#  AuraPrice | Enterprise Dynamic Pricing SaaS Engine

AuraPrice is a professional, production-ready corporate SaaS application that combines a real-time relational analytics backend with embedded machine learning demand prediction models. It features a modern light-mode marketing landing page, a live price elasticity simulator, and an authorized merchant dashboard.

---

##  Core Features

* **Public Interactive Elasticity Calculator**: Public guests can select catalog items and drag a price slider to see simulated sales quantities, gross revenues, and net profits. It draws **live Chart.js curves** of the demand and profit frontiers.
* **Role-Based JWT Authentication**: Secure merchant sign-up and login with custom `bcrypt` hashing (no `passlib` mixin dependencies) and HTTP-only JWT token authentication.
* **Merchant Control Board**: Authed pricing managers and admins can monitor stock statuses, review automatic heuristic suggestions (e.g. Scarcity Surge, Inventory Liquidation, Competitor Match), and apply optimizations with a single click.
* **Pricing Audit Trails**: A secure ledger records a chronological history of all price modifications, manual overrides, and strategy changes, showing the target item, original vs. new markup, user account, and time stamps.
* **Premium Corporate Light Theme**: Clean slate-grey off-white background (`#f8fafc`), white glassmorphic card containers, soft border styling, and professional emerald-to-teal green gradient controls.
* **Stock Market background doodles**: A custom canvas animation (`#bg-canvas`) drawing subtle scrolling price trendlines, grid ticks, drifting financial particles, and a crawling ticker tape of market data.

---

##  Technology Stack

* **Backend Framework**: Python 3.12+ with [FastAPI](https://fastapi.tiangolo.com/) for lightweight high-performance API endpoints and static page routing.
* **Database & Pools**: [MySQL](https://www.mysql.com/) database using raw, thread-safe connection pooling built with direct [PyMySQL](https://github.com/PyMySQL/PyMySQL) (intentionally built **without SQLAlchemy ORM** to avoid overhead).
* **Machine Learning**: [Scikit-Learn](https://scikit-learn.org/) Linear Regression models trained dynamically inside memory to fit demand curves ($Q = \alpha - \beta P$).
* **Frontend Design**: Plain, modular HTML5, Vanilla CSS3, and ES6 JavaScript (zero React/Vite/Tailwind dependencies) loaded with [Chart.js](https://www.chartjs.org/) for beautiful animations.

---

##  Repository Structure

```tree
├── backend/
│   ├── auth.py          # JWT creation, cookie token auth, and custom bcrypt hashing
│   ├── db.py            # Custom thread-safe pymysql connection pooling and session managers
│   ├── main.py          # FastAPI application initialization, API routes, and static page mounting
│   ├── pricing.py       # Scikit-learn demand regression models & rule-based heuristic pricing
│   └── seed.py          # Automated database schema creator and mock data seeder
├── static/
│   ├── css/
│   │   └── style.css    # Premium light corporate SaaS styling system
│   ├── js/
│   │   └── app.js       # Authentication logic, API fetch functions, and Chart.js integrations
│   ├── dashboard.html   # Merchant dashboard console
│   ├── history.html     # Chronological audit ledger view
│   └── index.html       # Landing page with public simulator and registration modal
├── .env.template        # Template for database credentials
├── .gitignore           # Excludes local environments and Pycaches
├── app.py               # Streamlit backup file
├── database_init.sql    # Relational schema declaration reference
└── README.md            # System documentation
```

---

##  Database Schema

* **`users`**: Manages authorized logins, role credentials (`Admin` or `Manager`), and password hashes.
* **`products`**: Catalog details, cost price margins, active sale prices, and stock inventory levels.
* **`historical_sales`**: 45 days of sales records (225+ logs generated programmatically) used to train regression curves.
* **`market_analytics`**: Trackers for competitor prices and rolling 7-day average sales velocity.
* **`audit_logs`**: Pricing alter ledger recording logs of optimizations and manual overrides.

---

##  Local Installation & Setup

### 1. Prerequisite Checklist
* Make sure you have **MySQL Server** installed and running on `localhost:3306`.
* Install **Python 3.12+** on your machine.

### 2. Configure Environment Secrets
Create a `.env` file at the root level using `.env.template` as a model:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD_HERE
DB_NAME=pricing_system
SECRET_KEY=YOUR_JWT_JWT_SECRET_KEY
```

### 3. Install Dependencies
Run the following pip commands to install the required libraries:
```bash
pip install fastapi uvicorn pymysql scikit-learn numpy bcrypt python-dotenv
```

### 4. Create Schemas & Seed Data
Execute the seeding script to initialize the database tables and populate them with the starter records (225 sales points, 50 market logs, and testing credentials):
```bash
python backend/seed.py
```

### 5. Launch the Server
Start the FastAPI uvicorn development server:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080 --reload
```

---

## 🔑 Default Sign-in Credentials

* **System Administrator**: Username: `admin` | Password: `admin123`
* **Pricing Manager**: Username: `manager` | Password: `manager123`
* *(You can also register a brand new account using the "Get Started" button in the navigation bar).*
