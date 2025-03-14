"""
Configuration settings for the Brazilian football scraper
"""

import os
import json

# Default configuration for sources
DEFAULT_CONFIG = {
    "news_sources": {
        "globo_esporte": True,
        "espn_brasil": True,
        "lance": True,
        "uol_esporte": True,
        "terra_esportes": True,
        "goal_brasil": True,
        "trivela": True,
        "footstats": True
    },
    "twitter_accounts": {
        # Club accounts
        "Flamengo": True,
        "Palmeiras": True,
        "SaoPauloFC": True,
        "Corinthians": True,
        "Gremio": True,
        "SCInternacional": True,
        "FluminenseFC": True,
        "Botafogo": True,
        "VascodaGama": True,
        "SantosFC": True,
        # Journalists and influencers
        "maurocezar": True,
        "jorgenicola": True,
        "benjaminback": True,
        "andrizek": True,
        "PVC": True,
        "RicaPerrone": True,
        "ArnaldoJRibeiro": True,
        "etironi": True,
        # General accounts
        "CBF_Futebol": True,
        "Brasileirao": True
    },
    "instagram_accounts": {
        # Club accounts
        "flamengo": True,
        "palmeiras": True,
        "saopaulofc": True,
        "corinthians": True,
        "gremio": True,
        "scinternacional": True,
        "fluminensefc": True,
        "botafogo": True,
        "vascodagama": True,
        "santosfc": True,
        # Players and influencers
        "neymarjr": True,
        "dejesusoficial": True,
        "gabigol": True,
        "richarlison": True,
        "casemiro": True,
        "ronaldinho": True,
        "benjaminback": True,
        # Additional accounts from original config
        "vinijr": True,
        "marcelotwelve": True,
        "alisson": True
    },
    "scraper_settings": {
        "news_interval_hours": 3,
        "twitter_interval_hours": 2,
        "instagram_interval_hours": 6,
        "max_posts_per_source": 5
    }
}

def get_config():
    """
    Gets the current configuration from the config file or returns the default
    configuration if the file doesn't exist
    """
    config_file = 'data/config.json'
    
    try:
        # Read the configuration file
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Check if there are new sources in DEFAULT_CONFIG that need to be added
        config_updated = False
        
        for source_type in ["news_sources", "twitter_accounts", "instagram_accounts"]:
            for source in DEFAULT_CONFIG[source_type]:
                if source not in config[source_type]:
                    config[source_type][source] = True  # Enable new sources by default
                    config_updated = True
        
        # Save the updated configuration if needed
        if config_updated:
            save_config(config)
            
        return config
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is invalid, save and return the default configuration
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """
    Saves the configuration to the config file
    """
    # Make sure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save the configuration
    with open('data/config.json', 'w') as f:
        json.dump(config, f, indent=4)

def get_enabled_news_sources():
    """
    Gets the enabled news sources
    """
    config = get_config()
    return [source for source, enabled in config["news_sources"].items() if enabled]

def get_enabled_twitter_accounts():
    """
    Gets the enabled Twitter accounts
    """
    config = get_config()
    return [account for account, enabled in config["twitter_accounts"].items() if enabled]

def get_enabled_instagram_accounts():
    """
    Gets the enabled Instagram accounts
    """
    config = get_config()
    return [account for account, enabled in config["instagram_accounts"].items() if enabled]

def update_source_settings(source_type, settings):
    """
    Updates the settings for a specific source type
    """
    config = get_config()
    
    if source_type in ["news_sources", "twitter_accounts", "instagram_accounts"]:
        # Check current configuration and add any missing sources with default value False
        for source in DEFAULT_CONFIG[source_type]:
            if source not in config[source_type]:
                config[source_type][source] = False
        
        # Update settings from the request
        for source, enabled in settings.items():
            if source in DEFAULT_CONFIG[source_type]:
                config[source_type][source] = enabled
        
        # Save the updated configuration
        save_config(config)
        return True
    else:
        return False

def update_scraper_settings(settings):
    """
    Updates the scraper settings
    """
    config = get_config()
    
    # Update the settings
    for setting, value in settings.items():
        if setting in config["scraper_settings"]:
            config["scraper_settings"][setting] = value
    
    # Save the updated configuration
    save_config(config)
    return True

# Initialize the config file if it doesn't exist
get_config()