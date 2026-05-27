# Enterprise Automated Dynamic Pricing Engine

A production-ready data product that combines a real-time relational analytics backend with an inline machine learning prediction system to dynamically calculate pricing elasticity and financial curves.

---

## System Architecture & Data Flow
1. **Ingestion Layer:** Constantly updates competitor prices, regional demand fluctuations, and direct warehouse stock status parameters.
2. **Database & Extraction Layer:** A **MySQL** instance handles data parsing. Leverages relational analytical schemas to isolate dynamic features.
3. **Machine Learning Model:** Features are fed into a live **Linear Regression model** to instantly isolate price elasticity metrics for individual items.
4. **Interactive Dashboard:** Built via **Streamlit** to generate dynamic charts for profit frontiers, giving operators a predictive workspace.

---

## Repository Structure

* `database_init.sql` — Relational schema declarations and downstream analytical views.
* `app.py` — Streamlit server presentation script and Scikit-Learn training loop execution.

---

## Future Enhancements Roadmap (SDE Track)
This system is intentionally designed to be modular so that its individual components can be easily refactored and scaled:
* **Dashboard Layer:** Migrating from basic layouts to a customizable grid system using custom CSS injections and individual state caching.
* **Database Scaling:** Transitioning the pipeline from a single local MySQL server to an asynchronous multi-node connection pool.
* **Predictive Complexity:** Upgrading the linear model to an ensemble regression network (e.g., LightGBM or XGBoost) to support complex seasonal trends.
