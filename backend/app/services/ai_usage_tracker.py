from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class AIUsageTracker:
    def __init__(self, max_daily_articles: int = 10, max_monthly_cost: float = 100.0):
        self.max_daily_articles = max_daily_articles
        self.max_monthly_cost = max_monthly_cost
        self.usage_file = Path("data/ai_usage.json")
        self.cache_file = Path("data/ai_cache.json")
        self._ensure_data_files()
        
    def _ensure_data_files(self):
        """Ensure data directory and files exist"""
        self.usage_file.parent.mkdir(exist_ok=True)
        self.cache_file.parent.mkdir(exist_ok=True)
        
        if not self.usage_file.exists():
            self._save_usage({
                "daily_articles": {},
                "monthly_costs": {},
                "total_tokens": 0,
                "total_cost": 0.0
            })
            
        if not self.cache_file.exists():
            self._save_cache({})
    
    def _load_usage(self) -> Dict:
        """Load usage data from file"""
        try:
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")
            return {
                "daily_articles": {},
                "monthly_costs": {},
                "total_tokens": 0,
                "total_cost": 0.0
            }
    
    def _save_usage(self, data: Dict):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage data: {e}")
    
    def _load_cache(self) -> Dict:
        """Load cache data from file"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache data: {e}")
            return {}
    
    def _save_cache(self, data: Dict):
        """Save cache data to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache data: {e}")
    
    def can_generate_article(self) -> bool:
        """Check if we can generate more articles today"""
        usage = self._load_usage()
        today = datetime.now().strftime("%Y-%m-%d")
        daily_count = usage["daily_articles"].get(today, 0)
        
        if daily_count >= self.max_daily_articles:
            logger.warning(f"Daily article limit ({self.max_daily_articles}) reached")
            return False
        return True
    
    def check_monthly_cost_limit(self) -> bool:
        """Check if we're approaching the monthly cost limit"""
        usage = self._load_usage()
        current_month = datetime.now().strftime("%Y-%m")
        monthly_cost = usage["monthly_costs"].get(current_month, 0.0)
        
        if monthly_cost >= self.max_monthly_cost * 0.8:  # 80% threshold
            logger.warning(f"Monthly cost threshold reached: ${monthly_cost:.2f}")
            return False
        return True
    
    def get_cached_article(self, content_hash: str) -> Optional[Dict]:
        """Get cached article if it exists"""
        cache = self._load_cache()
        return cache.get(content_hash)
    
    def cache_article(self, content_hash: str, article_data: Dict):
        """Cache an article for future reuse"""
        cache = self._load_cache()
        cache[content_hash] = article_data
        self._save_cache(cache)
    
    def track_usage(self, tokens_used: int, cost: float):
        """Track API usage and costs"""
        usage = self._load_usage()
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")
        
        # Update daily articles count
        usage["daily_articles"][today] = usage["daily_articles"].get(today, 0) + 1
        
        # Update monthly costs
        usage["monthly_costs"][current_month] = usage["monthly_costs"].get(current_month, 0.0) + cost
        
        # Update totals
        usage["total_tokens"] += tokens_used
        usage["total_cost"] += cost
        
        # Clean up old data (keep last 90 days)
        cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        usage["daily_articles"] = {k: v for k, v in usage["daily_articles"].items() 
                                 if k >= cutoff}
        
        self._save_usage(usage)
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        usage = self._load_usage()
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")
        
        return {
            "daily_articles": usage["daily_articles"].get(today, 0),
            "monthly_cost": usage["monthly_costs"].get(current_month, 0.0),
            "total_tokens": usage["total_tokens"],
            "total_cost": usage["total_cost"]
        } 