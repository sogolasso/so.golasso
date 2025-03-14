from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

class TrendAnalyzer:
    def __init__(self, google_trends_api_key: Optional[str] = None):
        self.google_trends_api_key = google_trends_api_key
        self.vectorizer = TfidfVectorizer(
            stop_words='portuguese',
            ngram_range=(1, 2)
        )
        self.trend_history = []
        self.trend_cache = {}
        self.cache_expiry = timedelta(hours=1)
        
    def analyze_social_trends(self, 
                            tweets: List[str],
                            instagram_posts: List[str],
                            timeframe_hours: int = 24) -> Dict:
        """Analyze social media trends based on recent content."""
        # Combine all social content
        all_content = tweets + instagram_posts
        
        if not all_content:
            return {
                "trending_topics": [],
                "trending_score": 0,
                "engagement_rate": 0,
                "velocity": 0
            }
            
        # Extract hashtags and mentions
        hashtags = []
        mentions = []
        for content in all_content:
            hashtags.extend(re.findall(r'#(\w+)', content.lower()))
            mentions.extend(re.findall(r'@(\w+)', content.lower()))
            
        # Count frequencies
        hashtag_freq = Counter(hashtags)
        mention_freq = Counter(mentions)
        
        # Calculate trending topics
        trending_topics = [
            {"topic": tag, "frequency": freq}
            for tag, freq in hashtag_freq.most_common(5)
        ]
        
        # Calculate engagement metrics
        total_interactions = sum(hashtag_freq.values()) + sum(mention_freq.values())
        engagement_rate = total_interactions / len(all_content) if all_content else 0
        
        # Calculate velocity (rate of increase)
        current_velocity = self._calculate_trend_velocity(hashtag_freq)
        
        return {
            "trending_topics": trending_topics,
            "trending_score": min(10, engagement_rate * 2),  # Scale 0-10
            "engagement_rate": engagement_rate,
            "velocity": current_velocity
        }
        
    def _calculate_trend_velocity(self, current_freq: Counter) -> float:
        """Calculate how quickly trends are growing."""
        if not self.trend_history:
            self.trend_history.append((datetime.now(), current_freq))
            return 0.0
            
        # Remove old history (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.trend_history = [(t, f) for t, f in self.trend_history if t > cutoff_time]
        
        # Add current frequencies
        self.trend_history.append((datetime.now(), current_freq))
        
        if len(self.trend_history) < 2:
            return 0.0
            
        # Calculate velocity
        old_time, old_freq = self.trend_history[0]
        new_time, new_freq = self.trend_history[-1]
        
        time_diff = (new_time - old_time).total_seconds() / 3600  # Convert to hours
        
        # Compare frequencies
        velocity_sum = 0
        for topic in set(new_freq.keys()) | set(old_freq.keys()):
            old_count = old_freq.get(topic, 0)
            new_count = new_freq.get(topic, 0)
            if time_diff > 0:
                velocity_sum += (new_count - old_count) / time_diff
                
        return min(10, max(0, velocity_sum / 10))  # Scale 0-10
        
    def check_google_trends(self, query: str) -> Dict:
        """Check if topic is trending on Google Trends."""
        cache_key = f"google_trends_{query}"
        
        # Check cache
        if cache_key in self.trend_cache:
            cached_time, cached_data = self.trend_cache[cache_key]
            if datetime.now() - cached_time < self.cache_expiry:
                return cached_data
                
        if not self.google_trends_api_key:
            return {"trending": False, "score": 0}
            
        try:
            # Use Google Trends API (you'll need to implement the actual API call)
            # This is a placeholder for the actual implementation
            response = {
                "trending": False,
                "score": 0
            }
            
            # Cache the result
            self.trend_cache[cache_key] = (datetime.now(), response)
            return response
            
        except Exception as e:
            print(f"Error checking Google Trends: {str(e)}")
            return {"trending": False, "score": 0}
            
    def find_related_content(self, 
                           main_content: str,
                           content_pool: List[str],
                           threshold: float = 0.3) -> List[Dict]:
        """Find related content using TF-IDF and cosine similarity."""
        if not content_pool:
            return []
            
        # Add main content to the pool
        all_content = [main_content] + content_pool
        
        try:
            # Create TF-IDF matrix
            tfidf_matrix = self.vectorizer.fit_transform(all_content)
            
            # Calculate similarity between main content and others
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            # Get related content above threshold
            related = []
            for idx, similarity in enumerate(similarities[0]):
                if similarity >= threshold:
                    related.append({
                        "content": content_pool[idx],
                        "similarity": float(similarity)
                    })
                    
            # Sort by similarity
            related.sort(key=lambda x: x["similarity"], reverse=True)
            return related
            
        except Exception as e:
            print(f"Error finding related content: {str(e)}")
            return []
            
    def get_trending_score(self,
                          content: str,
                          social_data: Dict,
                          google_trends_data: Dict) -> float:
        """Calculate overall trending score combining multiple sources."""
        # Weights for different factors
        weights = {
            "social_trending": 0.4,
            "social_velocity": 0.3,
            "google_trends": 0.3
        }
        
        # Calculate weighted score
        score = (
            social_data["trending_score"] * weights["social_trending"] +
            social_data["velocity"] * weights["social_velocity"] +
            google_trends_data["score"] * weights["google_trends"]
        )
        
        return min(10, max(0, score))  # Ensure score is between 0-10 