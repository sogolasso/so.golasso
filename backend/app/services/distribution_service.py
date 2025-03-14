from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from app.schemas.article import Article, AuthorStyle
from app.core.config import settings
import tweepy
from facebook import GraphAPI
from instabot import Bot
from tiktok_uploader import upload_video
import json

class DistributionService:
    def __init__(self):
        # Twitter API setup
        self.twitter_client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_SECRET
        )
        
        # Facebook API setup
        self.fb_client = GraphAPI(settings.FACEBOOK_ACCESS_TOKEN)
        
        # Instagram API setup
        self.ig_bot = Bot()
        self.ig_bot.login(
            username=settings.INSTAGRAM_USERNAME,
            password=settings.INSTAGRAM_PASSWORD
        )

    async def distribute_content(self, article: Article) -> Dict[str, str]:
        """Distribute content across platforms based on type and author style."""
        results = {}
        
        # Determine distribution strategy based on category and author style
        if article.is_trending:
            results.update(await self._distribute_trending(article))
        
        if article.category == "meme":
            results.update(await self._distribute_meme(article))
        
        elif article.category in ["match_result", "team_update"]:
            results.update(await self._distribute_news(article))
        
        elif article.category == "tactical":
            results.update(await self._distribute_tactical(article))
        
        return results

    async def _distribute_trending(self, article: Article) -> Dict[str, str]:
        """Distribute trending content across all platforms."""
        tasks = [
            self._post_to_twitter(article),
            self._post_to_facebook(article),
            self._post_to_instagram(article)
        ]
        results = await asyncio.gather(*tasks)
        return {
            "twitter": results[0],
            "facebook": results[1],
            "instagram": results[2]
        }

    async def _distribute_meme(self, article: Article) -> Dict[str, str]:
        """Distribute meme content to Instagram and Twitter."""
        caption = f"😂 {article.title}\n\n{article.excerpt}\n\n📝 Por: {article.author_name}\n\n#SoGolasso #FutebolComHumor"
        
        tasks = [
            self._post_to_instagram(article, caption=caption),
            self._post_to_twitter(article, add_emoji=True)
        ]
        results = await asyncio.gather(*tasks)
        return {
            "instagram": results[0],
            "twitter": results[1]
        }

    async def _distribute_news(self, article: Article) -> Dict[str, str]:
        """Distribute news content with focus on Twitter for live updates."""
        base_tweet = f"{article.title}\n\n{article.excerpt}\n\n🔗 {settings.FRONTEND_URL}/noticia/{article.slug}"
        
        if article.author_style == AuthorStyle.NARRACAO:
            base_tweet = f"🎙️ {article.author_name}:\n\n" + base_tweet
        
        tasks = [
            self._post_to_twitter(article, custom_text=base_tweet),
            self._post_to_facebook(article)
        ]
        results = await asyncio.gather(*tasks)
        return {
            "twitter": results[0],
            "facebook": results[1]
        }

    async def _distribute_tactical(self, article: Article) -> Dict[str, str]:
        """Distribute tactical analysis with focus on longer formats."""
        tasks = [
            self._post_to_facebook(article, is_tactical=True),
            self._post_to_twitter(article, is_tactical=True)
        ]
        results = await asyncio.gather(*tasks)
        return {
            "facebook": results[0],
            "twitter": results[1]
        }

    async def _post_to_twitter(
        self,
        article: Article,
        custom_text: Optional[str] = None,
        add_emoji: bool = False,
        is_tactical: bool = False
    ) -> str:
        """Post content to Twitter with appropriate formatting."""
        try:
            text = custom_text or self._format_tweet(article, add_emoji, is_tactical)
            response = await asyncio.to_thread(
                self.twitter_client.create_tweet,
                text=text
            )
            return f"https://twitter.com/user/status/{response.data['id']}"
        except Exception as e:
            print(f"Twitter posting error: {e}")
            return ""

    async def _post_to_facebook(
        self,
        article: Article,
        is_tactical: bool = False
    ) -> str:
        """Post content to Facebook with appropriate formatting."""
        try:
            message = self._format_facebook_post(article, is_tactical)
            response = await asyncio.to_thread(
                self.fb_client.put_object,
                parent_object="me",
                connection_name="feed",
                message=message,
                link=f"{settings.FRONTEND_URL}/noticia/{article.slug}"
            )
            return f"https://facebook.com/{response['id']}"
        except Exception as e:
            print(f"Facebook posting error: {e}")
            return ""

    async def _post_to_instagram(
        self,
        article: Article,
        caption: Optional[str] = None
    ) -> str:
        """Post content to Instagram with appropriate formatting."""
        try:
            caption = caption or self._format_instagram_caption(article)
            response = await asyncio.to_thread(
                self.ig_bot.upload_photo,
                article.image_url,
                caption=caption
            )
            return f"https://instagram.com/p/{response}"
        except Exception as e:
            print(f"Instagram posting error: {e}")
            return ""

    def _format_tweet(
        self,
        article: Article,
        add_emoji: bool = False,
        is_tactical: bool = False
    ) -> str:
        """Format tweet text based on content type."""
        emoji_prefix = "😂 " if add_emoji else "📰 "
        if is_tactical:
            emoji_prefix = "📊 Análise Tática:\n\n"
        
        text = f"{emoji_prefix}{article.title}\n\n{article.excerpt[:100]}..."
        url = f"\n\n🔗 {settings.FRONTEND_URL}/noticia/{article.slug}"
        
        # Ensure we don't exceed Twitter's character limit
        if len(text + url) > 280:
            text = text[:280 - len(url) - 3] + "..."
        
        return text + url

    def _format_facebook_post(self, article: Article, is_tactical: bool = False) -> str:
        """Format Facebook post text based on content type."""
        prefix = "📊 Análise Tática" if is_tactical else "⚽ Notícia"
        return f"""{prefix}

{article.title}

{article.excerpt}

✍️ Por: {article.author_name}

Leia mais: {settings.FRONTEND_URL}/noticia/{article.slug}

#SoGolasso #FutebolComEstilo"""

    def _format_instagram_caption(self, article: Article) -> str:
        """Format Instagram caption with appropriate hashtags."""
        return f"""{article.title}

{article.excerpt}

✍️ Por: {article.author_name}

Leia mais: Link na bio 🔗
#SoGolasso #FutebolBrasileiro #Futebol""" 