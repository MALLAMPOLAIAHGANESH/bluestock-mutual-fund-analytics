# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Bluestock Mutual Fund Analytics API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Path Configuration
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./bluestock_mf.db"
    
    # Security Settings
    SECRET_KEY: str = "production_super_secret_key_change_me_in_env_file_1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
