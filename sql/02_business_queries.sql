-- ============================================================
-- Bluestock Mutual Fund Analytics — Business SQL Query Library
-- ============================================================
-- Author  : [Your Name] — Data Analyst Intern, Bluestock Fintech
-- Created : 2026-06-23
-- Database: bluestock_mf
--
-- Query difficulty levels:
--   🟢 Beginner   — Basic SELECT, WHERE, GROUP BY, ORDER BY
--   🟡 Intermediate — JOINs, Subqueries, HAVING, date functions
--   🔴 Advanced   — CTEs, Window Functions, Complex aggregations
-- ============================================================


-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 🟢 SECTION 1: BEGINNER QUERIES
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ── Q1: How many schemes does each fund house manage? ─────────
-- Business Purpose: Market share by scheme count. 
-- Decision Makers Learn: Which AMCs have the widest product range?
-- Insight: Fund houses with 15+ schemes offer diversification across risk levels.

SELECT 
    fund_house,
    COUNT(*) AS total_schemes,
    COUNT(CASE WHEN plan = 'Direct'  THEN 1 END) AS direct_plans,
    COUNT(CASE WHEN plan = 'Regular' THEN 1 END) AS regular_plans
FROM fund_master
GROUP BY fund_house
ORDER BY total_schemes DESC;


-- ── Q2: Average expense ratio by category ────────────────────
-- Business Purpose: Help investors compare cost structures across fund types.
-- Decision Makers Learn: Are equity funds more expensive than debt? Do direct plans save money?
-- Insight: Direct plans save 0.5–1.0% annually — compounding over 20 years, this is lakhs.

SELECT 
    category,
    plan,
    ROUND(AVG(expense_ratio_pct)::NUMERIC, 2) AS avg_expense_ratio_pct,
    ROUND(MIN(expense_ratio_pct)::NUMERIC, 2) AS min_expense_ratio_pct,
    ROUND(MAX(expense_ratio_pct)::NUMERIC, 2) AS max_expense_ratio_pct,
    COUNT(*) AS fund_count
FROM fund_master
GROUP BY category, plan
ORDER BY category, plan;


-- ── Q3: Funds above SEBI expense ratio advisory threshold ─────
-- Business Purpose: Investor cost advisory — flag expensive funds.
-- Decision Makers Learn: Which funds are at the high end of expense costs?
-- Insight: A 1% higher expense ratio = ₹1 lakh less wealth per ₹10 lakh over 10 years at 12% returns.

SELECT 
    scheme_name,
    fund_house,
    category,
    plan,
    expense_ratio_pct
FROM fund_master
WHERE expense_ratio_pct > 1.5
ORDER BY expense_ratio_pct DESC;


-- ── Q4: Transaction volume by type ────────────────────────────
-- Business Purpose: Understand investor behavior patterns.
-- Decision Makers Learn: Are investors net buyers or sellers? What is preferred investment mode?
-- Insight: Redemption spike signals market panic — early warning for fund managers.

SELECT 
    transaction_type,
    COUNT(*)                                    AS transaction_count,
    SUM(amount_inr)                             AS total_amount_inr,
    ROUND(AVG(amount_inr)::NUMERIC, 0)          AS avg_ticket_size_inr,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) 
          OVER ()::NUMERIC, 1)                  AS pct_of_total
FROM investor_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;


-- ── Q5: Monthly SIP inflow trend ──────────────────────────────
-- Business Purpose: Track India's SIP culture growth story.
-- Decision Makers Learn: Is retail investor participation growing month over month?
-- Insight: SIP crossing ₹20,000 Cr/month in 2024 signals maturation of India's MF industry.

SELECT 
    TO_CHAR(month, 'YYYY-MM') AS month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    new_sip_accounts_lakh,
    COALESCE(ROUND(yoy_growth_pct::NUMERIC, 1)::TEXT, 'N/A (first year)') AS yoy_growth_pct
FROM monthly_sip_inflows
ORDER BY month;


