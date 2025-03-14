from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from .article_generator import ArticleGenerator, ArticleStyle
from .content_scorer import ContentType
from .content_scheduler import ContentScheduler
import os
from dotenv import load_dotenv
from performance_monitor import PerformanceMonitor

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Só Golasso AI Writer",
    description="API for generating football articles with Brazilian flair",
    version="1.0.0"
)

# Initialize components
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

article_generator = ArticleGenerator(api_key)
content_scheduler = ContentScheduler()

# Initialize performance monitor
performance_monitor = PerformanceMonitor()

class ArticleRequest(BaseModel):
    news: str
    tweets: Optional[List[str]] = []
    instagram_posts: Optional[List[str]] = []
    style: str = "narracao"  # Default to narrator style
    content_type: str = "match_result"  # Default to match result
    engagement_count: int = 0
    is_trending: bool = False
    has_engagement: bool = False

class ArticleResponse(BaseModel):
    titulo: str
    subtitulo: str
    corpo: str
    hashtags: List[str]
    perguntas_interativas: List[str]
    metadata: dict
    social_media: dict
    scheduling: dict

@app.post("/generate-article", response_model=ArticleResponse)
async def generate_article(request: ArticleRequest):
    """Generate and schedule a football article based on input content."""
    try:
        # Convert style string to enum
        try:
            style = ArticleStyle(request.style)
            content_type = ContentType(request.content_type)
        except ValueError:
            style = ArticleStyle.NARRACAO
            content_type = ContentType.MATCH_RESULT
        
        # Generate the article
        article_content = article_generator.generate_article(
            news=request.news,
            tweets=request.tweets,
            instagram_posts=request.instagram_posts,
            style=style
        )
        
        if not article_content:
            raise HTTPException(status_code=500, detail="Failed to generate article")
        
        # Optimize for SEO
        article_content = article_generator.optimize_seo(article_content)
        
        # Create social media posts
        social_media_posts = article_generator.create_social_media_posts(article_content)
        article_content["social_media"] = social_media_posts
        
        # Schedule the content
        scheduling = content_scheduler.schedule_content(
            content=article_content,
            content_type=content_type,
            engagement_count=request.engagement_count,
            is_trending=request.is_trending,
            has_engagement=request.has_engagement
        )
        
        article_content["scheduling"] = scheduling
        
        return article_content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/styles")
async def get_available_styles():
    """Get list of available article styles."""
    return {
        "styles": [
            {
                "id": style.value,
                "name": style.name,
                "description": {
                    "narracao": "Estilo de narrador esportivo, empolgante e dramático",
                    "tatica": "Análise tática profissional e técnica",
                    "zoacao": "Estilo bem-humorado com memes e zoação"
                }[style.value]
            }
            for style in ArticleStyle
        ]
    }

@app.get("/content-types")
async def get_content_types():
    """Get list of available content types."""
    return {
        "content_types": [
            {
                "id": ct.value,
                "name": ct.name,
                "base_score": {
                    "match_result": 10,
                    "transfer_news": 8,
                    "tactical_analysis": 6,
                    "team_update": 4,
                    "rumor": 2
                }[ct.value]
            }
            for ct in ContentType
        ]
    }

@app.get("/schedule")
async def get_schedule():
    """Get current publishing schedule."""
    return content_scheduler.get_publishing_schedule()

@app.get("/daily-stats")
async def get_daily_stats():
    """Get current daily publishing statistics."""
    return content_scheduler.get_daily_stats()

@app.get("/health")
async def health_check():
    """Check if the service is running."""
    return {"status": "healthy", "version": "1.0.0"}

# Add monitoring endpoints
@app.post("/track-interaction")
async def track_interaction(
    content_id: str,
    user_id: str,
    style: str,
    metrics: Dict
):
    """Track content interaction metrics."""
    performance_monitor.track_interaction(
        content_id=content_id,
        user_id=user_id,
        style=style,
        metrics=metrics
    )
    return {"status": "success"}

@app.get("/content-performance/{content_id}")
async def get_content_performance(content_id: str):
    """Get performance metrics for specific content."""
    metrics = performance_monitor.get_content_performance(content_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return metrics

@app.get("/style-performance/{style}")
async def get_style_performance(style: str):
    """Get performance metrics for a writing style."""
    metrics = performance_monitor.get_style_performance(style)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Style not found")
    return metrics

@app.get("/daily-summary")
async def get_daily_summary(days: int = 7):
    """Get daily performance summary."""
    return performance_monitor.get_daily_summary(days)

@app.get("/hourly-summary")
async def get_hourly_summary(hours: int = 24):
    """Get hourly performance summary."""
    return performance_monitor.get_hourly_summary(hours)

@app.get("/top-performing")
async def get_top_performing(metric: str = "views", limit: int = 10):
    """Get top performing content."""
    return performance_monitor.get_top_performing_content(metric, limit)

@app.get("/style-comparison")
async def get_style_comparison():
    """Compare performance across different writing styles."""
    return performance_monitor.get_style_comparison()

@app.get("/dashboard")
async def get_dashboard():
    """Get comprehensive dashboard data."""
    return performance_monitor.get_dashboard_data() 