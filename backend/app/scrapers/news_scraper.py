import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import logging
import re
import asyncio

class NewsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.sources = {
            'ge': 'https://ge.globo.com/futebol/',
            'espn': 'https://www.espn.com.br/futebol/',
            'lance': 'https://www.lance.com.br/futebol/',
            'uol': 'https://www.uol.com.br/esporte/futebol/'
        }
        
        # Enhanced keywords for content categorization
        self.keywords = {
            'MATCH_RESULT': [
                'vence', 'empata', 'derrota', 'x', 'ganha', 'perde', 'vitória',
                'empate', 'placar', 'gol', 'final', 'resultado', 'classificação',
                'vencedor', 'perdedor', 'jogo', 'partida'
            ],
            'TRANSFER_NEWS': [
                'contrata', 'transferência', 'assina', 'reforço', 'negociação',
                'contrato', 'acordo', 'proposta', 'interesse', 'sondagem',
                'mercado', 'janela', 'empréstimo', 'rescisão', 'multa'
            ],
            'TACTICAL_ANALYSIS': [
                'tática', 'esquema', 'formação', 'estratégia', 'posicionamento',
                'sistema', 'análise', 'desempenho', '4-3-3', '4-4-2', '3-5-2',
                'meio-campo', 'ataque', 'defesa', 'pressão', 'marcação'
            ],
            'TEAM_UPDATE': [
                'treino', 'departamento', 'médico', 'prepara', 'lesão',
                'recuperação', 'preparação', 'elenco', 'relacionados',
                'concentração', 'desfalque', 'retorno', 'ausência'
            ],
            'RUMOR': [
                'especulação', 'pode', 'possível', 'rumor', 'cogita',
                'estuda', 'avalia', 'monitora', 'interesse', 'sondagem'
            ]
        }

    def _clean_text(self, text: str) -> str:
        """Clean scraped text by removing extra whitespace and newlines."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    def _format_content(self, paragraphs: List[str], max_paragraphs: int = 5) -> str:
        """Format article content with proper spacing and structure."""
        cleaned_paragraphs = [self._clean_text(p) for p in paragraphs if p.strip()]
        formatted_content = '\n\n'.join(cleaned_paragraphs[:max_paragraphs])
        return formatted_content

    def _determine_content_type(self, title: str, content: str) -> str:
        """Enhanced content type determination using weighted keyword matching."""
        text = f"{title.lower()} {content.lower()}"
        scores = {category: 0 for category in self.keywords.keys()}
        
        # Calculate scores based on keyword matches
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in text:
                    # Title matches are worth more
                    if keyword in title.lower():
                        scores[category] += 2
                    else:
                        scores[category] += 1
        
        # Get category with highest score
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'RUMOR'  # Default category if no strong matches

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch a page using aiohttp."""
        try:
            async with session.get(url, headers=self.headers, timeout=30) as response:
                return await response.text()
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return ""

    async def scrape_ge(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Scrape news from Globo Esporte."""
        articles = []
        try:
            html = await self._fetch_page(session, self.sources['ge'])
            if not html:
                return articles
                
            soup = BeautifulSoup(html, 'html.parser')
            
            for article in soup.find_all('div', class_='feed-post'):
                try:
                    title = article.find('a', class_='feed-post-link').text.strip()
                    link = article.find('a', class_='feed-post-link')['href']
                    
                    # Get full article content
                    article_html = await self._fetch_page(session, link)
                    if not article_html:
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    content_div = article_soup.find('div', class_='mc-article-body')
                    
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        content = self._format_content([p.text for p in paragraphs])
                        
                        if title and content:
                            content_type = self._determine_content_type(title, content)
                            articles.append(self._create_article_dict(title, content, content_type, 'Globo Esporte', link))
                    
                    await asyncio.sleep(1)  # Respect rate limiting
                except Exception as e:
                    logging.error(f"Error scraping GE article: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error scraping GE: {str(e)}")
        
        return articles

    async def scrape_espn(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Scrape news from ESPN Brasil."""
        articles = []
        try:
            html = await self._fetch_page(session, self.sources['espn'])
            if not html:
                return articles
                
            soup = BeautifulSoup(html, 'html.parser')
            
            for article in soup.find_all('article', class_='contentItem'):
                try:
                    title_elem = article.find('h2')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link = article.find('a')['href']
                    if not link.startswith('http'):
                        link = 'https://www.espn.com.br' + link
                    
                    # Get full article content
                    article_html = await self._fetch_page(session, link)
                    if not article_html:
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    content_div = article_soup.find('div', class_='article-body')
                    
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        content = self._format_content([p.text for p in paragraphs])
                        
                        if title and content:
                            content_type = self._determine_content_type(title, content)
                            articles.append(self._create_article_dict(title, content, content_type, 'ESPN Brasil', link))
                    
                    await asyncio.sleep(1)  # Respect rate limiting
                except Exception as e:
                    logging.error(f"Error scraping ESPN article: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error scraping ESPN: {str(e)}")
        
        return articles

    async def scrape_lance(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Scrape news from Lance."""
        articles = []
        try:
            html = await self._fetch_page(session, self.sources['lance'])
            if not html:
                return articles
                
            soup = BeautifulSoup(html, 'html.parser')
            
            for article in soup.find_all('article', class_='news-item'):
                try:
                    title = article.find('h2').text.strip()
                    link = article.find('a')['href']
                    
                    # Get full article content
                    article_html = await self._fetch_page(session, link)
                    if not article_html:
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    content_div = article_soup.find('div', class_='content-text')
                    
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        content = self._format_content([p.text for p in paragraphs])
                        
                        if title and content:
                            content_type = self._determine_content_type(title, content)
                            articles.append(self._create_article_dict(title, content, content_type, 'Lance!', link))
                    
                    await asyncio.sleep(1)  # Respect rate limiting
                except Exception as e:
                    logging.error(f"Error scraping Lance article: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error scraping Lance: {str(e)}")
        
        return articles

    def _create_article_dict(self, title: str, content: str, content_type: str, source: str, url: str) -> Dict:
        """Create a standardized article dictionary."""
        return {
            'title': title,
            'content': content,
            'content_type': content_type,
            'source': source,
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'engagement_count': 0,
            'is_trending': False,
            'has_engagement': False,
            'summary': content[:200] + "..." if len(content) > 200 else content
        }

    async def scrape_all(self) -> List[Dict]:
        """Scrape news from all sources."""
        all_articles = []
        
        async with aiohttp.ClientSession() as session:
            # Scrape from all sources
            ge_articles = await self.scrape_ge(session)
            all_articles.extend(ge_articles)
            logging.info(f"Scraped {len(ge_articles)} articles from Globo Esporte")
            
            espn_articles = await self.scrape_espn(session)
            all_articles.extend(espn_articles)
            logging.info(f"Scraped {len(espn_articles)} articles from ESPN Brasil")
            
            lance_articles = await self.scrape_lance(session)
            all_articles.extend(lance_articles)
            logging.info(f"Scraped {len(lance_articles)} articles from Lance!")
        
        return all_articles

    async def scrape(self) -> List[Dict]:
        """Scrape news from all sources."""
        try:
            return await self.scrape_all()
        except Exception as e:
            logging.error(f"Error scraping news: {str(e)}")
            return []

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
        print(f"Type: {article['content_type']}")
        print(f"Source: {article['source']}")
        print("-" * 80)
        print(article['summary'])
        print("=" * 80) 