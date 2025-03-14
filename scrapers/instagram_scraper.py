import os
import json
import time
from datetime import datetime, timedelta
import logging
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ClientError
from config import get_enabled_instagram_accounts
from database.firebase_handler import save_to_firebase

# Set up logging
logger = logging.getLogger(__name__)

# Global Instagram client
instagram_client = None

# Cache for Instagram posts
post_cache = {
    'data': {},
    'last_update': None,
    'cache_duration': timedelta(minutes=30)  # Cache posts for 30 minutes
}

def load_session():
    """
    Loads Instagram session from file
    """
    try:
        if os.path.exists('instagram_session.json'):
            with open('instagram_session.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading Instagram session: {str(e)}")
    return None

def save_session(session_data):
    """
    Saves Instagram session to file
    """
    try:
        with open('instagram_session.json', 'w') as f:
            json.dump(session_data, f)
    except Exception as e:
        logger.error(f"Error saving Instagram session: {str(e)}")

def authenticate_instagram():
    """
    Authenticates with Instagram with proper session management
    """
    global instagram_client
    
    try:
        # If client already exists and is logged in, return it
        if instagram_client and instagram_client.user_id:
            return instagram_client
        
        # Create new client
        instagram_client = Client()
        
        # Try to load existing session
        session = load_session()
        if session:
            try:
                instagram_client.load_settings(session)
                instagram_client.login_by_sessionid(session.get('sessionid'))
                logger.info("Successfully logged in to Instagram using saved session")
                return instagram_client
            except Exception as e:
                logger.warning(f"Failed to login with saved session: {str(e)}")
        
        # If session login failed, try username/password
        username = os.environ.get('INSTAGRAM_USERNAME')
        password = os.environ.get('INSTAGRAM_PASSWORD')
        
        if not username or not password:
            logger.error("Instagram credentials not found in environment variables")
            return None
        
        # Login with credentials
        instagram_client.login(username, password)
        
        # Save the session for future use
        save_session(instagram_client.get_settings())
        
        logger.info("Successfully logged in to Instagram with credentials")
        return instagram_client
        
    except TwoFactorRequired:
        logger.error("Two-factor authentication required for Instagram")
        return None
    except LoginRequired as e:
        logger.error(f"Instagram login required: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error authenticating with Instagram: {str(e)}")
        return None

def get_cached_posts(account):
    """
    Gets cached posts for an account if they exist and are not expired
    """
    now = datetime.now()
    
    if (post_cache['last_update'] and 
        account in post_cache['data'] and 
        now - post_cache['last_update'] < post_cache['cache_duration']):
        return post_cache['data'][account]
    
    return None

def cache_posts(account, posts):
    """
    Caches posts for an account
    """
    post_cache['data'][account] = posts
    post_cache['last_update'] = datetime.now()

def retry_with_backoff(func, max_retries=3):
    """
    Retries a function with exponential backoff
    """
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except ClientError as e:
            if 'Please wait a few minutes' in str(e):
                wait_time = 300  # 5 minutes for rate limits
                logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            elif retries < max_retries - 1:
                wait_time = (2 ** retries) * 10  # 10s, 20s, 40s
                logger.warning(f"Request failed (attempt {retries + 1}/{max_retries}): {str(e)}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
                continue
            raise
        except Exception as e:
            if retries < max_retries - 1:
                wait_time = (2 ** retries) * 10
                logger.warning(f"Request failed (attempt {retries + 1}/{max_retries}): {str(e)}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
                continue
            raise
    return None

def fetch_instagram_posts():
    """
    Fetches posts from specified Brazilian football Instagram accounts with proper error handling
    """
    logger.info("Starting Instagram scraping process...")
    posts_data = []
    
    # Authenticate with Instagram
    client = authenticate_instagram()
    
    if not client:
        logger.error("Failed to authenticate with Instagram")
        return posts_data
    
    # Get enabled Instagram accounts from configuration
    accounts = get_enabled_instagram_accounts()
    
    if not accounts:
        logger.warning("No Instagram accounts enabled in configuration")
        return posts_data
    
    for i, account in enumerate(accounts):
        try:
            logger.info(f"Fetching posts from {account}...")
            
            # Check cache first
            cached_posts = get_cached_posts(account)
            if cached_posts:
                logger.info(f"Using cached posts for {account}")
                posts_data.extend(cached_posts)
                continue
            
            # Get user info with retry
            user_id = retry_with_backoff(
                lambda: client.user_id_from_username(account)
            )
            
            if not user_id:
                logger.warning(f"Could not find user {account}")
                continue
            
            # Add progressive delay between requests
            delay = 5 + (i * 2)  # Progressive delay starting at 5 seconds
            logger.info(f"Adding {delay}s delay between requests")
            time.sleep(delay)
            
            # Get recent media with retry
            medias = retry_with_backoff(
                lambda: client.user_medias(user_id, 5)  # Fetch last 5 posts
            )
            
            if not medias:
                logger.warning(f"No posts found for {account}")
                continue
            
            # Process posts
            account_posts = []
            for media in medias:
                try:
                    post_data = {
                        'id': str(media.id),
                        'caption': media.caption_text if media.caption_text else '',
                        'type': media.media_type,
                        'url': media.thumbnail_url if media.media_type == 1 else media.video_url,
                        'created_at': media.taken_at.isoformat(),
                        'account': account,
                        'likes_count': media.like_count,
                        'comments_count': media.comment_count,
                        'scraped_at': datetime.now().isoformat()
                    }
                    account_posts.append(post_data)
                except Exception as e:
                    logger.error(f"Error processing post {media.id} from {account}: {str(e)}")
                    continue
            
            # Cache the posts
            cache_posts(account, account_posts)
            
            # Add to main list
            posts_data.extend(account_posts)
            
            logger.info(f"Successfully fetched posts from {account}")
            
            # Save data in batches
            if len(posts_data) >= 50:
                try:
                    save_to_firebase('instagram_posts', posts_data)
                    posts_data = []
                except Exception as e:
                    logger.error(f"Error saving to Firebase: {str(e)}")
                    # Keep the data in memory to try saving again later
            
        except Exception as e:
            logger.error(f"Error processing account {account}: {str(e)}")
            # Save what we've collected so far
            if posts_data:
                try:
                    save_to_firebase('instagram_posts', posts_data)
                except Exception as save_error:
                    logger.error(f"Error saving to Firebase: {str(save_error)}")
                    # Write to local file as backup
                    backup_file = f"data/instagram_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(backup_file, 'w') as f:
                        json.dump(posts_data, f)
                    logger.info(f"Saved backup to {backup_file}")
            continue
    
    # Save any remaining posts
    if posts_data:
        try:
            save_to_firebase('instagram_posts', posts_data)
        except Exception as e:
            logger.error(f"Error saving final batch to Firebase: {str(e)}")
            # Write to local file as backup
            backup_file = f"data/instagram_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(posts_data, f)
            logger.info(f"Saved backup to {backup_file}")
    
    return posts_data

def save_instagram_data(posts_data):
    """
    Saves the Instagram posts data to JSON files and Firebase
    """
    if not posts_data:
        logger.warning("No Instagram posts to save")
        return
    
    # Make sure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save to a timestamped JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'data/instagram_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=4)
    
    # Save to the latest Instagram posts file
    with open('data/instagram_latest.json', 'w', encoding='utf-8') as f:
        json.dump(posts_data[:10], f, ensure_ascii=False, indent=4)
    
    # Update stats
    update_stats(len(posts_data))
    
    # Save to Firebase
    try:
        save_to_firebase('instagram', posts_data)
        logger.info(f"Successfully saved {len(posts_data)} Instagram posts to Firebase")
    except Exception as e:
        logger.error(f"Error saving to Firebase: {str(e)}")
    
    logger.info(f"Successfully saved {len(posts_data)} Instagram posts to {filename}")

def update_stats(count):
    """
    Updates the stats file with the latest Instagram scraping statistics
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
    
    # Update Instagram stats
    stats["instagram"]["total"] += count
    stats["instagram"]["last_updated"] = datetime.now().isoformat()
    
    # Save updated stats
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)

if __name__ == "__main__":
    # Test the Instagram scraper
    fetch_instagram_posts()
