import pandas as pd
import os
from pathlib import Path

# Get the path to the data/raw folder
script_dir = os.path.dirname(os.path.abspath(__file__))
raw_data_path = os.path.join(script_dir, '..', 'data', 'raw')

# List to store all data
data_files = {}

# Get all CSV files from data/raw
csv_files = sorted([f for f in os.listdir(raw_data_path) if f.endswith('.csv')])

print("="*80)
print("DATA INGESTION & ANALYSIS REPORT")
print("="*80)
print(f"\nTotal CSV files found: {len(csv_files)}\n")

# Load and analyze each CSV file
for i, file in enumerate(csv_files, 1):
    file_path = os.path.join(raw_data_path, file)
    df = pd.read_csv(file_path)
    data_files[file] = df
    
    print(f"\n{'─'*80}")
    print(f"FILE {i}: {file}")
    print(f"{'─'*80}")
    
    # 1. Shape (rows and columns)
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # 2. Column names
    print(f"\nColumn Names:")
    for col in df.columns:
        print(f"  - {col}")
    
    # 3. Data types
    print(f"\nData Types:")
    print(df.dtypes.to_string())
    
    # 4. First 5 rows
    print(f"\nFirst 5 Rows:")
    print(df.head())
    
    # 5. Missing values
    print(f"\nMissing Values:")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("  No missing values found ✓")
    else:
        for col, count in missing.items():
            if count > 0:
                percentage = (count / len(df)) * 100
                print(f"  - {col}: {count} ({percentage:.2f}%)")

print(f"\n{'='*80}")
print("DATA INGESTION COMPLETE")
print(f"{'='*80}\n")