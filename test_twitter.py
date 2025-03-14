import os
import json
import logging
from datetime import datetime
import tweepy
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('twitter_test')

# Twitter accounts to monitor
ACCOUNTS = {
    'clubs': [
        'Flamengo',
        'Palmeiras',
        'SaoPauloFC',
        'Corinthians',
        'Gremio',
        'SCInternacional',
        'FluminenseFC',
        'Botafogo',
        'VascodaGama',
        'SantosFC'
    ],
    'journalists': [
        'maurocezar',
        'jorgenicola',
        'benjaminback',
        'andrizek',
        'PVC',
        'RicaPerrone',
        'ArnaldoJRibeiro',
        'etironi'
    ]
}

# Hashtags to track
HASHTAGS = [
    'Brasileirão',
    'Flamengo',
    'Palmeiras',
    'Libertadores'
]

def authenticate_twitter():
    """Authenticate with Twitter API."""
    try:
        auth = tweepy.OAuthHandler(
            os.environ.get('TWITTER_API_KEY'),
            os.environ.get('TWITTER_API_SECRET')
        )
        auth.set_access_token(
            os.environ.get('TWITTER_ACCESS_TOKEN'),
            os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        client = tweepy.Client(
            bearer_token=os.environ.get('TWITTER_BEARER_TOKEN'),
            consumer_key=os.environ.get('TWITTER_API_KEY'),
            consumer_secret=os.environ.get('TWITTER_API_SECRET'),
            access_token=os.environ.get('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        return client
        
    except Exception as e:
        logger.error(f"Error authenticating with Twitter: {str(e)}")
        return None

def test_twitter_api(client: tweepy.Client, username: str) -> Optional[Dict]:
    """Test fetching tweets from a single account."""
    try:
        logger.info(f"Testing Twitter API for @{username}...")
        
        # Get user ID
        user = client.get_user(username=username)
        if not user or not user.data:
            logger.error(f"Could not find user @{username}")
            return None
            
        user_id = user.data.id
        logger.info(f"Found user @{username} (ID: {user_id})")
        
        # Get recent tweets
        tweets = client.get_users_tweets(
            user_id,
            max_results=5,
            tweet_fields=['created_at', 'public_metrics']
        )
        
        if not tweets or not tweets.data:
            logger.warning(f"No tweets found for @{username}")
            return None
            
        # Process tweets
        processed_tweets = []
        for tweet in tweets.data:
            processed_tweets.append({
                'id': str(tweet.id),
                'text': tweet.text,
                'created_at': str(tweet.created_at),
                'metrics': tweet.public_metrics
            })
            
        account_data = {
            'username': username,
            'user_id': str(user_id),
            'tweets': processed_tweets
        }
        
        logger.info(f"Successfully fetched {len(processed_tweets)} tweets from @{username}")
        return account_data
        
    except Exception as e:
        logger.error(f"Error testing Twitter API for @{username}: {str(e)}")
        return None

def test_all_accounts():
    """Test fetching tweets from all configured accounts."""
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Authenticate
        client = authenticate_twitter()
        if not client:
            logger.error("Failed to authenticate with Twitter")
            return False
            
        results = {
            'clubs': {},
            'journalists': {}
        }
        
        # Test club accounts
        for username in ACCOUNTS['clubs']:
            account_data = test_twitter_api(client, username)
            if account_data:
                results['clubs'][username] = account_data
                
        # Test journalist accounts
        for username in ACCOUNTS['journalists']:
            account_data = test_twitter_api(client, username)
            if account_data:
                results['journalists'][username] = account_data
        
        if results['clubs'] or results['journalists']:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/twitter_test_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Test results saved to {output_file}")
            
            return True
        else:
            logger.error("No Twitter accounts were successfully tested")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Twitter accounts: {str(e)}")
        return False

if __name__ == "__main__":
    test_all_accounts() 