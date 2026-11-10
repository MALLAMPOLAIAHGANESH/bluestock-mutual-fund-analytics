-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- SQL Table DDL Definitions (3NF) — Component 1: Tables
-- ============================================================

-- TABLE 1: fund_master
CREATE TABLE IF NOT EXISTS fund_master (
    amfi_code           BIGINT          PRIMARY KEY,
    fund_house          VARCHAR(200)    NOT NULL,
    scheme_name         VARCHAR(500)    NOT NULL,
    category            VARCHAR(100)    NOT NULL,
    sub_category        VARCHAR(100)    NOT NULL,
    plan                VARCHAR(20)     NOT NULL,
    launch_date         DATE,
    benchmark           VARCHAR(200),
    expense_ratio_pct   NUMERIC(5,2)    NOT NULL,
    exit_load_pct       NUMERIC(5,2)    DEFAULT 0,
    min_sip_amount      INTEGER         NOT NULL,
    min_lumpsum_amount  INTEGER         NOT NULL,
    fund_manager        VARCHAR(300),
    risk_category       VARCHAR(50)     NOT NULL,
    sebi_category_code  VARCHAR(20),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 2: nav_history
CREATE TABLE IF NOT EXISTS nav_history (
    nav_id      BIGSERIAL       PRIMARY KEY,
    amfi_code   BIGINT          NOT NULL,
    nav_date    DATE            NOT NULL,
    nav         NUMERIC(12,4)   NOT NULL
);

-- TABLE 3: scheme_performance
CREATE TABLE IF NOT EXISTS scheme_performance (
    amfi_code           BIGINT          PRIMARY KEY,
    return_1yr_pct      NUMERIC(8,2),
    return_3yr_pct      NUMERIC(8,2),
    return_5yr_pct      NUMERIC(8,2),
    benchmark_3yr_pct   NUMERIC(8,2),
    alpha               NUMERIC(8,2),
    beta                NUMERIC(6,4),
    sharpe_ratio        NUMERIC(8,4),
    sortino_ratio       NUMERIC(8,4),
    std_dev_ann_pct     NUMERIC(8,2),
    max_drawdown_pct    NUMERIC(8,2),
    aum_crore           NUMERIC(14,2),
    expense_ratio_pct   NUMERIC(5,2),
    morningstar_rating  SMALLINT,
    risk_grade          VARCHAR(50),
    as_of_date          DATE            DEFAULT CURRENT_DATE,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 4: investor_transactions
CREATE TABLE IF NOT EXISTS investor_transactions (
    transaction_id      BIGSERIAL       PRIMARY KEY,
    investor_id         VARCHAR(20)     NOT NULL,
    transaction_date    DATE            NOT NULL,
    amfi_code           BIGINT          NOT NULL,
    transaction_type    VARCHAR(20)     NOT NULL,
    amount_inr          NUMERIC(14,2)   NOT NULL,
    state               VARCHAR(100),
    city                VARCHAR(100),
    city_tier           VARCHAR(10),
    age_group           VARCHAR(20),
    gender              VARCHAR(20),
    annual_income_lakh  NUMERIC(10,2),
    payment_mode        VARCHAR(50),
    kyc_status          VARCHAR(20),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 5: portfolio_holdings
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id          BIGSERIAL       PRIMARY KEY,
    amfi_code           BIGINT          NOT NULL,
    stock_symbol        VARCHAR(20)     NOT NULL,
    stock_name          VARCHAR(300)    NOT NULL,
    sector              VARCHAR(100),
    weight_pct          NUMERIC(6,2)    NOT NULL,
    market_value_cr     NUMERIC(14,2),
    current_price_inr   NUMERIC(12,2),
    portfolio_date      DATE            NOT NULL,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 6: aum_by_fund_house
CREATE TABLE IF NOT EXISTS aum_by_fund_house (
    aum_id              SERIAL          PRIMARY KEY,
    snapshot_date       DATE            NOT NULL,
    fund_house          VARCHAR(200)    NOT NULL,
    aum_lakh_crore      NUMERIC(10,4),
    aum_crore           NUMERIC(14,2)   NOT NULL,
    num_schemes         INTEGER,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 7: monthly_sip_inflows
CREATE TABLE IF NOT EXISTS monthly_sip_inflows (
    month                       DATE        PRIMARY KEY,
    sip_inflow_crore            NUMERIC(12,2)   NOT NULL,
    active_sip_accounts_crore   NUMERIC(10,4),
    new_sip_accounts_lakh       NUMERIC(10,4),
    sip_aum_lakh_crore          NUMERIC(10,4),
    yoy_growth_pct              NUMERIC(8,2),
    created_at                  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 8: category_inflows
CREATE TABLE IF NOT EXISTS category_inflows (
    inflow_id           SERIAL          PRIMARY KEY,
    month               DATE            NOT NULL,
    category            VARCHAR(100)    NOT NULL,
    net_inflow_crore    NUMERIC(12,2)   NOT NULL,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 9: industry_folio_count
CREATE TABLE IF NOT EXISTS industry_folio_count (
    month                   DATE            PRIMARY KEY,
    total_folios_crore      NUMERIC(8,4)    NOT NULL,
    equity_folios_crore     NUMERIC(8,4),
    debt_folios_crore       NUMERIC(8,4),
    hybrid_folios_crore     NUMERIC(8,4),
    others_folios_crore     NUMERIC(8,4),
    created_at              TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 10: benchmark_indices
CREATE TABLE IF NOT EXISTS benchmark_indices (
    index_id    BIGSERIAL       PRIMARY KEY,
    index_date  DATE            NOT NULL,
    index_name  VARCHAR(100)    NOT NULL,
    close_value NUMERIC(12,4)   NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);
