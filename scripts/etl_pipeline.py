"""
etl_pipeline.py
===============
Bluestock Mutual Fund Capstone — Full ETL Pipeline
Author  : MALLAM POLAIAH GANESH — Data Analyst Intern, Bluestock Fintech

Pipeline Stages
---------------
  1. Extract   — Load all 10 raw CSVs using pathlib (no hardcoded paths)
  2. Transform — Type coercion, date parsing, NAV gap-fill, duplicate removal
  3. Validate  — Null checks, range checks, referential integrity
  4. Load      — Bulk insert into SQLite via pandas.to_sql() (WAL mode)
  5. Report    — Row counts, timing, JSON audit log

Common mistakes avoided
-----------------------
  * Paths  : pathlib.Path(__file__).parent — never os.getcwd()
  * CAGR   : annualised with 252 trading days, not calendar days
  * NAV    : ffill() after reindexing to full weekday date range
  * Units  : column names include units (e.g. aum_crore, amount_inr)
  * Secrets: no hardcoded credentials (SQLite needs none)

Usage
-----
  py scripts/etl_pipeline.py               # full pipeline
  py scripts/etl_pipeline.py --dry-run     # validate only, no DB write
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths (all derived from __file__ — portable) ─────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
RAW        = ROOT / "data" / "raw"
PROCESSED  = ROOT / "data" / "processed"
REPORTS    = ROOT / "reports"
DB_PATH    = ROOT / "data" / "bluestock_mf.db"

REPORTS.mkdir(exist_ok=True)
PROCESSED.mkdir(exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(REPORTS / "etl_pipeline.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── Audit accumulator ─────────────────────────────────────────────────────────
audit = {"started_at": datetime.now().isoformat(), "stages": {}}

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — EXTRACT
# ─────────────────────────────────────────────────────────────────────────────
def extract() -> dict:
    """Load all 10 raw CSV files. Returns {table_name: DataFrame}."""
    log.info("=" * 60)
    log.info("STAGE 1 — EXTRACT")
    log.info("=" * 60)

    file_map = {
        "fund_master"          : "01_fund_master.csv",
        "nav_history"          : "02_nav_history.csv",
        "aum_by_fund_house"    : "03_aum_by_fund_house.csv",
        "monthly_sip_inflows"  : "04_monthly_sip_inflows.csv",
        "category_inflows"     : "05_category_inflows.csv",
        "industry_folio_count" : "06_industry_folio_count.csv",
        "scheme_performance"   : "07_scheme_performance.csv",
        "investor_transactions": "08_investor_transactions.csv",
        "portfolio_holdings"   : "09_portfolio_holdings.csv",
        "benchmark_indices"    : "10_benchmark_indices.csv",
    }

    frames = {}
    for table, fname in file_map.items():
        path = RAW / fname
        if not path.exists():
            # Fall back to processed if raw missing
            path = PROCESSED / fname
        if not path.exists():
            log.warning("  SKIP  %s — file not found: %s", table, fname)
            continue
        df = pd.read_csv(path, low_memory=False)
        frames[table] = df
        log.info("  OK    %-28s  %6d rows  %d cols", table, len(df), len(df.columns))

    audit["stages"]["extract"] = {t: len(df) for t, df in frames.items()}
    return frames

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — TRANSFORM
# ─────────────────────────────────────────────────────────────────────────────
def _clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    """Clean fund_master: types, categories, units."""
    df = df.copy()
    df["amfi_code"]          = pd.to_numeric(df["amfi_code"], errors="coerce").astype("Int64")
    df["launch_date"]        = pd.to_datetime(df["launch_date"], errors="coerce")
    df["expense_ratio_pct"]  = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")
    df["exit_load_pct"]      = pd.to_numeric(df["exit_load_pct"], errors="coerce").fillna(0)
    df["min_sip_amount"]     = pd.to_numeric(df["min_sip_amount"], errors="coerce")
    df["min_lumpsum_amount"] = pd.to_numeric(df["min_lumpsum_amount"], errors="coerce")
    df["risk_category"]      = df.get("risk_category", df.get("risk_grade", pd.Series(dtype=str)))
    df = df.drop_duplicates(subset=["amfi_code"])
    df["launch_date"]        = df["launch_date"].dt.strftime("%Y-%m-%d")
    return df.reset_index(drop=True)


def _clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean nav_history.
    Key: ffill() after reindexing to full weekday range — handles gaps/holidays.
    """
    df = df.copy()
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce").astype("Int64")
    df["date"]      = pd.to_datetime(df["date"], errors="coerce")
    df["nav"]       = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["amfi_code", "date", "nav"])
    df = df[df["nav"] > 0]                   # remove zero/negative NAV
    df = df.drop_duplicates(subset=["amfi_code", "date"])

    # Forward-fill over weekday gaps (holidays, missing submissions)
    parts = []
    for code, grp in df.groupby("amfi_code"):
        grp = grp.set_index("date").sort_index()
        full_idx = pd.date_range(grp.index.min(), grp.index.max(), freq="B")  # business days
        grp = grp.reindex(full_idx)
        grp["nav"] = grp["nav"].ffill()
        grp["amfi_code"] = code
        grp = grp.reset_index().rename(columns={"index": "date"})
        parts.append(grp)

    out = pd.concat(parts, ignore_index=True)
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def _clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce").astype("Int64")
    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "aum_crore", "expense_ratio_pct",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates(subset=["amfi_code"])
    return df.reset_index(drop=True)


