# Bluestock Mutual Fund Capstone — Final Report
**Author:** MALLAM POLAIAH GANESH — Data Analyst Intern, Bluestock Fintech
**Date:** July 2026

## 1. Executive Summary
This capstone project provides a comprehensive end-to-end data pipeline and analytics platform for mutual fund data. Built on a dataset of 40 AMFI-registered equity schemes spanning 2022–2025, the project encompasses data engineering, exploratory data analysis, performance metrics, risk analytics, and advanced portfolio optimisation.

Key achievements:
- **Data Engineering:** Automated ETL pipeline converting 10 raw CSVs into a robust 3NF SQLite database (5.4 MB, 10 tables) handling over 46,000 NAV records.
- **Analytics:** Calculation of Alpha, Beta, Sharpe Ratio, Sortino Ratio, and Historical VaR (95%).
- **Interactive Dashboard:** A 4-page Streamlit web app providing dynamic filtering across funds, categories, and risk grades.
- **Advanced Modelling:** Monte Carlo simulation for 5-year NAV projections and Markowitz Efficient Frontier for portfolio optimisation.

## 2. Data Architecture & ETL
The ETL pipeline (`scripts/etl_pipeline.py`) performs extraction, transformation, validation, and loading:
- **Transformation:** Handles missing values, data type coercion, and normalisation. Critically, gaps in NAV history (e.g., weekends/holidays) are forward-filled after reindexing to a complete business day calendar.
- **Validation:** Referential integrity checks ensure all transactions and NAV entries link to valid `amfi_code` values in `fund_master`.
- **Loading:** Data is loaded into a local `bluestock_mf.db` SQLite database using `pandas.to_sql` with batching to avoid parameter limits.

## 3. Exploratory Data Analysis (EDA) Findings
- **AUM Dominance:** Large Cap funds command the majority of the Assets Under Management (AUM), with SBI and HDFC leading the market share.
- **SIP Inflows:** A steady month-on-month increase in SIP inflows, highlighting retail investor confidence.
- **Geographic Distribution:** Tier 1 cities account for the highest transaction volumes, though Tier 2 and Tier 3 cities show rapid growth in SIP adoption.

## 4. Performance Metrics
Using daily NAV returns and the NIFTY 50 as a benchmark (with a 6.5% risk-free rate):
- **Sharpe Ratio:** Evaluated risk-adjusted returns. Top performers consistently clustered in the Mid Cap and Small Cap categories.
- **Alpha & Beta:** Small Cap funds generally exhibited higher Beta (>1.0) and significant positive Alpha, compensating investors for the additional volatility.

## 5. Investor Behaviour Analysis
- **Cohort Analysis:** Grouping investors by their first transaction year revealed that older cohorts tend to have higher average SIP amounts.
- **SIP Continuity:** Analysis of transaction gaps flagged investors with irregular contributions, providing a basis for potential churn prediction models.

## 6. Portfolio Analytics
### Herfindahl-Hirschman Index (HHI)
Sector concentration was evaluated using HHI. Funds with HHI > 0.15 were flagged as highly concentrated, exposing them to sector-specific shocks.

### Monte Carlo Simulation
10,000 Geometric Brownian Motion (GBM) paths were simulated over 5 years. Results indicate significant upside potential for Mid/Small Cap funds, albeit with wider confidence bands compared to Large Cap funds.

### Markowitz Efficient Frontier
A 5-fund portfolio optimisation was conducted. The Maximum Sharpe portfolio heavily weighted high risk-adjusted return funds, while the Minimum Variance portfolio favoured less volatile Large Cap funds.

## 7. Recommendations
1. **For Conservative Investors:** Allocate heavily to Large Cap funds with low historical VaR and high Sortino ratios.
2. **For Aggressive Investors:** Mid Cap and Small Cap funds offer higher Alphas but require a longer investment horizon due to wider Monte Carlo confidence bands.
3. **Business Strategy:** Target SIP marketing campaigns towards Tier 2 cities, which show high growth potential based on cohort trends.

## 8. Appendix
- **Data Sources:** AMFI India, Bluestock Fintech internal datasets.
- **Key Tools:** Python (Pandas, NumPy, Plotly, Streamlit), SQLite.
- **Database Schema:** Available in `sql/01_create_schema.sql` (converted to SQLite dialect during ETL).
