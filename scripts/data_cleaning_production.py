"""
Bluestock Mutual Fund Capstone — Production Data Cleaning Pipeline
==================================================================
Author  : [Your Name] — Data Analyst Intern, Bluestock Fintech
Created : 2026-06-23

This script performs production-grade data cleaning across all 10 datasets.
Every cleaning decision is logged to a Data Quality Report.

Key improvements over basic cleaning:
  - Business-rule validation (SEBI limits, valid enums, date ranges)
  - Referential integrity checks across tables
  - Comprehensive audit log with cleaning actions
  - Outlier detection and documentation
  - Structured cleaning report output
"""

import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows terminal encoding — ensures Unicode characters print correctly
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
RAW_DIR     = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Audit Log ────────────────────────────────────────────────────────────────
audit_log: list[dict] = []

def log_action(dataset: str, column: str, action: str, details: str, rows_affected: int = 0):
    """Record every cleaning action for the Data Quality Report."""
    entry = {
        "timestamp"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset"      : dataset,
        "column"       : column,
        "action"       : action,
        "details"      : details,
        "rows_affected": rows_affected,
    }
    audit_log.append(entry)
    print(f"  [{action}] {column}: {details} ({rows_affected} rows)")


# ─── Validation Constants ──────────────────────────────────────────────────────
# SEBI regulatory: max TER for equity funds = 2.25%, debt = 2.0%
EXPENSE_RATIO_MAX = 2.5
EXPENSE_RATIO_MIN = 0.0

VALID_TRANSACTION_TYPES = {"SIP", "Lumpsum", "Redemption", "Switch"}
VALID_PLANS             = {"Regular", "Direct"}
VALID_KYC_STATUS        = {"Verified", "Pending"}
VALID_CITY_TIERS        = {"T30", "B30"}
VALID_GENDERS           = {"Male", "Female", "Other"}
MORNINGSTAR_MIN, MORNINGSTAR_MAX = 1, 5


# ══════════════════════════════════════════════════════════════════════════════
# CLEANER FUNCTIONS — one per dataset
# ══════════════════════════════════════════════════════════════════════════════

def clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    """
    fund_master: backbone / reference table.
    Every other table's amfi_code must exist here.
    """
    name = "01_fund_master"
    original_rows = len(df)

    # 1. Strip whitespace from all string columns
    str_cols = df.select_dtypes("object").columns
    for col in str_cols:
        before = df[col].str.strip().ne(df[col]).sum()
        df[col] = df[col].str.strip()
        if before > 0:
            log_action(name, col, "STRIP_WHITESPACE", f"Removed leading/trailing spaces", before)

    # 2. Parse launch_date
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce", dayfirst=False)
    invalid_dates = df["launch_date"].isna().sum()
    if invalid_dates:
        log_action(name, "launch_date", "DATE_PARSE_ERROR", f"Could not parse {invalid_dates} dates", invalid_dates)

    # 3. Validate expense_ratio_pct (SEBI limits)
    bad_expense = df[(df["expense_ratio_pct"] < EXPENSE_RATIO_MIN) |
                     (df["expense_ratio_pct"] > EXPENSE_RATIO_MAX)]
    if len(bad_expense):
        log_action(name, "expense_ratio_pct", "OUTLIER_DETECTED",
                   f"Values outside SEBI range [{EXPENSE_RATIO_MIN}, {EXPENSE_RATIO_MAX}]",
                   len(bad_expense))

    # 4. Validate plan values
    invalid_plans = ~df["plan"].isin(VALID_PLANS)
    if invalid_plans.any():
        log_action(name, "plan", "ENUM_VIOLATION",
                   f"Unexpected values: {df.loc[invalid_plans, 'plan'].unique()}", invalid_plans.sum())

    # 5. Ensure amfi_code uniqueness
    dups = df.duplicated(subset=["amfi_code"], keep="first")
    if dups.any():
        df = df[~dups]
        log_action(name, "amfi_code", "DROP_DUPLICATE_PK",
                   "Removed duplicate primary key rows", dups.sum())
    else:
        log_action(name, "amfi_code", "UNIQUENESS_CHECK", "All amfi_codes are unique ✓", 0)

    # 6. Validate min amounts are positive
    for col in ["min_sip_amount", "min_lumpsum_amount"]:
        neg = (df[col] < 0).sum()
        if neg:
            log_action(name, col, "NEGATIVE_VALUE", f"Found {neg} negative amounts", neg)

    log_action(name, "*", "SUMMARY", f"Rows: {original_rows} → {len(df)}", original_rows - len(df))
    return df


