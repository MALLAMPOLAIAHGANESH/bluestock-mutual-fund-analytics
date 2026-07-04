# backend/app/database/schemas.py
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional

# --- Fund House ---
class FundHouseBase(BaseModel):
    name: str = Field(..., max_length=200)

class FundHouseCreate(FundHouseBase):
    pass

class FundHouse(FundHouseBase):
    id: int
    
    class Config:
        from_attributes = True

# --- Category ---
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)

class Category(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True

# --- Risk Metrics ---
class RiskMetricsBase(BaseModel):
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    std_dev_ann_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None

class RiskMetrics(RiskMetricsBase):
    amfi_code: int
    
    class Config:
        from_attributes = True

# --- Returns ---
class ReturnsBase(BaseModel):
    return_1yr_pct: Optional[float] = None
    return_3yr_pct: Optional[float] = None
    return_5yr_pct: Optional[float] = None
    benchmark_3yr_pct: Optional[float] = None

class Returns(ReturnsBase):
    amfi_code: int
    
    class Config:
        from_attributes = True

# --- Scheme ---
class SchemeBase(BaseModel):
    amfi_code: int
    scheme_name: str = Field(..., max_length=500)
    sub_category: Optional[str] = None
    plan: str = Field(..., max_length=20)
    launch_date: Optional[date] = None
    benchmark: Optional[str] = None
    expense_ratio_pct: float = 0.0
    exit_load_pct: float = 0.0
    min_sip_amount: float = 500.0
    min_lumpsum_amount: float = 1000.0
    fund_manager: Optional[str] = None
    risk_category: Optional[str] = None

class SchemeCreate(SchemeBase):
    fund_house_id: int
    category_id: int

class Scheme(SchemeBase):
    fund_house: FundHouse
    category: Category
    risk_metrics: Optional[RiskMetrics] = None
    returns: Optional[Returns] = None
    
    class Config:
        from_attributes = True

# --- NAV History ---
class NAVHistoryBase(BaseModel):
    nav_date: date
    nav: float = Field(..., gt=0)

class NAVHistoryCreate(NAVHistoryBase):
    amfi_code: int

class NAVHistory(NAVHistoryBase):
    id: int
    amfi_code: int
    
    class Config:
        from_attributes = True

# --- Investor ---
class InvestorBase(BaseModel):
    investor_id: str
    age_group: Optional[str] = None
    gender: Optional[str] = None
    annual_income_lakh: Optional[float] = None

class Investor(InvestorBase):
    class Config:
        from_attributes = True

# --- Portfolio Holdings ---
class PortfolioHoldingBase(BaseModel):
    amfi_code: int
    weight_pct: float = Field(..., gt=0, le=100)

class PortfolioHoldingCreate(PortfolioHoldingBase):
    pass

class PortfolioHolding(PortfolioHoldingBase):
    id: int
    portfolio_id: int
    scheme: Scheme
    
    class Config:
        from_attributes = True

# --- Portfolio ---
class PortfolioBase(BaseModel):
    name: str = Field("My Portfolio", max_length=100)

class PortfolioCreate(PortfolioBase):
    investor_id: str
    holdings: List[PortfolioHoldingCreate]

class Portfolio(PortfolioBase):
    id: int
    investor_id: str
    created_at: datetime
    holdings: List[PortfolioHolding]
    
    class Config:
        from_attributes = True

# --- Portfolio Optimization ---
class PortfolioOptimizeRequest(BaseModel):
    amfi_codes: List[int]
    risk_free_rate: float = 6.5

class PortfolioOptimizeResponse(BaseModel):
    optimal_weights: dict
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float

# --- Transaction ---
class TransactionBase(BaseModel):
    investor_id: str
    amfi_code: int
    transaction_type: str = Field(..., pattern="^(SIP|Lumpsum|Redemption)$")
    amount_inr: float = Field(..., gt=0)
    transaction_date: date
    city_tier: Optional[str] = None
    state: Optional[str] = None

class Transaction(TransactionBase):
    id: int
    scheme: Scheme
    
    class Config:
        from_attributes = True

# --- Dashboard Summary ---
class DashboardSummary(BaseModel):
    total_aum: float
    active_schemes_count: int
    fund_houses_count: int
    average_cagr_3y: float
    average_expense_ratio: float
    portfolio_health_score: float
    best_performing_fund: str
    lowest_volatility_fund: str