-- ── Q6: Count of investors by gender and age group ────────────
-- Business Purpose: Demographic profile of investor base.
-- Decision Makers Learn: Who is investing? Enables targeted marketing and product design.

SELECT 
    age_group,
    gender,
    COUNT(DISTINCT investor_id) AS unique_investors,
    COUNT(*)                    AS total_transactions
FROM investor_transactions
GROUP BY age_group, gender
ORDER BY age_group, gender;


-- ── Q7: Funds with 5-star Morningstar rating ──────────────────
-- Business Purpose: Identify top-rated funds for investor recommendations.
-- Decision Makers Learn: Which funds meet the highest quality bar?

SELECT 
    fm.scheme_name,
    fm.fund_house,
    fm.category,
    fm.plan,
    sp.morningstar_rating,
    sp.return_3yr_pct,
    sp.sharpe_ratio
FROM fund_master fm
JOIN scheme_performance sp ON fm.amfi_code = sp.amfi_code
WHERE sp.morningstar_rating = 5
ORDER BY sp.return_3yr_pct DESC;


-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 🟡 SECTION 2: INTERMEDIATE QUERIES
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ── Q8: Top 10 funds by 5-year returns with alpha ─────────────
-- Business Purpose: Identify funds generating genuine excess returns over benchmark.
-- Decision Makers Learn: Is performance due to market or manager skill?
-- Insight: Alpha > 1% consistently = strong fund manager skill. This justifies management fees.

SELECT 
    sp.scheme_name,
    sp.fund_house,
    sp.category,
    sp.return_1yr_pct,
    sp.return_3yr_pct,
    sp.return_5yr_pct,
    sp.benchmark_3yr_pct,
    ROUND((sp.return_3yr_pct - sp.benchmark_3yr_pct)::NUMERIC, 2) AS alpha_vs_benchmark,
    sp.morningstar_rating
FROM scheme_performance sp
ORDER BY sp.return_5yr_pct DESC
LIMIT 10;


-- ── Q9: Risk-adjusted returns — Best Sharpe Ratio ─────────────
-- Business Purpose: Find funds maximizing returns per unit of risk.
-- Decision Makers Learn: Pure return comparison is misleading. Risk-adjusted metrics
--                        show which funds are truly efficient.
-- Insight: Sharpe > 1.0 = excellent. A fund with Sharpe 0.9 and 15% return beats
--          one with Sharpe 0.6 and 20% return for risk-conscious investors.

SELECT 
    fm.scheme_name,
    fm.fund_house,
    fm.category,
    sp.return_3yr_pct,
    sp.std_dev_ann_pct,
    sp.sharpe_ratio,
    sp.sortino_ratio,
    sp.max_drawdown_pct,
    sp.risk_grade
FROM fund_master fm
JOIN scheme_performance sp ON fm.amfi_code = sp.amfi_code
WHERE sp.sharpe_ratio > 0
ORDER BY sp.sharpe_ratio DESC;


-- ── Q10: HAVING — Fund houses with avg 3yr return > 12% ───────
-- Business Purpose: Identify consistently strong-performing AMCs.
-- Decision Makers Learn: Which fund houses deserve capital allocation?

SELECT 
    fm.fund_house,
    COUNT(*)                                AS schemes_count,
    ROUND(AVG(sp.return_3yr_pct)::NUMERIC, 2) AS avg_3yr_return,
    ROUND(AVG(sp.sharpe_ratio)::NUMERIC, 2)   AS avg_sharpe_ratio,
    ROUND(MIN(sp.return_3yr_pct)::NUMERIC, 2) AS min_3yr_return,
    ROUND(MAX(sp.return_3yr_pct)::NUMERIC, 2) AS max_3yr_return
FROM fund_master fm
JOIN scheme_performance sp ON fm.amfi_code = sp.amfi_code
GROUP BY fm.fund_house
HAVING AVG(sp.return_3yr_pct) > 12
ORDER BY avg_3yr_return DESC;


