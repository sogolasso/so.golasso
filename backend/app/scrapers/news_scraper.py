import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        """Initialize news scrapers"""
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
        
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def _fetch_page(self, url: str) -> str:
        """Fetch a page using aiohttp."""
        try:
            session = await self._get_session()
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Error fetching {url}: Status {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return ""
            
    async def scrape_globo_esporte(self) -> List[Dict]:
        """Scrape football news from Globo Esporte"""
        articles = []
        try:
            html = await self._fetch_page("https://ge.globo.com/futebol/")
            if not html:
                return articles
                
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('div', class_='feed-post-body')
            
            for item in news_items:
                try:
                    title_elem = item.find('a', class_='feed-post-link')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    content_elem = item.find('div', class_='feed-post-body-resumo')
                    content = content_elem.get_text(strip=True) if content_elem else ''
                    
                    time_elem = item.find('span', class_='feed-post-datetime')
                    timestamp = time_elem.get_text(strip=True) if time_elem else ''
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'content': content,
                            'source_url': link,
                            'source_type': 'news',
                            'author': 'Globo Esporte',
                            'published_at': datetime.now().isoformat(),
                            'engagement_count': 0
                        })
                        
                    await asyncio.sleep(1)  # Respect rate limiting
                except Exception as e:
                    logger.error(f"Error processing Globo Esporte article: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Globo Esporte: {str(e)}")
            
        return articles
        
    async def scrape_espn_brasil(self) -> List[Dict]:
        """Scrape football news from ESPN Brasil"""
        articles = []
        try:
            html = await self._fetch_page("https://www.espn.com.br/futebol/")
            if not html:
                return articles
                
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('div', class_='contentItem__content')
            
            for item in news_items:
                try:
                    title_elem = item.find('a', class_='contentItem__title')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    content_elem = item.find('p', class_='contentItem__subhead')
                    content = content_elem.get_text(strip=True) if content_elem else ''
                    
                    time_elem = item.find('span', class_='contentItem__timestamp')
                    timestamp = time_elem.get_text(strip=True) if time_elem else ''
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'content': content,
                            'source_url': link,
                            'source_type': 'news',
                            'author': 'ESPN Brasil',
                            'published_at': datetime.now().isoformat(),
                            'engagement_count': 0
                        })
                        
                    await asyncio.sleep(1)  # Respect rate limiting
                except Exception as e:
                    logger.error(f"Error processing ESPN article: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping ESPN Brasil: {str(e)}")
            
        return articles
        
    async def scrape_lance(self) -> List[Dict]:
        """Scrape football news from Lance!"""
        articles = []
        try:
            html = await self._fetch_page("https://www.lance.com.br/futebol/")
            if not html:
                return articles
                
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('div', class_='article-card')
            
            for item in news_items:
                try:
                    title_elem = item.find('h2', class_='article-card__title')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    link = title_elem.find('a').get('href', '') if title_elem.find('a') else ''
                    
                    content_elem = item.find('p', class_='article-card__description')
                    content = content_elem.get_text(strip=True) if content_elem else ''
                    
                    time_elem = item.find('time', class_='article-card__date')
                    timestamp = time_elem.get_text(strip=True) if time_elem else ''
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'content': content,
                            'source_url': link,
                            'source_type': 'news',
                            'author': 'Lance!',
                            'published_at': datetime.now().isoformat(),
                            'engagement_count': 0
                        })
                        
                    await asyncio.sleep(1)  # Respect rate limiting
                except Exception as e:
                    logger.error(f"Error processing Lance! article: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Lance!: {str(e)}")
            
        return articles
        
    async def scrape_all(self) -> List[Dict]:
        """Scrape all news sources"""
        all_articles = []
        
        try:
            # Initialize session
            await self._get_session()
            
            # Scrape Globo Esporte
            try:
                globo_articles = await self.scrape_globo_esporte()
                all_articles.extend(globo_articles)
                logger.info(f"Scraped {len(globo_articles)} articles from Globo Esporte")
            except Exception as e:
                logger.error(f"Globo Esporte scraping failed: {str(e)}")
                
            # Scrape ESPN Brasil
            try:
                espn_articles = await self.scrape_espn_brasil()
                all_articles.extend(espn_articles)
                logger.info(f"Scraped {len(espn_articles)} articles from ESPN Brasil")
            except Exception as e:
                logger.error(f"ESPN Brasil scraping failed: {str(e)}")
                
            # Scrape Lance!
            try:
                lance_articles = await self.scrape_lance()
                all_articles.extend(lance_articles)
                logger.info(f"Scraped {len(lance_articles)} articles from Lance!")
            except Exception as e:
                logger.error(f"Lance! scraping failed: {str(e)}")
                
        finally:
            # Always close the session
            await self._close_session()
            
        return all_articles

async def get_latest_news() -> List[Dict]:
    """Get the latest football news."""
    scraper = NewsScraper()
    articles = await scraper.scrape_all()
    return articles

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get and display articles
    articles = asyncio.run(get_latest_news())
    print(f"\nFound {len(articles)} articles:")
    for idx, article in enumerate(articles, 1):
        print(f"\n{idx}. {article['title']}")
        print(f"Type: {article['source_type']}")
        print(f"Source: {article['author']}")
        print("-" * 80)
        print(article['content'])
        print("=" * 80) 