# 📊 BusinessVerse — Business Analytics Platform

A professional, end-to-end business analytics platform built with Python, Streamlit, SQL, and Machine Learning. Designed to help businesses analyze sales performance, customer behavior, product trends, and predict future outcomes.

---

## 🖥️ Screenshots

| Dashboard | Analytics | ML Predictions |
|-----------|-----------|----------------|
| KPI cards, revenue trends, top products | Sales trends, profit analysis, time series | Sales forecast, churn prediction, segmentation |

---

## ✨ Features

### 🔐 Authentication
- Session-based login with role management (Admin / Analyst / Viewer)
- Demo accounts included for quick access

### 📊 Dashboard
- 6 KPI cards: Revenue, Orders, Customers, Profit, Avg Order Value, Profit Margin
- Monthly revenue & profit trend chart
- Revenue by category (donut chart)
- Top 8 products by revenue (horizontal bar)
- Region-wise revenue comparison
- Order status & payment method breakdown
- Recent transactions table

### 📤 Data Upload
- Upload any CSV file
- Load built-in sample datasets (orders, customers, products)
- Dataset overview: rows, columns, missing values, duplicates, memory
- Preview, statistics, missing value report, column info tabs

### 🧹 Data Cleaning
- Drop null rows / fill with mean, median, mode, or zero
- Remove duplicate rows
- Convert column data types
- Feature selection (keep/drop columns)
- Before vs. after comparison panel
- Download cleaned CSV

### 🗄️ SQL Database
- Supports SQLite (default), MySQL, PostgreSQL
- One-click data load from CSV to DB
- Pre-built analytics queries with charts:
  - KPI summary
  - Monthly revenue trend
  - Top N products
  - Region-wise sales
  - Category performance
- Custom SQL query editor

### 📈 Analytics
- **Sales Trends**: Monthly trend, daily revenue, day-of-week analysis
- **Profit Analysis**: Revenue vs profit by category, margin %, scatter plot
- **Customer Analysis**: Region distribution, top customers, spend histogram
- **Product Analysis**: Units sold, top products, category trend over time
- **Time Series**: Daily/Weekly/Monthly/Quarterly with rolling average + range slider, QoQ comparison
- Global filters: Date range, Region, Category

### 🤖 ML Predictions
- **Sales Prediction** (Linear Regression): Lag features, forecast up to 12 months, R² & MAE metrics
- **Churn Prediction** (Random Forest): Confusion matrix, feature importance, probability distribution, single-customer predictor with gauge chart
- **Customer Segmentation** (K-Means): Auto-labeled segments, scatter plot, segment summary table
- All models saved with Joblib

### 📄 Reports & Exports
- Filter by period, region, category
- Download orders/customers/products as CSV or Excel
- Generate full analytics report (Excel with 5 sheets: KPIs, Monthly, Region, Category, Top Products)
- Export as JSON
- Download cleaned dataset

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.35 |
| Data | Pandas, NumPy |
| Charts | Plotly |
| ML | Scikit-learn, Joblib |
| Database | SQLite / MySQL / PostgreSQL |
| ORM | SQLAlchemy |
| Export | XlsxWriter, OpenPyXL |

---

## 📁 Project Structure

```
BusinessVerse/
│
├── data/                        # Generated CSV datasets
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
│
├── models/                      # Saved ML models (Joblib)
│   ├── sales_model.pkl
│   ├── churn_model.pkl
│   ├── churn_scaler.pkl
│   ├── kmeans_model.pkl
│   └── kmeans_scaler.pkl
│
├── sql/
│   └── schema.sql               # MySQL/PostgreSQL schema + views
│
├── notebooks/
│   └── exploration.ipynb        # EDA notebook
│
├── streamlit_app/
│   ├── .streamlit/
│   │   └── config.toml          # Theme & server config
│   ├── pages/
│   │   ├── Home.py              # Dashboard
│   │   ├── Data_Upload.py
│   │   ├── Data_Cleaning.py
│   │   ├── SQL_Database.py
│   │   ├── Analytics.py
│   │   ├── ML_Predictions.py
│   │   └── Reports.py
│   ├── utils/
│   │   ├── auth.py              # Authentication
│   │   ├── chart_helpers.py     # Plotly chart factory
│   │   ├── data_processing.py   # Cleaning utilities
│   │   └── db_connector.py      # SQLAlchemy connector
│   └── app.py                   # Entry point
│
├── generate_data.py             # Sample data generator
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Installation & Setup

### 1. Clone / Download the project

```bash
cd BusinessVerse
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate sample data

```bash
python generate_data.py
```

This creates `data/customers.csv`, `data/products.csv`, and `data/orders.csv` with:
- 500 customers
- 70 products across 7 categories
- 5,000 orders spanning 2022–2024

### 5. Run the app

```bash
cd streamlit_app
streamlit run app.py
```

Open your browser at **http://localhost:8501**

### 6. Login

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| analyst | analyst123 | Business Analyst |
| viewer | viewer123 | Viewer |

---

## 🗄️ Database Setup (Optional — MySQL/PostgreSQL)

By default the app uses **SQLite** (no setup needed).

To use MySQL or PostgreSQL:

1. Copy `.env.example` to `.env`
2. Fill in your database credentials:

```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=businessverse
DB_USER=root
DB_PASSWORD=yourpassword
```

3. For MySQL, run the schema first:

```bash
mysql -u root -p < sql/schema.sql
```

4. In the app, go to **SQL Database → Load Sample Data to DB**

---

## 🤖 Machine Learning Models

| Model | Algorithm | Target | Key Features |
|-------|-----------|--------|--------------|
| Sales Prediction | Linear Regression | Monthly Revenue | Month, Quarter, Year, Lag-1/2/3 |
| Churn Prediction | Random Forest | Churn (0/1) | Purchase frequency, avg spend, days inactive, support tickets, satisfaction |
| Segmentation | K-Means | Customer Segment | Total spent, frequency, avg order, days inactive, satisfaction |

Train models from the **ML Predictions** page. Models are saved to `models/` and persist across sessions.

---

## 📊 Sample Dataset Overview

| Dataset | Rows | Key Columns |
|---------|------|-------------|
| customers.csv | 500 | customer_id, name, region, churn, satisfaction_score, total_spent |
| products.csv | 70 | product_id, product_name, category, price, cost, profit_margin |
| orders.csv | 5,000 | order_id, customer_id, product_name, category, region, order_date, total_amount, profit, status |

---

## 🔮 Future Improvements

- [ ] JWT-based authentication with user registration
- [ ] Real-time data streaming with WebSockets
- [ ] Email report scheduling
- [ ] Advanced forecasting with Prophet / ARIMA
- [ ] PDF report export
- [ ] Multi-tenant support
- [ ] REST API layer (FastAPI)
- [ ] Docker containerization
- [ ] Cloud deployment (AWS / GCP / Azure)

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using Python & Streamlit*
