import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from slugify import slugify

from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.article import Article, ArticleStatus
from app.schemas.article import ArticleCreate
from app.services.ai_writer import AIWriter
from app.services.email_service import EmailService
from app.services.monitoring_service import MonitoringService
from app.scrapers.news_scraper import NewsScraper
from app.scrapers.social_scraper import SocialScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingScheduler:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required but not set in configuration")
        self.news_scraper = NewsScraper()
        self.social_scraper = SocialScraper()
        self.ai_writer = AIWriter(
            api_key=settings.OPENAI_API_KEY,
            max_daily_articles=settings.POSTS_PER_DAY,
            max_monthly_cost=settings.MAX_MONTHLY_AI_COST
        )
        self.db = SessionLocal()
        self.email_service = EmailService()
        self.monitoring_service = MonitoringService(self.db, self.email_service)
        
    def _score_content(self, item: Dict[str, Any]) -> float:
        """Score content based on relevance and engagement potential"""
        score = 0.0
        
        # Base score
        score += 1.0
        
        # Engagement score (0-5)
        engagement = item.get('engagement_count', 0)
        if engagement > 1000:
            score += 5.0
        elif engagement > 500:
            score += 4.0
        elif engagement > 100:
            score += 3.0
        elif engagement > 50:
            score += 2.0
        elif engagement > 10:
            score += 1.0
            
        # Trending bonus
        if item.get('is_trending', False):
            score += 3.0
            
        # Content type score
        content_type = item.get('content_type', '').upper()
        type_scores = {
            'MATCH_RESULT': 4.0,
            'TRANSFER_NEWS': 3.5,
            'TACTICAL_ANALYSIS': 3.0,
            'TEAM_UPDATE': 2.5,
            'RUMOR': 2.0
        }
        score += type_scores.get(content_type, 1.0)
        
        # Source credibility score
        source = item.get('source', '').lower()
        source_scores = {
            'globo esporte': 5.0,
            'espn brasil': 4.5,
            'lance!': 4.0
        }
        score += source_scores.get(source, 3.0)
        
        # Content length score (0-2)
        content_length = len(item.get('content', ''))
        if content_length > 1000:
            score += 2.0
        elif content_length > 500:
            score += 1.0
            
        # Recent content bonus
        if 'scraped_at' in item:
            try:
                scraped_time = datetime.fromisoformat(item['scraped_at'])
                age_hours = (datetime.now() - scraped_time).total_seconds() / 3600
                if age_hours < 1:
                    score += 2.0
                elif age_hours < 3:
                    score += 1.0
            except Exception:
                pass
                
        return score
        
    def _filter_duplicate_content(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicate or very similar content"""
        seen_titles = set()
        unique_items = []
        
        for item in items:
            title = item.get('title', '').lower()
            # Simple similarity check - can be enhanced with more sophisticated methods
            if not any(title in seen_title or seen_title in title for seen_title in seen_titles):
                seen_titles.add(title)
                unique_items.append(item)
                
        return unique_items
        
    async def gather_source_data(self) -> List[Dict]:
        """Gather and filter data from all sources"""
        try:
            logger.info("Starting to gather source data...")
            
            # Gather news from traditional sources
            news_articles = await self.news_scraper.scrape_all()
            logger.info(f"Gathered {len(news_articles)} news articles")
            
            # Gather news from social media
            social_articles = await self.social_scraper.scrape_all()
            logger.info(f"Gathered {len(social_articles)} social media articles")
            
            # Combine all articles
            all_articles = news_articles + social_articles
            logger.info(f"Total articles gathered: {len(all_articles)}")
            
            # Score and filter content
            scored_articles = []
            for article in all_articles:
                score = self._score_content(article)
                if score >= settings.MIN_CONTENT_SCORE:
                    article['score'] = score
                    scored_articles.append(article)
            
            # Sort by score and select top articles
            scored_articles.sort(key=lambda x: x['score'], reverse=True)
            selected_articles = scored_articles[:settings.MAX_ARTICLES_PER_CYCLE]
            logger.info(f"Selected {len(selected_articles)} articles after scoring and filtering")
            
            return selected_articles
            
        except Exception as e:
            logger.error(f"Error gathering source data: {str(e)}", exc_info=True)
            return []

    async def process_source_data(self, source_data: List[Dict[str, Any]]) -> List[Article]:
        """Process source data and generate articles"""
        try:
            logger.info("Processing source data...")
            articles = []

            for data in source_data:
                try:
                    # Generate article using AI
                    article_data = await self.ai_writer.generate_article(
                        title=data.get("title", ""),
                        source_text=data.get("content", ""),
                        source_type=data.get("source_type", "news")
                    )
                    
                    if article_data is None:
                        logger.warning("Article generation skipped due to limits")
                        continue

                    # Create article object
                    article = Article(
                        title=article_data["title"],
                        slug=article_data["slug"],
                        content=article_data["content"],
                        summary=article_data["summary"],
                        category=article_data["category"],
                        author_name=article_data["author_name"],
                        author_style=article_data["author_style"],
                        source_url=data.get("url"),
                        source_type=data.get("source_type"),
                        status=ArticleStatus.PUBLISHED,
                        meta_description=article_data["meta_description"],
                        meta_keywords=article_data["meta_keywords"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        published_at=datetime.utcnow()
                    )
                    articles.append(article)
                    logger.info(f"Generated article: {article.title}")

                except Exception as e:
                    logger.error(f"Error processing source item: {str(e)}", exc_info=True)
                    continue

            logger.info(f"Successfully processed {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Error in process_source_data: {str(e)}", exc_info=True)
            return []

    def save_articles(self, articles: List[Article]) -> bool:
        """Save generated articles to database"""
        try:
            logger.info(f"Saving {len(articles)} articles to database...")
            for article in articles:
                try:
                    self.db.add(article)
                    self.db.commit()
                    logger.info(f"Successfully saved and published article: {article.title}")
                    
                    # Send email notification
                    article_url = f"{settings.FRONTEND_URL}/articles/{article.slug}"
                    self.email_service.send_article_notification(article.title, article_url)
                    
                except Exception as e:
                    logger.error(f"Error saving article {article.title}: {str(e)}")
                    self.db.rollback()
                    self.email_service.send_error_notification(str(e))
            return True
        except Exception as e:
            logger.error(f"Error in save_articles: {str(e)}", exc_info=True)
            self.email_service.send_error_notification(str(e))
            return False

    def cleanup_old_drafts(self):
        """Clean up draft articles older than 24 hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            old_drafts = self.db.query(Article).filter(
                Article.status == ArticleStatus.DRAFT,
                Article.created_at < cutoff_time
            ).all()

            for draft in old_drafts:
                try:
                    self.db.delete(draft)
                    logger.info(f"Deleted old draft: {draft.title}")
                except Exception as e:
                    logger.error(f"Error deleting draft {draft.title}: {str(e)}")
                    continue

            self.db.commit()
        except Exception as e:
            logger.error(f"Error in cleanup_old_drafts: {str(e)}", exc_info=True)
            self.db.rollback()

    async def run_scraping_cycle(self):
        """Run a single scraping cycle"""
        try:
            logger.info("Starting scraping cycle...")
            
            # Verify OpenAI API key
            if not settings.OPENAI_API_KEY:
                logger.error("OpenAI API key is not set!")
                return
            else:
                logger.info("OpenAI API key is configured")
            
            # Verify database connection
            try:
                self.db.execute("SELECT 1")
                logger.info("Database connection verified")
            except Exception as e:
                logger.error(f"Database connection failed: {str(e)}")
                return
            
            # Gather source data
            logger.info("Starting to gather source data...")
            source_data = await self.gather_source_data()
            if not source_data:
                logger.warning("No source data gathered, skipping cycle")
                return
            
            logger.info(f"Gathered {len(source_data)} items from sources")
            
            # Log source data details
            for idx, item in enumerate(source_data):
                logger.info(f"Source item {idx + 1}:")
                logger.info(f"  Title: {item.get('title', 'No title')}")
                logger.info(f"  Source: {item.get('source_type', 'Unknown source')}")
                logger.info(f"  Score: {item.get('score', 0)}")
            
            # Process source data
            logger.info("Starting article generation...")
            articles = await self.process_source_data(source_data)
            if not articles:
                logger.warning("No articles generated, skipping cycle")
                return
                
            logger.info(f"Generated {len(articles)} articles")
            
            # Log generated articles
            for idx, article in enumerate(articles):
                logger.info(f"Generated article {idx + 1}:")
                logger.info(f"  Title: {article.title}")
                logger.info(f"  Category: {article.category}")
                logger.info(f"  Author: {article.author_name}")
            
            # Save articles
            logger.info("Starting to save articles...")
            success = self.save_articles(articles)
            if success:
                logger.info("Successfully saved articles")
            else:
                logger.error("Failed to save articles")
            
            # Cleanup old drafts
            self.cleanup_old_drafts()
            logger.info("Completed scraping cycle")
            
        except Exception as e:
            logger.error(f"Error in scraping cycle: {str(e)}", exc_info=True)
            self.email_service.send_error_notification(f"Scraping cycle error: {str(e)}")
            
    async def run(self):
        """Run the scheduler continuously"""
        logger.info("Starting scheduler...")
        
        # Verify configuration
        logger.info("Verifying configuration...")
        logger.info(f"OPENAI_API_KEY set: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
        logger.info(f"DATABASE_URL set: {'Yes' if settings.DATABASE_URL else 'No'}")
        logger.info(f"SMTP settings configured: {'Yes' if settings.SMTP_USER and settings.SMTP_PASSWORD else 'No'}")
        logger.info(f"Max articles per cycle: {settings.MAX_ARTICLES_PER_CYCLE}")
        logger.info(f"Min content score: {settings.MIN_CONTENT_SCORE}")
        
        while True:
            try:
                await self.run_scraping_cycle()
                logger.info(f"Waiting {settings.SCRAPING_INTERVAL_MINUTES} minutes until next cycle")
                await asyncio.sleep(settings.SCRAPING_INTERVAL_MINUTES * 60)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}", exc_info=True)
                self.email_service.send_error_notification(f"Scheduler error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying after error

async def run_scheduler():
    """Run the scraping scheduler continuously"""
    scheduler = ScrapingScheduler()
    await scheduler.run()

if __name__ == "__main__":
    logger.info("Starting automation manager")
    asyncio.run(run_scheduler()) 