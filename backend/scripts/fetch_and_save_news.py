import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.scrapers.news_scraper import get_latest_news
from app.database import SessionLocal
from app.models.article import Article
from app.schemas.article import ArticleCreate
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_articles_to_db():
    """Fetch latest news and save to database."""
    # Get articles from scraper
    articles = get_latest_news()
    logger.info(f"Fetched {len(articles)} articles")
    
    # Create database session
    db = SessionLocal()
    try:
        for article_data in articles:
            # Check if article already exists (by title)
            existing = db.query(Article).filter(Article.title == article_data['title']).first()
            if existing:
                logger.info(f"Article already exists: {article_data['title']}")
                continue
            
            # Create new article
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                content_type=article_data['content_type'],
                source_url=article_data['url'],
                source_name=article_data['source'],
                engagement_count=0,
                is_trending=False,
                has_engagement=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(article)
            logger.info(f"Added new article: {article_data['title']}")
        
        db.commit()
        logger.info("Successfully saved articles to database")
        
        # Print the latest articles
        latest_articles = db.query(Article).order_by(Article.created_at.desc()).limit(5).all()
        print("\nLatest 5 articles in database:")
        for idx, article in enumerate(latest_articles, 1):
            print(f"\n{idx}. {article.title}")
            print(f"Type: {article.content_type}")
            print(f"Source: {article.source_name}")
            print("-" * 80)
            print(article.content[:200] + "...")  # First 200 chars
            print("=" * 80)
            
    except Exception as e:
        logger.error(f"Error saving articles: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    save_articles_to_db() 