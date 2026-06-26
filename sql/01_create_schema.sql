-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- PostgreSQL Database Schema — Production Design (3NF)
-- ============================================================
-- Author  : MALLAM POLAIAH GANESH — Data Analyst Intern, Bluestock Fintech
-- Created : 2026-06-23
-- Database: bluestock_mf
--
-- Design Philosophy:
--   Third Normal Form (3NF) — eliminates transitive dependencies
--   fund_master is the central reference table (dimension table)
--   All fund-level tables FK-reference fund_master.amfi_code
--   Aggregate tables (SIP, AUM, folio) have no FK (industry-level)
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- PRE-REQUISITE: Create the database (run as superuser)
-- ────────────────────────────────────────────────────────────
-- CREATE DATABASE bluestock_mf;
-- \c bluestock_mf

-- ────────────────────────────────────────────────────────────
-- EXTENSIONS
-- ────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- For fuzzy text search on fund names

-- ============================================================
-- TABLE 1: fund_master
-- Purpose : Master reference for all 40 mutual fund schemes
-- PK      : amfi_code (AMFI-assigned unique scheme identifier)
-- Role    : PARENT table — all fund-level tables FK to this
-- ============================================================
CREATE TABLE IF NOT EXISTS fund_master (
    amfi_code           BIGINT          PRIMARY KEY,
    fund_house          VARCHAR(200)    NOT NULL,
    scheme_name         VARCHAR(500)    NOT NULL,
    category            VARCHAR(100)    NOT NULL,        -- Equity / Debt / Hybrid
    sub_category        VARCHAR(100)    NOT NULL,        -- Large Cap, Mid Cap, etc.
    plan                VARCHAR(20)     NOT NULL         -- Regular / Direct
                            CHECK (plan IN ('Regular', 'Direct')),
    launch_date         DATE,
    benchmark           VARCHAR(200),
    expense_ratio_pct   NUMERIC(5,2)    NOT NULL         -- SEBI max: 2.25% equity
                            CHECK (expense_ratio_pct BETWEEN 0 AND 2.5),
    exit_load_pct       NUMERIC(5,2)    DEFAULT 0
                            CHECK (exit_load_pct BETWEEN 0 AND 5),
    min_sip_amount      INTEGER         NOT NULL
                            CHECK (min_sip_amount > 0),
    min_lumpsum_amount  INTEGER         NOT NULL
                            CHECK (min_lumpsum_amount > 0),
    fund_manager        VARCHAR(300),
    risk_category       VARCHAR(50)     NOT NULL,        -- Low / Moderate / High / Very High
    sebi_category_code  VARCHAR(20),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  fund_master IS 'Master reference table for all mutual fund schemes. Central parent table.';
COMMENT ON COLUMN fund_master.amfi_code IS 'AMFI (Association of Mutual Funds in India) official scheme code. Globally unique.';
COMMENT ON COLUMN fund_master.expense_ratio_pct IS 'Annual management fee as % of AUM. SEBI cap: 2.25% for equity funds.';
COMMENT ON COLUMN fund_master.exit_load_pct IS 'Redemption penalty if redeemed before lock-in period. 0 = no load.';


-- ============================================================
-- TABLE 2: nav_history
-- Purpose : Daily Net Asset Value (unit price) for all funds
-- PK      : Composite (amfi_code, date) — one NAV per fund per day
-- FK      : amfi_code → fund_master
-- ============================================================
CREATE TABLE IF NOT EXISTS nav_history (
    nav_id      BIGSERIAL       PRIMARY KEY,    -- Surrogate key for ORM convenience
    amfi_code   BIGINT          NOT NULL,
    nav_date    DATE            NOT NULL,
    nav         NUMERIC(12,4)   NOT NULL
                    CHECK (nav > 0),            -- NAV can never be zero or negative
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_nav_amfi_date UNIQUE (amfi_code, nav_date),
    CONSTRAINT fk_nav_fund FOREIGN KEY (amfi_code)
        REFERENCES fund_master(amfi_code)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

COMMENT ON TABLE  nav_history IS 'Daily NAV price history. One record per fund per trading day. 46,000+ records.';
COMMENT ON COLUMN nav_history.nav IS 'Net Asset Value in INR per unit. Must be positive.';


-- ============================================================
-- TABLE 3: scheme_performance
-- Purpose : Risk-adjusted performance metrics per fund
-- PK      : amfi_code (1:1 with fund_master)
-- FK      : amfi_code → fund_master
-- Note    : Separate table because metrics change over time
--           and would violate 3NF if embedded in fund_master
-- ============================================================
CREATE TABLE IF NOT EXISTS scheme_performance (
    amfi_code           BIGINT          PRIMARY KEY,
    return_1yr_pct      NUMERIC(8,2),           -- 1-year absolute return
    return_3yr_pct      NUMERIC(8,2),           -- 3-year CAGR
    return_5yr_pct      NUMERIC(8,2),           -- 5-year CAGR
    benchmark_3yr_pct   NUMERIC(8,2),           -- Benchmark 3-yr return (for alpha calc)
    alpha               NUMERIC(8,2),           -- Excess return over benchmark
    beta                NUMERIC(6,4),           -- Market sensitivity (1.0 = market)
    sharpe_ratio        NUMERIC(8,4),           -- Return per unit of total risk
    sortino_ratio       NUMERIC(8,4),           -- Return per unit of downside risk
    std_dev_ann_pct     NUMERIC(8,2),           -- Annualized volatility (%)
    max_drawdown_pct    NUMERIC(8,2),           -- Peak-to-trough max loss (negative)
                            CHECK (max_drawdown_pct <= 0),
    aum_crore           NUMERIC(14,2),          -- Assets Under Management (₹ crore)
    expense_ratio_pct   NUMERIC(5,2),
    morningstar_rating  SMALLINT                -- 1–5 stars
                            CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade          VARCHAR(50),            -- Moderate / High / Very High
    as_of_date          DATE            DEFAULT CURRENT_DATE,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_perf_fund FOREIGN KEY (amfi_code)
        REFERENCES fund_master(amfi_code)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

COMMENT ON TABLE  scheme_performance IS '1:1 with fund_master. Risk-adjusted performance metrics as of snapshot date.';
COMMENT ON COLUMN scheme_performance.alpha IS 'Positive alpha = fund manager added value above benchmark return.';
COMMENT ON COLUMN scheme_performance.beta  IS 'Beta > 1.0 = more volatile than market. Beta < 1.0 = defensive.';
COMMENT ON COLUMN scheme_performance.max_drawdown_pct IS 'Maximum peak-to-trough loss. Always negative or zero. e.g. -21.7 = 21.7% loss.';


-- ============================================================
-- TABLE 4: investor_transactions
-- Purpose : Individual investor transaction records
-- PK      : transaction_id (SERIAL — no natural unique key)
-- FK      : amfi_code → fund_master
-- Note    : No investor_master table (data is anonymized)
-- ============================================================
CREATE TABLE IF NOT EXISTS investor_transactions (
    transaction_id      BIGSERIAL       PRIMARY KEY,
    investor_id         VARCHAR(20)     NOT NULL,       -- Anonymized: INVxxxxxx
    transaction_date    DATE            NOT NULL,
    amfi_code           BIGINT          NOT NULL,
    transaction_type    VARCHAR(20)     NOT NULL
                            CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption', 'Switch')),
    amount_inr          NUMERIC(14,2)   NOT NULL
                            CHECK (amount_inr > 0),
    state               VARCHAR(100),
    city                VARCHAR(100),
    city_tier           VARCHAR(10)
                            CHECK (city_tier IN ('T30', 'B30')),
    age_group           VARCHAR(20),                    -- 18-25, 26-35, 36-45, 46-55, 56+
    gender              VARCHAR(20)
                            CHECK (gender IN ('Male', 'Female', 'Other')),
    annual_income_lakh  NUMERIC(10,2)
                            CHECK (annual_income_lakh >= 0),
    payment_mode        VARCHAR(50),                    -- UPI, Mandate, Cheque, NetBanking
    kyc_status          VARCHAR(20)
                            CHECK (kyc_status IN ('Verified', 'Pending')),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_txn_fund FOREIGN KEY (amfi_code)
        REFERENCES fund_master(amfi_code)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

COMMENT ON TABLE  investor_transactions IS '32,778 anonymized investor transactions. Granular — investor_id is not a FK (no investor_master).';
COMMENT ON COLUMN investor_transactions.city_tier IS 'T30 = Top 30 cities; B30 = Beyond Top 30. SEBI reporting metric for geographic penetration.';
COMMENT ON COLUMN investor_transactions.kyc_status IS 'KYC compliance status. Only Verified investors can redeem beyond ₹50,000/day.';


-- ============================================================
-- TABLE 5: portfolio_holdings
-- Purpose : Underlying stock positions held by each fund
-- PK      : Composite (amfi_code, stock_symbol, portfolio_date)
-- FK      : amfi_code → fund_master
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id          BIGSERIAL       PRIMARY KEY,
    amfi_code           BIGINT          NOT NULL,
    stock_symbol        VARCHAR(20)     NOT NULL,
    stock_name          VARCHAR(300)    NOT NULL,
    sector              VARCHAR(100),
    weight_pct          NUMERIC(6,2)    NOT NULL
                            CHECK (weight_pct BETWEEN 0 AND 100),
    market_value_cr     NUMERIC(14,2),
    current_price_inr   NUMERIC(12,2)
                            CHECK (current_price_inr > 0),
    portfolio_date      DATE            NOT NULL,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_holding UNIQUE (amfi_code, stock_symbol, portfolio_date),
    CONSTRAINT fk_holding_fund FOREIGN KEY (amfi_code)
        REFERENCES fund_master(amfi_code)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

COMMENT ON TABLE  portfolio_holdings IS 'Monthly portfolio disclosure — stock-level holdings per fund. 322 records (top 10 holdings per fund).';


-- ============================================================
-- TABLE 6: aum_by_fund_house
-- Purpose : Quarterly AUM snapshots per AMC
-- PK      : Composite (date, fund_house)
-- Note    : No FK — fund_house is denormalized here (not a code)
-- ============================================================
CREATE TABLE IF NOT EXISTS aum_by_fund_house (
    aum_id              SERIAL          PRIMARY KEY,
    snapshot_date       DATE            NOT NULL,
    fund_house          VARCHAR(200)    NOT NULL,
    aum_lakh_crore      NUMERIC(10,4),
    aum_crore           NUMERIC(14,2)   NOT NULL
                            CHECK (aum_crore >= 0),
    num_schemes         INTEGER
                            CHECK (num_schemes >= 0),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_aum_date_house UNIQUE (snapshot_date, fund_house)
);

COMMENT ON TABLE  aum_by_fund_house IS 'Quarterly AUM per fund house for market share analysis. Industry aggregate table — no FK to fund_master.';


-- ============================================================
-- TABLE 7: monthly_sip_inflows
-- Purpose : Industry-wide SIP data by month
-- PK      : month (one row per calendar month)
-- Note    : Pure aggregate — no FK possible
-- ============================================================
CREATE TABLE IF NOT EXISTS monthly_sip_inflows (
    month                       DATE        PRIMARY KEY,
    sip_inflow_crore            NUMERIC(12,2)   NOT NULL
                                    CHECK (sip_inflow_crore >= 0),
    active_sip_accounts_crore   NUMERIC(10,4),
    new_sip_accounts_lakh       NUMERIC(10,4),
    sip_aum_lakh_crore          NUMERIC(10,4),
    yoy_growth_pct              NUMERIC(8,2),   -- NULL for first 12 months (expected)
    created_at                  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  monthly_sip_inflows IS 'Industry-level monthly SIP inflow data. yoy_growth_pct is NULL for first 12 months (no prior year baseline — intentional).';


-- ============================================================
-- TABLE 8: category_inflows
-- Purpose : Monthly net inflows by fund category
-- PK      : Composite (month, category)
-- ============================================================
CREATE TABLE IF NOT EXISTS category_inflows (
    inflow_id           SERIAL          PRIMARY KEY,
    month               DATE            NOT NULL,
    category            VARCHAR(100)    NOT NULL,
    net_inflow_crore    NUMERIC(12,2)   NOT NULL,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_category_month UNIQUE (month, category)
);

COMMENT ON TABLE  category_inflows IS 'Monthly net fund inflows by category (Large Cap, Mid Cap, Small Cap etc.). Indicator of investor sentiment.';


-- ============================================================
-- TABLE 9: industry_folio_count
-- Purpose : Quarterly unique investor accounts by asset class
-- PK      : month
-- ============================================================
CREATE TABLE IF NOT EXISTS industry_folio_count (
    month                   DATE            PRIMARY KEY,
    total_folios_crore      NUMERIC(8,4)    NOT NULL,
    equity_folios_crore     NUMERIC(8,4),
    debt_folios_crore       NUMERIC(8,4),
    hybrid_folios_crore     NUMERIC(8,4),
    others_folios_crore     NUMERIC(8,4),
    created_at              TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  industry_folio_count IS 'Quarterly count of unique investor folios. Proxy for retail investor adoption.';


-- ============================================================
-- TABLE 10: benchmark_indices
-- Purpose : Daily closing values for market indices
-- PK      : Composite (date, index_name)
-- ============================================================
CREATE TABLE IF NOT EXISTS benchmark_indices (
    index_id    BIGSERIAL       PRIMARY KEY,
    index_date  DATE            NOT NULL,
    index_name  VARCHAR(100)    NOT NULL,
    close_value NUMERIC(12,4)   NOT NULL
                    CHECK (close_value > 0),
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_index_date UNIQUE (index_date, index_name)
);

COMMENT ON TABLE  benchmark_indices IS 'Daily benchmark index closing values (NIFTY50, NIFTY500 etc.) for alpha and relative return calculations.';


-- ============================================================
-- INDEXES — Optimized for Common Query Patterns
-- ============================================================

-- nav_history: most frequently queried by date range per fund
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date
    ON nav_history(amfi_code, nav_date DESC);

-- nav_history: date-range scans (monthly/yearly returns)
CREATE INDEX IF NOT EXISTS idx_nav_date
    ON nav_history(nav_date DESC);

-- investor_transactions: investor-level lookups
CREATE INDEX IF NOT EXISTS idx_txn_investor_id
    ON investor_transactions(investor_id);

-- investor_transactions: date range analysis
CREATE INDEX IF NOT EXISTS idx_txn_date
    ON investor_transactions(transaction_date DESC);

-- investor_transactions: geographic analysis (T30/B30)
CREATE INDEX IF NOT EXISTS idx_txn_city_tier
    ON investor_transactions(city_tier);

-- investor_transactions: transaction type analytics
CREATE INDEX IF NOT EXISTS idx_txn_type
    ON investor_transactions(transaction_type);

-- fund_master: category-based filtering (most common WHERE clause)
CREATE INDEX IF NOT EXISTS idx_fund_category
    ON fund_master(category);

-- fund_master: fund house filtering
CREATE INDEX IF NOT EXISTS idx_fund_house
    ON fund_master(fund_house);

-- portfolio_holdings: sector-level analysis
CREATE INDEX IF NOT EXISTS idx_holding_sector
    ON portfolio_holdings(sector);

-- scheme_performance: return ranking queries
CREATE INDEX IF NOT EXISTS idx_perf_sharpe
    ON scheme_performance(sharpe_ratio DESC);

CREATE INDEX IF NOT EXISTS idx_perf_return_3yr
    ON scheme_performance(return_3yr_pct DESC);

-- benchmark_indices: time series queries
CREATE INDEX IF NOT EXISTS idx_bench_date_name
    ON benchmark_indices(index_date DESC, index_name);


-- ============================================================
-- VERIFICATION QUERIES — Run after loading data
-- ============================================================

-- Check record counts
-- SELECT 'fund_master'            AS table_name, COUNT(*) FROM fund_master
-- UNION ALL
-- SELECT 'nav_history',                          COUNT(*) FROM nav_history
-- UNION ALL
-- SELECT 'scheme_performance',                   COUNT(*) FROM scheme_performance
-- UNION ALL
-- SELECT 'investor_transactions',                COUNT(*) FROM investor_transactions
-- UNION ALL
-- SELECT 'portfolio_holdings',                   COUNT(*) FROM portfolio_holdings
-- UNION ALL
-- SELECT 'aum_by_fund_house',                    COUNT(*) FROM aum_by_fund_house
-- UNION ALL
-- SELECT 'monthly_sip_inflows',                  COUNT(*) FROM monthly_sip_inflows
-- UNION ALL
-- SELECT 'category_inflows',                     COUNT(*) FROM category_inflows
-- UNION ALL
-- SELECT 'industry_folio_count',                 COUNT(*) FROM industry_folio_count
-- UNION ALL
-- SELECT 'benchmark_indices',                    COUNT(*) FROM benchmark_indices
-- ORDER BY 1;
