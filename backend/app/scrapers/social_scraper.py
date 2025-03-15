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
        # Twitter setup
        if all([settings.TWITTER_BEARER_TOKEN]):
            self.twitter_client = tweepy.Client(
                bearer_token=settings.TWITTER_BEARER_TOKEN,
                wait_on_rate_limit=True  # Enable built-in rate limit handling
            )
        else:
            self.twitter_client = None
            logger.warning("Twitter credentials not configured")
            
        # Instagram setup
        if all([settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD]):
            self.instagram = instaloader.Instaloader()
            self._setup_instagram()
        else:
            self.instagram = None
            logger.warning("Instagram credentials not configured")
            
        # Cache setup
        self.twitter_cache = {}
        self.twitter_cache_time = {}
        self.twitter_rate_limit_reset = {}
        self.twitter_backoff_time = 15  # Initial backoff time in seconds
        
        # Twitter accounts to monitor
        self.twitter_accounts = [
            'ge',             # Globo Esporte (updated from geglobo)
            'espnbrasil',     # ESPN Brasil (lowercase)
            'lancenet',       # Lance!
            'cbf_futebol',    # CBF (lowercase)
            'brasileirao',    # Brasileirão (lowercase)
            'LibertadoresBR', # Libertadores
            'copadobrasil'    # Copa do Brasil (lowercase)
        ]
        
        # Instagram accounts to monitor
        self.instagram_accounts = [
            'cbf_futebol',
            'brasileirao',
            'libertadores',
            'copadobr'
        ]
        
    def _setup_instagram(self):
        """Setup Instagram session"""
        try:
            session_path = Path("/tmp/instagram_session")
            if session_path.exists():
                # Try to load existing session
                self.instagram.load_session_from_file(
                    settings.INSTAGRAM_USERNAME,
                    session_path
                )
                logger.info("Loaded existing Instagram session")
            else:
                # Create new session
                self.instagram.login(
                    settings.INSTAGRAM_USERNAME,
                    settings.INSTAGRAM_PASSWORD
                )
                # Save session for future use
                self.instagram.save_session_to_file(session_path)
                logger.info("Created and saved new Instagram session")
                
            logger.info("Successfully logged in to Instagram")
            
        except Exception as e:
            logger.error(f"Instagram setup failed: {str(e)}")
            self.instagram = None

    def _check_twitter_rate_limit(self, endpoint: str = "tweets") -> bool:
        """Check if we can make a Twitter API request"""
        now = datetime.now()
        
        # Check if we're in a backoff period
        if endpoint in self.twitter_rate_limit_reset:
            reset_time = self.twitter_rate_limit_reset[endpoint]
            if now < reset_time:
                wait_time = (reset_time - now).total_seconds()
                logger.warning(f"Rate limit for {endpoint} resets in {wait_time:.0f} seconds")
                return False
                
        return True
        
    def _handle_twitter_rate_limit(self, endpoint: str, error_response=None):
        """Handle Twitter rate limit with exponential backoff"""
        now = datetime.now()
        
        # Get reset time from headers if available
        if error_response and hasattr(error_response, 'response'):
            reset_time = error_response.response.headers.get('x-rate-limit-reset')
            if reset_time:
                reset_time = datetime.fromtimestamp(int(reset_time))
                self.twitter_rate_limit_reset[endpoint] = reset_time
                logger.info(f"Rate limit for {endpoint} resets at {reset_time}")
                return
        
        # If no reset time in headers, use exponential backoff
        if endpoint not in self.twitter_backoff_time:
            self.twitter_backoff_time[endpoint] = 15  # Start with 15 seconds
        else:
            self.twitter_backoff_time[endpoint] *= 2  # Double the backoff time
            
        # Cap maximum backoff at 5 minutes
        self.twitter_backoff_time[endpoint] = min(self.twitter_backoff_time[endpoint], 300)
        
        # Set reset time
        reset_time = now + timedelta(seconds=self.twitter_backoff_time[endpoint])
        self.twitter_rate_limit_reset[endpoint] = reset_time
        logger.info(f"Using exponential backoff: {self.twitter_backoff_time[endpoint]} seconds")

    async def _get_twitter_user(self, username: str) -> Optional[Dict]:
        """Get Twitter user info with caching"""
        # Check cache first
        if username in self.twitter_cache:
            cache_time = self.twitter_cache_time.get(username)
            if cache_time and datetime.now() - cache_time < timedelta(hours=24):
                return self.twitter_cache[username]
        
        # Check rate limits
        if not self._check_twitter_rate_limit("users"):
            return None
            
        try:
            response = self.twitter_client.get_user(username=username)
            
            # Handle both Response object and dictionary responses
            if isinstance(response, dict):
                user_data = response.get('data', {})
            else:
                user_data = response.data if hasattr(response, 'data') else None
                
            if user_data:
                user_info = {
                    'id': user_data.get('id') if isinstance(user_data, dict) else user_data.id,
                    'name': user_data.get('name') if isinstance(user_data, dict) else user_data.name,
                    'username': user_data.get('username') if isinstance(user_data, dict) else user_data.username
                }
                # Cache for 24 hours
                self.twitter_cache[username] = user_info
                self.twitter_cache_time[username] = datetime.now()
                return user_info
                
        except tweepy.TooManyRequests as e:
            logger.warning("Twitter rate limit exceeded for user lookup")
            self._handle_twitter_rate_limit("users", e)
        except Exception as e:
            logger.error(f"Error getting Twitter user {username}: {str(e)}")
            
        return None

    async def _get_twitter_tweets(self, user_id: str) -> Optional[Dict]:
        """Get Twitter tweets with rate limit handling"""
        # Check rate limits
        if not self._check_twitter_rate_limit("tweets"):
            return None
            
        try:
            response = self.twitter_client.get_users_tweets(
                user_id,
                max_results=5,  # Reduced from 10 to save on API calls
                tweet_fields=['created_at', 'public_metrics'],
                exclude=['retweets', 'replies']
            )
            
            # Handle both Response object and dictionary responses
            if isinstance(response, dict):
                return response
            else:
                return {
                    'data': response.data,
                    'meta': response.meta if hasattr(response, 'meta') else {}
                }
                
        except tweepy.TooManyRequests as e:
            logger.warning("Twitter rate limit exceeded for tweet lookup")
            self._handle_twitter_rate_limit("tweets", e)
        except Exception as e:
            logger.error(f"Error getting tweets for user {user_id}: {str(e)}")
            
        return None

    async def scrape_twitter(self) -> List[Dict]:
        """Scrape football news from Twitter accounts"""
        if not self.twitter_client:
            logger.warning("Twitter client not configured, skipping Twitter scraping")
            return []
            
        articles = []
        try:
            for username in self.twitter_accounts:
                try:
                    # Get user info with caching
                    user = await self._get_twitter_user(username)
                    if not user:
                        logger.warning(f"Could not find Twitter user: {username}")
                        continue
                    
                    # Get tweets with rate limit handling
                    tweets_response = await self._get_twitter_tweets(user['id'])
                    if not tweets_response:
                        continue
                        
                    tweets_data = tweets_response.get('data', [])
                    if not tweets_data:
                        continue
                    
                    # Process tweets
                    for tweet in tweets_data:
                        # Handle both dictionary and Response.Tweet objects
                        if isinstance(tweet, dict):
                            tweet_text = tweet.get('text', '')
                            tweet_id = tweet.get('id')
                            created_at = tweet.get('created_at')
                            metrics = tweet.get('public_metrics', {})
                        else:
                            tweet_text = tweet.text
                            tweet_id = tweet.id
                            created_at = tweet.created_at
                            metrics = tweet.public_metrics
                            
                        retweets = metrics.get('retweet_count', 0) if isinstance(metrics, dict) else metrics.retweet_count
                        likes = metrics.get('like_count', 0) if isinstance(metrics, dict) else metrics.like_count
                        
                        if retweets > 10 or likes > 50:
                            articles.append({
                                'title': tweet_text[:100] + '...' if len(tweet_text) > 100 else tweet_text,
                                'content': tweet_text,
                                'source_url': f"https://twitter.com/{username}/status/{tweet_id}",
                                'source_type': 'twitter',
                                'published_at': created_at,
                                'author': username,
                                'engagement_count': retweets + likes
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
        if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
            logger.warning("Instagram credentials not configured, skipping Instagram scraping")
            return []
            
        articles = []
        
        # Verify/refresh session before starting
        try:
            session_path = Path("/tmp/instagram_session")
            if not session_path.exists():
                self._setup_instagram()
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
        """Scrape all social media sources"""
        all_articles = []
        
        # Scrape Twitter
        twitter_articles = await self.scrape_twitter()
        all_articles.extend(twitter_articles)
        logger.info(f"Scraped {len(twitter_articles)} articles from Twitter")
        
        # Scrape Instagram if configured
        if self.instagram:
            instagram_articles = await self.scrape_instagram()
            all_articles.extend(instagram_articles)
            logger.info(f"Scraped {len(instagram_articles)} articles from Instagram")
        
        return all_articles 