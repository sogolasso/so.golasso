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
from app.scrapers.news_scraper import NewsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingScheduler:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required but not set in configuration")
        self.news_scraper = NewsScraper()
        self.ai_writer = AIWriter(
            api_key=settings.OPENAI_API_KEY,
            max_daily_articles=settings.POSTS_PER_DAY,
            max_monthly_cost=settings.MAX_MONTHLY_AI_COST
        )
        self.db = SessionLocal()
        self.email_service = EmailService()
        
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
        
    async def gather_source_data(self) -> List[Dict[str, Any]]:
        """Gather and filter data from all sources"""
        try:
            logger.info("Starting to gather source data...")
            all_data = []

            # Gather news data
            news_data = await self.news_scraper.scrape()
            if news_data:
                all_data.extend(news_data)
                logger.info(f"Gathered {len(news_data)} news items")

            # Remove duplicates
            unique_data = self._filter_duplicate_content(all_data)
            logger.info(f"Filtered to {len(unique_data)} unique items")
            
            # Score and sort content
            scored_data = [(item, self._score_content(item)) for item in unique_data]
            scored_data.sort(key=lambda x: x[1], reverse=True)
            
            # Take top N items based on settings
            top_items = [item for item, score in scored_data[:settings.POSTS_PER_DAY]]
            logger.info(f"Selected top {len(top_items)} items for processing")

            return top_items

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
                except Exception as e:
                    logger.error(f"Error saving article {article.title}: {str(e)}")
                    self.db.rollback()
            return True
        except Exception as e:
            logger.error(f"Error in save_articles: {str(e)}", exc_info=True)
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
        """Run one complete scraping cycle"""
        try:
            logger.info("Starting scraping cycle...")
            
            # Gather data from sources
            source_data = await self.gather_source_data()
            if not source_data:
                logger.warning("No source data gathered")
                return

            # Process data and generate articles
            articles = await self.process_source_data(source_data)
            if not articles:
                logger.warning("No articles generated")
                return

            # Save articles to database
            if self.save_articles(articles):
                logger.info("Scraping cycle completed successfully")
            else:
                logger.error("Failed to save articles")

            # Clean up old drafts
            self.cleanup_old_drafts()

        except Exception as e:
            logger.error(f"Error in scraping cycle: {str(e)}", exc_info=True)

async def run_scheduler():
    """Run the scraping scheduler continuously"""
    scheduler = ScrapingScheduler()
    while True:
        try:
            await scheduler.run_scraping_cycle()
            await asyncio.sleep(1800)  # Wait 30 minutes
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}", exc_info=True)
            await asyncio.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    logger.info("Starting automation manager")
    asyncio.run(run_scheduler()) 