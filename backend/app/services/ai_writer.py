import logging
from typing import Dict, Any
from openai import AsyncOpenAI
import hashlib
import json
from .ai_usage_tracker import AIUsageTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIWriter:
    def __init__(self, api_key: str, max_daily_articles: int = 10, max_monthly_cost: float = 100.0):
        self.client = AsyncOpenAI(api_key=api_key)
        self.usage_tracker = AIUsageTracker(max_daily_articles, max_monthly_cost)
        
    def _calculate_content_hash(self, title: str, source_text: str, source_type: str) -> str:
        """Calculate a hash for the content to use as cache key"""
        content = f"{title}|{source_text}|{source_type}"
        return hashlib.md5(content.encode()).hexdigest()
        
    async def generate_article(
        self,
        title: str,
        source_text: str,
        source_type: str
    ) -> Dict[str, Any]:
        """Generate an article using OpenAI's GPT model with usage tracking and caching"""
        try:
            # Log the attempt
            logger.info(f"Attempting to generate article: {title}")
            
            # Check if we can generate more articles today
            if not self.usage_tracker.can_generate_article():
                logger.warning("Daily article limit reached")
                return None
                
            # Check monthly cost limit
            if not self.usage_tracker.check_monthly_cost_limit():
                logger.warning("Monthly cost limit approaching")
                return None
                
            # Check cache first
            content_hash = self._calculate_content_hash(title, source_text, source_type)
            cached_article = self.usage_tracker.get_cached_article(content_hash)
            if cached_article:
                logger.info("Using cached article")
                return cached_article
            
            # Create a prompt based on the source type and content
            prompt = self._create_prompt(title, source_text, source_type)
            
            # Generate content using OpenAI
            logger.info("Sending request to OpenAI...")
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional sports journalist specializing in football (soccer). Write engaging, accurate, and well-structured articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Calculate cost (approximate)
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * 0.002  # $0.002 per 1K tokens for GPT-3.5
            
            # Track usage
            self.usage_tracker.track_usage(tokens_used, cost)
            
            # Parse the response
            content = response.choices[0].message.content
            logger.info("Successfully generated article content")
            
            # Generate a summary
            logger.info("Generating summary...")
            summary = await self._generate_summary(content)
            
            # Determine category and author details
            logger.info("Determining category and author details...")
            category = await self._determine_category(content)
            author_details = await self._generate_author_details(content)
            
            # Create article data
            article_data = {
                "title": title,
                "content": content,
                "summary": summary,
                "category": category,
                "author_style": author_details["style"],
                "author_name": author_details["name"],
                "meta_description": summary[:160],
                "meta_keywords": self._extract_keywords(content),
                "slug": self._generate_slug(title)
            }
            
            # Cache the article
            self.usage_tracker.cache_article(content_hash, article_data)
            logger.info(f"Successfully generated article: {title}")
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error generating article '{title}': {str(e)}", exc_info=True)
            return None
            
    def _create_prompt(self, title: str, source_text: str, source_type: str) -> str:
        """Create a prompt for the AI based on source type"""
        return f"""Write a Brazilian football article based on the following information:

Title: {title}

Source Content: {source_text}

Type: {source_type}

Guidelines:
1. Write in Brazilian Portuguese
2. Use engaging and dynamic language
3. Include relevant context and background
4. Keep it concise (500-700 words)
5. Focus on key facts and analysis
6. Maintain journalistic integrity

Please structure the article with:
- Engaging introduction
- Main content with clear paragraphs
- Conclusion or future implications"""

    async def _generate_summary(self, content: str) -> str:
        """Generate a brief summary of the article"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Create a brief summary of this football article in 2-3 sentences."},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return content[:200] + "..."
            
    async def _determine_category(self, content: str) -> str:
        """Determine the article category"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Changed from gpt-4-turbo-preview
                messages=[
                    {"role": "system", "content": "Categorize this football article into one of these categories: Transfer News, Match Report, Player News, Team News, Analysis, Opinion"},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=20
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error determining category: {e}")
            return "General"
    
    async def _generate_author_details(self, content: str) -> Dict[str, str]:
        """Generate author details based on content"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Changed from gpt-4-turbo-preview
                messages=[
                    {"role": "system", "content": "Based on this article's content and style, suggest an author name and writing style (e.g., Analytical, Narrative, Technical, etc.)"},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=50
            )
            result = response.choices[0].message.content.strip().split("\n")
            return {
                "name": result[0] if len(result) > 0 else "Sports Desk",
                "style": result[1] if len(result) > 1 else "Journalistic"
            }
        except Exception as e:
            logger.error(f"Error generating author details: {e}")
            return {"name": "Sports Desk", "style": "Journalistic"}
    
    def _extract_keywords(self, content: str) -> str:
        """Extract relevant keywords from the content"""
        # Enhanced keyword extraction
        common_keywords = [
            "futebol", "gol", "campeonato", "brasileiro", "copa",
            "time", "jogador", "técnico", "partida", "vitória",
            "derrota", "empate", "clássico", "torneio", "liga"
        ]
        keywords = []
        
        content_words = content.lower().split()
        for word in content_words:
            if len(word) > 3 and (word in common_keywords or any(kw in word for kw in common_keywords)):
                keywords.append(word)
                
        return ",".join(set(keywords[:10]))  # Limit to top 10 keywords
        
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from the title"""
        from slugify import slugify
        return slugify(title)  # Using python-slugify for better slug generation
        
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from the title"""
        return "-".join(title.lower().split()[:8]) 