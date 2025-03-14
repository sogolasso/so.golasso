import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ClientError, ChallengeRequired
import time
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('instagram_test')

# Instagram accounts to monitor
ACCOUNTS = {
    'clubs': [
        'flamengo',
        'palmeiras',
        'saopaulofc',
        'corinthians',
        'gremio',
        'scinternacional',
        'fluminensefc',
        'botafogo',
        'vascodagama',
        'santosfc'
    ],
    'players': [
        'neymarjr',
        'dejesusoficial',
        'gabigol',
        'richarlison',
        'casemiro',
        'ronaldinho'
    ],
    'influencers': [
        'benjaminback'
    ]
}

def handle_verification(username, verification_type):
    """Handle verification code for Instagram login."""
    logger.info(f"Handling verification for {username} (type: {verification_type})")
    return "601505"  # Return the provided verification code

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

def authenticate_instagram():
    """
    Authenticates with Instagram with proper session management
    """
    try:
        # Create new client with custom settings
        client = Client()
        client.delay_range = [1, 3]
        client.request_timeout = 30
        
        # Set verification code handler
        client.challenge_code_handler = handle_verification
        
        # Get credentials
        username = os.environ.get('INSTAGRAM_USERNAME')
        password = os.environ.get('INSTAGRAM_PASSWORD')
        
        if not username or not password:
            logger.error("Instagram credentials not found in environment variables")
            return None
        
        logger.info(f"Attempting to login with username: {username}")
        
        # Set up basic settings
        client.set_settings({
            "uuids": {
                "phone_id": "57d64c41-a916-3fa5-bd7a-3796c1dab122",
                "uuid": "8aa373c6-f316-44d7-b49e-d74563f4a8f3",
                "client_session_id": "6c296d0a-3534-4dce-b5aa-a6a6ab017443",
                "advertising_id": "8dc88b76-dfbc-44dc-abbc-31a6f1d54b04",
                "device_id": "android-e021b636049dc0e9"
            },
            "device_settings": {
                "app_version": "269.0.0.18.75",
                "android_version": 26,
                "android_release": "8.0.0",
                "dpi": "480dpi",
                "resolution": "1080x1920",
                "manufacturer": "OnePlus",
                "device": "devitron",
                "model": "6T",
                "cpu": "qcom",
                "version_code": "314665256"
            },
            "user_agent": "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; 6T; devitron; qcom; en_US; 314665256)"
        })
        
        try:
            # Try to login
            client.login(username, password)
            
            # If login successful, save session
            try:
                with open('instagram_session.json', 'w') as f:
                    json.dump(client.get_settings(), f)
                logger.info("Successfully saved Instagram session")
            except Exception as e:
                logger.error(f"Error saving Instagram session: {str(e)}")
            
            logger.info("Successfully logged in to Instagram with credentials")
            return client
            
        except Exception as e:
            if "challenge_required" in str(e):
                logger.info("Challenge required, attempting to handle...")
                try:
                    # Get the last challenge URL from the client's state
                    challenge_url = client.last_json.get('challenge', {}).get('api_path')
                    if challenge_url:
                        # Send verification code
                        client.send_challenge_code(challenge_url)
                        # Submit the verification code
                        client.challenge_code("601505")
                        logger.info("Challenge completed successfully")
                        
                        # Save session after successful challenge
                        try:
                            with open('instagram_session.json', 'w') as f:
                                json.dump(client.get_settings(), f)
                            logger.info("Successfully saved Instagram session after challenge")
                        except Exception as save_err:
                            logger.error(f"Error saving Instagram session after challenge: {str(save_err)}")
                        
                        return client
                    else:
                        logger.error("No challenge URL found")
                        return None
                except Exception as ce:
                    logger.error(f"Challenge failed: {str(ce)}")
                    return None
            else:
                logger.error(f"Login failed: {str(e)}")
                return None
        
    except Exception as e:
        logger.error(f"Error in authentication process: {str(e)}")
        return None

def test_instagram_account(client: Client, username: str) -> Optional[Dict]:
    """Test fetching posts from a single Instagram account."""
    try:
        logger.info(f"Testing Instagram API for @{username}...")
        
        # Get user ID
        user_id = client.user_id_from_username(username)
        if not user_id:
            logger.error(f"Could not find user @{username}")
            return None
            
        logger.info(f"Found user @{username} (ID: {user_id})")
        
        # Get recent media
        medias = client.user_medias(user_id, amount=5)
        if not medias:
            logger.warning(f"No posts found for @{username}")
            return None
            
        # Process posts
        processed_posts = []
        for media in medias:
            processed_posts.append({
                'id': str(media.id),
                'caption': media.caption_text if media.caption_text else '',
                'timestamp': str(media.taken_at),
                'media_type': media.media_type,
                'like_count': media.like_count,
                'comment_count': media.comment_count,
                'url': media.thumbnail_url if media.media_type == 1 else media.video_url
            })
            
        account_data = {
            'username': username,
            'user_id': str(user_id),
            'posts': processed_posts
        }
        
        logger.info(f"Successfully fetched {len(processed_posts)} posts from @{username}")
        return account_data
        
    except Exception as e:
        logger.error(f"Error testing Instagram API for @{username}: {str(e)}")
        return None

def test_all_accounts():
    """Test fetching posts from all configured accounts."""
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Initialize client
        client = Client()
        client.challenge_code_handler = handle_verification
        client.delay_range = [1, 3]
        
        # Login
        username = "so.golasso"
        password = "XaaVii123456!"
        
        logger.info(f"Attempting to login with username: {username}")
        try:
            login_result = client.login(username, password)
            logger.info("Successfully logged in to Instagram!")
        except LoginRequired as e:
            logger.error(f"Login failed - credentials error: {str(e)}")
            return False
        except ChallengeRequired as e:
            logger.error(f"Login failed - challenge required: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Login failed - unexpected error: {str(e)}")
            return False
            
        results = {
            'clubs': {},
            'players': {},
            'influencers': {}
        }
        
        # Test club accounts
        for username in ACCOUNTS['clubs']:
            account_data = test_instagram_account(client, username)
            if account_data:
                results['clubs'][username] = account_data
                time.sleep(5)  # Add delay between requests
                
        # Test player accounts
        for username in ACCOUNTS['players']:
            account_data = test_instagram_account(client, username)
            if account_data:
                results['players'][username] = account_data
                time.sleep(5)  # Add delay between requests
                
        # Test influencer accounts
        for username in ACCOUNTS['influencers']:
            account_data = test_instagram_account(client, username)
            if account_data:
                results['influencers'][username] = account_data
                time.sleep(5)  # Add delay between requests
        
        if results['clubs'] or results['players'] or results['influencers']:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/instagram_test_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Test results saved to {output_file}")
            
            return True
        else:
            logger.error("No Instagram accounts were successfully tested")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Instagram accounts: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    test_all_accounts() 