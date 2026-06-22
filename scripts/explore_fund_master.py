import pandas as pd

# Load fund master data
df = pd.read_csv('data/raw/01_fund_master.csv')

print("="*80)
print("FUND MASTER EXPLORATION")
print("="*80)

# 1. Unique Fund Houses
print("\n1. UNIQUE FUND HOUSES:")
print(df['fund_house'].unique())
print(f"Total: {df['fund_house'].nunique()}")

# 2. Unique Categories
print("\n" + "─"*80)
print("2. UNIQUE CATEGORIES:")
print(df['category'].unique())
print(f"Total: {df['category'].nunique()}")

# 3. Unique Sub-Categories
print("\n" + "─"*80)
print("3. UNIQUE SUB-CATEGORIES:")
print(df['sub_category'].unique())
print(f"Total: {df['sub_category'].nunique()}")

# 4. Unique Risk Grades
print("\n" + "─"*80)
print("4. UNIQUE RISK GRADES:")
print(df['risk_category'].unique())
print(f"Total: {df['risk_category'].nunique()}")

# 5. Category Count
print("\n" + "─"*80)
print("5. CATEGORY COUNT:")
print(df['category'].value_counts())

print("\n" + "="*80)
print("EXPLORATION COMPLETE")
print("="*80)