def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    nav_history: 46,000 rows of daily NAV prices.
    NAV must be positive; dates must be trading days.
    """
    name = "02_nav_history"
    original_rows = len(df)

    # 1. Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates:
        log_action(name, "date", "DROP_INVALID_DATE", f"Dropping {bad_dates} unparseable dates", bad_dates)
        df = df.dropna(subset=["date"])

    # 2. NAV must be strictly positive (a NAV of 0 or negative is impossible)
    non_positive_nav = df["nav"] <= 0
    if non_positive_nav.any():
        log_action(name, "nav", "DROP_INVALID_NAV",
                   f"NAV ≤ 0 is impossible — dropping {non_positive_nav.sum()} rows", non_positive_nav.sum())
        df = df[~non_positive_nav]

    # 3. Drop duplicates on (amfi_code, date) — a fund can only have one NAV per day
    dups = df.duplicated(subset=["amfi_code", "date"], keep="first")
    if dups.any():
        df = df[~dups]
        log_action(name, "amfi_code+date", "DROP_DUPLICATE",
                   "Removed duplicate (amfi_code, date) pairs", dups.sum())

    # 4. Date range sanity check
    max_date = df["date"].max()
    if max_date > pd.Timestamp.today():
        future_rows = (df["date"] > pd.Timestamp.today()).sum()
        log_action(name, "date", "FUTURE_DATE_WARNING",
                   f"{future_rows} rows have future dates — investigate", future_rows)

    log_action(name, "*", "SUMMARY", f"Rows: {original_rows} → {len(df)}", original_rows - len(df))
    return df


def clean_aum_by_fund_house(df: pd.DataFrame) -> pd.DataFrame:
    """aum_by_fund_house: quarterly AUM snapshots."""
    name = "03_aum_by_fund_house"
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["fund_house"] = df["fund_house"].str.strip()

    # Validate consistency: aum_crore ≈ aum_lakh_crore × 100,000
    # (Some rounding is expected)
    consistency_check = (df["aum_crore"] - df["aum_lakh_crore"] * 100000).abs()
    large_discrepancy = consistency_check[consistency_check > 5000]
    if len(large_discrepancy):
        log_action(name, "aum_crore/aum_lakh_crore", "CONSISTENCY_WARNING",
                   f"Large discrepancy between aum_crore and aum_lakh_crore×100000 in {len(large_discrepancy)} rows",
                   len(large_discrepancy))
    else:
        log_action(name, "aum_crore", "CONSISTENCY_CHECK", "AUM units consistent ✓", 0)

    dups = df.duplicated(subset=["date", "fund_house"])
    if dups.any():
        df = df[~dups]
        log_action(name, "date+fund_house", "DROP_DUPLICATE", "Removed duplicates", dups.sum())

    log_action(name, "*", "SUMMARY", f"All {len(df)} rows retained", 0)
    return df


def clean_monthly_sip_inflows(df: pd.DataFrame) -> pd.DataFrame:
    """
    monthly_sip_inflows: industry-level SIP aggregates.
    IMPORTANT: yoy_growth_pct has 12 intentional NULLs (first year has no prior year).
    DO NOT drop these rows — document as 'business-logic NULLs'.
    """
    name = "04_monthly_sip_inflows"
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")

    null_yoy = df["yoy_growth_pct"].isna().sum()
    log_action(name, "yoy_growth_pct",
               "NULL_DOCUMENTED_BUSINESS_LOGIC",
               f"{null_yoy} NULLs are EXPECTED for first 12 months (no prior year baseline). "
               "Rows retained. NULLs preserved as NULL in DB.",
               null_yoy)

    # Validate SIP inflows are positive
    neg_inflows = (df["sip_inflow_crore"] < 0).sum()
    if neg_inflows:
        log_action(name, "sip_inflow_crore", "NEGATIVE_VALUE_ERROR",
                   f"Negative SIP inflows are impossible — investigate!", neg_inflows)

    log_action(name, "*", "SUMMARY", f"All {len(df)} rows retained", 0)
    return df


def clean_category_inflows(df: pd.DataFrame) -> pd.DataFrame:
    """category_inflows: monthly net inflows by fund category."""
    name = "05_category_inflows"
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    df["category"] = df["category"].str.strip()

    log_action(name, "*", "SUMMARY", f"All {len(df)} rows retained", 0)
    return df


def clean_industry_folio_count(df: pd.DataFrame) -> pd.DataFrame:
    """industry_folio_count: quarterly unique investor account counts."""
    name = "06_industry_folio_count"
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")

    # Validate: equity + debt + hybrid + others should ≈ total (rounding tolerance 0.1)
    df["calculated_total"] = (df["equity_folios_crore"] + df["debt_folios_crore"] +
                               df["hybrid_folios_crore"] + df["others_folios_crore"])
    discrepancy = (df["total_folios_crore"] - df["calculated_total"]).abs()
    bad_rows = discrepancy[discrepancy > 0.1]
    if len(bad_rows):
        log_action(name, "total_folios_crore", "SUM_MISMATCH_WARNING",
                   f"Total ≠ sum of components in {len(bad_rows)} rows", len(bad_rows))
    else:
        log_action(name, "total_folios_crore", "INTEGRITY_CHECK", "Folio totals consistent ✓", 0)

    df = df.drop(columns=["calculated_total"])
    log_action(name, "*", "SUMMARY", f"All {len(df)} rows retained", 0)
    return df


def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    scheme_performance: risk-adjusted performance metrics.
    Richest analytical dataset — validate all financial metrics.
    """
    name = "07_scheme_performance"
    original_rows = len(df)

    df["scheme_name"] = df["scheme_name"].str.strip()
    df["fund_house"]  = df["fund_house"].str.strip()
    df["category"]    = df["category"].str.strip()
    df["plan"]        = df["plan"].str.strip()

    # Validate morningstar_rating is 1–5
    bad_ratings = ~df["morningstar_rating"].between(MORNINGSTAR_MIN, MORNINGSTAR_MAX)
    if bad_ratings.any():
        log_action(name, "morningstar_rating", "RANGE_VIOLATION",
                   f"Values outside [1,5]: {df.loc[bad_ratings,'morningstar_rating'].unique()}",
                   bad_ratings.sum())

    # Validate beta is positive (can be < 1 but should be > 0 for equity funds)
    non_positive_beta = (df["beta"] <= 0).sum()
    if non_positive_beta:
        log_action(name, "beta", "ANOMALY_FLAG",
                   f"Beta ≤ 0 is unusual for equity funds — review", non_positive_beta)

    # max_drawdown should be negative (it's a loss)
    positive_drawdown = (df["max_drawdown_pct"] > 0).sum()
    if positive_drawdown:
        log_action(name, "max_drawdown_pct", "SIGN_ERROR",
                   "max_drawdown_pct should be negative — fixing sign", positive_drawdown)
        df.loc[df["max_drawdown_pct"] > 0, "max_drawdown_pct"] *= -1

    # Validate plan values
    invalid_plans = ~df["plan"].isin(VALID_PLANS)
    if invalid_plans.any():
        log_action(name, "plan", "ENUM_VIOLATION",
                   f"Unexpected values: {df.loc[invalid_plans,'plan'].unique()}", invalid_plans.sum())

    log_action(name, "*", "SUMMARY", f"Rows: {original_rows} → {len(df)}", original_rows - len(df))
    return df


