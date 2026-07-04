# backend/app/database/repositories.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from .models import FundHouse, Category, Scheme, NAVHistory, RiskMetrics, Returns, Investor, Portfolio, PortfolioHolding, Transaction

class BaseRepository:
    def __init__(self, db: Session):
        self.db = db

class FundRepository(BaseRepository):
    def get_fund_house_by_name(self, name: str) -> Optional[FundHouse]:
        return self.db.query(FundHouse).filter(FundHouse.name == name).first()
        
    def create_fund_house(self, name: str) -> FundHouse:
        fh = FundHouse(name=name)
        self.db.add(fh)
        self.db.commit()
        self.db.refresh(fh)
        return fh

    def get_category_by_name(self, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.name == name).first()

    def create_category(self, name: str) -> Category:
        cat = Category(name=name)
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def get_scheme(self, amfi_code: int) -> Optional[Scheme]:
        return self.db.query(Scheme).options(
            joinedload(Scheme.fund_house),
            joinedload(Scheme.category),
            joinedload(Scheme.risk_metrics),
            joinedload(Scheme.returns)
        ).filter(Scheme.amfi_code == amfi_code).first()

    def get_schemes(self, skip: int = 0, limit: int = 100, category: Optional[str] = None, search: Optional[str] = None) -> List[Scheme]:
        query = self.db.query(Scheme).options(
            joinedload(Scheme.fund_house),
            joinedload(Scheme.category),
            joinedload(Scheme.risk_metrics),
            joinedload(Scheme.returns)
        )
        if category:
            query = query.join(Category).filter(Category.name == category)
        if search:
            query = query.filter(Scheme.scheme_name.ilike(f"%{search}%"))
        return query.offset(skip).limit(limit).all()

    def create_scheme(self, scheme_data: dict) -> Scheme:
        scheme = Scheme(**scheme_data)
        self.db.add(scheme)
        self.db.commit()
        self.db.refresh(scheme)
        return scheme

    def update_risk_metrics(self, amfi_code: int, metrics: dict) -> RiskMetrics:
        db_metrics = self.db.query(RiskMetrics).filter(RiskMetrics.amfi_code == amfi_code).first()
        if not db_metrics:
            db_metrics = RiskMetrics(amfi_code=amfi_code, **metrics)
            self.db.add(db_metrics)
        else:
            for k, v in metrics.items():
                setattr(db_metrics, k, v)
        self.db.commit()
        self.db.refresh(db_metrics)
        return db_metrics

    def update_returns(self, amfi_code: int, returns_data: dict) -> Returns:
        db_returns = self.db.query(Returns).filter(Returns.amfi_code == amfi_code).first()
        if not db_returns:
            db_returns = Returns(amfi_code=amfi_code, **returns_data)
            self.db.add(db_returns)
        else:
            for k, v in returns_data.items():
                setattr(db_returns, k, v)
        self.db.commit()
        self.db.refresh(db_returns)
        return db_returns

class NAVRepository(BaseRepository):
    def bulk_insert_navs(self, nav_records: List[dict]):
        self.db.bulk_insert_mappings(NAVHistory, nav_records)
        self.db.commit()

    def get_nav_history(self, amfi_code: int) -> List[NAVHistory]:
        return self.db.query(NAVHistory).filter(NAVHistory.amfi_code == amfi_code).order_by(NAVHistory.nav_date.asc()).all()

class InvestorRepository(BaseRepository):
    def get_or_create_investor(self, investor_id: str, age_group: str = None, gender: str = None, income: float = None) -> Investor:
        investor = self.db.query(Investor).filter(Investor.investor_id == investor_id).first()
        if not investor:
            investor = Investor(investor_id=investor_id, age_group=age_group, gender=gender, annual_income_lakh=income)
            self.db.add(investor)
            self.db.commit()
            self.db.refresh(investor)
        return investor

class PortfolioRepository(BaseRepository):
    def create_portfolio(self, investor_id: str, name: str, holdings: List[dict]) -> Portfolio:
        portfolio = Portfolio(investor_id=investor_id, name=name)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        for holding in holdings:
            db_holding = PortfolioHolding(
                portfolio_id=portfolio.id,
                amfi_code=holding["amfi_code"],
                weight_pct=holding["weight_pct"]
            )
            self.db.add(db_holding)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        return self.db.query(Portfolio).options(
            joinedload(Portfolio.holdings).joinedload(PortfolioHolding.scheme)
        ).filter(Portfolio.id == portfolio_id).first()

class TransactionRepository(BaseRepository):
    def bulk_insert_transactions(self, tx_records: List[dict]):
        self.db.bulk_insert_mappings(Transaction, tx_records)
        self.db.commit()

    def get_transactions(self, skip: int = 0, limit: int = 100) -> List[Transaction]:
        return self.db.query(Transaction).offset(skip).limit(limit).all()
