"""
BusinessVerse - Database Connector Utility
Handles SQL database connections and CRUD operations.
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# ─── Database Configuration ───────────────────────────────────────────────────
DB_CONFIG = {
    "type":     os.getenv("DB_TYPE",     "sqlite"),   # sqlite | mysql | postgresql
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "3306"),
    "database": os.getenv("DB_NAME",     "businessverse"),
    "username": os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}


@st.cache_resource(show_spinner=False)
def get_engine():
    """Create and return a SQLAlchemy engine (cached)."""
    db_type = DB_CONFIG["type"]
    
    if db_type == "sqlite":
        # Use absolute path so it works from any working directory
        db_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../data/businessverse.db")
        )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        url = f"sqlite:///{db_path}"
    elif db_type == "mysql":
        url = (
            f"mysql+pymysql://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
    elif db_type == "postgresql":
        url = (
            f"postgresql+psycopg2://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")
    
    engine = create_engine(url, echo=False, pool_pre_ping=True)
    return engine


def init_database(engine):
    """Create tables if they don't exist."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id       TEXT    PRIMARY KEY,
        name              TEXT,
        email             TEXT    UNIQUE,
        age               INTEGER,
        region            TEXT,
        registration_date TEXT,
        purchase_frequency INTEGER DEFAULT 0,
        avg_order_value   REAL    DEFAULT 0,
        last_purchase_days_ago INTEGER DEFAULT 0,
        support_tickets   INTEGER DEFAULT 0,
        satisfaction_score INTEGER,
        total_spent       REAL    DEFAULT 0,
        churn             INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id    TEXT  PRIMARY KEY,
        product_name  TEXT,
        category      TEXT,
        price         REAL,
        cost          REAL,
        profit_margin REAL,
        stock_quantity INTEGER DEFAULT 0,
        supplier      TEXT,
        rating        REAL
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id       TEXT  PRIMARY KEY,
        customer_id    TEXT,
        product_id     TEXT,
        product_name   TEXT,
        category       TEXT,
        region         TEXT,
        order_date     TEXT,
        quantity       INTEGER DEFAULT 1,
        unit_price     REAL,
        discount_pct   REAL    DEFAULT 0,
        total_amount   REAL,
        cost           REAL,
        profit         REAL,
        payment_method TEXT,
        status         TEXT
    );
    """
    with engine.connect() as conn:
        for statement in create_sql.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()


def load_csv_to_db(engine, customers_path, products_path, orders_path):
    """Load CSV files into the database."""
    customers_df = pd.read_csv(customers_path)
    products_df  = pd.read_csv(products_path)
    orders_df    = pd.read_csv(orders_path)
    
    customers_df.to_sql("customers", engine, if_exists="replace", index=False)
    products_df.to_sql("products",  engine, if_exists="replace", index=False)
    orders_df.to_sql("orders",    engine, if_exists="replace", index=False)
    
    return len(customers_df), len(products_df), len(orders_df)


# ─── Analytics Queries ────────────────────────────────────────────────────────

def query_monthly_revenue(engine):
    """Monthly revenue and profit totals."""
    sql = """
        SELECT
            SUBSTR(order_date, 1, 7) AS month,
            SUM(total_amount)        AS revenue,
            SUM(profit)              AS profit,
            COUNT(*)                 AS order_count
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY SUBSTR(order_date, 1, 7)
        ORDER BY month
    """
    return pd.read_sql(text(sql), engine)


def query_top_products(engine, limit=10):
    """Top products by revenue."""
    sql = f"""
        SELECT
            product_name,
            category,
            COUNT(order_id)     AS total_orders,
            SUM(quantity)       AS units_sold,
            ROUND(SUM(total_amount), 2) AS revenue,
            ROUND(SUM(profit), 2)       AS profit
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY product_name, category
        ORDER BY revenue DESC
        LIMIT {limit}
    """
    return pd.read_sql(text(sql), engine)


def query_region_sales(engine):
    """Sales breakdown by region."""
    sql = """
        SELECT
            region,
            COUNT(*)                    AS total_orders,
            ROUND(SUM(total_amount), 2) AS revenue,
            ROUND(SUM(profit), 2)       AS profit,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY region
        ORDER BY revenue DESC
    """
    return pd.read_sql(text(sql), engine)


def query_category_performance(engine):
    """Performance metrics by product category."""
    sql = """
        SELECT
            category,
            COUNT(*)                    AS total_orders,
            ROUND(SUM(total_amount), 2) AS revenue,
            ROUND(SUM(profit), 2)       AS profit,
            SUM(quantity)               AS units_sold
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY category
        ORDER BY revenue DESC
    """
    return pd.read_sql(text(sql), engine)


def query_customer_summary(engine):
    """Customer spending and purchase summary."""
    sql = """
        SELECT
            c.customer_id,
            c.name,
            c.region,
            c.churn,
            COUNT(o.order_id)           AS total_orders,
            ROUND(SUM(o.total_amount), 2) AS total_spent,
            ROUND(AVG(o.total_amount), 2) AS avg_order_value,
            MAX(o.order_date)           AS last_order_date
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.name, c.region, c.churn
        ORDER BY total_spent DESC
    """
    return pd.read_sql(text(sql), engine)


def query_kpis(engine):
    """Core KPI metrics."""
    sql = """
        SELECT
            ROUND(SUM(total_amount), 2) AS total_revenue,
            COUNT(*)                    AS total_orders,
            ROUND(SUM(profit), 2)       AS total_profit,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM orders
        WHERE status != 'Cancelled'
    """
    return pd.read_sql(text(sql), engine).iloc[0]


def query_recent_orders(engine, limit=10):
    """Recent orders for transactions table."""
    sql = f"""
        SELECT
            o.order_id,
            c.name   AS customer_name,
            o.product_name,
            o.category,
            o.region,
            o.order_date,
            o.total_amount,
            o.status
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
        LIMIT {limit}
    """
    return pd.read_sql(text(sql), engine)
