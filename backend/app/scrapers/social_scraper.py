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
from app.models.article import Article
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class SocialScraper:
    def __init__(self):
        """Initialize social media scrapers"""
        self.twitter_client = None
        self.instagram_client = None
        self.db = SessionLocal()
        
        # Initialize Twitter client if credentials are available
        if all([
            settings.TWITTER_API_KEY,
            settings.TWITTER_API_SECRET,
            settings.TWITTER_BEARER_TOKEN
        ]):
            try:
                self.twitter_client = tweepy.Client(
                    bearer_token=settings.TWITTER_BEARER_TOKEN,
                    consumer_key=settings.TWITTER_API_KEY,
                    consumer_secret=settings.TWITTER_API_SECRET,
                    access_token=settings.TWITTER_ACCESS_TOKEN,
                    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
                    wait_on_rate_limit=True
                )
                logger.info("Twitter client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client: {str(e)}")
        
        # Initialize Instagram client if credentials are available
        if all([settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD]):
            try:
                self.instagram_client = instaloader.Instaloader(
                    download_pictures=False,
                    download_videos=False,
                    download_video_thumbnails=False,
                    download_geotags=False,
                    download_comments=False,
                    save_metadata=False
                )
                self.instagram_client.login(
                    settings.INSTAGRAM_USERNAME,
                    settings.INSTAGRAM_PASSWORD
                )
                logger.info("Instagram client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Instagram client: {str(e)}")
        
        # Twitter accounts to follow
        self.twitter_accounts = [
            "geglobo",  # Globo Esporte
            "ESPNBrasil",  # ESPN Brasil
            "Lance",  # Lance!
            "UOLesporte",  # UOL Esporte
            "TNTsportsBR",  # TNT Sports
            "sportv",  # SporTV
            "FOXSportsBR",  # FOX Sports
            "ESPNFC",  # ESPN FC
            "brfootball",  # BR Football
            "futebol_info"  # Futebol Info
        ]
        
        # Instagram accounts to follow
        self.instagram_accounts = [
            "ge.globoesporte",  # Globo Esporte
            "espnbrasil",  # ESPN Brasil
            "lance",  # Lance!
            "uolesporte",  # UOL Esporte
            "sportv",  # SporTV
            "foxsportsbr",  # FOX Sports
            "brfootball",  # BR Football
            "futebol_info"  # Futebol Info
        ]
        
    async def scrape_twitter(self) -> List[Dict]:
        """Scrape tweets from configured accounts"""
        if not self.twitter_client:
            logger.warning("Twitter client not initialized, skipping Twitter scraping")
            return []
            
        tweets = []
        try:
            for username in self.twitter_accounts:
                try:
                    # Get user ID first
                    user = self.twitter_client.get_user(username=username)
                    if not user.data:
                        logger.warning(f"Could not find Twitter user: {username}")
                        continue
                        
                    user_id = user.data.id
                    
                    # Get tweets with error handling
                    try:
                        tweets_data = self.twitter_client.get_users_tweets(
                            user_id,
                            max_results=10,
                            exclude=['retweets', 'replies'],
                            tweet_fields=['created_at', 'public_metrics']
                        )
                        
                        if not tweets_data.data:
                            continue
                            
                        for tweet in tweets_data.data:
                            try:
                                # Calculate engagement score
                                metrics = tweet.public_metrics
                                engagement = (
                                    metrics.get('like_count', 0) +
                                    metrics.get('retweet_count', 0) +
                                    metrics.get('reply_count', 0) +
                                    metrics.get('quote_count', 0)
                                )
                                
                                # Only include tweets with sufficient engagement
                                if engagement >= settings.MIN_ENGAGEMENT_SCORE:
                                    tweets.append({
                                        'title': tweet.text[:100] + '...' if len(tweet.text) > 100 else tweet.text,
                                        'content': tweet.text,
                                        'source_url': f"https://twitter.com/{username}/status/{tweet.id}",
                                        'source_type': 'twitter',
                                        'author': username,
                                        'published_at': tweet.created_at,
                                        'engagement_count': engagement
                                    })
                            except Exception as e:
                                logger.error(f"Error processing tweet: {str(e)}")
                                continue
                                
                    except tweepy.TooManyRequests:
                        logger.warning(f"Rate limit exceeded for user {username}, skipping")
                        continue
                    except Exception as e:
                        logger.error(f"Error fetching tweets for {username}: {str(e)}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing Twitter account {username}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Twitter scraping: {str(e)}")
            
        return tweets
        
    async def scrape_instagram(self) -> List[Dict]:
        """Scrape posts from configured Instagram accounts"""
        if not self.instagram_client:
            logger.warning("Instagram client not initialized, skipping Instagram scraping")
            return []
            
        posts = []
        try:
            for username in self.instagram_accounts:
                try:
                    profile = instaloader.Profile.from_username(
                        self.instagram_client.context,
                        username
                    )
                    
                    # Get recent posts
                    for post in profile.get_posts():
                        try:
                            # Calculate engagement score
                            engagement = (
                                post.likes +
                                post.comments +
                                post.video_view_count
                            )
                            
                            # Only include posts with sufficient engagement
                            if engagement >= settings.MIN_ENGAGEMENT_SCORE:
                                posts.append({
                                    'title': post.caption[:100] + '...' if post.caption and len(post.caption) > 100 else (post.caption or 'No caption'),
                                    'content': post.caption or 'No caption',
                                    'source_url': f"https://www.instagram.com/p/{post.shortcode}/",
                                    'source_type': 'instagram',
                                    'author': username,
                                    'published_at': post.date,
                                    'engagement_count': engagement
                                })
                        except Exception as e:
                            logger.error(f"Error processing Instagram post: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing Instagram account {username}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Instagram scraping: {str(e)}")
            
        return posts
        
    async def scrape_all(self) -> List[Dict]:
        """Scrape content from all social media sources"""
        all_content = []
        
        # Scrape Twitter
        try:
            tweets = await self.scrape_twitter()
            all_content.extend(tweets)
            logger.info(f"Scraped {len(tweets)} tweets")
        except Exception as e:
            logger.error(f"Twitter scraping failed: {str(e)}")
        
        # Scrape Instagram
        try:
            posts = await self.scrape_instagram()
            all_content.extend(posts)
            logger.info(f"Scraped {len(posts)} Instagram posts")
        except Exception as e:
            logger.error(f"Instagram scraping failed: {str(e)}")
        
        return all_content 