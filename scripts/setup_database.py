"""
Setup PostgreSQL Database and Load Mutual Fund Data
This script creates tables and loads CSV data into PostgreSQL
"""

import pandas as pd
import psycopg2
from psycopg2 import sql
from pathlib import Path
import sys

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # Change this if your password is different
    'database': 'bluestock_mf'
}

def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        return conn
    except psycopg2.Error as e:
        print(f"Unable to connect to PostgreSQL: {e}")
        sys.exit(1)

def create_database():
    """Create the bluestock_mf database if it doesn't exist"""
    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP DATABASE IF EXISTS bluestock_mf;")
        cursor.execute("CREATE DATABASE bluestock_mf;")
        print("✓ Database 'bluestock_mf' created successfully")
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
    finally:
        cursor.close()
        conn.close()

def create_tables(cursor):
    """Create all required tables"""
    
    # Fund Master table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fund_master (
            amfi_code BIGINT PRIMARY KEY,
            scheme_name VARCHAR(500),
            fund_house VARCHAR(200),
            category VARCHAR(100),
            sub_category VARCHAR(100),
            risk_category VARCHAR(50),
            expense_ratio_pct FLOAT,
            min_sip_amount FLOAT,
            min_lumpsum_amount FLOAT,
            launch_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✓ Created fund_master table")
    
    # NAV History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nav_history (
            id SERIAL PRIMARY KEY,
            amfi_code BIGINT,
            nav FLOAT,
            date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (amfi_code) REFERENCES fund_master(amfi_code)
        );
    """)
    print("✓ Created nav_history table")
    
    # Scheme Performance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheme_performance (
            amfi_code BIGINT PRIMARY KEY,
            scheme_name VARCHAR(500),
            fund_house VARCHAR(200),
            category VARCHAR(100),
            plan VARCHAR(50),
            return_1yr_pct FLOAT,
            return_3yr_pct FLOAT,
            return_5yr_pct FLOAT,
            benchmark_3yr_pct FLOAT,
            alpha FLOAT,
            beta FLOAT,
            sharpe_ratio FLOAT,
            sortino_ratio FLOAT,
            std_dev_ann_pct FLOAT,
            max_drawdown_pct FLOAT,
            aum_crore FLOAT,
            expense_ratio_pct FLOAT,
            morningstar_rating INT,
            risk_grade VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (amfi_code) REFERENCES fund_master(amfi_code)
        );
    """)
    print("✓ Created scheme_performance table")

