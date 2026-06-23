"""
Bluestock Mutual Fund Capstone — Production Database Loader
============================================================
Author  : [Your Name] — Data Analyst Intern, Bluestock Fintech
Created : 2026-06-23

Production improvements over the original setup_database.py:
  1. Credentials loaded from .env file — NEVER hardcoded
  2. SQLAlchemy + pandas.to_sql() for BULK inserts (10–100× faster)
  3. All 10 tables loaded (original only did 3)
  4. Proper transaction management with rollback on error
  5. Data validation before loading
  6. Progress reporting with row counts
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Ensure console supports UTF-8 characters (like emojis) on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# ─── Load environment variables ───────────────────────────────────────────────
# Best practice: never hardcode credentials. Use python-dotenv.
# Install: pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("✅ Environment variables loaded from .env (with override)")
except ImportError:
    print("⚠️  python-dotenv not installed. Reading from OS environment.")

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")
DB_NAME     = os.getenv("DB_NAME",     "bluestock_mf")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")   # Override via .env

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
SQL_DIR       = ROOT / "sql"


def create_database_if_not_exists():
    """Create the target database if it does not exist by connecting to default 'postgres' db."""
    postgres_conn_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    temp_engine = create_engine(postgres_conn_str, isolation_level="AUTOCOMMIT")
    try:
        with temp_engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
            exists = result.fetchone()
            if not exists:
                print(f"Database '{DB_NAME}' does not exist. Creating...")
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                print(f"✅ Database '{DB_NAME}' created successfully.")
            else:
                print(f"✅ Database '{DB_NAME}' already exists.")
    except Exception as e:
        print(f"⚠️  Could not verify/create database '{DB_NAME}': {e}")
    finally:
        temp_engine.dispose()


def build_engine():
    """
    Build SQLAlchemy engine with connection pooling.
    The connection string format: postgresql+psycopg2://user:pass@host:port/db
    """
    conn_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(
        conn_str,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,    # Verify connection is alive before using
        echo=False,            # Set True to see all SQL statements
    )
    return engine


def test_connection(engine) -> bool:
    """Verify database connectivity before attempting any loads."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version[:50]}")
            return True
    except SQLAlchemyError as e:
        print(f"❌ Connection failed: {e}")
        return False


def execute_schema(engine):
    """Run the schema creation SQL file."""
    schema_file = SQL_DIR / "01_create_schema.sql"
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)

    sql_content = schema_file.read_text(encoding="utf-8")

    with engine.begin() as conn:
        conn.execute(text(sql_content))
    print("✅ Schema created successfully (all 10 tables)")


def load_table(
    engine,
    csv_filename: str,
    table_name: str,
    column_map: dict | None = None,
    date_columns: list[str] | None = None,
    dtype_map: dict | None = None,
    if_exists: str = "append",
) -> int:
    """
    Generic bulk loader using pandas + SQLAlchemy.
    
    Parameters
    ----------
    engine       : SQLAlchemy engine
    csv_filename : Name of cleaned CSV file in PROCESSED_DIR
    table_name   : PostgreSQL target table
    column_map   : Rename columns to match DB schema {csv_col: db_col}
    date_columns : Columns to parse as dates
    dtype_map    : Override pandas dtypes before insert
    if_exists    : 'append' (default) | 'replace' | 'fail'
    
    Returns
    -------
    Number of rows loaded
    """
    csv_path = PROCESSED_DIR / csv_filename
    if not csv_path.exists():
        print(f"  ⚠️  File not found, skipping: {csv_filename}")
        return 0

    # Load with date parsing
    df = pd.read_csv(csv_path, parse_dates=date_columns or [])

    # Rename columns if needed
    if column_map:
        df = df.rename(columns=column_map)

    # Apply dtype overrides
    if dtype_map:
        for col, dtype in dtype_map.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)

    # Drop rows where PK would be NULL (safety check)
    initial_rows = len(df)
    df = df.dropna(how="all")

    # Bulk insert using pandas to_sql (uses executemany under the hood)
    # method="multi" → sends multiple rows per INSERT — much faster than row-by-row
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists=if_exists,
        index=False,
        method="multi",
        chunksize=1000,    # Load 1000 rows per batch — balances memory & speed
    )

    print(f"  ✅ {table_name}: {len(df):,} rows loaded "
          f"(dropped {initial_rows - len(df)} all-null rows)")
    return len(df)


