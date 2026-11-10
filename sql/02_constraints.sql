-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- SQL Table DDL Definitions (3NF) — Component 2: Constraints
-- ============================================================

-- Alter Table 1: fund_master CHECK constraints
ALTER TABLE fund_master ADD CONSTRAINT chk_plan CHECK (plan IN ('Regular', 'Direct'));
ALTER TABLE fund_master ADD CONSTRAINT chk_expense CHECK (expense_ratio_pct BETWEEN 0 AND 2.5);
ALTER TABLE fund_master ADD CONSTRAINT chk_exit_load CHECK (exit_load_pct BETWEEN 0 AND 5);
ALTER TABLE fund_master ADD CONSTRAINT chk_min_sip CHECK (min_sip_amount > 0);
ALTER TABLE fund_master ADD CONSTRAINT chk_min_lumpsum CHECK (min_lumpsum_amount > 0);

-- Alter Table 2: nav_history UNIQUE and FK constraints
ALTER TABLE nav_history ADD CONSTRAINT uq_nav_amfi_date UNIQUE (amfi_code, nav_date);
ALTER TABLE nav_history ADD CONSTRAINT fk_nav_fund FOREIGN KEY (amfi_code)
    REFERENCES fund_master(amfi_code)
    ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE nav_history ADD CONSTRAINT chk_nav CHECK (nav > 0);

-- Alter Table 3: scheme_performance FK and CHECK constraints
ALTER TABLE scheme_performance ADD CONSTRAINT fk_perf_fund FOREIGN KEY (amfi_code)
    REFERENCES fund_master(amfi_code)
    ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE scheme_performance ADD CONSTRAINT chk_max_drawdown CHECK (max_drawdown_pct <= 0);
ALTER TABLE scheme_performance ADD CONSTRAINT chk_rating CHECK (morningstar_rating BETWEEN 1 AND 5);

-- Alter Table 4: investor_transactions FK and CHECK constraints
ALTER TABLE investor_transactions ADD CONSTRAINT fk_txn_fund FOREIGN KEY (amfi_code)
    REFERENCES fund_master(amfi_code)
    ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE investor_transactions ADD CONSTRAINT chk_txn_type CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption', 'Switch'));
ALTER TABLE investor_transactions ADD CONSTRAINT chk_amount CHECK (amount_inr > 0);
ALTER TABLE investor_transactions ADD CONSTRAINT chk_city_tier CHECK (city_tier IN ('T30', 'B30'));
ALTER TABLE investor_transactions ADD CONSTRAINT chk_gender CHECK (gender IN ('Male', 'Female', 'Other'));
ALTER TABLE investor_transactions ADD CONSTRAINT chk_income CHECK (annual_income_lakh >= 0);
ALTER TABLE investor_transactions ADD CONSTRAINT chk_kyc CHECK (kyc_status IN ('Verified', 'Pending'));

-- Alter Table 5: portfolio_holdings UNIQUE and FK constraints
ALTER TABLE portfolio_holdings ADD CONSTRAINT uq_holding UNIQUE (amfi_code, stock_symbol, portfolio_date);
ALTER TABLE portfolio_holdings ADD CONSTRAINT fk_holding_fund FOREIGN KEY (amfi_code)
    REFERENCES fund_master(amfi_code)
    ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE portfolio_holdings ADD CONSTRAINT chk_weight CHECK (weight_pct BETWEEN 0 AND 100);
ALTER TABLE portfolio_holdings ADD CONSTRAINT chk_stock_price CHECK (current_price_inr > 0);

-- Alter Table 6: aum_by_fund_house UNIQUE and CHECK constraints
ALTER TABLE aum_by_fund_house ADD CONSTRAINT uq_aum_date_house UNIQUE (snapshot_date, fund_house);
ALTER TABLE aum_by_fund_house ADD CONSTRAINT chk_aum_crore CHECK (aum_crore >= 0);
ALTER TABLE aum_by_fund_house ADD CONSTRAINT chk_num_schemes CHECK (num_schemes >= 0);

-- Alter Table 7: monthly_sip_inflows CHECK constraints
ALTER TABLE monthly_sip_inflows ADD CONSTRAINT chk_sip_inflow CHECK (sip_inflow_crore >= 0);

-- Alter Table 8: category_inflows UNIQUE constraint
ALTER TABLE category_inflows ADD CONSTRAINT uq_category_month UNIQUE (month, category);

-- Alter Table 10: benchmark_indices UNIQUE and CHECK constraints
ALTER TABLE benchmark_indices ADD CONSTRAINT uq_index_date UNIQUE (index_date, index_name);
ALTER TABLE benchmark_indices ADD CONSTRAINT chk_close CHECK (close_value > 0);