def load_data(cursor, processed_dir):
    """Load data from CSV files into tables"""
    
    # Load Fund Master
    print("\nLoading Fund Master...")
    fund_master_df = pd.read_csv(processed_dir / 'cleaned_01_fund_master.csv')
    for _, row in fund_master_df.iterrows():
        cursor.execute("""
            INSERT INTO fund_master 
            (amfi_code, scheme_name, fund_house, category, sub_category, 
             risk_category, expense_ratio_pct, min_sip_amount, min_lumpsum_amount, launch_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (amfi_code) DO NOTHING
        """, (
            int(row['amfi_code']),
            row['scheme_name'],
            row['fund_house'],
            row['category'],
            row['sub_category'],
            row['risk_category'],
            float(row['expense_ratio_pct']) if pd.notna(row['expense_ratio_pct']) else None,
            float(row['min_sip_amount']) if pd.notna(row['min_sip_amount']) else None,
            float(row['min_lumpsum_amount']) if pd.notna(row['min_lumpsum_amount']) else None,
            row['launch_date'] if pd.notna(row['launch_date']) else None
        ))
    print(f"✓ Loaded {len(fund_master_df)} fund master records")
    
    # Load NAV History
    print("Loading NAV History...")
    nav_history_df = pd.read_csv(processed_dir / 'cleaned_02_nav_history.csv')
    for _, row in nav_history_df.iterrows():
        cursor.execute("""
            INSERT INTO nav_history (amfi_code, nav, date)
            VALUES (%s, %s, %s)
        """, (
            int(row['amfi_code']),
            float(row['nav']) if pd.notna(row['nav']) else None,
            row['date'] if pd.notna(row['date']) else None
        ))
    print(f"✓ Loaded {len(nav_history_df)} NAV history records")
    
    # Load Scheme Performance
    print("Loading Scheme Performance...")
    performance_df = pd.read_csv(processed_dir / 'cleaned_07_scheme_performance.csv')
    for _, row in performance_df.iterrows():
        cursor.execute("""
            INSERT INTO scheme_performance 
            (amfi_code, scheme_name, fund_house, category, plan, 
             return_1yr_pct, return_3yr_pct, return_5yr_pct, benchmark_3yr_pct,
             alpha, beta, sharpe_ratio, sortino_ratio, std_dev_ann_pct, max_drawdown_pct,
             aum_crore, expense_ratio_pct, morningstar_rating, risk_grade)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (amfi_code) DO NOTHING
        """, (
            int(row['amfi_code']),
            row['scheme_name'],
            row['fund_house'],
            row['category'],
            row['plan'],
            float(row['return_1yr_pct']) if pd.notna(row['return_1yr_pct']) else None,
            float(row['return_3yr_pct']) if pd.notna(row['return_3yr_pct']) else None,
            float(row['return_5yr_pct']) if pd.notna(row['return_5yr_pct']) else None,
            float(row['benchmark_3yr_pct']) if pd.notna(row['benchmark_3yr_pct']) else None,
            float(row['alpha']) if pd.notna(row['alpha']) else None,
            float(row['beta']) if pd.notna(row['beta']) else None,
            float(row['sharpe_ratio']) if pd.notna(row['sharpe_ratio']) else None,
            float(row['sortino_ratio']) if pd.notna(row['sortino_ratio']) else None,
            float(row['std_dev_ann_pct']) if pd.notna(row['std_dev_ann_pct']) else None,
            float(row['max_drawdown_pct']) if pd.notna(row['max_drawdown_pct']) else None,
            float(row['aum_crore']) if pd.notna(row['aum_crore']) else None,
            float(row['expense_ratio_pct']) if pd.notna(row['expense_ratio_pct']) else None,
            int(row['morningstar_rating']) if pd.notna(row['morningstar_rating']) else None,
            row['risk_grade']
        ))
    print(f"✓ Loaded {len(performance_df)} performance records")

def create_indexes(cursor):
    """Create indexes for better query performance"""
    cursor.execute("CREATE INDEX idx_nav_amfi_date ON nav_history(amfi_code, date);")
    cursor.execute("CREATE INDEX idx_fund_category ON fund_master(category);")
    cursor.execute("CREATE INDEX idx_perf_category ON scheme_performance(category);")
    print("✓ Created indexes for better performance")

def main():
    # Get processed data directory
    root = Path(__file__).parent.parent
    processed_dir = root / 'data' / 'processed'
    
    if not processed_dir.exists():
        print(f"Error: Processed data directory not found: {processed_dir}")
        sys.exit(1)
    
    print("Starting database setup...\n")
    
    # Create database
    create_database()
    
    # Connect to the new database
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        # Create tables
        print("\nCreating tables...")
        create_tables(cursor)
        conn.commit()
        
        # Load data
        print("\nLoading data...")
        load_data(cursor, processed_dir)
        conn.commit()
        
        # Create indexes
        print("\nCreating indexes...")
        create_indexes(cursor)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*50)
        print("✓ Database setup complete!")
        print("="*50)
        print("\nDatabase: bluestock_mf")
        print("Host: localhost:5432")
        print("User: postgres")
        print("\nYou can now:")
        print("1. Open pgAdmin4 to manage the database")
        print("2. Run SQL queries for analysis")
        print("3. Connect with Python using psycopg2")
        
    except psycopg2.Error as e:
        print(f"Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
