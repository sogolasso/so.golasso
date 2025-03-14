from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.database import get_db
from app.schemas.article import Article, ArticleCreate, ArticleUpdate
from app.services.article_service import ArticleService
from app.services.distribution_service import DistributionService
from app.services.seo_service import SEOService
from app.services.monetization_service import MonetizationService

router = APIRouter()

@router.post("/articles/", response_model=Article)
async def create_article(
    article: ArticleCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new article and process it for distribution."""
    article_service = ArticleService(db)
    distribution_service = DistributionService()
    seo_service = SEOService()
    monetization_service = MonetizationService()
    
    # Create article
    db_article = await article_service.create_article(article)
    
    # Process article in background
    background_tasks.add_task(
        process_article_distribution,
        db_article,
        distribution_service,
        seo_service,
        monetization_service
    )
    
    return db_article

@router.get("/articles/{article_id}", response_model=Article)
async def get_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Get article with processed content."""
    article_service = ArticleService(db)
    monetization_service = MonetizationService()
    
    article = await article_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Process content for monetization
    processed = await monetization_service.process_content(article)
    article.content = processed["processed_content"]
    
    return article

@router.put("/articles/{article_id}", response_model=Article)
async def update_article(
    article_id: str,
    article: ArticleUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update article and reprocess distribution if needed."""
    article_service = ArticleService(db)
    distribution_service = DistributionService()
    seo_service = SEOService()
    monetization_service = MonetizationService()
    
    db_article = await article_service.update_article(article_id, article)
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Reprocess article in background if content changed
    if "content" in article.dict(exclude_unset=True):
        background_tasks.add_task(
            process_article_distribution,
            db_article,
            distribution_service,
            seo_service,
            monetization_service
        )
    
    return db_article

@router.get("/articles/", response_model=List[Article])
async def list_articles(
    skip: int = 0,
    limit: int = 10,
    category: str = None,
    is_trending: bool = None,
    db: Session = Depends(get_db)
):
    """List articles with optional filters."""
    article_service = ArticleService(db)
    return await article_service.get_articles(
        skip=skip,
        limit=limit,
        category=category,
        is_trending=is_trending
    )

@router.post("/articles/{article_id}/distribute")
async def trigger_distribution(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Manually trigger article distribution."""
    article_service = ArticleService(db)
    distribution_service = DistributionService()
    seo_service = SEOService()
    monetization_service = MonetizationService()
    
    article = await article_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    results = await process_article_distribution(
        article,
        distribution_service,
        seo_service,
        monetization_service
    )
    
    return {"status": "success", "results": results}

async def process_article_distribution(
    article: Article,
    distribution_service: DistributionService,
    seo_service: SEOService,
    monetization_service: MonetizationService
) -> Dict:
    """Process article for distribution, SEO, and monetization."""
    results = {}
    
    # Optimize for SEO
    seo_data = await seo_service.optimize_article(article)
    results["seo"] = seo_data
    
    # Process content for monetization
    monetization_data = await monetization_service.process_content(article)
    results["monetization"] = monetization_data
    
    # Distribute to social media
    distribution_data = await distribution_service.distribute_content(article)
    results["distribution"] = distribution_data
    
    # Submit to Google News
    news_submission = await seo_service.submit_to_google_news(article)
    results["google_news"] = news_submission
    
    return results 