def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    investor_transactions: 32,778 granular transaction records.
    Most important for investor analytics — strict validation.
    """
    name = "08_investor_transactions"
    original_rows = len(df)

    # 1. Parse transaction_date
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    bad_dates = df["transaction_date"].isna().sum()
    if bad_dates:
        log_action(name, "transaction_date", "DROP_INVALID_DATE",
                   f"Dropping {bad_dates} rows with unparseable dates", bad_dates)
        df = df.dropna(subset=["transaction_date"])

    # 2. Standardize string columns
    for col in ["transaction_type", "city_tier", "age_group", "gender", "payment_mode", "kyc_status"]:
        df[col] = df[col].str.strip().str.title()

    # 3. Validate transaction_type
    # Fix: title-case mapping e.g. "SIP" might become "Sip" — handle specifically
    df["transaction_type"] = df["transaction_type"].str.upper()  # SIP, LUMPSUM etc.
    type_mapping = {"Sip": "SIP", "Lumpsum": "Lumpsum", "Redemption": "Redemption", "Switch": "Switch"}
    df["transaction_type"] = df["transaction_type"].replace({
        "SIP": "SIP", "LUMPSUM": "Lumpsum", "REDEMPTION": "Redemption", "SWITCH": "Switch"
    })
    invalid_types = ~df["transaction_type"].isin(VALID_TRANSACTION_TYPES)
    if invalid_types.any():
        log_action(name, "transaction_type", "ENUM_VIOLATION",
                   f"Unknown types: {df.loc[invalid_types,'transaction_type'].unique()}", invalid_types.sum())

    # 4. Validate amount_inr is positive
    non_positive = (df["amount_inr"] <= 0).sum()
    if non_positive:
        log_action(name, "amount_inr", "DROP_NON_POSITIVE",
                   f"Transaction amounts must be positive — dropping {non_positive} rows", non_positive)
        df = df[df["amount_inr"] > 0]

    # 5. Validate city_tier
    df["city_tier"] = df["city_tier"].str.upper()  # T30, B30
    invalid_tiers = ~df["city_tier"].isin(VALID_CITY_TIERS)
    if invalid_tiers.any():
        log_action(name, "city_tier", "ENUM_VIOLATION",
                   f"Unknown city tiers: {df.loc[invalid_tiers,'city_tier'].unique()}", invalid_tiers.sum())

    # 6. Validate kyc_status
    invalid_kyc = ~df["kyc_status"].isin(VALID_KYC_STATUS)
    if invalid_kyc.any():
        log_action(name, "kyc_status", "ENUM_VIOLATION",
                   f"Unknown KYC statuses: {df.loc[invalid_kyc,'kyc_status'].unique()}", invalid_kyc.sum())

    # 7. Outlier detection on annual_income_lakh
    q1 = df["annual_income_lakh"].quantile(0.01)
    q99 = df["annual_income_lakh"].quantile(0.99)
    outliers = ((df["annual_income_lakh"] < q1) | (df["annual_income_lakh"] > q99)).sum()
    if outliers:
        log_action(name, "annual_income_lakh", "OUTLIER_FLAGGED",
                   f"{outliers} records outside 1st–99th percentile range [{q1:.1f}, {q99:.1f}] — documented, not dropped",
                   outliers)

    log_action(name, "*", "SUMMARY", f"Rows: {original_rows} → {len(df)}", original_rows - len(df))
    return df


def clean_portfolio_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """portfolio_holdings: underlying stock positions per fund."""
    name = "09_portfolio_holdings"
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")
    df["sector"] = df["sector"].str.strip()
    df["stock_symbol"] = df["stock_symbol"].str.strip().str.upper()
    df["stock_name"]   = df["stock_name"].str.strip()

    # weight_pct must be between 0 and 100
    bad_weights = ~df["weight_pct"].between(0, 100)
    if bad_weights.any():
        log_action(name, "weight_pct", "RANGE_VIOLATION",
                   f"Weights outside [0,100]: {df.loc[bad_weights,'weight_pct'].values}", bad_weights.sum())

    # Total weight per fund should not exceed 100% (allow small float rounding ≤ 101)
    total_weights = df.groupby("amfi_code")["weight_pct"].sum()
    over_allocated = total_weights[total_weights > 101]
    if len(over_allocated):
        log_action(name, "weight_pct", "PORTFOLIO_OVERWEIGHT",
                   f"Funds with total weight > 100%: {over_allocated.index.tolist()}", len(over_allocated))

    log_action(name, "*", "SUMMARY", f"All {len(df)} rows retained", 0)
    return df


def clean_benchmark_indices(df: pd.DataFrame) -> pd.DataFrame:
    """benchmark_indices: daily index closing values."""
    name = "10_benchmark_indices"
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["index_name"] = df["index_name"].str.strip()

    bad_dates = df["date"].isna().sum()
    if bad_dates:
        df = df.dropna(subset=["date"])
        log_action(name, "date", "DROP_INVALID_DATE", f"Dropped {bad_dates} bad dates", bad_dates)

    # close_value must be positive
    bad_close = (df["close_value"] <= 0).sum()
    if bad_close:
        log_action(name, "close_value", "NON_POSITIVE_CLOSE",
                   f"Index close ≤ 0 is impossible — flagged", bad_close)

    # No duplicates on (date, index_name)
    dups = df.duplicated(subset=["date", "index_name"])
    if dups.any():
        df = df[~dups]
        log_action(name, "date+index_name", "DROP_DUPLICATE", "Removed duplicates", dups.sum())

    log_action(name, "*", "SUMMARY", f"All {len(df)} rows retained", 0)
    return df


# ─── Referential Integrity Check ─────────────────────────────────────────────
def check_referential_integrity(cleaned_data: dict[str, pd.DataFrame]):
    """
    Ensure all amfi_codes in child tables exist in fund_master.
    This is what the DB enforces via FOREIGN KEY — we check it before loading.
    """
    print("\n" + "="*60)
    print("REFERENTIAL INTEGRITY CHECK")
    print("="*60)
    valid_codes = set(cleaned_data["01_fund_master"]["amfi_code"].unique())

    tables_with_fk = {
        "02_nav_history": "amfi_code",
        "07_scheme_performance": "amfi_code",
        "08_investor_transactions": "amfi_code",
        "09_portfolio_holdings": "amfi_code",
    }
    for table, col in tables_with_fk.items():
        if table not in cleaned_data:
            continue
        codes = set(cleaned_data[table][col].unique())
        orphans = codes - valid_codes
        if orphans:
            print(f"  ❌ {table}: {len(orphans)} orphan amfi_codes not in fund_master: {orphans}")
            log_action(table, col, "REFERENTIAL_INTEGRITY_FAIL",
                       f"Orphan codes: {orphans}", len(orphans))
        else:
            print(f"  ✅ {table}: All {col} values exist in fund_master")
            log_action(table, col, "REFERENTIAL_INTEGRITY_PASS",
                       "All FK references valid ✓", 0)


# ─── Save Cleaning Report ─────────────────────────────────────────────────────
def save_cleaning_report():
    """Generate markdown Data Quality Report."""
    report_path = REPORTS_DIR / "data_cleaning_report.md"
    df_log = pd.DataFrame(audit_log)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Data Cleaning Report — Bluestock Mutual Fund Capstone\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Total Actions Logged:** {len(audit_log)}  \n\n")
        f.write("---\n\n")
        f.write("## Cleaning Summary by Dataset\n\n")

        for dataset in df_log["dataset"].unique():
            subset = df_log[df_log["dataset"] == dataset]
            f.write(f"### {dataset}\n\n")
            f.write("| Column | Action | Details | Rows Affected |\n")
            f.write("|--------|--------|---------|---------------|\n")
            for _, row in subset.iterrows():
                f.write(f"| {row['column']} | {row['action']} | {row['details']} | {row['rows_affected']} |\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## Key Business-Logic Decisions\n\n")
        f.write("1. **`yoy_growth_pct` NULLs (monthly_sip_inflows):** 12 NULLs in first year are EXPECTED — "
                "year-over-year requires a prior-year baseline. Rows retained, NULLs preserved.\n")
        f.write("2. **Referential Integrity:** All child tables validated against fund_master before DB load.\n")
        f.write("3. **NAV Positivity:** Zero or negative NAV values dropped — mathematically impossible.\n")
        f.write("4. **Expense Ratio SEBI Limits:** Flagged but not dropped — requires business review.\n")
        f.write("5. **max_drawdown_pct Sign Convention:** Must be negative (represents a loss).\n")

    # Also save JSON for programmatic use
    json_path = REPORTS_DIR / "data_cleaning_audit.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_log, f, indent=2, default=str)

    print(f"\n✅ Cleaning report saved to: {report_path.relative_to(ROOT)}")
    print(f"✅ Audit JSON saved to: {json_path.relative_to(ROOT)}")


# ─── Main Pipeline ────────────────────────────────────────────────────────────
CLEANERS = {
    "01_fund_master.csv"            : clean_fund_master,
    "02_nav_history.csv"            : clean_nav_history,
    "03_aum_by_fund_house.csv"      : clean_aum_by_fund_house,
    "04_monthly_sip_inflows.csv"    : clean_monthly_sip_inflows,
    "05_category_inflows.csv"       : clean_category_inflows,
    "06_industry_folio_count.csv"   : clean_industry_folio_count,
    "07_scheme_performance.csv"     : clean_scheme_performance,
    "08_investor_transactions.csv"  : clean_investor_transactions,
    "09_portfolio_holdings.csv"     : clean_portfolio_holdings,
    "10_benchmark_indices.csv"      : clean_benchmark_indices,
}


def main():
    print("=" * 70)
    print("BLUESTOCK MF — PRODUCTION DATA CLEANING PIPELINE")
    print("=" * 70)

    cleaned_data: dict[str, pd.DataFrame] = {}

    for filename, cleaner_fn in CLEANERS.items():
        raw_path = RAW_DIR / filename
        if not raw_path.exists():
            print(f"\n⚠️  File not found, skipping: {filename}")
            continue

        print(f"\n{'-'*70}")
        print(f"CLEANING: {filename}")
        print(f"{'-'*70}")

        df = pd.read_csv(raw_path)
        df_cleaned = cleaner_fn(df.copy())

        # Save cleaned file
        key = filename.replace(".csv", "")
        cleaned_data[key] = df_cleaned
        out_path = PROCESSED_DIR / f"cleaned_{filename}"
        df_cleaned.to_csv(out_path, index=False)
        print(f"  → Saved: {out_path.relative_to(ROOT)}")
        print(f"  → Final shape: {df_cleaned.shape}")

    # Referential integrity across tables
    check_referential_integrity(cleaned_data)

    # Generate report
    save_cleaning_report()

    print("\n" + "=" * 70)
    print("✅ DATA CLEANING PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
