import pandas as pd

# Load the two CSV files
fund_master = pd.read_csv('data/raw/01_fund_master.csv')
nav_history = pd.read_csv('data/raw/02_nav_history.csv')

# Get AMFI codes from both files
fund_amfi_codes = set(fund_master['amfi_code'].astype(str))
nav_amfi_codes = set(nav_history['amfi_code'].astype(str))

# Find missing codes
missing_codes = sorted(fund_amfi_codes - nav_amfi_codes)

print("="*80)
print("AMFI CODE VALIDATION")
print("="*80)

print(f"\nTotal AMFI codes in fund master: {len(fund_amfi_codes)}")
print(f"Total AMFI codes in nav history: {len(nav_amfi_codes)}")

if missing_codes:
    print(f"\nMissing codes found: {len(missing_codes)}")
    print("Missing codes:")
    for code in missing_codes:
        print(f"  - {code}")
else:
    print("\nNo missing AMFI codes found.")

print("\n" + "="*80)
print("VALIDATION COMPLETE")
print("="*80)