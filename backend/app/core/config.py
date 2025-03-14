from pydantic_settings import BaseSettings
from typing import Optional, Literal, List
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Base settings
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    PROJECT_NAME: str = "Só Golasso"
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = "https://sogolasso.me"
    DEBUG: bool = False
    
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
    
    # OpenAI (Required)
    OPENAI_API_KEY: str
    MAX_MONTHLY_AI_COST: float = 100.0
    
    # Content Settings
    MIN_ARTICLE_LENGTH: int = 300
    MAX_ARTICLE_LENGTH: int = 5000
    CONTENT_RETENTION_DAYS: int = 365
    
    # Distribution Settings
    POSTS_PER_DAY: int = 10
    MIN_TIME_BETWEEN_POSTS: int = 30  # minutes
    MAX_DAILY_TRENDING_POSTS: int = 5
    MAX_DAILY_MEME_POSTS: int = 2
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 