import asyncio
import logging
from datetime import datetime, timedelta
import schedule
import time
from app.core.scraping_scheduler import ScrapingScheduler
from app.core.database import SessionLocal
from app.models.article import Article, ArticleStatus

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

class AutomationManager:
    def __init__(self):
        self.scraping_scheduler = ScrapingScheduler()
        
    async def run_scraping_cycle(self):
        """Run a complete scraping cycle"""
        try:
            logger.info("Starting scraping cycle")
            await self.scraping_scheduler.run_scraping_cycle()
            logger.info("Completed scraping cycle")
            
            # Clean up old drafts
            self.cleanup_old_drafts()
            
        except Exception as e:
            logger.error(f"Error in scraping cycle: {e}")

    def cleanup_old_drafts(self):
        """Clean up draft articles older than 24 hours"""
        try:
            db = SessionLocal()
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            old_drafts = (
                db.query(Article)
                .filter(Article.status == ArticleStatus.DRAFT)
                .filter(Article.created_at < cutoff_time)
                .all()
            )
            
            for draft in old_drafts:
                db.delete(draft)
            
            db.commit()
            logger.info(f"Cleaned up {len(old_drafts)} old draft articles")
            
        except Exception as e:
            logger.error(f"Error cleaning up drafts: {e}")
        finally:
            db.close()

async def main():
    automation = AutomationManager()
    
    # Run initial cycle
    await automation.run_scraping_cycle()
    
    # Schedule regular runs
    schedule.every(30).minutes.do(
        lambda: asyncio.run(automation.run_scraping_cycle())
    )
    
    # Keep the script running
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

if __name__ == "__main__":
    logger.info("Starting automation manager")
    asyncio.run(main()) 