# backend/app/api/v1/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.database import schemas
from app.database.repositories import FundRepository, NAVRepository
from app.services.services import FundService, PortfolioService, SimulationService

router = APIRouter()

# --- 1. Dashboard Endpoint ---
@router.get("/dashboard", response_model=schemas.DashboardSummary)
def get_dashboard(db: Session = Depends(get_db)):
    """Retrieve high-level business analytics KPIs for the main dashboard."""
    try:
        service = FundService(db)
        return service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error compiling dashboard metrics: {e}"
        )

# --- 2. Funds Endpoints ---
@router.get("/funds", response_model=List[schemas.Scheme])
def get_funds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List mutual fund schemes with optional category filtering and search."""
    repo = FundRepository(db)
    return repo.get_schemes(skip=skip, limit=limit, category=category, search=search)

@router.get("/fund/{amfi_code}", response_model=schemas.Scheme)
def get_fund_by_id(amfi_code: int, db: Session = Depends(get_db)):
    """Retrieve detailed scheme specs by its AMFI code."""
    repo = FundRepository(db)
    scheme = repo.get_scheme(amfi_code)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    return scheme

# --- 3. NAV History ---
@router.get("/fund/{amfi_code}/nav", response_model=List[schemas.NAVHistory])
def get_nav_history(amfi_code: int, db: Session = Depends(get_db)):
    """Fetch complete daily NAV price timeline for a scheme."""
    repo = NAVRepository(db)
    return repo.get_nav_history(amfi_code)

# --- 4. Risk & Analytics ---
@router.get("/risk", response_model=List[schemas.RiskMetrics])
def get_risk_metrics(db: Session = Depends(get_db)):
    """List calculated volatility, Sharpe, Sortino, VaR, and max drawdowns."""
    from app.database.models import RiskMetrics as DB_RiskMetrics
    return db.query(DB_RiskMetrics).all()

# --- 5. Portfolio Optimization ---
@router.post("/portfolio/optimize", response_model=schemas.PortfolioOptimizeResponse)
def run_portfolio_optimizer(payload: schemas.PortfolioOptimizeRequest, db: Session = Depends(get_db)):
    """Calculate maximum Sharpe weights for selected assets using Markowitz frontier."""
    try:
        service = PortfolioService(db)
        return service.optimize_portfolio_weights(payload.amfi_codes, payload.risk_free_rate)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {e}"
        )

@router.get("/portfolio/recommend", response_model=List[dict])
def get_recommendations(
    risk_tier: str = Query("Moderate", pattern="^(Low|Moderate|High|Very High)$"),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Recommend top performing funds based on user risk profiles."""
    service = PortfolioService(db)
    return service.recommend_funds_for_user(risk_tier, limit)

# --- 6. Monte Carlo Forecasts ---
@router.get("/monte-carlo/{amfi_code}")
def get_monte_carlo_sim(
    amfi_code: int,
    years: int = Query(5, ge=1, le=10),
    simulations: int = Query(1000, ge=100, le=10000),
    db: Session = Depends(get_db)
):
    """Simulate 5-year growth trajectory using Geometric Brownian Motion (10,000 paths)."""
    try:
        service = SimulationService(db)
        return service.run_monte_carlo_simulation(amfi_code, years, simulations)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monte carlo simulation failed: {e}"
        )
