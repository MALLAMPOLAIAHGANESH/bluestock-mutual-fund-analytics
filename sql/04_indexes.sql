-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- SQL Performance Tuning — Component 4: Indexes
-- ============================================================

-- Index 1: Optimizing Daily NAV history lookups by fund and date order
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date
    ON nav_history(amfi_code, nav_date DESC);

-- Index 2: Optimizing date-range scans for historical performance calculations
CREATE INDEX IF NOT EXISTS idx_nav_date
    ON nav_history(nav_date DESC);

-- Index 3: Optimizing investor-level transaction queries
CREATE INDEX IF NOT EXISTS idx_txn_investor_id
    ON investor_transactions(investor_id);

-- Index 4: Optimizing transaction trend time-series scans
CREATE INDEX IF NOT EXISTS idx_txn_date
    ON investor_transactions(transaction_date DESC);

-- Index 5: Geographic and demographic analysis indexing
CREATE INDEX IF NOT EXISTS idx_txn_city_tier
    ON investor_transactions(city_tier);

CREATE INDEX IF NOT EXISTS idx_txn_type
    ON investor_transactions(transaction_type);

-- Index 6: Optimizing filter operations on Scheme category and AMCs
CREATE INDEX IF NOT EXISTS idx_fund_category
    ON fund_master(category);

CREATE INDEX IF NOT EXISTS idx_fund_house
    ON fund_master(fund_house);

-- Index 7: Sector-level concentration query optimizations
CREATE INDEX IF NOT EXISTS idx_holding_sector
    ON portfolio_holdings(sector);

-- Index 8: Dynamic ranking index on risk-adjusted ratios
CREATE INDEX IF NOT EXISTS idx_perf_sharpe
    ON scheme_performance(sharpe_ratio DESC);

CREATE INDEX IF NOT EXISTS idx_perf_return_3yr
    ON scheme_performance(return_3yr_pct DESC);

-- Index 9: Benchmark index history indexing
CREATE INDEX IF NOT EXISTS idx_bench_date_name
    ON benchmark_indices(index_date DESC, index_name);
