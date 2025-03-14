import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the parent directory to Python path so we can import from app
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

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

from app.core.scraping_scheduler import ScrapingScheduler

async def run_scheduler():
    """Run the scraping scheduler continuously"""
    try:
        scheduler = ScrapingScheduler()
        logger.info("Starting scraping scheduler...")
        
        while True:
            try:
                logger.info("Starting new scraping cycle...")
                await scheduler.run_scraping_cycle()
                logger.info("Scraping cycle completed. Waiting for next cycle...")
                
                # Wait for 1 hour before next cycle
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in scraping cycle: {str(e)}")
                # Wait 5 minutes before retrying after an error
                await asyncio.sleep(300)
                
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler stopped due to error: {str(e)}")
        sys.exit(1) 