-- ── Q11: T30 vs B30 city transaction analysis ─────────────────
-- Business Purpose: SEBI mandatory reporting metric for geographic financial inclusion.
-- Decision Makers Learn: Are we penetrating beyond metro cities? SEBI incentivizes B30 reach
--                        by allowing higher TER on B30 flows.
-- Insight: B30 cities represent 70% of India's geography but often < 15% of AUM — 
--          massive growth opportunity.

SELECT 
    city_tier,
    COUNT(*)                                AS transaction_count,
    COUNT(DISTINCT investor_id)             AS unique_investors,
    ROUND(SUM(amount_inr) / 1e7, 2)        AS total_inflow_crore,
    ROUND(AVG(amount_inr)::NUMERIC, 0)      AS avg_ticket_size,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()::NUMERIC, 1) AS pct_transactions
FROM investor_transactions
WHERE transaction_type IN ('SIP', 'Lumpsum')
GROUP BY city_tier
ORDER BY total_inflow_crore DESC;


-- ── Q12: Month-over-month category inflow changes ────────────
-- Business Purpose: Track shifting investor preferences across categories.
-- Decision Makers Learn: When do investors shift from Large Cap to Mid/Small Cap?
--                        This reflects risk appetite and market phase.
-- Insight: Equity inflow > Debt inflow = bull market sentiment signal.

SELECT 
    ci.month,
    ci.category,
    ci.net_inflow_crore,
    ci.net_inflow_crore - LAG(ci.net_inflow_crore) 
        OVER (PARTITION BY ci.category ORDER BY ci.month) AS mom_change_crore
FROM category_inflows ci
ORDER BY ci.category, ci.month;


-- ── Q13: Portfolio sector concentration per fund ──────────────
-- Business Purpose: Risk management — detect concentrated sector bets.
-- Decision Makers Learn: Is a fund overly concentrated in one sector?
-- Insight: SEBI guidelines: No single stock > 10%. Sector >30% = concentration risk.

SELECT 
    fm.scheme_name,
    fm.fund_house,
    ph.sector,
    ROUND(SUM(ph.weight_pct)::NUMERIC, 2) AS sector_weight_pct,
    COUNT(ph.stock_symbol)                AS stocks_in_sector
FROM portfolio_holdings ph
JOIN fund_master fm ON ph.amfi_code = fm.amfi_code
GROUP BY fm.scheme_name, fm.fund_house, ph.sector
ORDER BY fm.scheme_name, sector_weight_pct DESC;


-- ── Q14: Subquery — Funds with above-average AUM in category ──
-- Business Purpose: Identify dominant funds within each peer group.
-- Decision Makers Learn: Fund size signals investor confidence. Large AUM 
--                        = harder to manage (liquidity constraints), but also = trusted.

SELECT 
    sp.scheme_name,
    sp.fund_house,
    sp.category,
    sp.aum_crore,
    ROUND(
        (SELECT AVG(aum_crore) FROM scheme_performance sp2 WHERE sp2.category = sp.category)::NUMERIC,
    0) AS category_avg_aum_crore
FROM scheme_performance sp
WHERE sp.aum_crore > (
    SELECT AVG(aum_crore)
    FROM scheme_performance sp2
    WHERE sp2.category = sp.category
)
ORDER BY sp.category, sp.aum_crore DESC;


-- ── Q15: Investor payment mode analysis ──────────────────────
-- Business Purpose: Understand payment infrastructure adoption.
-- Decision Makers Learn: UPI adoption rate — high UPI = low friction, higher SIP retention.
-- Insight: UPI-linked mandates have highest SIP continuity rate vs. post-dated cheques.

SELECT 
    payment_mode,
    transaction_type,
    COUNT(*)                            AS transactions,
    ROUND(AVG(amount_inr)::NUMERIC, 0)  AS avg_amount
FROM investor_transactions
GROUP BY payment_mode, transaction_type
ORDER BY transactions DESC;


