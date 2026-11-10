import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

DATE_COLUMNS = {
    "01_fund_master.csv": ["launch_date"],
    "02_nav_history.csv": ["date"],
    "03_aum_by_fund_house.csv": ["date"],
    "04_monthly_sip_inflows.csv": ["month"],
    "05_category_inflows.csv": ["month"],
    "06_industry_folio_count.csv": ["month"],
    "08_investor_transactions.csv": ["transaction_date"],
    "09_portfolio_holdings.csv": ["portfolio_date"],
    "10_benchmark_indices.csv": ["date"],
}

print("=" * 80)
print("DATA CLEANING SCRIPT")
print("=" * 80)

for raw_file in sorted(RAW_DIR.glob("*.csv")):
    df = pd.read_csv(raw_file)
    file_name = raw_file.name

    for column in DATE_COLUMNS.get(file_name, []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce", dayfirst=True)

    df = df.drop_duplicates()

    output_path = PROCESSED_DIR / f"cleaned_{file_name}"
    df.to_csv(output_path, index=False)

    print(f"Processed: {file_name}")
    print(f"  -> Saved to: {output_path.relative_to(ROOT)}")
    print(f"  -> Rows after cleaning: {len(df)}")

print("\n" + "=" * 80)
print("DATA CLEANING COMPLETE")
print("=" * 80)
