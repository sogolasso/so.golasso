import feedparser
import logging
import json
import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rss_test')

# RSS feed URLs with alternatives
RSS_FEEDS = {
    'globo_esporte': [
        'https://ge.globo.com/rss/feed/pagina/ultimas/futebol.xml',  # Latest football news
        'https://ge.globo.com/rss/feed/pagina/ultimas.xml',          # Latest news
        'https://ge.globo.com/rss/feed/pagina/futebol.xml'           # Football feed
    ],
    'espn_brasil': [
        'https://www.espn.com.br/rss',                               # Main feed (working)
        'https://www.espn.com.br/rss/futebol',                       # Football specific feed
        'https://www.espn.com.br/rss/news/futebol'                  # Alternative feed
    ],
    'lance': [
        'https://www.lance.com.br/feed',                             # Main feed
        'https://www.lance.com.br/feed/ultimas',                     # Latest news
        'https://www.lance.com.br/feed/futebol'                      # Football feed
    ]
}

def get_headers():
    """Get headers for RSS feed requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, application/atom+xml, text/xml, */*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

def retry_with_backoff(func, max_retries=3, initial_delay=1.5):
    """Retry a function with exponential backoff."""
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        try:
            return func()
        except requests.exceptions.RequestException as e:
            if retries == max_retries - 1:
                raise
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                # For rate limiting, use a longer delay
                delay = delay * 3
            else:
                delay = delay * 2
            logger.warning(f"Attempt {retries + 1} failed: {str(e)}. Waiting {delay}s...")
            time.sleep(delay)
            retries += 1
    return None

def fetch_feed_content(url: str) -> Optional[str]:
    """Fetch RSS feed content with proper headers and error handling."""
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if not any(t in content_type for t in ['xml', 'rss', 'atom']):
            logger.warning(f"Unexpected content type from {url}: {content_type}")
        
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Feed not found at {url}")
        elif e.response.status_code == 410:
            logger.warning(f"Feed no longer available at {url}")
        elif e.response.status_code == 429:
            logger.warning(f"Rate limited while accessing {url}")
        else:
            logger.warning(f"HTTP error {e.response.status_code} for {url}: {str(e)}")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error while accessing {url}")
        return None
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout while accessing {url}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching feed content from {url}: {str(e)}")
        return None

def test_rss_feed(feed_name: str, feed_urls: List[str]) -> Optional[Dict]:
    """Test RSS feed with multiple URL attempts and improved error handling."""
    for feed_url in feed_urls:
        try:
            logging.info(f"Attempting to fetch {feed_name} from {feed_url}")
            
            # Try to fetch feed content with retry
            content = retry_with_backoff(lambda: fetch_feed_content(feed_url))
            if not content:
                continue
                
            # Parse feed
            feed = feedparser.parse(content)
            
            # Check for feed parsing errors
            if feed.bozo:
                logging.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
                continue
                
            # Validate feed has entries
            if not feed.entries:
                logging.warning(f"No entries found in feed {feed_url}")
                continue
                
            # Process entries
            entries = []
            for entry in feed.entries[:5]:  # Get up to 5 entries
                if not (entry.get('title') and entry.get('link')):
                    continue
                    
                entries.append({
                    'title': entry.get('title'),
                    'link': entry.get('link'),
                    'published': entry.get('published', entry.get('updated', '')),
                    'summary': entry.get('summary', entry.get('description', ''))
                })
            
            if entries:
                logging.info(f"Successfully fetched {len(entries)} entries from {feed_url}")
                return {
                    'feed_name': feed_name,
                    'feed_url': feed_url,
                    'entries': entries
                }
            else:
                logging.warning(f"No valid entries found in feed {feed_url}")
                
        except Exception as e:
            logging.warning(f"Error processing feed {feed_url}: {str(e)}")
            
    logging.error(f"All URLs failed for {feed_name}")
    return None

def test_all_rss_feeds():
    """Test all configured RSS feeds."""
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        results = {}
        for feed_name, feed_urls in RSS_FEEDS.items():
            feed_data = test_rss_feed(feed_name, feed_urls)
            if feed_data:
                results[feed_name] = feed_data
        
        if results:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/rss_test_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Test results saved to {output_file}")
            
            return True
        else:
            logger.error("No RSS feeds were successfully tested")
            return False
            
    except Exception as e:
        logger.error(f"Error testing RSS feeds: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    test_all_rss_feeds() 