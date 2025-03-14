import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.core.scraping_scheduler import ScrapingScheduler
from app.db.session import SessionLocal
from app.models.article import Article
from app.models.enums import ArticleStatus

async def test_pipeline():
    """Test the entire pipeline from scraping to publishing"""
    db = None
    try:
        logger.info("Starting pipeline test...")
        
        # Initialize scheduler and database session
        scheduler = ScrapingScheduler()
        db = SessionLocal()
        
        # Test database connection
        try:
            total_articles = db.query(Article).count()
            published_articles = db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED).count()
            logger.info(f"Current database state: {total_articles} total articles, {published_articles} published")
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return

        # Run scraping cycle
        logger.info("Running scraping cycle...")
        source_data = await scheduler.gather_source_data()
        if not source_data:
            logger.warning("No source data gathered")
            return

        # Process and save articles
        articles = await scheduler.process_source_data(source_data)
        if not articles:
            logger.warning("No articles generated")
            return

        if scheduler.save_articles(articles):
            logger.info("Articles saved successfully")
        else:
            logger.error("Failed to save articles")
            return

        # Check results
        new_total = db.query(Article).count()
        new_published = db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED).count()
        logger.info(f"After scraping: {new_total} total articles, {new_published} published")

        # Get latest article details
        latest_article = db.query(Article).order_by(Article.created_at.desc()).first()
        if latest_article:
            logger.info("Latest article details:")
            logger.info(f"Title: {latest_article.title}")
            logger.info(f"Status: {latest_article.status}")
            logger.info(f"URL: {latest_article.source_url}")
            logger.info(f"Category: {latest_article.category}")
            logger.info(f"Author: {latest_article.author_name}")
            logger.info(f"Created at: {latest_article.created_at}")
        
    except Exception as e:
        logger.error(f"Error in test_pipeline: {str(e)}", exc_info=True)
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pipeline()) 