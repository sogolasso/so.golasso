from typing import Dict, List, Optional
from datetime import datetime
import json
import pytrends
from pytrends.request import TrendReq
from app.schemas.article import Article
from app.core.config import settings
import openai
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

class SEOService:
    def __init__(self):
        self.trends = TrendReq(hl='pt-BR', tz=180)  # Brazil timezone
        openai.api_key = settings.OPENAI_API_KEY
        self.last_trends_update = None
        self.cached_trends = {}

    async def optimize_article(self, article: Article) -> Dict[str, str]:
        """Optimize article content for SEO."""
        # Get trending topics
        trending_terms = await self._get_trending_topics()
        
        # Generate SEO-optimized title and meta description
        seo_data = await self._generate_seo_metadata(
            article,
            trending_terms
        )
        
        # Generate schema markup
        schema = self._generate_schema_markup(article)
        
        return {
            "title": seo_data["title"],
            "meta_description": seo_data["description"],
            "schema_markup": schema,
            "keywords": seo_data["keywords"]
        }

    async def _get_trending_topics(self) -> List[str]:
        """Get trending football topics from Google Trends."""
        # Cache trends for 1 hour
        if (self.last_trends_update and 
            (datetime.now() - self.last_trends_update).seconds < 3600):
            return self.cached_trends
        
        try:
            # Get football-related trends in Brazil
            self.trends.build_payload(
                kw_list=['futebol'],
                geo='BR',
                timeframe='now 1-d'
            )
            trends_df = self.trends.related_topics()
            
            # Extract relevant terms
            trending_terms = []
            for topic in trends_df['futebol']['top'].itertuples():
                trending_terms.append(topic.topic_title)
            
            self.cached_trends = trending_terms[:10]
            self.last_trends_update = datetime.now()
            return self.cached_trends
        
        except Exception as e:
            print(f"Error fetching trends: {e}")
            return []

    async def _generate_seo_metadata(
        self,
        article: Article,
        trending_terms: List[str]
    ) -> Dict[str, str]:
        """Generate SEO-optimized metadata using OpenAI."""
        try:
            prompt = f"""Generate SEO metadata in Portuguese for a football article:

Title: {article.title}
Content: {article.excerpt}
Trending terms: {', '.join(trending_terms)}

Please provide:
1. SEO-optimized title (max 60 chars)
2. Meta description (max 160 chars)
3. Keywords (comma-separated)

Format: JSON"""

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an SEO expert for Brazilian football content."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            seo_data = json.loads(response.choices[0].message.content)
            return {
                "title": seo_data["title"],
                "description": seo_data["meta_description"],
                "keywords": seo_data["keywords"]
            }
        
        except Exception as e:
            print(f"Error generating SEO metadata: {e}")
            return {
                "title": article.title,
                "description": article.excerpt[:160],
                "keywords": ""
            }

    def _generate_schema_markup(self, article: Article) -> Dict:
        """Generate schema.org markup for the article."""
        return {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": article.title,
            "description": article.excerpt,
            "image": article.image_url,
            "author": {
                "@type": "Person",
                "name": article.author_name
            },
            "publisher": {
                "@type": "Organization",
                "name": "Só Golasso",
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{settings.FRONTEND_URL}/logo.png"
                }
            },
            "datePublished": article.created_at.isoformat(),
            "dateModified": (article.updated_at or article.created_at).isoformat()
        }

    async def submit_to_google_news(self, article: Article) -> bool:
        """Submit article to Google News via RSS and sitemap."""
        try:
            # Update sitemap
            await self._update_sitemap(article)
            
            # Ping Google News
            ping_url = (
                "https://www.google.com/ping"
                f"?sitemap={settings.FRONTEND_URL}/sitemap.xml"
            )
            response = requests.get(ping_url)
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error submitting to Google News: {e}")
            return False

    async def _update_sitemap(self, article: Article) -> None:
        """Update sitemap.xml with new article."""
        try:
            sitemap_path = "public/sitemap.xml"
            
            try:
                tree = ET.parse(sitemap_path)
                root = tree.getroot()
            except (FileNotFoundError, ET.ParseError):
                # Create new sitemap if doesn't exist
                root = ET.Element("urlset")
                root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
                root.set("xmlns:news", "http://www.google.com/schemas/sitemap-news/0.9")
                tree = ET.ElementTree(root)
            
            # Add new URL entry
            url = ET.SubElement(root, "url")
            
            # Basic URL data
            loc = ET.SubElement(url, "loc")
            loc.text = f"{settings.FRONTEND_URL}/noticia/{article.slug}"
            
            lastmod = ET.SubElement(url, "lastmod")
            lastmod.text = datetime.now(timezone.utc).isoformat()
            
            # News-specific data
            news = ET.SubElement(url, "news:news")
            
            publication = ET.SubElement(news, "news:publication")
            name = ET.SubElement(publication, "news:name")
            name.text = "Só Golasso"
            lang = ET.SubElement(publication, "news:language")
            lang.text = "pt-BR"
            
            pub_date = ET.SubElement(news, "news:publication_date")
            pub_date.text = article.created_at.isoformat()
            
            title = ET.SubElement(news, "news:title")
            title.text = article.title
            
            # Save updated sitemap
            tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
            
        except Exception as e:
            print(f"Error updating sitemap: {e}")
            raise 