import pytest
import sqlite3
import pandas as pd

def test_database_load():
    # Test in-memory SQLite DB creation and operations
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create table schema mockup
    cursor.execute("""
        CREATE TABLE fund_master (
            amfi_code INTEGER PRIMARY KEY,
            fund_house TEXT,
            category TEXT
        )
    """)
    
    # Insert mock records
    cursor.execute("INSERT INTO fund_master VALUES (119551, 'SBI Mutual Fund', 'Equity')")
    conn.commit()
    
    # Query database
    df = pd.read_sql_query("SELECT * FROM fund_master", conn)
    assert len(df) == 1
    assert df.iloc[0]["fund_house"] == "SBI Mutual Fund"
    assert df.iloc[0]["category"] == "Equity"
    
    conn.close()