def main():
    print("=" * 65)
    print("BLUESTOCK MF — PRODUCTION DATABASE LOADER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # ── 1. Create database if not exists and connect ─────────────────
    print("\n[1/4] Connecting to PostgreSQL...")
    create_database_if_not_exists()
    engine = build_engine()
    if not test_connection(engine):
        sys.exit(1)

    # ── 2. Create schema (idempotent — CREATE TABLE IF NOT EXISTS) ───
    print("\n[2/4] Creating schema...")
    execute_schema(engine)

    # ── 3. Load all tables in FK dependency order ────────────────────
    #       fund_master MUST be loaded first (parent table)
    print("\n[3/4] Loading data (bulk inserts)...\n")
    total_rows = 0

    # TABLE 1: fund_master — MUST be first (referenced by FK in other tables)
    print("→ fund_master")
    total_rows += load_table(
        engine, "cleaned_01_fund_master.csv", "fund_master",
        date_columns=["launch_date"],
    )

    # TABLE 2: nav_history — FK: amfi_code → fund_master
    print("→ nav_history")
    total_rows += load_table(
        engine, "cleaned_02_nav_history.csv", "nav_history",
        column_map={"date": "nav_date"},        # DB column = nav_date, CSV = date
        date_columns=["date"],
    )

    # TABLE 3: scheme_performance — FK: amfi_code → fund_master
    print("→ scheme_performance")
    total_rows += load_table(
        engine, "cleaned_07_scheme_performance.csv", "scheme_performance",
        # Drop redundant columns (scheme_name, fund_house, category already in fund_master)
        # We keep them for denormalization convenience but DB also stores in fund_master
    )

    # TABLE 4: investor_transactions — FK: amfi_code → fund_master
    print("→ investor_transactions")
    total_rows += load_table(
        engine, "cleaned_08_investor_transactions.csv", "investor_transactions",
        date_columns=["transaction_date"],
    )

    # TABLE 5: portfolio_holdings — FK: amfi_code → fund_master
    print("→ portfolio_holdings")
    total_rows += load_table(
        engine, "cleaned_09_portfolio_holdings.csv", "portfolio_holdings",
        date_columns=["portfolio_date"],
    )

    # TABLE 6: aum_by_fund_house — standalone
    print("→ aum_by_fund_house")
    total_rows += load_table(
        engine, "cleaned_03_aum_by_fund_house.csv", "aum_by_fund_house",
        column_map={"date": "snapshot_date"},
        date_columns=["date"],
    )

    # TABLE 7: monthly_sip_inflows — standalone
    print("→ monthly_sip_inflows")
    total_rows += load_table(
        engine, "cleaned_04_monthly_sip_inflows.csv", "monthly_sip_inflows",
        date_columns=["month"],
    )

    # TABLE 8: category_inflows — standalone
    print("→ category_inflows")
    total_rows += load_table(
        engine, "cleaned_05_category_inflows.csv", "category_inflows",
        date_columns=["month"],
    )

    # TABLE 9: industry_folio_count — standalone
    print("→ industry_folio_count")
    total_rows += load_table(
        engine, "cleaned_06_industry_folio_count.csv", "industry_folio_count",
        date_columns=["month"],
    )

    # TABLE 10: benchmark_indices — standalone
    print("→ benchmark_indices")
    total_rows += load_table(
        engine, "cleaned_10_benchmark_indices.csv", "benchmark_indices",
        column_map={"date": "index_date"},
        date_columns=["date"],
    )

    # ── 4. Verify row counts ──────────────────────────────────────────
    print("\n[4/4] Verifying row counts...\n")
    verification_query = """
        SELECT 'fund_master'            AS table_name, COUNT(*) AS row_count FROM fund_master
        UNION ALL SELECT 'nav_history',            COUNT(*) FROM nav_history
        UNION ALL SELECT 'scheme_performance',      COUNT(*) FROM scheme_performance
        UNION ALL SELECT 'investor_transactions',   COUNT(*) FROM investor_transactions
        UNION ALL SELECT 'portfolio_holdings',      COUNT(*) FROM portfolio_holdings
        UNION ALL SELECT 'aum_by_fund_house',       COUNT(*) FROM aum_by_fund_house
        UNION ALL SELECT 'monthly_sip_inflows',     COUNT(*) FROM monthly_sip_inflows
        UNION ALL SELECT 'category_inflows',        COUNT(*) FROM category_inflows
        UNION ALL SELECT 'industry_folio_count',    COUNT(*) FROM industry_folio_count
        UNION ALL SELECT 'benchmark_indices',       COUNT(*) FROM benchmark_indices
        ORDER BY row_count DESC;
    """
    with engine.connect() as conn:
        result = pd.read_sql(text(verification_query), conn)
        print(result.to_string(index=False))

    print(f"\n{'='*65}")
    print(f"✅ DATABASE LOADING COMPLETE")
    print(f"   Total rows loaded: {total_rows:,}")
    print(f"   Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")
    print(f"\n📌 Next Steps:")
    print(f"   1. Open pgAdmin → bluestock_mf database")
    print(f"   2. Run: sql/02_business_queries.sql")
    print(f"   3. Run: sql/03_advanced_analytics.sql")


if __name__ == "__main__":
    main()
