import requests
import logging
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('html_test')

# News websites to scrape
WEBSITES = {
    'globo_esporte': {
        'url': 'https://ge.globo.com/',
        'article_selector': 'div.feed-post',
        'title_selector': 'a.feed-post-link',
        'link_selector': 'a.feed-post-link',
        'summary_selector': 'div.feed-post-body-resumo'
    },
    'uol_esporte': {
        'url': 'https://www.uol.com.br/esporte/futebol/',
        'article_selector': 'div.results__list article',
        'title_selector': 'h3.title__element',
        'link_selector': 'a.thumbnail__link',
        'summary_selector': 'p.title__element'
    },
    'terra_esportes': {
        'url': 'https://www.terra.com.br/esportes/futebol/brasileiro-serie-a/',
        'article_selector': 'div.card',
        'title_selector': 'h2, h3',
        'link_selector': 'a',
        'summary_selector': 'p'
    },
    'lance': {
        'url': 'https://www.lance.com.br/futebol/',
        'article_selector': 'article.c-news-item',
        'title_selector': 'h2.c-news-item__title',
        'link_selector': 'a.c-news-item__link',
        'summary_selector': 'p.c-news-item__excerpt',
        'use_mobile': True,  # Use mobile version for better structure
        'mobile_url': 'https://m.lance.com.br/futebol/'
    },
    'goal_brasil': {
        'url': 'https://www.goal.com/br/noticias/futebol',
        'article_selector': 'div[data-testid="news-card"]',
        'title_selector': 'h3[data-testid="news-card-title"]',
        'link_selector': 'a[data-testid="news-card-link"]',
        'summary_selector': 'p[data-testid="news-card-description"]',
        'base_url': 'https://www.goal.com'
    },
    'trivela': {
        'url': 'https://trivela.com.br/futebol-brasileiro/',
        'article_selector': 'article.post',
        'title_selector': 'h2.entry-title',
        'link_selector': 'a.post-thumbnail',
        'summary_selector': 'div.entry-content',
        'alternative_selectors': {
            'title': 'h1.entry-title',
            'link': 'link[rel="canonical"]',
            'summary': 'div.entry-excerpt'
        }
    },
    'footstats': {
        'url': 'https://www.footstats.com.br/blog/',
        'article_selector': 'article.post',
        'title_selector': 'h2.entry-title',
        'link_selector': 'a.entry-link',
        'summary_selector': 'div.entry-summary',
        'pagination': {
            'enabled': True,
            'param': 'page',
            'max_pages': 2
        }
    }
}

def get_headers(mobile=False):
    """Get headers for HTTP requests."""
    base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    if mobile:
        base_headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
    else:
        base_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    
    return base_headers

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
                delay = delay * 3
            else:
                delay = delay * 2
            logger.warning(f"Attempt {retries + 1} failed: {str(e)}. Waiting {delay}s...")
            time.sleep(delay)
            retries += 1
    return None

def get_page_content(url: str, config: Dict) -> Optional[str]:
    """Get page content with proper headers and retries."""
    try:
        use_mobile = config.get('use_mobile', False)
        if use_mobile and 'mobile_url' in config:
            url = config['mobile_url']
            
        headers = get_headers(mobile=use_mobile)
        response = retry_with_backoff(lambda: requests.get(url, headers=headers, timeout=30))
        
        if response:
            response.raise_for_status()
            return response.text
        return None
    except Exception as e:
        logger.error(f"Error fetching content from {url}: {str(e)}")
        return None

def process_article(article, config: Dict, base_url: str) -> Optional[Dict]:
    """Process a single article with fallback selectors."""
    try:
        # Try primary selectors
        title_elem = article.select_one(config['title_selector'])
        link_elem = article.select_one(config['link_selector'])
        summary_elem = article.select_one(config['summary_selector'])
        
        # Try alternative selectors if available
        if not title_elem and 'alternative_selectors' in config:
            title_elem = article.select_one(config['alternative_selectors'].get('title', ''))
            
        if not link_elem and 'alternative_selectors' in config:
            link_elem = article.select_one(config['alternative_selectors'].get('link', ''))
            
        if not summary_elem and 'alternative_selectors' in config:
            summary_elem = article.select_one(config['alternative_selectors'].get('summary', ''))
        
        # Extract data
        title = title_elem.get_text().strip() if title_elem else ""
        
        # Handle different link scenarios
        link = ""
        if link_elem:
            if link_elem.name == 'link':
                link = link_elem.get('href', '')
            else:
                href = link_elem.get('href', '')
                if href:
                    if 'base_url' in config:
                        link = urljoin(config['base_url'], href)
                    else:
                        link = urljoin(base_url, href)
        
        summary = summary_elem.get_text().strip() if summary_elem else ""
        
        if title and link:
            return {
                'title': title,
                'link': link,
                'summary': summary
            }
    except Exception as e:
        logger.warning(f"Error processing article: {str(e)}")
    
    return None

def test_website_scraping(site_name: str, config: Dict) -> Optional[Dict]:
    """Test scraping a single website."""
    try:
        logger.info(f"Testing HTML scraping for {site_name}...")
        
        # Get page content
        content = get_page_content(config['url'], config)
        if not content:
            return None
            
        # Parse HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # Find articles
        articles = soup.select(config['article_selector'])
        if not articles:
            logger.warning(f"No articles found on {site_name} using selector: {config['article_selector']}")
            return None
            
        # Process articles
        processed_articles = []
        for article in articles[:5]:
            article_data = process_article(article, config, config['url'])
            if article_data:
                processed_articles.append(article_data)
        
        # Handle pagination if enabled
        if config.get('pagination', {}).get('enabled', False) and len(processed_articles) < 5:
            page = 2
            max_pages = config['pagination'].get('max_pages', 2)
            param = config['pagination'].get('param', 'page')
            
            while len(processed_articles) < 5 and page <= max_pages:
                paginated_url = f"{config['url']}?{param}={page}"
                content = get_page_content(paginated_url, config)
                if content:
                    soup = BeautifulSoup(content, 'lxml')
                    articles = soup.select(config['article_selector'])
                    
                    for article in articles:
                        if len(processed_articles) >= 5:
                            break
                        article_data = process_article(article, config, config['url'])
                        if article_data:
                            processed_articles.append(article_data)
                
                page += 1
        
        if processed_articles:
            site_data = {
                'site_name': site_name,
                'url': config['url'],
                'articles': processed_articles
            }
            
            logger.info(f"Successfully scraped {len(processed_articles)} articles from {site_name}")
            return site_data
        else:
            logger.warning(f"No articles could be processed from {site_name}")
            return None
            
    except Exception as e:
        logger.error(f"Error scraping {site_name}: {str(e)}")
        return None

def test_all_websites():
    """Test scraping all configured websites."""
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        results = {}
        for site_name, config in WEBSITES.items():
            site_data = test_website_scraping(site_name, config)
            if site_data:
                results[site_name] = site_data
        
        if results:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/html_test_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Test results saved to {output_file}")
            
            return True
        else:
            logger.error("No websites were successfully scraped")
            return False
            
    except Exception as e:
        logger.error(f"Error testing website scraping: {str(e)}")
        return False

if __name__ == "__main__":
    test_all_websites() 