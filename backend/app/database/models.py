# backend/app/database/models.py
from sqlalchemy import Column, Integer, BigInteger, Float, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

class FundHouse(Base):
    __tablename__ = "fund_houses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    
    schemes = relationship("Scheme", back_populates="fund_house")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    schemes = relationship("Scheme", back_populates="category")

class Scheme(Base):
    __tablename__ = "schemes"
    
    amfi_code = Column(BigInteger, primary_key=True, index=True)
    scheme_name = Column(String(500), nullable=False)
    fund_house_id = Column(Integer, ForeignKey("fund_houses.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sub_category = Column(String(100))
    plan = Column(String(20), nullable=False)  # Regular / Direct
    launch_date = Column(Date)
    benchmark = Column(String(200))
    expense_ratio_pct = Column(Float, default=0.0)
    exit_load_pct = Column(Float, default=0.0)
    min_sip_amount = Column(Float, default=500.0)
    min_lumpsum_amount = Column(Float, default=1000.0)
    fund_manager = Column(String(300))
    risk_category = Column(String(50))  # Low / Moderate / High / Very High
    
    fund_house = relationship("FundHouse", back_populates="schemes")
    category = relationship("Category", back_populates="schemes")
    nav_history = relationship("NAVHistory", back_populates="scheme", cascade="all, delete-orphan")
    risk_metrics = relationship("RiskMetrics", uselist=False, back_populates="scheme")
    returns = relationship("Returns", uselist=False, back_populates="scheme")

class NAVHistory(Base):
    __tablename__ = "nav_history"
    
    id = Column(BigInteger, primary_key=True, index=True)
    amfi_code = Column(BigInteger, ForeignKey("schemes.amfi_code"), nullable=False)
    nav_date = Column(Date, nullable=False, index=True)
    nav = Column(Float, nullable=False)
    
    scheme = relationship("Scheme", back_populates="nav_history")
    
    __table_args__ = (UniqueConstraint("amfi_code", "nav_date", name="uq_scheme_nav_date"),)

class RiskMetrics(Base):
    __tablename__ = "risk_metrics"
    
    amfi_code = Column(BigInteger, ForeignKey("schemes.amfi_code"), primary_key=True)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    treynor_ratio = Column(Float)
    alpha = Column(Float)
    beta = Column(Float)
    std_dev_ann_pct = Column(Float)
    max_drawdown_pct = Column(Float)
    var_95 = Column(Float)
    cvar_95 = Column(Float)
    tracking_error = Column(Float)
    information_ratio = Column(Float)
    calmar_ratio = Column(Float)
    
    scheme = relationship("Scheme", back_populates="risk_metrics")

class Returns(Base):
    __tablename__ = "returns"
    
    amfi_code = Column(BigInteger, ForeignKey("schemes.amfi_code"), primary_key=True)
    return_1yr_pct = Column(Float)
    return_3yr_pct = Column(Float)
    return_5yr_pct = Column(Float)
    benchmark_3yr_pct = Column(Float)
    
    scheme = relationship("Scheme", back_populates="returns")

class Investor(Base):
    __tablename__ = "investors"
    
    investor_id = Column(String(50), primary_key=True, index=True)
    age_group = Column(String(20))
    gender = Column(String(20))
    annual_income_lakh = Column(Float)
    
    portfolios = relationship("Portfolio", back_populates="investor")
    transactions = relationship("Transaction", back_populates="investor")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(String(50), ForeignKey("investors.investor_id"), nullable=False)
    name = Column(String(100), default="My Portfolio")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    investor = relationship("Investor", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    amfi_code = Column(BigInteger, ForeignKey("schemes.amfi_code"), nullable=False)
    weight_pct = Column(Float, nullable=False)  # Weight in percentage (e.g. 25.0)
    
    portfolio = relationship("Portfolio", back_populates="holdings")
    scheme = relationship("Scheme")
    
    __table_args__ = (UniqueConstraint("portfolio_id", "amfi_code", name="uq_portfolio_scheme"),)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    investor_id = Column(String(50), ForeignKey("investors.investor_id"), nullable=False)
    amfi_code = Column(BigInteger, ForeignKey("schemes.amfi_code"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # SIP / Lumpsum / Redemption
    amount_inr = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    city_tier = Column(String(10))  # T30 / B30
    state = Column(String(100))
    
    investor = relationship("Investor", back_populates="transactions")
    scheme = relationship("Scheme")