-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 🔴 SECTION 3: ADVANCED QUERIES
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ── Q16: CTE + Window — Fund performance ranking in peer group ─
-- Business Purpose: Peer-relative ranking is more meaningful than absolute return.
-- Decision Makers Learn: How does each fund rank within its category?
-- Insight: A 14% return ranked #1 in Large Cap beats a 20% return ranked #8 in Small Cap.

WITH performance_ranked AS (
    SELECT 
        fm.amfi_code,
        fm.scheme_name,
        fm.fund_house,
        fm.sub_category,
        fm.plan,
        sp.return_1yr_pct,
        sp.return_3yr_pct,
        sp.return_5yr_pct,
        sp.sharpe_ratio,
        sp.aum_crore,
        RANK() OVER (
            PARTITION BY fm.sub_category, fm.plan
            ORDER BY sp.return_3yr_pct DESC
        ) AS rank_3yr_in_category,
        COUNT(*) OVER (
            PARTITION BY fm.sub_category, fm.plan
        ) AS peers_count
    FROM fund_master fm
    JOIN scheme_performance sp ON fm.amfi_code = sp.amfi_code
)
SELECT 
    scheme_name,
    fund_house,
    sub_category,
    plan,
    return_3yr_pct,
    rank_3yr_in_category,
    peers_count,
    CASE 
        WHEN rank_3yr_in_category = 1                          THEN '🥇 Category Topper'
        WHEN rank_3yr_in_category <= CEIL(peers_count * 0.25)  THEN '🟢 Top Quartile'
        WHEN rank_3yr_in_category <= CEIL(peers_count * 0.50)  THEN '🟡 Second Quartile'
        WHEN rank_3yr_in_category <= CEIL(peers_count * 0.75)  THEN '🟠 Third Quartile'
        ELSE                                                        '🔴 Bottom Quartile'
    END AS quartile_label
FROM performance_ranked
ORDER BY sub_category, plan, rank_3yr_in_category;


-- ── Q17: CTE — Identify consistent benchmark beaters ──────────
-- Business Purpose: Find funds demonstrating GENUINE skill across multiple periods.
-- Decision Makers Learn: One good year can be luck. Beating benchmark across 1Y + 3Y + 5Y = skill.
-- Insight: Only ~20% of active funds beat their benchmark across all three time horizons globally.

WITH alpha_analysis AS (
    SELECT 
        fm.amfi_code,
        fm.scheme_name,
        fm.fund_house,
        fm.category,
        fm.plan,
        sp.return_1yr_pct,
        sp.return_3yr_pct,
        sp.return_5yr_pct,
        sp.benchmark_3yr_pct,
        sp.alpha,
        CASE WHEN sp.return_1yr_pct > sp.benchmark_3yr_pct THEN 1 ELSE 0 END AS beats_1yr,
        CASE WHEN sp.return_3yr_pct > sp.benchmark_3yr_pct THEN 1 ELSE 0 END AS beats_3yr,
        CASE WHEN sp.return_5yr_pct > sp.benchmark_3yr_pct THEN 1 ELSE 0 END AS beats_5yr
    FROM fund_master fm
    JOIN scheme_performance sp ON fm.amfi_code = sp.amfi_code
)
SELECT 
    scheme_name,
    fund_house,
    category,
    plan,
    return_1yr_pct,
    return_3yr_pct,
    return_5yr_pct,
    benchmark_3yr_pct,
    alpha,
    (beats_1yr + beats_3yr + beats_5yr) AS periods_beating_benchmark,
    CASE 
        WHEN (beats_1yr + beats_3yr + beats_5yr) = 3 THEN 'Consistent Outperformer ✅'
        WHEN (beats_1yr + beats_3yr + beats_5yr) = 2 THEN 'Moderate Outperformer'
        WHEN (beats_1yr + beats_3yr + beats_5yr) = 1 THEN 'Inconsistent'
        ELSE                                               'Underperformer ❌'
    END AS performance_label
FROM alpha_analysis
ORDER BY periods_beating_benchmark DESC, return_3yr_pct DESC;


