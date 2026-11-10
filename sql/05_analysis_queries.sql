-- ============================================================
-- Bluestock Mutual Fund Analytics Platform
-- SQL Showcase: Advanced Analytics & Window Functions
-- ============================================================

-- ── 1. Ranking Funds Within Category by Sharpe Ratio ──────────
-- Business Use Case: Allows portfolio managers to identify the best
-- risk-adjusted schemes inside specific asset classes.
WITH ranked_funds AS (
    SELECT 
        amfi_code,
        scheme_name,
        category,
        sharpe_ratio,
        return_3yr_pct,
        DENSE_RANK() OVER (
            PARTITION BY category 
            ORDER BY sharpe_ratio DESC
        ) AS sharpe_rank_in_category
    FROM scheme_performance
    WHERE sharpe_ratio IS NOT NULL
)
SELECT * 
FROM ranked_funds
WHERE sharpe_rank_in_category <= 3
ORDER BY category, sharpe_rank_in_category;


-- ── 2. Cohort Retention and Ticket Size Growth ────────────────
-- Business Use Case: Customer Lifetime Value (CLV) analysis by state
-- to understand regional penetration.
SELECT 
    state,
    city_tier,
    COUNT(DISTINCT investor_id) AS active_investors,
    SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END) AS total_sip_volume,
    SUM(CASE WHEN transaction_type = 'Lumpsum' THEN amount_inr ELSE 0 END) AS total_lumpsum_volume,
    ROUND(AVG(amount_inr), 2) AS average_ticket_size,
    PERCENT_RANK() OVER (ORDER BY SUM(amount_inr) DESC) AS percentile_contribution
FROM investor_transactions
GROUP BY state, city_tier
ORDER BY total_sip_volume DESC;


-- ── 3. Cross-Fund Stock Overlap and Systemic Risk ─────────────
-- Business Use Case: Detect if multiple funds are holding the same stock,
-- which could create high systemic vulnerability if that stock crashes.
WITH stock_weights AS (
    SELECT 
        stock_name,
        stock_symbol,
        sector,
        COUNT(DISTINCT amfi_code) AS holding_funds_count,
        ROUND(AVG(weight_pct), 2) AS average_weight_pct,
        ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
    FROM portfolio_holdings
    GROUP BY stock_name, stock_symbol, sector
)
SELECT * 
FROM stock_weights
WHERE holding_funds_count > 1
ORDER BY total_market_value_cr DESC
LIMIT 10;


-- ── 4. Rolling 3-Month SIP Growth Rate ───────────────────────
-- Business Use Case: Smooth out seasonality and detect trends in retail
-- investor capital inflows.
SELECT 
    month,
    sip_inflow_crore,
    AVG(sip_inflow_crore) OVER (
        ORDER BY month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3m_avg_inflow,
    sip_inflow_crore - LAG(sip_inflow_crore, 1) OVER (ORDER BY month) AS net_momy_growth_crore
FROM monthly_sip_inflows
ORDER BY month;
