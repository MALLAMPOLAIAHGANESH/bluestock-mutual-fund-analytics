# Data Cleaning Report — Bluestock Mutual Fund Capstone

**Generated:** 2026-06-23 11:26:01  
**Total Actions Logged:** 19  

---

## Cleaning Summary by Dataset

### 01_fund_master

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| amfi_code | UNIQUENESS_CHECK | All amfi_codes are unique ✓ | 0 |
| * | SUMMARY | Rows: 40 → 40 | 0 |

### 02_nav_history

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| * | SUMMARY | Rows: 46000 → 46000 | 0 |
| amfi_code | REFERENTIAL_INTEGRITY_PASS | All FK references valid ✓ | 0 |

### 03_aum_by_fund_house

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| aum_crore | CONSISTENCY_CHECK | AUM units consistent ✓ | 0 |
| * | SUMMARY | All 90 rows retained | 0 |

### 04_monthly_sip_inflows

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| yoy_growth_pct | NULL_DOCUMENTED_BUSINESS_LOGIC | 12 NULLs are EXPECTED for first 12 months (no prior year baseline). Rows retained. NULLs preserved as NULL in DB. | 12 |
| * | SUMMARY | All 48 rows retained | 0 |

### 05_category_inflows

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| * | SUMMARY | All 144 rows retained | 0 |

### 06_industry_folio_count

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| total_folios_crore | INTEGRITY_CHECK | Folio totals consistent ✓ | 0 |
| * | SUMMARY | All 21 rows retained | 0 |

### 07_scheme_performance

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| * | SUMMARY | Rows: 40 → 40 | 0 |
| amfi_code | REFERENTIAL_INTEGRITY_PASS | All FK references valid ✓ | 0 |

### 08_investor_transactions

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| annual_income_lakh | OUTLIER_FLAGGED | 587 records outside 1st–99th percentile range [3.3, 90.6] — documented, not dropped | 587 |
| * | SUMMARY | Rows: 32778 → 32778 | 0 |
| amfi_code | REFERENTIAL_INTEGRITY_PASS | All FK references valid ✓ | 0 |

### 09_portfolio_holdings

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| * | SUMMARY | All 322 rows retained | 0 |
| amfi_code | REFERENTIAL_INTEGRITY_PASS | All FK references valid ✓ | 0 |

### 10_benchmark_indices

| Column | Action | Details | Rows Affected |
|--------|--------|---------|---------------|
| * | SUMMARY | All 8050 rows retained | 0 |

---

## Key Business-Logic Decisions

1. **`yoy_growth_pct` NULLs (monthly_sip_inflows):** 12 NULLs in first year are EXPECTED — year-over-year requires a prior-year baseline. Rows retained, NULLs preserved.
2. **Referential Integrity:** All child tables validated against fund_master before DB load.
3. **NAV Positivity:** Zero or negative NAV values dropped — mathematically impossible.
4. **Expense Ratio SEBI Limits:** Flagged but not dropped — requires business review.
5. **max_drawdown_pct Sign Convention:** Must be negative (represents a loss).
