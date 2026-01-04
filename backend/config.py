from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str
    DATABASE_NAME: str = "chat_app"
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://chat-application-2-woad.vercel.app"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Port (for production deployment)
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"   
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Initialize settings
settings = Settings()


# Log configuration on startup (without sensitive data)
def log_config():
    """Log configuration for debugging (without sensitive values)."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_NAME}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Port: {settings.PORT}")
    logger.info(f"Is Production: {settings.is_production}")





