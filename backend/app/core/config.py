from pydantic_settings import BaseSettings
from typing import Optional, Literal
from functools import lru_cache

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
    SECRET_KEY: Optional[str] = "dummy-secret-key-for-development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Social Media API Keys (Optional for launch)
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_SECRET: Optional[str] = None
    
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    
    # OpenAI (Optional for launch)
    OPENAI_API_KEY: Optional[str] = None
    MAX_MONTHLY_AI_COST: float = 100.0  # Maximum monthly spending on OpenAI API
    
    # Google Services (Optional for launch)
    GOOGLE_ANALYTICS_ID: Optional[str] = None
    ADSENSE_CLIENT_ID: Optional[str] = None
    ADSENSE_IN_ARTICLE_SLOT: Optional[str] = None
    ADSENSE_SIDEBAR_SLOT: Optional[str] = None
    
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
    MIN_CONTENT_SCORE: float = 5.0  # Minimum score for content to be processed
    USE_GPT4_THRESHOLD: float = 8.0  # Score threshold to use GPT-4 instead of GPT-3.5
    CACHE_DURATION_DAYS: int = 7  # How long to cache AI-generated content
    
    # SEO Settings
    GOOGLE_NEWS_PING_INTERVAL: int = 60  # minutes
    SITEMAP_UPDATE_INTERVAL: int = 60  # minutes
    
    # Monetization Settings
    AD_FREQUENCY: int = 3  # ads per article
    MIN_WORDS_BETWEEN_ADS: int = 150
    
    # Application settings
    APP_NAME: str = "Só Golasso API"
    APP_VERSION: str = "1.0.0"
    
    # CORS settings
    FRONTEND_URL: str = "https://sogolasso.me"
    
    # AWS S3 settings for media storage (Optional for now)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Redis settings for caching (Optional for launch)
    REDIS_URL: Optional[str] = None

    # Email settings (Optional for launch)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAIL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 