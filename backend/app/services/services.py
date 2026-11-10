# backend/app/services/services.py
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from app.database.repositories import FundRepository, NAVRepository, PortfolioRepository
from app.analytics.engine import calculate_hhi
from app.machine_learning.engine import optimize_portfolio, run_monte_carlo, recommend_funds
from app.database.models import Scheme, RiskMetrics, Returns

class FundService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FundRepository(db)

    def get_dashboard_summary(self) -> Dict[str, Any]:
        # Query total AUM, scheme count, and amc count
        query_aum = self.db.query(
            func.sum(RiskMetrics.aum_crore),
            func.count(Scheme.amfi_code)
        ).select_from(Scheme).join(RiskMetrics, isouter=True).first()
        
        total_aum = float(query_aum[0] or 0.0)
        total_funds = int(query_aum[1] or 0)
        
        total_amcs = self.db.query(func.count(func.distinct(Scheme.fund_house_id))).scalar()
        
        # Calculate averages
        avg_cagr = self.db.query(func.avg(Returns.return_3yr_pct)).scalar() or 0.0
        avg_expense = self.db.query(func.avg(Scheme.expense_ratio_pct)).scalar() or 0.0
        
        # Best performing fund (3Y CAGR)
        best_fund = self.db.query(Scheme.scheme_name, Returns.return_3yr_pct)\
            .join(Returns).order_by(Returns.return_3yr_pct.desc()).first()
        best_name = best_fund[0] if best_fund else "N/A"
        
        # Lowest volatility fund
        lowest_vol = self.db.query(Scheme.scheme_name, RiskMetrics.std_dev_ann_pct)\
            .join(RiskMetrics).order_by(RiskMetrics.std_dev_ann_pct.asc()).first()
        lowest_vol_name = lowest_vol[0] if lowest_vol else "N/A"
        
        # Health score: % of schemes beating benchmark return or with Sharpe > 0.8
        total_valid = self.db.query(func.count(RiskMetrics.amfi_code)).filter(RiskMetrics.sharpe_ratio > 0.8).scalar()
        health_score = (total_valid / total_funds * 100.0) if total_funds > 0 else 100.0
        
        return {
            "total_aum": total_aum,
            "active_schemes_count": total_funds,
            "fund_houses_count": total_amcs,
            "average_cagr_3y": float(avg_cagr),
            "average_expense_ratio": float(avg_expense),
            "portfolio_health_score": float(health_score),
            "best_performing_fund": best_name,
            "lowest_volatility_fund": lowest_vol_name
        }

# SQLAlchemy func import for safety
from sqlalchemy import func

class PortfolioService:
    def __init__(self, db: Session):
        self.db = db
        self.nav_repo = NAVRepository(db)
        self.repo = PortfolioRepository(db)

    def optimize_portfolio_weights(self, amfi_codes: List[int], risk_free_rate: float) -> Dict[str, Any]:
        # Fetch NAV histories
        nav_dfs = []
        for code in amfi_codes:
            navs = self.nav_repo.get_nav_history(code)
            if not navs:
                continue
            dates = [n.nav_date for n in navs]
            prices = [n.nav for n in navs]
            df = pd.DataFrame({"date": dates, str(code): prices})
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            nav_dfs.append(df)
            
        if not nav_dfs:
            raise ValueError("No historical NAV data found for chosen funds.")
            
        # Align prices on date index
        aligned_df = nav_dfs[0]
        for df in nav_dfs[1:]:
            aligned_df = aligned_df.join(df, how="inner")
            
        # Calculate daily returns
        returns_df = aligned_df.pct_change().dropna()
        
        if len(returns_df) < 10:
            raise ValueError("Insufficient overlapping trading days to calculate covariance.")
            
        weights, p_ret, p_vol, sharpe = optimize_portfolio(returns_df, risk_free_rate)
        
        # Map weights back to codes
        opt_weights_dict = {str(code): float(w) for code, w in zip(amfi_codes, weights)}
        
        return {
            "optimal_weights": opt_weights_dict,
            "expected_return": float(p_ret),
            "expected_volatility": float(p_vol),
            "sharpe_ratio": float(sharpe)
        }

    def recommend_funds_for_user(self, risk_tier: str, top_n: int = 3) -> List[Dict[str, Any]]:
        # Fetch all funds with performance
        schemes = self.db.query(Scheme).options(
            joinedload(Scheme.risk_metrics),
            joinedload(Scheme.returns)
        ).all()
        
        funds_list = []
        for s in schemes:
            funds_list.append({
                "amfi_code": s.amfi_code,
                "scheme_name": s.scheme_name,
                "risk_category": s.risk_category,
                "sharpe_ratio": s.risk_metrics.sharpe_ratio if s.risk_metrics else 0.0
            })
            
        return recommend_funds(risk_tier, funds_list, top_n)

class SimulationService:
    def __init__(self, db: Session):
        self.db = db

    def run_monte_carlo_simulation(self, amfi_code: int, years: int = 5, simulations: int = 1000) -> Dict[str, Any]:
        # Get latest NAV, CAGR, and volatility
        scheme = self.db.query(Scheme).filter(Scheme.amfi_code == amfi_code).first()
        if not scheme:
            raise ValueError("Scheme not found.")
            
        latest_nav_record = self.db.query(NAVHistory).filter(NAVHistory.amfi_code == amfi_code)\
            .order_by(NAVHistory.nav_date.desc()).first()
        initial_nav = latest_nav_record.nav if latest_nav_record else 10.0
        
        # Query return and risk metrics
        returns = self.db.query(Returns).filter(Returns.amfi_code == amfi_code).first()
        risk = self.db.query(RiskMetrics).filter(RiskMetrics.amfi_code == amfi_code).first()
        
        annual_return = float(returns.return_3yr_pct) if returns and returns.return_3yr_pct else 12.0
        annual_volatility = float(risk.std_dev_ann_pct) if risk and risk.std_dev_ann_pct else 15.0
        
        paths = run_monte_carlo(
            initial_nav=initial_nav,
            annual_return=annual_return,
            annual_volatility=annual_volatility,
            num_years=years,
            num_simulations=simulations
        )
        
        # Calculate percentiles (final outcomes)
        final_values = paths[-1, :]
        percentiles = {
            "10th_percentile": float(np.percentile(final_values, 10)),
            "50th_percentile": float(np.percentile(final_values, 50)),
            "90th_percentile": float(np.percentile(final_values, 90))
        }
        
        # Convert steps to readable date-relative list or select subset of paths for charting
        steps_count = paths.shape[0]
        # Choose 10 sample paths to return to frontend
        sample_paths = [paths[:, i].tolist() for i in range(min(10, simulations))]
        
        return {
            "amfi_code": amfi_code,
            "scheme_name": scheme.scheme_name,
            "initial_nav": initial_nav,
            "simulated_percentiles": percentiles,
            "sample_paths": sample_paths
        }

from sqlalchemy.orm import joinedload
