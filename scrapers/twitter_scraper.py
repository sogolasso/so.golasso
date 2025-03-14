import os
import json
import logging
import tweepy
import time
from datetime import datetime, timedelta
from database.firebase_handler import save_to_firebase
from config import get_enabled_twitter_accounts

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='data/scraper.log',
                    filemode='a')
logger = logging.getLogger('twitter_scraper')

# Twitter accounts to scrape
FOOTBALL_CLUBS = [
    'Flamengo', 'Palmeiras', 'SaoPauloFC', 'Corinthians'
]

FOOTBALL_INFLUENCERS = [
    'jorgenicola', 'maurocezar', 'benjaminback'
]

# Rate limit tracking
rate_limits = {
    'reset_time': None,
    'remaining_calls': None,
    'last_check': None,
    'backoff_time': 5  # Start with 5 seconds backoff
}

# Cache for Twitter responses
tweet_cache = {
    'data': {},
    'last_update': None,
    'cache_duration': timedelta(minutes=15)  # Cache tweets for 15 minutes
}

def authenticate_twitter():
    """
    Authenticates with Twitter API using environment variables
    """
    try:
        # Get Twitter API credentials from environment variables
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        
        if not bearer_token:
            logger.error("Missing Twitter bearer token")
            return None
        
        # Create Twitter API client with only bearer token
        client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True  # Let tweepy handle rate limiting
        )
        
        return client
        
    except Exception as e:
        logger.error(f"Error authenticating with Twitter API: {str(e)}")
        return None

def handle_rate_limit(e):
    """
    Handles rate limit errors with exponential backoff
    """
    global rate_limits
    
    # Get reset time from headers if available
    if hasattr(e.response, 'headers') and 'x-rate-limit-reset' in e.response.headers:
        reset_time = int(e.response.headers['x-rate-limit-reset'])
        rate_limits['reset_time'] = datetime.fromtimestamp(reset_time)
    else:
        # Use exponential backoff if no reset time available
        rate_limits['backoff_time'] = min(rate_limits['backoff_time'] * 2, 900)  # Max 15 minutes
        rate_limits['reset_time'] = datetime.now() + timedelta(seconds=rate_limits['backoff_time'])
    
    rate_limits['remaining_calls'] = 0
    wait_time = (rate_limits['reset_time'] - datetime.now()).total_seconds()
    
    logger.info(f"Rate limit exceeded. Waiting {wait_time:.1f} seconds (backoff: {rate_limits['backoff_time']}s)")
    time.sleep(max(1, wait_time))
    return True  # Indicate that we handled the rate limit

def retry_with_backoff(func, max_retries=3):
    """
    Retries a function with exponential backoff
    """
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except tweepy.TooManyRequests as e:
            if handle_rate_limit(e):
                continue  # Try again after handling rate limit
            raise  # Re-raise if we couldn't handle it
        except (tweepy.HTTPException, tweepy.Unauthorized) as e:
            wait_time = (2 ** retries) * 5  # Exponential backoff: 5s, 10s, 20s
            logger.warning(f"Request failed (attempt {retries + 1}/{max_retries}): {str(e)}. Waiting {wait_time}s...")
            time.sleep(wait_time)
            retries += 1
    return None

def check_rate_limits():
    """
    Checks if we should wait for rate limits to reset
    Returns True if we should wait, False otherwise
    """
    now = datetime.now()
    
    # If we have rate limit info and haven't reached the reset time
    if (rate_limits['reset_time'] and 
        rate_limits['remaining_calls'] is not None and 
        now < rate_limits['reset_time']):
        
        # If we're out of calls, wait until reset
        if rate_limits['remaining_calls'] <= 0:
            wait_time = (rate_limits['reset_time'] - now).total_seconds() + 5
            logger.info(f"Rate limit will reset in {wait_time:.1f} seconds. Waiting...")
            time.sleep(wait_time)
            rate_limits['reset_time'] = None
            rate_limits['remaining_calls'] = None
            return True
            
        # If we're running low on calls, add some delay
        elif rate_limits['remaining_calls'] < 10:
            delay = 5 + (10 - rate_limits['remaining_calls'])  # Increase delay as remaining calls decrease
            logger.info(f"Running low on API calls ({rate_limits['remaining_calls']} remaining). Adding {delay}s delay.")
            time.sleep(delay)
            
    return False

