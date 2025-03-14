import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from scrapers.news_scraper import fetch_news
from scrapers.twitter_scraper import fetch_tweets
from scrapers.instagram_scraper import fetch_instagram_posts
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='data/scraper.log',
                    filemode='a')
logger = logging.getLogger('scheduler')

# Create a scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """
    Starts the scraper scheduler
    """
    # Make sure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Log the scheduler start
    logger.info("Starting the scraper scheduler...")
    
    # Get scraper settings from configuration
    config = get_config()
    scraper_settings = config.get("scraper_settings", {})
    
    # Get interval settings with defaults
    news_interval = scraper_settings.get("news_interval_hours", 3)
    twitter_interval = scraper_settings.get("twitter_interval_hours", 2)
    instagram_interval = scraper_settings.get("instagram_interval_hours", 6)
    
    logger.info(f"Scheduling scrapers with intervals: News={news_interval}h, Twitter={twitter_interval}h, Instagram={instagram_interval}h")
    
    # Add jobs to the scheduler
    
    # News scraper job
    scheduler.add_job(
        fetch_news,
        'interval',
        hours=news_interval,
        id='news_scraper',
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately when starting
    )
    
    # Twitter scraper job
    scheduler.add_job(
        fetch_tweets,
        'interval',
        hours=twitter_interval,
        id='twitter_scraper',
        replace_existing=True
    )
    
    # Instagram scraper job
    scheduler.add_job(
        fetch_instagram_posts,
        'interval',
        hours=instagram_interval,
        id='instagram_scraper',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    return scheduler

def stop_scheduler():
    """
    Stops the scraper scheduler
    """
    logger.info("Stopping the scraper scheduler...")
    scheduler.shutdown()
    logger.info("Scheduler stopped")

def get_scheduler_jobs():
    """
    Gets the current scheduler jobs
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'interval': str(job.trigger),
        })
    return jobs

def run_job_now(job_id):
    """
    Runs a specific job immediately
    
    Args:
        job_id (str): The ID of the job to run
    """
    try:
        job = scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Job {job_id} scheduled to run immediately")
            return True
        else:
            logger.error(f"Job {job_id} not found")
            return False
    except Exception as e:
        logger.error(f"Error running job {job_id}: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the scheduler
    start_scheduler()
