# backend/app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import Base, engine, SessionLocal
from app.api.v1.endpoints import router as api_router
from app.etl.pipeline import ETLPipeline

# 1. Setup logging
setup_logging()

# 2. Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade Clean Architecture Mutual Fund Analytics API featuring portfolio optimization and risk simulations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Request validation failure on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )

# 5. Startup Event: Setup DB and Run ETL
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if database is already populated
        from app.database.models import Scheme
        if db.query(Scheme).count() == 0:
            logger.info("Database is empty. Initiating ETL pipeline...")
            # Resolve raw directory path relative to project
            raw_dir = settings.BASE_DIR / "data" / "raw"
            if not raw_dir.exists():
                # Try fallback parent directory path
                raw_dir = settings.BASE_DIR / "bluestock_mf_capstone" / "data" / "raw"
                
            if raw_dir.exists():
                etl = ETLPipeline(db, raw_dir)
                etl.run_pipeline()
            else:
                logger.error(f"ETL raw data folder not found at: {raw_dir}")
        else:
            logger.info("Database already populated. Skipping ETL startup process.")
    except Exception as e:
        logger.error(f"Startup task failed: {e}")
    finally:
        db.close()

# 6. Include Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