def _clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount_inr"]       = pd.to_numeric(df["amount_inr"], errors="coerce")
    df["amfi_code"]        = pd.to_numeric(df["amfi_code"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["investor_id", "transaction_date", "amount_inr"])
    df = df[df["amount_inr"] > 0]            # remove non-positive amounts
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates()
    return df.reset_index(drop=True)


def _clean_benchmark_indices(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Column may be named 'close_value' or 'value' depending on source
    if "close_value" in df.columns and "value" not in df.columns:
        df = df.rename(columns={"close_value": "value"})
    df["date"]  = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    df = df[df["value"] > 0]
    df = df.drop_duplicates(subset=["index_name", "date"])

    # ffill per index over weekday gaps
    parts = []
    for idx_name, grp in df.groupby("index_name"):
        grp = grp.set_index("date").sort_index()
        full_idx = pd.date_range(grp.index.min(), grp.index.max(), freq="B")
        grp = grp.reindex(full_idx)
        grp["value"] = grp["value"].ffill()
        grp["index_name"] = idx_name
        grp = grp.reset_index().rename(columns={"index": "date"})
        parts.append(grp)

    out = pd.concat(parts, ignore_index=True)
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def _generic_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Default cleaner: strip strings, parse obvious date columns."""
    df = df.copy()
    for col in df.select_dtypes("object").columns:
        df[col] = df[col].str.strip()
    for col in df.columns:
        if "date" in col.lower() or "month" in col.lower():
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notna().mean() > 0.5:
                df[col] = converted.dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates()
    return df.reset_index(drop=True)


CLEANERS = {
    "fund_master"          : _clean_fund_master,
    "nav_history"          : _clean_nav_history,
    "scheme_performance"   : _clean_scheme_performance,
    "investor_transactions": _clean_investor_transactions,
    "benchmark_indices"    : _clean_benchmark_indices,
}


def transform(frames: dict) -> dict:
    """Apply table-specific cleaners; fall back to generic cleaner."""
    log.info("=" * 60)
    log.info("STAGE 2 — TRANSFORM")
    log.info("=" * 60)

    cleaned = {}
    for table, df in frames.items():
        cleaner = CLEANERS.get(table, _generic_clean)
        try:
            out = cleaner(df)
            log.info("  OK    %-28s  %6d -> %6d rows", table, len(df), len(out))
            cleaned[table] = out
        except Exception as exc:
            log.error("  FAIL  %s — %s", table, exc)
            cleaned[table] = df  # use raw on failure

    audit["stages"]["transform"] = {t: len(df) for t, df in cleaned.items()}
    return cleaned

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — VALIDATE
# ─────────────────────────────────────────────────────────────────────────────
def validate(cleaned: dict) -> list:
    """Run integrity checks. Returns list of (level, message) tuples."""
    log.info("=" * 60)
    log.info("STAGE 3 — VALIDATE")
    log.info("=" * 60)

    issues = []

    def warn(msg):
        issues.append(("WARN", msg))
        log.warning("  WARN  %s", msg)

    def err(msg):
        issues.append(("ERROR", msg))
        log.error("  ERROR %s", msg)

    fm   = cleaned.get("fund_master")
    nav  = cleaned.get("nav_history")
    perf = cleaned.get("scheme_performance")
    txn  = cleaned.get("investor_transactions")

    if fm is not None:
        nulls = fm["amfi_code"].isna().sum()
        if nulls:
            err(f"fund_master: {nulls} null amfi_codes")
        dupes = fm["amfi_code"].duplicated().sum()
        if dupes:
            err(f"fund_master: {dupes} duplicate amfi_codes")
        log.info("  OK    fund_master validation passed (%d records)", len(fm))

    if nav is not None and fm is not None:
        nav_codes = set(nav["amfi_code"].dropna().unique())
        fm_codes  = set(fm["amfi_code"].dropna().unique())
        extra     = nav_codes - fm_codes
        if extra:
            warn(f"nav_history: {len(extra)} amfi_codes not in fund_master")
        if (nav["nav"] <= 0).any():
            err("nav_history: non-positive NAV values found")
        log.info("  OK    nav_history validation passed (%d rows)", len(nav))

    if perf is not None:
        if "sharpe_ratio" in perf.columns:
            extreme = (perf["sharpe_ratio"].abs() > 20).sum()
            if extreme:
                warn(f"scheme_performance: {extreme} extreme Sharpe ratios (|x|>20)")
        log.info("  OK    scheme_performance validation passed (%d records)", len(perf))

    if txn is not None:
        neg_amt = (txn["amount_inr"] <= 0).sum()
        if neg_amt:
            warn(f"investor_transactions: {neg_amt} non-positive amounts")
        log.info("  OK    investor_transactions validation passed (%d rows)", len(txn))

    audit["stages"]["validate"] = {
        "issues": len(issues),
        "errors": sum(1 for lvl, _ in issues if lvl == "ERROR"),
        "warnings": sum(1 for lvl, _ in issues if lvl == "WARN"),
    }
    return issues

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — LOAD (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
SQLITE_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS fund_master (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT    NOT NULL,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL    DEFAULT 0,
    min_sip_amount      REAL,
    min_lumpsum_amount  REAL,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT,
    created_at          TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nav_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL REFERENCES fund_master(amfi_code),
    date        TEXT    NOT NULL,
    nav         REAL    NOT NULL CHECK(nav > 0),
    UNIQUE(amfi_code, date)
);
CREATE INDEX IF NOT EXISTS idx_nav_code_date ON nav_history(amfi_code, date);

CREATE TABLE IF NOT EXISTS scheme_performance (
    amfi_code           INTEGER PRIMARY KEY REFERENCES fund_master(amfi_code),
    scheme_name         TEXT,
    fund_house          TEXT,
    category            TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS aum_by_fund_house (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house      TEXT    NOT NULL,
    aum_crore       REAL,
    month           TEXT,
    market_share_pct REAL
);

CREATE TABLE IF NOT EXISTS monthly_sip_inflows (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    month       TEXT,
    inflow_crore REAL,
    sip_count   INTEGER,
    avg_sip_inr REAL
);

CREATE TABLE IF NOT EXISTS category_inflows (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category        TEXT,
    month           TEXT,
    inflow_crore    REAL,
    redemption_crore REAL,
    net_flow_crore  REAL
);

CREATE TABLE IF NOT EXISTS industry_folio_count (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    month       TEXT,
    folio_count INTEGER,
    sip_folios  INTEGER,
    new_folios  INTEGER
);

CREATE TABLE IF NOT EXISTS investor_transactions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id        TEXT    NOT NULL,
    transaction_date   TEXT    NOT NULL,
    amfi_code          INTEGER NOT NULL REFERENCES fund_master(amfi_code),
    transaction_type   TEXT,
    amount_inr         REAL    NOT NULL CHECK(amount_inr > 0),
    state              TEXT,
    city               TEXT,
    city_tier          TEXT,
    age_group          TEXT,
    gender             TEXT,
    annual_income_lakh REAL,
    payment_mode       TEXT,
    kyc_status         TEXT
);
CREATE INDEX IF NOT EXISTS idx_txn_investor ON investor_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_txn_fund     ON investor_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_txn_date     ON investor_transactions(transaction_date);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL REFERENCES fund_master(amfi_code),
    stock_symbol    TEXT,
    stock_name      TEXT,
    sector          TEXT,
    weight_pct      REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date  TEXT
);
CREATE INDEX IF NOT EXISTS idx_hold_fund ON portfolio_holdings(amfi_code);

CREATE TABLE IF NOT EXISTS benchmark_indices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name  TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    value       REAL    NOT NULL CHECK(value > 0),
    UNIQUE(index_name, date)
);
CREATE INDEX IF NOT EXISTS idx_bench_name_date ON benchmark_indices(index_name, date);
"""


def load(cleaned: dict, dry_run: bool = False) -> dict:
    """Write all tables to SQLite using pandas.to_sql (WAL mode)."""
    log.info("=" * 60)
    log.info("STAGE 4 — LOAD  (SQLite: %s)", DB_PATH if not dry_run else "DRY RUN")
    log.info("=" * 60)

    row_counts = {}

    if dry_run:
        log.info("  DRY RUN — skipping database write")
        audit["stages"]["load"] = {"dry_run": True}
        return {}

    # Create DB and schema — disable FK temporarily for bulk load
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = OFF")   # re-enabled after load
    con.executescript(SQLITE_SCHEMA)
    con.commit()

    # Table load order: parent tables first
    LOAD_ORDER = [
        "fund_master", "nav_history", "scheme_performance",
        "aum_by_fund_house", "monthly_sip_inflows", "category_inflows",
        "industry_folio_count", "investor_transactions",
        "portfolio_holdings", "benchmark_indices",
    ]
    ordered = [(t, cleaned[t]) for t in LOAD_ORDER if t in cleaned]
    orphans = [(t, cleaned[t]) for t in cleaned if t not in LOAD_ORDER]

    # Table → SQLite table name (same in this project)
    for table, df in ordered + orphans:
        try:
            df_load = df.copy()

            # Replace any Int64 nullable ints with plain float (SQLite compat)
            for col in df_load.select_dtypes("Int64").columns:
                df_load[col] = df_load[col].astype(float)

            n_cols   = len(df_load.columns)
            # SQLite limit: 999 variables per statement → chunksize = 999 // n_cols
            chunksize = max(1, min(500, 999 // n_cols))

            df_load.to_sql(
                table, con,
                if_exists="replace",   # idempotent on re-run
                index=False,
                method="multi",
                chunksize=chunksize,
            )
            cnt = len(df_load)
            row_counts[table] = cnt
            log.info("  OK    %-28s  %6d rows loaded", table, cnt)
        except Exception as exc:
            log.error("  FAIL  %s — %s", table, exc)

    # Also save cleaned CSVs to processed/
    for table, df in cleaned.items():
        out_path = PROCESSED / f"{table}_clean.csv"
        df.to_csv(out_path, index=False)

    con.close()
    audit["stages"]["load"] = row_counts
    log.info("  DB saved: %s  (%.1f MB)", DB_PATH, DB_PATH.stat().st_size / 1e6)
    return row_counts

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5 — REPORT
# ─────────────────────────────────────────────────────────────────────────────
def report(t0: float, issues: list) -> None:
    audit["finished_at"]   = datetime.now().isoformat()
    audit["elapsed_sec"]   = round(time.time() - t0, 2)
    audit["issues"]        = [{"level": lvl, "message": msg} for lvl, msg in issues]
    audit["db_path"]       = str(DB_PATH)
    audit["db_size_bytes"] = DB_PATH.stat().st_size if DB_PATH.exists() else 0

    out = REPORTS / "etl_audit.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    log.info("=" * 60)
    log.info("STAGE 5 — REPORT")
    log.info("=" * 60)
    log.info("  Elapsed   : %.2f seconds", audit["elapsed_sec"])
    log.info("  Issues    : %d errors, %d warnings",
             sum(1 for lvl, _ in issues if lvl == "ERROR"),
             sum(1 for lvl, _ in issues if lvl == "WARN"))
    log.info("  Audit log : %s", out)
    log.info("  DB path   : %s", DB_PATH)
    log.info("=" * 60)
    log.info("ETL COMPLETE")
    log.info("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main(dry_run: bool = False) -> None:
    t0 = time.time()
    log.info("Bluestock MF Capstone — ETL Pipeline")
    log.info("Root: %s", ROOT)

    frames  = extract()
    cleaned = transform(frames)
    issues  = validate(cleaned)

    errors = [i for i in issues if i[0] == "ERROR"]
    if errors and not dry_run:
        log.error("Aborting load: %d validation errors found.", len(errors))
        sys.exit(1)

    load(cleaned, dry_run=dry_run)
    report(t0, issues)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bluestock MF ETL Pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate only — skip SQLite write")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
