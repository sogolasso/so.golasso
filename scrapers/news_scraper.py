import os
import json
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import trafilatura
from database.firebase_handler import save_to_firebase
from config import get_enabled_news_sources

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='data/scraper.log',
                    filemode='a')
logger = logging.getLogger('news_scraper')

# RSS feed URLs for major Brazilian football news sites
RSS_FEEDS = {
    'globo_esporte': 'https://ge.globo.com/rss/',
    'espn_brasil': 'https://www.espn.com.br/rss/',
    'lance': 'https://www.lance.com.br/rss/'
}

def fetch_news():
    """
    Fetches news from Brazilian football news sites using their RSS feeds
    """
    logger.info("Starting news scraping process...")
    news_items = []
    
    # Get enabled news sources from configuration
    enabled_sources = get_enabled_news_sources()
    
    if not enabled_sources:
        logger.warning("No news sources enabled in configuration")
        return news_items
    
    # Filter RSS feeds to only include enabled sources
    feeds_to_scrape = {source: url for source, url in RSS_FEEDS.items() if source in enabled_sources}
    
    if not feeds_to_scrape:
        logger.warning("No matching RSS feeds found for enabled sources")
        return news_items
    
    for source, url in feeds_to_scrape.items():
        try:
            logger.info(f"Fetching news from {source}...")
            feed = feedparser.parse(url)
            
            source_items = []  # Track items per source for logging
            
            for entry in feed.entries:
                # Filter for football content
                if is_football_related(entry):
                    news_item = {
                        'source': source,
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', ''),
                        'content': get_full_content(entry.link),
                        'scraped_at': datetime.now().isoformat()
                    }
                    news_items.append(news_item)
                    source_items.append(news_item)
            
            logger.info(f"Successfully fetched {len(source_items)} news items from {source}")
        except Exception as e:
            logger.error(f"Error fetching news from {source}: {str(e)}")
    
    # Save news items to JSON and Firebase
    save_news_data(news_items)
    return news_items

def is_football_related(entry):
    """
    Checks if an RSS entry is related to Brazilian football
    """
    # List of Brazilian football keywords to check against
    football_keywords = [
        'futebol', 'brasileirão', 'copa do brasil', 'libertadores', 
        'flamengo', 'palmeiras', 'são paulo', 'corinthians', 'santos', 
        'grêmio', 'internacional', 'atlético', 'cruzeiro', 'fluminense',
        'botafogo', 'vasco', 'seleção brasileira', 'série a', 'campeonato brasileiro'
    ]
    
    # Check title and summary for football keywords
    text_to_check = (entry.title + ' ' + entry.get('summary', '')).lower()
    
    for keyword in football_keywords:
        if keyword.lower() in text_to_check:
            return True
    
    return False

def get_full_content(url):
    """
    Gets the full article content using trafilatura
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text if text else ""
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return ""

def save_news_data(news_items):
    """
    Saves the news data to JSON files and Firebase
    """
    if not news_items:
        logger.warning("No news items to save")
        return
    
    # Make sure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save to a timestamped JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'data/news_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=4)
    
    # Save to the latest news file
    with open('data/news_latest.json', 'w', encoding='utf-8') as f:
        json.dump(news_items[:10], f, ensure_ascii=False, indent=4)
    
    # Update stats
    update_stats(len(news_items))
    
    # Save to Firebase
    try:
        save_to_firebase('news', news_items)
        logger.info(f"Successfully saved {len(news_items)} news items to Firebase")
    except Exception as e:
        logger.error(f"Error saving to Firebase: {str(e)}")
    
    logger.info(f"Successfully saved {len(news_items)} news items to {filename}")

def update_stats(count):
    """
    Updates the stats file with the latest news scraping statistics
    """
    stats_file = 'data/stats.json'
    
    try:
        # Read existing stats
        with open(stats_file, 'r') as f:
            stats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize stats if file doesn't exist or is invalid
        stats = {
            "news": {"total": 0, "last_updated": "Never"},
            "twitter": {"total": 0, "last_updated": "Never"},
            "instagram": {"total": 0, "last_updated": "Never"}
        }
    
    # Update news stats
    stats["news"]["total"] += count
    stats["news"]["last_updated"] = datetime.now().isoformat()
    
    # Save updated stats
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)

if __name__ == "__main__":
    # Test the news scraper
    fetch_news()