-- ── Q18: Window — 3-Month Moving Average NAV ──────────────────
-- Business Purpose: Smooth daily NAV noise to identify real trend direction.
-- Decision Makers Learn: Is the fund in an uptrend or downtrend? 
-- Insight: Used in quantitative models — 3M MA crossing 12M MA = potential entry/exit signal.

WITH monthly_nav AS (
    SELECT 
        amfi_code,
        DATE_TRUNC('month', nav_date)::DATE AS month,
        ROUND(AVG(nav)::NUMERIC, 4)         AS avg_monthly_nav
    FROM nav_history
    GROUP BY amfi_code, DATE_TRUNC('month', nav_date)
)
SELECT 
    fm.scheme_name,
    mn.month,
    mn.avg_monthly_nav,
    ROUND(
        AVG(mn.avg_monthly_nav) OVER (
            PARTITION BY mn.amfi_code
            ORDER BY mn.month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        )::NUMERIC, 4
    ) AS nav_3m_moving_avg,
    ROUND(
        AVG(mn.avg_monthly_nav) OVER (
            PARTITION BY mn.amfi_code
            ORDER BY mn.month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        )::NUMERIC, 4
    ) AS nav_12m_moving_avg
FROM monthly_nav mn
JOIN fund_master fm ON mn.amfi_code = fm.amfi_code
ORDER BY fm.scheme_name, mn.month;


-- ── Q19: CTE — Year-over-year NAV return per fund ────────────
-- Business Purpose: Calculate verified annual returns from raw NAV data.
-- Decision Makers Learn: Cross-validate published returns against raw data — standard audit practice.
-- Insight: Fund factsheets sometimes show point-to-point returns vs. CAGR — this query uses
--          actual start/end NAV for precise verification.

