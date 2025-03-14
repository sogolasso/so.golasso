import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.scraping_scheduler import run_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting scraping scheduler...")
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Scraping scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error running scraping scheduler: {e}")
        sys.exit(1) 