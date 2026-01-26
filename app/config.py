from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import json

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/survey_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Clerk Authentication
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_WEBHOOK_SECRET: Optional[str] = None
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # File Upload
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/gif,image/webp"
    
    # Server
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Production settings
    PRODUCTION: bool = False
    
    # Vercel / Production URLs
    VERCEL_URL: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS as a list."""
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        if os.getenv("PRODUCTION_FRONTEND_URL"):
            origins.append(os.getenv("PRODUCTION_FRONTEND_URL"))
        if self.VERCEL_URL:
            origins.append(f"https://{self.VERCEL_URL}")
        return origins
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Parse ALLOWED_IMAGE_TYPES as a list."""
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

settings = Settings()