def update_rate_limits(response):
    """
    Updates rate limit tracking based on Twitter API response
    """
    if hasattr(response, 'rate_limit'):
        rate_limits['remaining_calls'] = response.rate_limit.remaining
        rate_limits['reset_time'] = datetime.fromtimestamp(response.rate_limit.reset)
        rate_limits['last_check'] = datetime.now()
        logger.debug(f"Rate limits updated: {rate_limits['remaining_calls']} calls remaining, resets at {rate_limits['reset_time']}")

def get_cached_tweets(account):
    """
    Gets cached tweets for an account if they exist and are not expired
    """
    now = datetime.now()
    
    if (tweet_cache['last_update'] and 
        account in tweet_cache['data'] and 
        now - tweet_cache['last_update'] < tweet_cache['cache_duration']):
        return tweet_cache['data'][account]
    
    return None

def cache_tweets(account, tweets):
    """
    Caches tweets for an account
    """
    tweet_cache['data'][account] = tweets
    tweet_cache['last_update'] = datetime.now()

def fetch_tweets():
    """
    Fetches tweets from specified Brazilian football accounts with improved rate limit handling
    """
    logger.info("Starting Twitter scraping process...")
    tweets_data = []
    
    # Authenticate with Twitter API
    client = authenticate_twitter()
    
    if not client:
        logger.error("Failed to authenticate with Twitter API")
        return tweets_data
    
    # Get enabled Twitter accounts from configuration
    accounts = get_enabled_twitter_accounts()
    
    if not accounts:
        logger.warning("No Twitter accounts enabled in configuration")
        return tweets_data
        
    for i, account in enumerate(accounts):
        try:
            logger.info(f"Fetching tweets from {account}...")
            
            # Check cache first
            cached_tweets = get_cached_tweets(account)
            if cached_tweets:
                logger.info(f"Using cached tweets for {account}")
                tweets_data.extend(cached_tweets)
                continue
            
            # Check rate limits before making request
            check_rate_limits()
            
            # Add delay between requests
            delay = 10 + (i * 2)  # Progressive delay starting at 10 seconds
            logger.info(f"Adding {delay}s delay between requests")
            time.sleep(delay)
            
            # Fetch user info with retry
            user_response = retry_with_backoff(
                lambda: client.get_user(username=account)
            )
            
            if not user_response or not user_response.data:
                logger.warning(f"Could not find user {account}")
                continue
                
            user_id = user_response.data.id
            
            # Update rate limits
            update_rate_limits(user_response)
            
            # Check rate limits again before fetching tweets
            check_rate_limits()
            
            # Add delay before fetching tweets
            time.sleep(5)
            
            # Fetch recent tweets with retry
            tweets = retry_with_backoff(
                lambda: client.get_users_tweets(
                    user_id,
                    max_results=10,
                    tweet_fields=['created_at', 'public_metrics', 'text'],
                    exclude=['retweets', 'replies']
                )
            )
            
            # Update rate limits
            if tweets:
                update_rate_limits(tweets)
            
            if not tweets or not tweets.data:
                logger.warning(f"No tweets found for {account}")
                continue
            
            # Process tweets
            account_tweets = []
            for tweet in tweets.data:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'account': account,
                    'metrics': tweet.public_metrics,
                    'scraped_at': datetime.now().isoformat()
                }
                account_tweets.append(tweet_data)
            
            # Cache the tweets
            cache_tweets(account, account_tweets)
            
            # Add to main list
            tweets_data.extend(account_tweets)
            
            logger.info(f"Successfully fetched tweets from {account}")
            
            # Save data in batches to avoid losing everything if an error occurs
            if len(tweets_data) >= 50:
                try:
                    save_to_firebase('tweets', tweets_data)
                    tweets_data = []
                except Exception as e:
                    logger.error(f"Error saving to Firebase: {str(e)}")
                    # Keep the data in memory to try saving again later
            
        except Exception as e:
            logger.error(f"Error processing account {account}: {str(e)}")
            # Save what we've collected so far
            if tweets_data:
                try:
                    save_to_firebase('tweets', tweets_data)
                except Exception as save_error:
                    logger.error(f"Error saving to Firebase: {str(save_error)}")
                    # Write to local file as backup
                    backup_file = f"data/twitter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(backup_file, 'w') as f:
                        json.dump(tweets_data, f)
                    logger.info(f"Saved backup to {backup_file}")
            continue
    
    # Save any remaining tweets
    if tweets_data:
        try:
            save_to_firebase('tweets', tweets_data)
        except Exception as e:
            logger.error(f"Error saving final batch to Firebase: {str(e)}")
            # Write to local file as backup
            backup_file = f"data/twitter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(tweets_data, f)
            logger.info(f"Saved backup to {backup_file}")
    
    return tweets_data

