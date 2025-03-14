from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
from collections import defaultdict

class StoryThread:
    def __init__(self, title: str, main_keywords: List[str]):
        self.title = title
        self.main_keywords = main_keywords
        self.articles = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.engagement_stats = {
            "views": 0,
            "shares": 0,
            "comments": 0
        }
        
    def add_article(self, article: Dict):
        """Add an article to the story thread."""
        self.articles.append({
            "content": article,
            "added_at": datetime.now()
        })
        self.last_updated = datetime.now()
        
    def update_engagement(self, views: int = 0, shares: int = 0, comments: int = 0):
        """Update engagement statistics for the thread."""
        self.engagement_stats["views"] += views
        self.engagement_stats["shares"] += shares
        self.engagement_stats["comments"] += comments
        
    def get_timeline(self) -> List[Dict]:
        """Get chronological timeline of the story."""
        timeline = [
            {
                "content": article["content"],
                "timestamp": article["added_at"].isoformat()
            }
            for article in sorted(self.articles, key=lambda x: x["added_at"])
        ]
        return timeline
        
    def to_dict(self) -> Dict:
        """Convert thread to dictionary format."""
        return {
            "title": self.title,
            "main_keywords": self.main_keywords,
            "article_count": len(self.articles),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "engagement_stats": self.engagement_stats,
            "timeline": self.get_timeline()
        }

class ContentClusterer:
    def __init__(self,
                 similarity_threshold: float = 0.3,
                 min_cluster_size: int = 2,
                 max_thread_age_days: int = 7):
        self.vectorizer = TfidfVectorizer(
            stop_words='portuguese',
            ngram_range=(1, 2)
        )
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size
        self.max_thread_age = timedelta(days=max_thread_age_days)
        self.story_threads = []
        
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract main keywords from text."""
        try:
            # Create TF-IDF matrix for single document
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top keywords
            dense = tfidf_matrix.todense()
            scores = list(zip(feature_names, dense[0].tolist()[0]))
            sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
            
            return [word for word, score in sorted_scores[:top_n]]
            
        except Exception as e:
            print(f"Error extracting keywords: {str(e)}")
            return []
            
    def _find_similar_thread(self, content: str, keywords: List[str]) -> Optional[StoryThread]:
        """Find an existing thread that matches the content."""
        # Remove old threads
        current_time = datetime.now()
        self.story_threads = [
            thread for thread in self.story_threads
            if current_time - thread.last_updated <= self.max_thread_age
        ]
        
        if not self.story_threads:
            return None
            
        # Create content vector
        all_texts = [content] + [
            thread.articles[-1]["content"]["corpo"]
            for thread in self.story_threads
        ]
        
        try:
            # Calculate similarities
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            similarities = (tfidf_matrix * tfidf_matrix.T).toarray()[0][1:]
            
            # Find most similar thread
            max_sim_idx = np.argmax(similarities)
            if similarities[max_sim_idx] >= self.similarity_threshold:
                return self.story_threads[max_sim_idx]
                
        except Exception as e:
            print(f"Error finding similar thread: {str(e)}")
            
        return None
        
    def process_content(self, content: Dict) -> Dict:
        """Process new content and assign to appropriate story thread."""
        main_text = content["corpo"]
        keywords = self._extract_keywords(main_text)
        
        # Try to find existing thread
        thread = self._find_similar_thread(main_text, keywords)
        
        if thread:
            # Add to existing thread
            thread.add_article(content)
            thread_info = {
                "thread_id": self.story_threads.index(thread),
                "is_new_thread": False,
                "thread_data": thread.to_dict()
            }
        else:
            # Create new thread
            new_thread = StoryThread(
                title=content["titulo"],
                main_keywords=keywords
            )
            new_thread.add_article(content)
            self.story_threads.append(new_thread)
            thread_info = {
                "thread_id": len(self.story_threads) - 1,
                "is_new_thread": True,
                "thread_data": new_thread.to_dict()
            }
            
        return thread_info
        
    def get_active_threads(self) -> List[Dict]:
        """Get all active story threads."""
        current_time = datetime.now()
        active_threads = []
        
        for idx, thread in enumerate(self.story_threads):
            if current_time - thread.last_updated <= self.max_thread_age:
                thread_data = thread.to_dict()
                thread_data["thread_id"] = idx
                active_threads.append(thread_data)
                
        return active_threads
        
    def get_thread_by_id(self, thread_id: int) -> Optional[Dict]:
        """Get specific thread by ID."""
        if 0 <= thread_id < len(self.story_threads):
            thread = self.story_threads[thread_id]
            thread_data = thread.to_dict()
            thread_data["thread_id"] = thread_id
            return thread_data
        return None
        
    def update_thread_engagement(self, thread_id: int, engagement_data: Dict):
        """Update engagement statistics for a thread."""
        if 0 <= thread_id < len(self.story_threads):
            thread = self.story_threads[thread_id]
            thread.update_engagement(
                views=engagement_data.get("views", 0),
                shares=engagement_data.get("shares", 0),
                comments=engagement_data.get("comments", 0)
            ) 