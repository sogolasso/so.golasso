import schedule
import time
import logging
from pathlib import Path
import sys

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from scripts.fetch_and_save_news import save_articles_to_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_fetcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def job():
    """Run the news fetching job."""
    logging.info("Starting scheduled news fetch...")
    try:
        save_articles_to_db()
        logging.info("Completed scheduled news fetch successfully")
    except Exception as e:
        logging.error(f"Error in scheduled news fetch: {str(e)}")

def run_scheduler():
    """Run the scheduler with defined intervals."""
    # Schedule jobs
    schedule.every(30).minutes.do(job)  # Fetch every 30 minutes
    schedule.every().day.at("06:00").do(job)  # Morning fetch
    schedule.every().day.at("12:00").do(job)  # Noon fetch
    schedule.every().day.at("18:00").do(job)  # Evening fetch
    schedule.every().day.at("22:00").do(job)  # Night fetch

    # Run job immediately on start
    job()

    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
            break
        except Exception as e:
            logging.error(f"Error in scheduler: {str(e)}")
            time.sleep(300)  # Wait 5 minutes before retrying on error

if __name__ == "__main__":
    logging.info("Starting news fetcher scheduler...")
    run_scheduler() 