import logging
import tweepy
import instaloader
from typing import List, Dict
from datetime import datetime, timedelta
from app.core.config import settings
import time

logger = logging.getLogger(__name__)

class SocialScraper:
    def __init__(self):
        # Twitter API credentials
        self.twitter_client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Instagram client
        self.instagram = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False
        )
        
        # Try to login to Instagram
        try:
            if settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD:
                self.instagram.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
                logger.info("Successfully logged in to Instagram")
            else:
                logger.warning("Instagram credentials not provided, will scrape without authentication")
        except Exception as e:
            logger.error(f"Failed to login to Instagram: {str(e)}")
        
        # Rate limiting settings
        self.twitter_rate_limit = {
            'users_lookup': 300,  # 300 requests per 15 minutes
            'users_tweets': 900,  # 900 requests per 15 minutes
            'last_reset': datetime.now()
        }
        
        self.twitter_requests_count = {
            'users_lookup': 0,
            'users_tweets': 0
        }
        
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

    def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if we've hit the rate limit for a Twitter endpoint"""
        now = datetime.now()
        
        # Reset counters if 15 minutes have passed
        if (now - self.twitter_rate_limit['last_reset']).total_seconds() > 900:
            self.twitter_rate_limit['last_reset'] = now
            self.twitter_requests_count[endpoint] = 0
            
        # Check if we've hit the limit
        if self.twitter_requests_count[endpoint] >= self.twitter_rate_limit[endpoint]:
            logger.warning(f"Rate limit reached for Twitter endpoint: {endpoint}")
            return False
            
        return True

    def _increment_request_count(self, endpoint: str):
        """Increment the request count for a Twitter endpoint"""
        self.twitter_requests_count[endpoint] += 1

    def scrape_twitter(self) -> List[Dict]:
        """Scrape football news from Twitter accounts"""
        articles = []
        try:
            for username in self.twitter_accounts:
                # Check rate limit before making request
                if not self._check_rate_limit('users_lookup'):
                    logger.warning("Skipping Twitter scraping due to rate limit")
                    break
                    
                try:
                    user = self.twitter_client.get_user(username=username)
                    self._increment_request_count('users_lookup')
                except Exception as e:
                    logger.error(f"Error getting Twitter user {username}: {str(e)}")
                    continue
                
                # Check rate limit before getting tweets
                if not self._check_rate_limit('users_tweets'):
                    logger.warning("Skipping tweet fetching due to rate limit")
                    break
                    
                try:
                    tweets = self.twitter_client.get_users_tweets(
                        user.data.id,
                        max_results=5,  # Reduced from 10 to save on API calls
                        tweet_fields=['created_at', 'public_metrics']
                    )
                    self._increment_request_count('users_tweets')
                except Exception as e:
                    logger.error(f"Error getting tweets for {username}: {str(e)}")
                    continue
                
                if not tweets.data:
                    continue
                    
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
                
                # Add a small delay between accounts to avoid hitting rate limits
                time.sleep(1)
                        
        except Exception as e:
            logger.error(f"Error scraping Twitter: {str(e)}")
            
        return articles

    def scrape_instagram(self) -> List[Dict]:
        """Scrape football news from Instagram accounts"""
        articles = []
        try:
            for username in self.instagram_accounts:
                try:
                    profile = instaloader.Profile.from_username(self.instagram.context, username)
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
                except Exception as e:
                    logger.error(f"Error scraping Instagram user {username}: {str(e)}")
                    continue
                    
                # Add a small delay between accounts to avoid rate limiting
                time.sleep(2)
                        
        except Exception as e:
            logger.error(f"Error scraping Instagram: {str(e)}")
            
        return articles

    def scrape_all(self) -> List[Dict]:
        """Scrape from all social media sources"""
        articles = []
        
        # Scrape Twitter
        twitter_articles = self.scrape_twitter()
        articles.extend(twitter_articles)
        
        # Add delay between platforms
        time.sleep(2)
        
        # Scrape Instagram
        instagram_articles = self.scrape_instagram()
        articles.extend(instagram_articles)
        
        return articles 