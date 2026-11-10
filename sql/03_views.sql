-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- SQL Analytical Views — Component 3: Views
-- ============================================================

-- View 1: Complete Scheme Performance Summary
-- Combines master static data with dynamically calculated performance metrics.
CREATE OR REPLACE VIEW vw_fund_performance_summary AS
SELECT 
    fm.amfi_code,
    fm.scheme_name,
    fm.fund_house,
    fm.category,
    fm.sub_category,
    fm.plan,
    fm.launch_date,
    fm.benchmark,
    sp.return_1yr_pct,
    sp.return_3yr_pct,
    sp.return_5yr_pct,
    sp.alpha,
    sp.beta,
    sp.sharpe_ratio,
    sp.sortino_ratio,
    sp.std_dev_ann_pct,
    sp.max_drawdown_pct,
    sp.aum_crore,
    sp.morningstar_rating,
    sp.risk_grade
FROM fund_master fm
LEFT JOIN scheme_performance sp 
    ON fm.amfi_code = sp.amfi_code;

-- View 2: Investor Demographic and Behavioral Insights
-- Aggregates transaction volumes and sizes by region, gender, and income tier.
CREATE OR REPLACE VIEW vw_investor_demographics AS
SELECT 
    state,
    city_tier,
    gender,
    age_group,
    COUNT(transaction_id) AS total_transactions,
    ROUND(SUM(amount_inr), 2) AS total_investment_inr,
    ROUND(AVG(amount_inr), 2) AS average_ticket_size_inr,
    COUNT(DISTINCT investor_id) AS unique_investors
FROM investor_transactions
GROUP BY state, city_tier, gender, age_group;

-- View 3: Sector and Asset Concentration View
-- Calculates HHI and sector weight distribution across fund schemes.
CREATE OR REPLACE VIEW vw_sector_concentration AS
SELECT 
    amfi_code,
    sector,
    COUNT(holding_id) AS stock_count,
    ROUND(SUM(weight_pct), 2) AS sector_weight_pct,
    ROUND(SUM(market_value_cr), 2) AS sector_value_cr
FROM portfolio_holdings
GROUP BY amfi_code, sector;
