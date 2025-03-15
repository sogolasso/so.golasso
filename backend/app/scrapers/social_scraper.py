import logging
import tweepy
import instaloader
import os
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
from app.core.config import settings
import time
import asyncio

logger = logging.getLogger(__name__)

class SocialScraper:
    def __init__(self):
        # Twitter API credentials
        self.twitter_client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True  # Let tweepy handle rate limiting
        )
        
        # Instagram client
        self.instagram = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            max_connection_attempts=3
        )
        
        # Try to login to Instagram using session
        try:
            if settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD:
                self._login_instagram()
                logger.info("Successfully logged in to Instagram")
            else:
                logger.warning("Instagram credentials not provided, will scrape without authentication")
        except Exception as e:
            logger.error(f"Failed to login to Instagram: {str(e)}")
        
        # List of accounts to follow
        self.twitter_accounts = [
            "geglobo",  # Globo Esporte
            "ESPNBrasil",  # ESPN Brasil
            "Lance",  # Lance!
            "CBF_Futebol",  # CBF
            "Flamengo",  # Flamengo
            "Palmeiras",  # Palmeiras
            "Corinthians",  # Corinthians
            "SaoPauloFC",  # São Paulo
            "SantosFC",  # Santos
            "Cruzeiro"  # Cruzeiro
        ]
        
        self.instagram_accounts = [
            "ge.globo",  # Globo Esporte
            "espnbrasil",  # ESPN Brasil
            "lance",  # Lance!
            "cbf_futebol",  # CBF
            "flamengo",  # Flamengo
            "palmeiras",  # Palmeiras
            "corinthians",  # Corinthians
            "saopaulofc",  # São Paulo
            "santosfc",  # Santos
            "cruzeiro"  # Cruzeiro
        ]
        
        # Track Instagram request times
        self.instagram_requests = []
        
    def _login_instagram(self):
        """Handle Instagram login with session support"""
        session_path = Path("/tmp/instagram_session")
        
        # Try to load existing session
        if session_path.exists():
            try:
                self.instagram.load_session_from_file(settings.INSTAGRAM_USERNAME, session_path)
                logger.info("Loaded existing Instagram session")
                return
            except Exception as e:
                logger.warning(f"Failed to load Instagram session: {str(e)}")
                if session_path.exists():
                    session_path.unlink()  # Delete invalid session file
        
        # Create new session
        try:
            self.instagram.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
            self.instagram.save_session_to_file(session_path)
            logger.info("Created and saved new Instagram session")
        except Exception as e:
            error_msg = str(e)
            if "Checkpoint required" in error_msg:
                checkpoint_url = error_msg.split("Point your browser to ")[1].split(" -")[0]
                logger.error(f"Instagram requires security verification. Please visit: {checkpoint_url}")
                logger.error("After completing verification, delete the session file and restart the service")
            else:
                logger.error(f"Failed to create Instagram session: {error_msg}")
            raise
    
    def _check_instagram_rate_limit(self) -> bool:
        """Check if we've hit Instagram's rate limit"""
        now = datetime.now()
        window_start = now - timedelta(minutes=settings.INSTAGRAM_WINDOW_MINUTES)
        
        # Remove old requests from tracking
        self.instagram_requests = [t for t in self.instagram_requests if t > window_start]
        
        # Check if we've hit the limit
        if len(self.instagram_requests) >= settings.INSTAGRAM_REQUESTS_PER_WINDOW:
            logger.warning("Instagram rate limit reached")
            return False
        
        return True
    
    def _track_instagram_request(self):
        """Track a new Instagram request"""
        self.instagram_requests.append(datetime.now())

    async def scrape_twitter(self) -> List[Dict]:
        """Scrape football news from Twitter accounts"""
        articles = []
        try:
            for username in self.twitter_accounts:
                try:
                    # tweepy will handle rate limiting automatically
                    user = self.twitter_client.get_user(username=username)
                    
                    tweets = self.twitter_client.get_users_tweets(
                        user.data.id,
                        max_results=5,  # Reduced from 10 to save on API calls
                        tweet_fields=['created_at', 'public_metrics']
                    )
                    
                    if tweets and tweets.data:
                        for tweet in tweets.data:
                            # Only include tweets with media or significant engagement
                            if tweet.public_metrics['retweet_count'] > 10 or tweet.public_metrics['like_count'] > 50:
                                articles.append({
                                    'title': tweet.text[:100] + '...' if len(tweet.text) > 100 else tweet.text,
                                    'content': tweet.text,
                                    'source_url': f"https://twitter.com/{username}/status/{tweet.id}",
                                    'source_type': 'twitter',
                                    'published_at': tweet.created_at,
                                    'author': username,
                                    'engagement_count': tweet.public_metrics['retweet_count'] + tweet.public_metrics['like_count']
                                })
                    
                    # Small delay between accounts even with rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing Twitter user {username}: {str(e)}")
                    continue
                        
        except Exception as e:
            logger.error(f"Error scraping Twitter: {str(e)}")
            
        return articles

    async def scrape_instagram(self) -> List[Dict]:
        """Scrape football news from Instagram accounts"""
        articles = []
        try:
            for username in self.instagram_accounts:
                # Check rate limit
                if not self._check_instagram_rate_limit():
                    logger.warning(f"Skipping Instagram user {username} due to rate limit")
                    await asyncio.sleep(60)  # Wait a minute before next attempt
                    continue
                
                try:
                    self._track_instagram_request()
                    profile = instaloader.Profile.from_username(self.instagram.context, username)
                    
                    # Get posts with retries
                    retry_count = 0
                    max_retries = 3
                    while retry_count < max_retries:
                        try:
                            posts = list(profile.get_posts())[:5]  # Get latest 5 posts
                            break
                        except Exception as e:
                            retry_count += 1
                            if retry_count == max_retries:
                                raise
                            logger.warning(f"Retry {retry_count} for {username} posts: {str(e)}")
                            await asyncio.sleep(5 * retry_count)  # Exponential backoff
                    
                    for post in posts:
                        # Only include posts with significant engagement
                        if post.likes + post.comments > 100:
                            caption = post.caption if post.caption else ''
                            articles.append({
                                'title': caption[:100] + '...' if len(caption) > 100 else caption,
                                'content': caption,
                                'source_url': f"https://instagram.com/p/{post.shortcode}",
                                'source_type': 'instagram',
                                'published_at': post.date_local,
                                'author': username,
                                'engagement_count': post.likes + post.comments
                            })
                except Exception as e:
                    logger.error(f"Error scraping Instagram user {username}: {str(e)}")
                    continue
                
                # Longer delay between Instagram requests
                await asyncio.sleep(5)
                        
        except Exception as e:
            logger.error(f"Error scraping Instagram: {str(e)}")
            
        return articles

    async def scrape_all(self) -> List[Dict]:
        """Scrape from all social media sources"""
        articles = []
        
        # Scrape Twitter
        try:
            twitter_articles = await self.scrape_twitter()
            articles.extend(twitter_articles)
            logger.info(f"Scraped {len(twitter_articles)} articles from Twitter")
        except Exception as e:
            logger.error(f"Failed to scrape Twitter: {str(e)}")
        
        # Add delay between platforms
        await asyncio.sleep(5)
        
        # Try Instagram only if we have credentials and no checkpoint required
        try:
            if settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD:
                instagram_articles = await self.scrape_instagram()
                articles.extend(instagram_articles)
                logger.info(f"Scraped {len(instagram_articles)} articles from Instagram")
            else:
                logger.info("Skipping Instagram scraping - no credentials provided")
        except Exception as e:
            if "Checkpoint required" in str(e):
                logger.warning("Skipping Instagram scraping - security verification required")
            else:
                logger.error(f"Failed to scrape Instagram: {str(e)}")
        
        return articles 