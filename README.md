# 📊 Bluestock Mutual Fund Analytics Capstone Project

An end-to-end **Mutual Fund Analytics & Data Engineering** project built using **Python, Pandas, SQLAlchemy, SQLite, SQL, and Power BI**. This project demonstrates the complete data analytics lifecycle—from raw data ingestion and cleaning to database design, SQL analytics, and business intelligence dashboard preparation.

---

# 📌 Project Overview

The objective of this project is to build a production-ready data analytics pipeline for mutual fund data.

The project includes:

* Data Ingestion
* Data Cleaning & Validation
* Data Quality Assessment
* Data Dictionary Documentation
* SQLite Star Schema Design
* ETL Pipeline
* SQL Analytics
* Exploratory Data Analysis (EDA)
* Power BI Dashboard Preparation

---

# 🛠 Tech Stack

| Category        | Technology                  |
| --------------- | --------------------------- |
| Language        | Python 3                    |
| Data Processing | Pandas, NumPy               |
| Database        | SQLite                      |
| ORM             | SQLAlchemy                  |
| Visualization   | Matplotlib, Seaborn, Plotly |
| Notebook        | Jupyter Notebook            |
| SQL             | SQLite SQL                  |
| Version Control | Git & GitHub                |
| Dashboard       | Power BI                    |
| IDE             | VS Code                     |

---

# 📁 Project Structure

```text
bluestock_mf_capstone/
│
├── data/
│   ├── raw/
│   │   ├── 01_fund_master.csv
│   │   ├── 02_nav_history.csv
│   │   ├── 03_aum_by_fund_house.csv
│   │   ├── 04_monthly_sip_inflows.csv
│   │   ├── 05_category_inflows.csv
│   │   ├── 06_industry_folio_counts.csv
│   │   ├── 07_scheme_performance.csv
│   │   ├── 08_investor_transactions.csv
│   │   ├── 09_portfolio_holdings.csv
│   │   └── 10_benchmark_indices.csv
│   │
│   └── processed/
│       ├── 02_nav_history_clean.csv
│       ├── 07_scheme_performance_clean.csv
│       └── 08_investor_transactions_clean.csv
│
├── database/
│   └── mutual_fund.db
│
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda.ipynb
│   └── 04_visualizations.ipynb
│
├── reports/
│   ├── data_quality_report.md
│   ├── data_dictionary.md
│   ├── project_summary.md
│   └── final_report.pdf
│
├── scripts/
│   ├── data_ingestion.py
│   ├── data_cleaning.py
│   ├── validation.py
│   ├── setup_database.py
│   ├── load_database_production.py
│   ├── feature_engineering.py
│   └── utils.py
│
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_business_queries.sql
│   ├── 03_star_schema.sql
│   └── analytical_queries.sql
│
├── dashboard/
│   ├── Mutual_Fund_Dashboard.pbix
│   └── dashboard_screenshots/
│
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

# 📂 Dataset Description

| Dataset               | Description                                   |
| --------------------- | --------------------------------------------- |
| Fund Master           | Master information of all mutual fund schemes |
| NAV History           | Daily Net Asset Value history                 |
| AUM Data              | Assets Under Management by AMC                |
| SIP Inflows           | Monthly SIP investment data                   |
| Category Inflows      | Fund category inflows/outflows                |
| Folio Counts          | Industry-wide investor folios                 |
| Scheme Performance    | Historical fund returns and expense ratios    |
| Investor Transactions | SIP, Lumpsum and Redemption transactions      |
| Portfolio Holdings    | Scheme-wise portfolio allocation              |
| Benchmark Indices     | Benchmark market index performance            |

---

# 🔄 Project Workflow

```text
Raw CSV Data
        │
        ▼
Data Ingestion
        │
        ▼
Data Cleaning
        │
        ▼
Data Validation
        │
        ▼
Data Quality Report
        │
        ▼
SQLite Database
        │
        ▼
Star Schema Design
        │
        ▼
SQL Analytics
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Power BI Dashboard
```

---

# ✅ Data Cleaning

The cleaning pipeline performs:

* Missing value handling
* Duplicate removal
* Date parsing
* Data type conversion
* Transaction standardization
* NAV validation
* Expense ratio validation
* Business rule validation
* Data integrity checks

---

# 🗄 Database Schema

Dimension Tables

* dim_fund
* dim_date

Fact Tables

* fact_nav
* fact_transactions
* fact_performance
* fact_aum

---

# 📈 Analytical SQL Queries

Implemented queries include:

* Top 5 Funds by AUM
* Monthly Average NAV
* SIP Year-over-Year Growth
* Transactions by State
* Expense Ratio Analysis
* Top Performing Funds
* Redemption Trends
* Monthly Investment Trends
* AMC-wise AUM
* Average Transaction Value

---

# 📊 Dashboard KPIs

* Total Assets Under Management
* Monthly SIP Inflows
* Total Transactions
* Average NAV
* Top Performing Funds
* Expense Ratio Distribution
* Investor State Distribution
* Monthly Growth Trends

---

# ▶️ How to Run

## Clone Repository

```bash
git clone https://github.com/MALLAMPOLAIAHGANESH/bluestock-mutual-fund-analytics.git
cd bluestock-mutual-fund-analytics
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Data Cleaning

```bash
python scripts/data_cleaning.py
```

## Load SQLite Database

```bash
python scripts/load_database_production.py
```

## Execute SQL Queries

Open SQLite and execute the SQL scripts from the `sql/` directory.

---

# 📚 Documentation

* Data Dictionary
* Data Quality Report
* SQL Documentation
* Database Schema
* ETL Workflow
* Dashboard Documentation

---

# 🚀 Future Enhancements

* Automated ETL Pipeline
* Apache Airflow Integration
* PostgreSQL Migration
* Streamlit Dashboard
* Machine Learning-Based Fund Recommendation
* Real-Time NAV Updates
* API Integration
* Cloud Deployment

---

# 👨‍💻 Author

**Mallam Polaiah Ganesh**

Aspiring Data Analyst | Data Science Enthusiast | Python | SQL | Power BI | Machine Learning

GitHub: https://github.com/MALLAMPOLAIAHGANESH

LinkedIn: https://www.linkedin.com/in/mallam-polaiah-ganesh-b33748218/

---

# ⭐ If you found this project useful, consider giving the repository a star.