WITH yearly_navs AS (
    SELECT 
        amfi_code,
        EXTRACT(YEAR FROM nav_date)           AS nav_year,
        FIRST_VALUE(nav) OVER (
            PARTITION BY amfi_code, EXTRACT(YEAR FROM nav_date)
            ORDER BY nav_date
        )                                     AS year_start_nav,
        LAST_VALUE(nav) OVER (
            PARTITION BY amfi_code, EXTRACT(YEAR FROM nav_date)
            ORDER BY nav_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                     AS year_end_nav
    FROM nav_history
),
deduped AS (
    SELECT DISTINCT amfi_code, nav_year, year_start_nav, year_end_nav
    FROM yearly_navs
)
SELECT 
    fm.scheme_name,
    fm.fund_house,
    d.nav_year::INT,
    ROUND(d.year_start_nav::NUMERIC, 2) AS year_start_nav,
    ROUND(d.year_end_nav::NUMERIC, 2)   AS year_end_nav,
    ROUND(
        ((d.year_end_nav - d.year_start_nav) / d.year_start_nav * 100)::NUMERIC, 2
    )                                   AS annual_return_pct
FROM deduped d
JOIN fund_master fm ON d.amfi_code = fm.amfi_code
ORDER BY fm.scheme_name, d.nav_year;


-- ── Q20: Window — Running AUM market share by quarter ─────────
-- Business Purpose: Track fund house competitive dynamics over time.
-- Decision Makers Learn: Which AMC is gaining/losing market share? 
--                        Sudden AUM share loss = investigate outflows, performance, or PR issues.

WITH quarterly_industry AS (
    SELECT snapshot_date, SUM(aum_crore) AS industry_total_aum
    FROM aum_by_fund_house
    GROUP BY snapshot_date
)
SELECT 
    a.snapshot_date,
    a.fund_house,
    a.aum_crore,
    ROUND(100.0 * a.aum_crore / qi.industry_total_aum, 2) AS market_share_pct,
    RANK() OVER (PARTITION BY a.snapshot_date ORDER BY a.aum_crore DESC) AS market_rank,
    ROUND(
        a.aum_crore - LAG(a.aum_crore) OVER (
            PARTITION BY a.fund_house ORDER BY a.snapshot_date
        ), 2
    )                                                         AS qoq_aum_change_crore
FROM aum_by_fund_house a
JOIN quarterly_industry qi ON a.snapshot_date = qi.snapshot_date
ORDER BY a.snapshot_date, market_rank;


-- ── Q21: Investor segmentation — Age × income behavior ────────
-- Business Purpose: Build data-driven investor personas.
-- Decision Makers Learn: What investment amount and type does each demographic prefer?
--                        Informs product design, onboarding flows, and marketing.

SELECT 
    age_group,
    CASE 
        WHEN annual_income_lakh < 5   THEN 'Low (<5L)'
        WHEN annual_income_lakh < 15  THEN 'Middle (5-15L)'
        WHEN annual_income_lakh < 30  THEN 'Upper-Middle (15-30L)'
        ELSE                               'High (30L+)'
    END AS income_segment,
    COUNT(DISTINCT investor_id)             AS unique_investors,
    ROUND(AVG(amount_inr)::NUMERIC, 0)      AS avg_ticket_size,
    ROUND(100.0 * SUM(CASE WHEN transaction_type = 'SIP'     THEN 1 ELSE 0 END) / COUNT(*), 1) AS sip_pct,
    ROUND(100.0 * SUM(CASE WHEN transaction_type = 'Lumpsum' THEN 1 ELSE 0 END) / COUNT(*), 1) AS lumpsum_pct
FROM investor_transactions
GROUP BY age_group, income_segment
ORDER BY age_group, income_segment;


-- ── Q22: Full fund fact-sheet JOIN query ─────────────────────
-- Business Purpose: Comprehensive single-fund report used in investor presentations.
-- Decision Makers Learn: All-in-one view combining static attributes + performance metrics.
-- Insight: In financial data platforms, this is the "fund detail page" backend query.

SELECT 
    -- Fund Attributes (from fund_master)
    fm.amfi_code,
    fm.scheme_name,
    fm.fund_house,
    fm.category,
    fm.sub_category,
    fm.plan,
    fm.benchmark,
    fm.fund_manager,
    fm.launch_date,
    fm.expense_ratio_pct,
    fm.exit_load_pct,
    fm.risk_category,
    -- Performance Metrics (from scheme_performance)
    sp.return_1yr_pct,
    sp.return_3yr_pct,
    sp.return_5yr_pct,
    sp.benchmark_3yr_pct,
    ROUND((sp.return_3yr_pct - sp.benchmark_3yr_pct)::NUMERIC, 2) AS alpha_3yr,
    sp.beta,
    sp.sharpe_ratio,
    sp.sortino_ratio,
    sp.max_drawdown_pct,
    sp.aum_crore,
    sp.morningstar_rating,
    sp.risk_grade
FROM fund_master fm
JOIN scheme_performance sp ON fm.amfi_code = sp.amfi_code
ORDER BY sp.sharpe_ratio DESC;


-- ── Q23: State-wise investor distribution ────────────────────
-- Business Purpose: Geographic penetration analysis for branch/distributor strategy.
-- Decision Makers Learn: Which states have underserved investor populations?
-- Insight: MH, DL, GJ traditionally dominate. States like UP, Bihar = B30 growth frontier.

SELECT 
    state,
    COUNT(DISTINCT investor_id)         AS unique_investors,
    COUNT(*)                            AS total_transactions,
    ROUND(SUM(amount_inr) / 1e7, 2)    AS total_inflow_crore,
    ROUND(AVG(amount_inr)::NUMERIC, 0)  AS avg_ticket_size,
    city_tier
FROM investor_transactions
GROUP BY state, city_tier
ORDER BY total_inflow_crore DESC
LIMIT 20;


-- ── Q24: Fund vs benchmark performance scatter data ───────────
-- Business Purpose: Risk-return scatter plot data for investment committee presentations.
-- Decision Makers Learn: Do funds above the benchmark line justify their higher risk?
-- Insight: Funds in the upper-left quadrant (high return, low risk) are "efficient".

SELECT 
    sp.scheme_name,
    sp.fund_house,
    sp.category,
    sp.std_dev_ann_pct      AS risk_x_axis,
    sp.return_3yr_pct       AS return_y_axis,
    sp.benchmark_3yr_pct    AS benchmark_return,
    sp.sharpe_ratio,
    CASE 
        WHEN sp.return_3yr_pct > sp.benchmark_3yr_pct AND sp.std_dev_ann_pct < 18 
            THEN 'Efficient (High Return, Low Risk)'
        WHEN sp.return_3yr_pct > sp.benchmark_3yr_pct 
            THEN 'Outperformer (High Risk)'
        WHEN sp.std_dev_ann_pct < 18 
            THEN 'Underperformer (Low Risk)'
        ELSE 
            'Inefficient (Low Return, High Risk)'
    END AS quadrant_label
FROM scheme_performance sp
ORDER BY sp.std_dev_ann_pct;


-- ── Q25: Most popular stocks across all funds (overlap analysis) ──
-- Business Purpose: Portfolio overlap analysis — how crowded is each stock?
-- Decision Makers Learn: If 80% of funds hold the same top stocks, diversification is an illusion.
-- Insight: High overlap in benchmark-heavy stocks = closet indexing. 
--          Investors should check if they're paying active fees for passive exposure.

SELECT 
    ph.stock_symbol,
    ph.stock_name,
    ph.sector,
    COUNT(DISTINCT ph.amfi_code)            AS fund_count,
    ROUND(AVG(ph.weight_pct)::NUMERIC, 2)   AS avg_weight_pct,
    ROUND(SUM(ph.market_value_cr)::NUMERIC, 2) AS total_market_value_cr
FROM portfolio_holdings ph
GROUP BY ph.stock_symbol, ph.stock_name, ph.sector
HAVING COUNT(DISTINCT ph.amfi_code) >= 3      -- Held by at least 3 funds
ORDER BY fund_count DESC, total_market_value_cr DESC;


-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 🔴 SECTION 4: EXECUTIVE DASHBOARD QUERIES (BONUS)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ── Q26: KPI Dashboard — Industry Snapshot ───────────────────
-- Business Purpose: One-line executive summary of the industry.

SELECT 
    (SELECT COUNT(DISTINCT fund_house) FROM fund_master)                    AS total_amcs,
    (SELECT COUNT(*) FROM fund_master)                                      AS total_schemes,
    (SELECT SUM(aum_crore) FROM aum_by_fund_house WHERE snapshot_date = 
        (SELECT MAX(snapshot_date) FROM aum_by_fund_house))                 AS latest_industry_aum_crore,
    (SELECT sip_inflow_crore FROM monthly_sip_inflows WHERE month = 
        (SELECT MAX(month) FROM monthly_sip_inflows))                       AS latest_monthly_sip_crore,
    (SELECT COUNT(DISTINCT investor_id) FROM investor_transactions)         AS total_unique_investors,
    (SELECT COUNT(*) FROM investor_transactions)                             AS total_transactions;


-- ── Q27: Data Quality Verification Query ─────────────────────
-- Business Purpose: Post-load validation — run after data loading to verify integrity.

SELECT 'fund_master'            AS table_name, COUNT(*) AS row_count FROM fund_master
UNION ALL SELECT 'nav_history',            COUNT(*) FROM nav_history
UNION ALL SELECT 'scheme_performance',     COUNT(*) FROM scheme_performance
UNION ALL SELECT 'investor_transactions',  COUNT(*) FROM investor_transactions
UNION ALL SELECT 'portfolio_holdings',     COUNT(*) FROM portfolio_holdings
UNION ALL SELECT 'aum_by_fund_house',      COUNT(*) FROM aum_by_fund_house
UNION ALL SELECT 'monthly_sip_inflows',    COUNT(*) FROM monthly_sip_inflows
UNION ALL SELECT 'category_inflows',       COUNT(*) FROM category_inflows
UNION ALL SELECT 'industry_folio_count',   COUNT(*) FROM industry_folio_count
UNION ALL SELECT 'benchmark_indices',      COUNT(*) FROM benchmark_indices
ORDER BY row_count DESC;
