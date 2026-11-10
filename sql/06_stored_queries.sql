-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- Standard SQL Business Queries Library
-- ============================================================

-- Q1: Total Assets Under Management (AUM) and Scheme Counts by AMC
SELECT 
    fund_house,
    COUNT(*) AS total_schemes,
    SUM(CASE WHEN plan = 'Direct' THEN 1 ELSE 0 END) AS direct_schemes,
    SUM(CASE WHEN plan = 'Regular' THEN 1 ELSE 0 END) AS regular_schemes
FROM fund_master
GROUP BY fund_house
ORDER BY total_schemes DESC;


-- Q2: Expense Ratio Summary by Fund Category and Plan Type
SELECT 
    category,
    plan,
    ROUND(AVG(expense_ratio_pct), 3) AS avg_expense_ratio_pct,
    MIN(expense_ratio_pct) AS min_expense_ratio_pct,
    MAX(expense_ratio_pct) AS max_expense_ratio_pct,
    COUNT(*) AS scheme_count
FROM fund_master
GROUP BY category, plan
ORDER BY category, plan;


-- Q3: Identifying Schemes with High Expense Ratios (above 1.5%)
SELECT 
    scheme_name,
    fund_house,
    category,
    plan,
    expense_ratio_pct
FROM fund_master
WHERE expense_ratio_pct > 1.5
ORDER BY expense_ratio_pct DESC;


-- Q4: Transaction Volumes and Average Ticket Sizes by Transaction Type
SELECT 
    transaction_type,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS total_volume_inr,
    ROUND(AVG(amount_inr), 2) AS avg_ticket_size_inr
FROM investor_transactions
GROUP BY transaction_type
ORDER BY total_volume_inr DESC;


-- Q5: Demographic Penetration Metrics (T30 vs B30 Cities)
SELECT 
    city_tier,
    COUNT(DISTINCT investor_id) AS unique_investors,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_investment_inr,
    ROUND(AVG(amount_inr), 2) AS average_ticket_size_inr
FROM investor_transactions
GROUP BY city_tier
ORDER BY total_investment_inr DESC;
