# backend/app/core/logging.py
import sys
from pathlib import Path
from loguru import logger
from .config import settings

def setup_logging():
    # Clear default handlers
    logger.remove()
    
    # Base format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True
    )
    
    # File handler with rotation and compression
    log_dir = settings.BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        format=log_format,
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True
    )
    
    logger.info("Structured logging pipeline initialized successfully.")
