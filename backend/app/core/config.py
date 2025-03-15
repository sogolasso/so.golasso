from pydantic_settings import BaseSettings
from typing import Optional, Literal, List
from functools import lru_cache
import os
from pydantic import validator

class Settings(BaseSettings):
    # Base settings
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    PROJECT_NAME: str = "Football Digest"
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    DEBUG: bool = False
    PORT: int = int(os.getenv("PORT", "10000"))  # Default to 10000 if not set
    VERSION: str = "1.0.0"  # Added version setting
    
    # Database (Required)
    DATABASE_URL: str
    
    # JWT (Optional for now)
    SECRET_KEY: str = "dummy-secret-key-for-development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Social Media API Keys (Optional for launch)
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    
    # Instagram Credentials (Optional for launch)
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    
    # OpenAI (Required)
    OPENAI_API_KEY: Optional[str] = None
    MAX_MONTHLY_AI_COST: float = 100.0
    
    # Content Settings
    MIN_ARTICLE_LENGTH: int = 300
    MAX_ARTICLE_LENGTH: int = 5000
    CONTENT_RETENTION_DAYS: int = 365
    MAX_ARTICLES_PER_CYCLE: int = 10
    
    # Distribution Settings
    POSTS_PER_DAY: int = 10
    MIN_TIME_BETWEEN_POSTS: int = 30  # minutes
    MAX_DAILY_TRENDING_POSTS: int = 5
    MAX_DAILY_MEME_POSTS: int = 2
    
    # Scheduler Settings
    SCRAPING_INTERVAL_MINUTES: int = 60
    
    # Rate Limiting Settings
    TWITTER_REQUESTS_PER_WINDOW: int = 100
    TWITTER_WINDOW_MINUTES: int = 15
    INSTAGRAM_REQUESTS_PER_WINDOW: int = 50
    INSTAGRAM_WINDOW_MINUTES: int = 30
    
    # AI Content Generation Settings
    MIN_CONTENT_SCORE: float = 5.0
    USE_GPT4_THRESHOLD: float = 8.0
    CACHE_DURATION_DAYS: int = 7
    
    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    NOTIFICATION_EMAILS: List[str] = [
        "so.mesmo.golasso@gmail.com",
        "goncalo.r.xavier@gmail.com"
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v
        
    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v):
        if not v:
            raise ValueError("OPENAI_API_KEY must be set")
        return v
        
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 