def save_tweets_data(tweets_data):
    """
    Saves the tweets data to JSON files and Firebase
    
    If this is a partial save during rate limiting, we'll merge with existing data
    to avoid losing tweets we've already collected
    """
    if not tweets_data:
        logger.warning("No tweets to save")
        return
    
    # Make sure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Try to load existing latest data to merge with new data (for rate-limited runs)
    existing_tweets = []
    try:
        with open('data/twitter_latest.json', 'r', encoding='utf-8') as f:
            existing_tweets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
        
    # Merge tweets and remove duplicates (based on tweet ID)
    merged_tweets = tweets_data.copy()
    existing_ids = {tweet['id'] for tweet in tweets_data}
    
    for tweet in existing_tweets:
        if tweet['id'] not in existing_ids:
            merged_tweets.append(tweet)
            existing_ids.add(tweet['id'])
    
    # Save to a timestamped JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'data/twitter_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_tweets, f, ensure_ascii=False, indent=4)
    
    # Save to the latest tweets file
    with open('data/twitter_latest.json', 'w', encoding='utf-8') as f:
        # Sort by created_at before saving to ensure latest tweets are first
        sorted_tweets = sorted(
            merged_tweets, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        json.dump(sorted_tweets[:20], f, ensure_ascii=False, indent=4)
    
    # Update stats (only count new tweets to avoid inflating numbers)
    update_stats(len(tweets_data))
    
    # Save to Firebase (only the new tweets)
    try:
        save_to_firebase('twitter', tweets_data)
        logger.info(f"Successfully saved {len(tweets_data)} tweets to Firebase")
    except Exception as e:
        logger.error(f"Error saving to Firebase: {str(e)}")
    
    logger.info(f"Successfully saved {len(tweets_data)} tweets to {filename} (Total with merged: {len(merged_tweets)})")

def update_stats(count):
    """
    Updates the stats file with the latest Twitter scraping statistics
    """
    stats_file = 'data/stats.json'
    
    try:
        # Read existing stats
        with open(stats_file, 'r') as f:
            stats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize stats if file doesn't exist or is invalid
        stats = {
            "news": {"total": 0, "last_updated": "Never"},
            "twitter": {"total": 0, "last_updated": "Never"},
            "instagram": {"total": 0, "last_updated": "Never"}
        }
    
    # Update twitter stats
    stats["twitter"]["total"] += count
    stats["twitter"]["last_updated"] = datetime.now().isoformat()
    
    # Save updated stats
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)

if __name__ == "__main__":
    # Test the Twitter scraper
    fetch_tweets()
