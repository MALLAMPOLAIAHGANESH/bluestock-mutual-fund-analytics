# backend/app/api/v1/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from app.core.database import get_db
from app.database import schemas
from app.database.repositories import FundRepository, NAVRepository
from app.services.services import FundService, PortfolioService, SimulationService
from app.core.config import settings

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

# --- 7. Downloads Management ---
DOWNLOADS_MAP = {
    # Fallback keys for Analysis Dashboard top headers
    "csv": ("datasets/processed_dataset.csv", "text/csv", "dataset.csv"),
    "excel": ("datasets/excel_dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "dataset.xlsx"),
    "pdf": ("reports/final_project_report.pdf", "application/pdf", "final_project_report.pdf"),

    "performance-pdf": ("reports/performance_report.pdf", "application/pdf", "performance_report.pdf"),
    "performance-excel": ("datasets/excel_dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "performance_report.xlsx"),
    "risk-pdf": ("reports/risk_report.pdf", "application/pdf", "risk_report.pdf"),
    "risk-csv": ("datasets/processed_dataset.csv", "text/csv", "risk_report.csv"),
    "risk-excel": ("datasets/excel_dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "risk_report.xlsx"),
    "risk-pdf-full": ("reports/final_project_report.pdf", "application/pdf", "final_project_report.pdf"),
    "sip-pdf": ("reports/sip_analysis_report.pdf", "application/pdf", "sip_analysis_report.pdf"),
    "sip-excel": ("datasets/excel_dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "sip_analysis_report.xlsx"),
    "tax-pdf": ("reports/tax_report.pdf", "application/pdf", "tax_report.pdf"),
    "tax-excel": ("datasets/excel_dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "tax_report.xlsx"),

    "raw-csv": ("datasets/raw_dataset.csv", "text/csv", "raw_dataset.csv"),
    "processed-csv": ("datasets/processed_dataset.csv", "text/csv", "processed_dataset.csv"),
    "excel-data": ("datasets/excel_dataset.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "excel_dataset.xlsx"),
    "zip-archive": ("datasets/zip_archive.zip", "application/zip", "zip_archive.zip"),
    "sample-csv": ("datasets/sample_dataset.csv", "text/csv", "sample_dataset.csv"),
    "dictionary-pdf": ("datasets/data_dictionary.pdf", "application/pdf", "data_dictionary.pdf"),

    "sqlite-db": ("database/sqlite_database.db", "application/x-sqlite3", "sqlite_database.db"),
    "sql-schema": ("database/sql_schema.sql", "text/plain", "sql_schema.sql"),
    "er-pdf": ("database/er_diagram.pdf", "application/pdf", "er_diagram.pdf"),
    "db-backup": ("database/database_backup.zip", "application/zip", "database_backup.zip"),

    "eda-ipynb": ("notebooks/eda_notebook.ipynb", "application/x-ipynb+json", "eda_notebook.ipynb"),
    "montecarlo-ipynb": ("notebooks/montecarlo_simulation.ipynb", "application/x-ipynb+json", "montecarlo_simulation.ipynb"),
    "markowitz-ipynb": ("notebooks/markowitz_optimization.ipynb", "application/x-ipynb+json", "markowitz_optimization.ipynb"),
    "risk-ipynb": ("notebooks/risk_analysis.ipynb", "application/x-ipynb+json", "risk_analysis.ipynb"),
    "notebooks-html": ("notebooks/notebooks_html.html", "text/html", "notebooks_html.html"),
    "notebooks-pdf": ("notebooks/notebooks_pdf.pdf", "application/pdf", "notebooks_pdf.pdf"),

    "powerbi-pbix": ("powerbi/powerbi_dashboard.pbix", "application/octet-stream", "powerbi_dashboard.pbix"),
    "powerbi-pbit": ("powerbi/powerbi_template.pbit", "application/octet-stream", "powerbi_template.pbit"),
    "powerbi-pdf": ("powerbi/powerbi_report.pdf", "application/pdf", "powerbi_report.pdf"),
    "powerbi-screenshots": ("powerbi/dashboard_screenshots.png", "image/png", "dashboard_screenshots.png"),

    "project-report-pdf": ("reports/final_project_report.pdf", "application/pdf", "final_project_report.pdf"),
    "summary-pdf": ("reports/executive_summary.pdf", "application/pdf", "executive_summary.pdf"),

    "etl-py": ("scripts/etl_pipeline.py", "text/plain", "etl_pipeline.py"),
    "clean-py": ("scripts/data_cleaning.py", "text/plain", "data_cleaning.py"),
    "risk-py": ("scripts/risk_analytics.py", "text/plain", "risk_analytics.py"),
    "montecarlo-py": ("scripts/monte_carlo.py", "text/plain", "monte_carlo.py"),
    "markowitz-py": ("scripts/markowitz.py", "text/plain", "markowitz.py"),
    "utils-py": ("scripts/utility_functions.py", "text/plain", "utility_functions.py"),
    "src-zip": ("scripts/complete_source_code.zip", "application/zip", "complete_source_code.zip"),
    "req-txt": ("scripts/requirements.txt", "text/plain", "requirements.txt"),
}

def _get_file_path(rel_path: str) -> str:
    """Helper to resolve the absolute file path across varying BASE_DIR levels."""
    # Attempt capstone root first
    root = os.path.join(settings.BASE_DIR, "downloads")
    if not os.path.exists(root):
        root = os.path.join(settings.BASE_DIR.parent, "downloads")
    return os.path.join(root, rel_path)

@router.get("/downloads/{file_key}/exists")
def check_file_existence(file_key: str):
    """Verify if a downloadable file exists in storage."""
    if file_key not in DOWNLOADS_MAP:
        return {"exists": False}
    rel_path, _, _ = DOWNLOADS_MAP[file_key]
    file_path = _get_file_path(rel_path)
    return {"exists": os.path.exists(file_path)}

@router.get("/downloads/{file_key}")
def download_file(file_key: str):
    """Serve the requested file directly to trigger browser download."""
    if file_key not in DOWNLOADS_MAP:
        raise HTTPException(status_code=404, detail="File mapping not found")
    rel_path, media_type, download_name = DOWNLOADS_MAP[file_key]
    file_path = _get_file_path(rel_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested file not found on disk")
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_name
    )
