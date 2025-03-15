import logging
import tweepy
import instaloader
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings
import time
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class SocialScraper:
    def __init__(self):
        # Twitter API credentials and client with better rate limit handling
        self.twitter_client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True,  # Let tweepy handle rate limiting
            return_type=dict  # Return dictionary instead of Response object
        )
        
        # Cache for Twitter user IDs to reduce API calls
        self.twitter_user_cache = {}
        
        # Track Twitter request times for manual rate limiting
        self.twitter_requests = []
        self.twitter_user_requests = []
        self.twitter_tweet_requests = []
        
        # Instagram client with more robust settings
        self.instagram = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            max_connection_attempts=3,
            request_timeout=30,
            sleep=True,  # Enable sleeping between requests
            fatal_status_codes=[400, 429]  # Don't consider 401 as fatal
        )
        
        # Set custom sleep time for Instagram requests
        if hasattr(self.instagram.context, "sleep_between_requests"):
            self.instagram.context.sleep_between_requests = 3
        
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
                
                # Verify session is valid
                try:
                    test_profile = instaloader.Profile.from_username(self.instagram.context, "instagram")
                    logger.info("Instagram session verified successfully")
                    return
                except Exception as e:
                    logger.warning("Existing session is invalid, will create new one")
                    if session_path.exists():
                        session_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to load Instagram session: {str(e)}")
                if session_path.exists():
                    session_path.unlink()
        
        # Create new session with retry logic
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Clear any existing cookies/session data
                self.instagram.context._session.cookies.clear()
                
                # Attempt login
                self.instagram.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
                
                # Save session if login successful
                self.instagram.save_session_to_file(session_path)
                logger.info("Created and saved new Instagram session")
                return
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "Checkpoint required" in error_msg:
                    logger.error("Instagram requires security verification!")
                    logger.error("Please follow these steps:")
                    logger.error("1. Login to Instagram in your browser with these credentials:")
                    logger.error(f"   Username: {settings.INSTAGRAM_USERNAME}")
                    logger.error("2. You should see a security verification prompt")
                    logger.error("3. Complete the security verification in your browser")
                    logger.error("4. After verification, run this command in your terminal:")
                    logger.error("   rm /tmp/instagram_session")
                    logger.error("5. Then restart the scheduler service in Render")
                    logger.error("\nNote: If you don't see the verification prompt when logging in,")
                    logger.error("try logging out of Instagram first, then log in again.")
                    raise
                
                if retry_count == max_retries:
                    logger.error(f"Failed to create Instagram session after {max_retries} attempts: {error_msg}")
                    raise
                
                logger.warning(f"Login attempt {retry_count} failed: {error_msg}")
                time.sleep(5 * retry_count)  # Exponential backoff

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

    def _check_twitter_rate_limit(self) -> bool:
        """Check if we're within Twitter rate limits"""
        now = datetime.now()
        window_start = now - timedelta(minutes=settings.TWITTER_WINDOW_MINUTES)
        
        # Clear old requests from history
        self.twitter_requests = [ts for ts in self.twitter_requests if ts > window_start]
        
        # Check if we're within limits
        return len(self.twitter_requests) < settings.TWITTER_REQUESTS_PER_WINDOW
        
    def _update_twitter_rate_limit(self):
        """Update Twitter rate limit tracking"""
        now = datetime.now()
        self.twitter_requests.append(now)
        
        # Cleanup old requests
        window_start = now - timedelta(minutes=settings.TWITTER_WINDOW_MINUTES)
        self.twitter_requests = [ts for ts in self.twitter_requests if ts > window_start]

    async def _get_twitter_user(self, username: str) -> Optional[Dict]:
        """Get Twitter user info with caching and retries"""
        # Check cache first
        cache_key = f"twitter_user_{username}"
        cached_user = self.twitter_user_cache.get(username)
        if cached_user:
            return cached_user
            
        # Check rate limits before making request
        if not self._check_twitter_rate_limit():
            logger.warning("Twitter rate limit would be exceeded, skipping user lookup")
            return None
            
        try:
            # Get user info
            user = self.twitter_client.get_user(username=username)
            if user and user.data:
                user_data = {
                    'id': user.data.id,
                    'name': user.data.name,
                    'username': user.data.username
                }
                # Cache for 24 hours
                self.twitter_user_cache[username] = user_data
                return user_data
                
        except Exception as e:
            if "Rate limit exceeded" in str(e):
                logger.warning("Twitter rate limit exceeded, will retry in next cycle")
                self._update_twitter_rate_limit()
            else:
                logger.error(f"Error getting Twitter user {username}: {str(e)}")
        return None
        
    async def _get_twitter_tweets(self, user_id: str) -> Optional[Dict]:
        """Get Twitter tweets with rate limit handling and retries"""
        # Check rate limit
        if not self._check_twitter_rate_limit():
            logger.warning("Twitter rate limit would be exceeded, skipping this cycle")
            return None
        
        try:
            # Get tweets without waiting on rate limit
            tweets = self.twitter_client.get_users_tweets(
                user_id,
                max_results=5,  # Reduced from 10 to save on API calls
                tweet_fields=['created_at', 'public_metrics'],
                exclude=['retweets', 'replies']  # Only get original tweets
            )
            
            if tweets and 'data' in tweets:
                return tweets
                
            return None
                
        except Exception as e:
            if "Rate limit exceeded" in str(e):
                logger.warning("Twitter rate limit exceeded, will retry in next cycle")
                self._update_twitter_rate_limit()
            else:
                logger.error(f"Error getting tweets for user {user_id}: {str(e)}")
            return None

    async def scrape_twitter(self) -> List[Dict]:
        """Scrape football news from Twitter accounts"""
        if not all([self.twitter_client]):
            logger.warning("Twitter client not configured, skipping Twitter scraping")
            return []
            
        articles = []
        try:
            # Only proceed if within rate limits
            if not self._check_twitter_rate_limit():
                logger.warning("Twitter rate limit would be exceeded, skipping this cycle")
                return []
                
            for username in self.twitter_accounts:
                try:
                    # Get user info with retries and caching
                    user = await self._get_twitter_user(username)
                    if not user:
                        logger.warning(f"Could not find Twitter user: {username}")
                        continue
                    
                    user_id = user['id']
                    
                    # Get tweets
                    tweets_response = await self._get_twitter_tweets(user_id)
                    if not tweets_response:
                        continue
                    
                    if 'data' in tweets_response:
                        for tweet in tweets_response['data']:
                            # Only include tweets with significant engagement
                            metrics = tweet['public_metrics']
                            if metrics['retweet_count'] > 10 or metrics['like_count'] > 50:
                                articles.append({
                                    'title': tweet['text'][:100] + '...' if len(tweet['text']) > 100 else tweet['text'],
                                    'content': tweet['text'],
                                    'source_url': f"https://twitter.com/{username}/status/{tweet['id']}",
                                    'source_type': 'twitter',
                                    'published_at': tweet['created_at'],
                                    'author': username,
                                    'engagement_count': metrics['retweet_count'] + metrics['like_count']
                                })
                    
                    # Small delay between accounts
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing Twitter user {username}: {str(e)}")
                    continue
                        
            # Update rate limit tracking after successful requests
            self._update_twitter_rate_limit()
            
        except Exception as e:
            if "Rate limit exceeded" in str(e):
                logger.warning("Twitter rate limit exceeded, will retry in next cycle")
                self._update_twitter_rate_limit()
            else:
                logger.error(f"Error scraping Twitter: {str(e)}")
            
        return articles

    async def scrape_instagram(self) -> List[Dict]:
        """Scrape football news from Instagram accounts"""
        if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
            logger.warning("Instagram credentials not configured, skipping Instagram scraping")
            return []
            
        articles = []
        
        # Verify/refresh session before starting
        try:
            session_path = Path("/tmp/instagram_session")
            if not session_path.exists():
                self._login_instagram()
        except Exception as e:
            if "Checkpoint required" in str(e):
                logger.error("Instagram requires security verification!")
                logger.error("Please follow these steps:")
                logger.error("1. Login to Instagram in your browser")
                logger.error("2. Complete the security verification")
                logger.error("3. Delete the session file: rm /tmp/instagram_session")
                logger.error("4. Restart the scheduler service")
            else:
                logger.error(f"Failed to verify/refresh Instagram session: {str(e)}")
            return articles
        
        try:
            for username in self.instagram_accounts:
                # Check rate limit
                if not self._check_instagram_rate_limit():
                    logger.warning(f"Skipping Instagram user {username} due to rate limit")
                    continue
                
                try:
                    self._track_instagram_request()
                    
                    # Get profile
                    profile = instaloader.Profile.from_username(self.instagram.context, username)
                    if not profile:
                        continue
                    
                    # Get latest posts
                    posts = list(profile.get_posts())[:5]  # Get latest 5 posts
                    
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
                    
                    # Delay between accounts
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    if "Checkpoint required" in str(e):
                        logger.error(f"Instagram checkpoint required for {username}")
                        break  # Stop processing other accounts
                    else:
                        logger.error(f"Error scraping Instagram user {username}: {str(e)}")
                    continue
                        
        except Exception as e:
            if "Checkpoint required" in str(e):
                logger.error("Instagram checkpoint required - please verify account")
            else:
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