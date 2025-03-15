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
            sleep_time_between_requests=3,  # Sleep 3 seconds between requests
            fatal_status_codes=[400, 429]  # Don't consider 401 as fatal
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

    def _check_twitter_rate_limit(self, request_type: str) -> bool:
        """Check if we've hit Twitter's rate limit for a specific request type"""
        now = datetime.now()
        
        # Different windows and limits for different request types
        if request_type == "user":
            window_minutes = 15
            max_requests = 75  # User lookup endpoint limit
            requests = self.twitter_user_requests
        elif request_type == "tweets":
            window_minutes = 15
            max_requests = 180  # User tweets endpoint limit
            requests = self.twitter_tweet_requests
        else:
            window_minutes = 15
            max_requests = 180  # Default limit
            requests = self.twitter_requests
            
        window_start = now - timedelta(minutes=window_minutes)
        
        # Remove old requests from tracking
        requests[:] = [t for t in requests if t > window_start]
        
        # Check if we've hit the limit
        if len(requests) >= max_requests:
            wait_time = (requests[0] + timedelta(minutes=window_minutes) - now).total_seconds()
            if wait_time > 0:
                logger.warning(f"Twitter rate limit reached for {request_type}. Need to wait {wait_time:.0f} seconds")
                return False
            
        return True
        
    def _track_twitter_request(self, request_type: str):
        """Track a new Twitter request"""
        now = datetime.now()
        self.twitter_requests.append(now)
        
        if request_type == "user":
            self.twitter_user_requests.append(now)
        elif request_type == "tweets":
            self.twitter_tweet_requests.append(now)

    async def _get_twitter_user(self, username: str) -> Optional[Dict]:
        """Get Twitter user info with caching and retries"""
        # Check cache first
        if username in self.twitter_user_cache:
            return self.twitter_user_cache[username]
            
        # Check rate limit
        if not self._check_twitter_rate_limit("user"):
            window_reset = self.twitter_user_requests[0] + timedelta(minutes=15)
            wait_time = (window_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.0f} seconds for Twitter user rate limit reset")
                await asyncio.sleep(wait_time)
        
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                self._track_twitter_request("user")
                loop = asyncio.get_event_loop()
                user = await loop.run_in_executor(
                    None,
                    lambda: self.twitter_client.get_user(id=None, username=username)
                )
                
                if user and 'data' in user:
                    # Cache the result
                    self.twitter_user_cache[username] = user
                    return user
                    
                return None
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Failed to get Twitter user {username} after {max_retries} retries: {str(e)}")
                    return None
                logger.warning(f"Retry {retry_count} for Twitter user {username}: {str(e)}")
                await asyncio.sleep(5 * retry_count)  # Exponential backoff

    async def _get_twitter_tweets(self, user_id: str) -> Optional[Dict]:
        """Get Twitter tweets with rate limit handling and retries"""
        # Check rate limit
        if not self._check_twitter_rate_limit("tweets"):
            window_reset = self.twitter_tweet_requests[0] + timedelta(minutes=15)
            wait_time = (window_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.0f} seconds for Twitter tweets rate limit reset")
                await asyncio.sleep(wait_time)
        
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                self._track_twitter_request("tweets")
                loop = asyncio.get_event_loop()
                tweets = await loop.run_in_executor(
                    None,
                    lambda: self.twitter_client.get_users_tweets(
                        user_id,
                        max_results=5,  # Reduced from 10 to save on API calls
                        tweet_fields=['created_at', 'public_metrics'],
                        exclude=['retweets', 'replies']  # Only get original tweets
                    )
                )
                
                if tweets and 'data' in tweets:
                    return tweets
                    
                return None
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Failed to get tweets for user {user_id} after {max_retries} retries: {str(e)}")
                    return None
                logger.warning(f"Retry {retry_count} for tweets from user {user_id}: {str(e)}")
                await asyncio.sleep(5 * retry_count)  # Exponential backoff

    async def scrape_twitter(self) -> List[Dict]:
        """Scrape football news from Twitter accounts"""
        articles = []
        try:
            for username in self.twitter_accounts:
                try:
                    # Get user info with retries and caching
                    user_response = await self._get_twitter_user(username)
                    if not user_response or 'data' not in user_response:
                        logger.warning(f"Could not find Twitter user: {username}")
                        continue
                    
                    user_id = user_response['data']['id']
                    
                    # Get tweets with retries
                    tweets_response = await self._get_twitter_tweets(user_id)
                    
                    if tweets_response and 'data' in tweets_response:
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
                        
        except Exception as e:
            logger.error(f"Error scraping Twitter: {str(e)}")
            
        return articles

    async def scrape_instagram(self) -> List[Dict]:
        """Scrape football news from Instagram accounts"""
        articles = []
        
        # Verify/refresh session before starting
        try:
            session_path = Path("/tmp/instagram_session")
            if not session_path.exists():
                self._login_instagram()
        except Exception as e:
            logger.error(f"Failed to verify/refresh Instagram session: {str(e)}")
            return articles
        
        try:
            for username in self.instagram_accounts:
                # Check rate limit
                if not self._check_instagram_rate_limit():
                    logger.warning(f"Skipping Instagram user {username} due to rate limit")
                    await asyncio.sleep(60)  # Wait a minute before next attempt
                    continue
                
                try:
                    self._track_instagram_request()
                    
                    # Get profile with retries
                    retry_count = 0
                    max_retries = 3
                    profile = None
                    while retry_count < max_retries:
                        try:
                            loop = asyncio.get_event_loop()
                            profile = await loop.run_in_executor(
                                None,
                                lambda: instaloader.Profile.from_username(self.instagram.context, username)
                            )
                            break
                        except Exception as e:
                            retry_count += 1
                            error_msg = str(e)
                            
                            # If we get a 401, try to refresh the session
                            if "HTTP error code 401" in error_msg and retry_count < max_retries:
                                logger.warning("Got 401 error, attempting to refresh session...")
                                try:
                                    self._login_instagram()
                                    continue
                                except Exception as login_error:
                                    logger.error(f"Failed to refresh session: {str(login_error)}")
                            
                            if retry_count == max_retries:
                                raise
                            
                            logger.warning(f"Retry {retry_count} for Instagram profile {username}: {error_msg}")
                            await asyncio.sleep(5 * retry_count)  # Exponential backoff
                    
                    if not profile:
                        continue
                    
                    # Get posts with retries
                    retry_count = 0
                    posts = None
                    while retry_count < max_retries:
                        try:
                            loop = asyncio.get_event_loop()
                            posts = await loop.run_in_executor(
                                None,
                                lambda: list(profile.get_posts())[:5]  # Get latest 5 posts
                            )
                            break
                        except Exception as e:
                            retry_count += 1
                            error_msg = str(e)
                            
                            # If we get a 401, try to refresh the session
                            if "HTTP error code 401" in error_msg and retry_count < max_retries:
                                logger.warning("Got 401 error, attempting to refresh session...")
                                try:
                                    self._login_instagram()
                                    continue
                                except Exception as login_error:
                                    logger.error(f"Failed to refresh session: {str(login_error)}")
                            
                            if retry_count == max_retries:
                                raise
                            
                            logger.warning(f"Retry {retry_count} for {username} posts: {error_msg}")
                            await asyncio.sleep(5 * retry_count)  # Exponential backoff
                    
                    if not posts:
                        continue
                    
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