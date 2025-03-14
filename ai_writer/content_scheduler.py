from typing import Dict, List, Optional
from datetime import datetime, time, timedelta
from .content_scorer import ContentScorer, ContentType, PublishType, TimeSlot
import heapq

class ContentItem:
    def __init__(self, 
                 content: Dict,
                 score: float,
                 publish_time: time,
                 publish_type: PublishType):
        self.content = content
        self.score = score
        self.publish_time = publish_time
        self.publish_type = publish_type
        self.created_at = datetime.now()
        
    def __lt__(self, other):
        # Priority queue ordering: higher score = higher priority
        if self.score == other.score:
            return self.created_at < other.created_at
        return self.score > other.score

class PublishQueue:
    def __init__(self):
        self.articles = []  # Priority queue for articles
        self.summaries = [] # Priority queue for website summaries
        self.social = []    # Priority queue for social media posts
        
    def add_content(self, item: ContentItem):
        """Add content to appropriate queue based on publish type."""
        if item.publish_type == PublishType.FULL_ARTICLE:
            heapq.heappush(self.articles, item)
        elif item.publish_type == PublishType.SUMMARY:
            heapq.heappush(self.summaries, item)
        elif item.publish_type == PublishType.SOCIAL:
            heapq.heappush(self.social, item)
            
    def get_next_article(self) -> Optional[ContentItem]:
        """Get highest priority article."""
        return heapq.heappop(self.articles) if self.articles else None
        
    def get_next_summary(self) -> Optional[ContentItem]:
        """Get highest priority summary."""
        return heapq.heappop(self.summaries) if self.summaries else None
        
    def get_next_social(self) -> Optional[ContentItem]:
        """Get highest priority social post."""
        return heapq.heappop(self.social) if self.social else None

class ContentScheduler:
    def __init__(self, max_daily_articles: int = 10, max_daily_social: int = 5):
        self.scorer = ContentScorer(max_daily_articles, max_daily_social)
        self.queue = PublishQueue()
        self.daily_stats = {
            "articles": 0,
            "summaries": 0,
            "social": 0,
            "date": datetime.now().date()
        }
        
    def reset_daily_stats(self):
        """Reset daily publishing statistics."""
        today = datetime.now().date()
        if self.daily_stats["date"] != today:
            self.daily_stats = {
                "articles": 0,
                "summaries": 0,
                "social": 0,
                "date": today
            }
            
    def can_publish_more(self, publish_type: PublishType) -> bool:
        """Check if we can publish more content of given type today."""
        self.reset_daily_stats()
        
        if publish_type == PublishType.FULL_ARTICLE:
            return self.daily_stats["articles"] < self.scorer.max_daily_articles
        elif publish_type == PublishType.SUMMARY:
            return self.daily_stats["summaries"] < self.scorer.max_daily_articles
        elif publish_type == PublishType.SOCIAL:
            return self.daily_stats["social"] < self.scorer.max_daily_social
        return False
        
    def schedule_content(self,
                        content: Dict,
                        content_type: ContentType,
                        engagement_count: int,
                        is_trending: bool,
                        has_engagement: bool) -> Dict:
        """
        Schedule content for publishing based on its evaluation.
        
        Args:
            content (Dict): The content to be published
            content_type (ContentType): Type of content
            engagement_count (int): Number of likes/shares
            is_trending (bool): Whether the topic is trending
            has_engagement (bool): Whether there's some engagement
            
        Returns:
            Dict: Scheduling result with recommendations
        """
        # Evaluate content
        evaluation = self.scorer.evaluate_content(
            content_type, engagement_count, is_trending, has_engagement
        )
        
        publish_type = PublishType(evaluation["publish_type"])
        
        # Check if we can publish more of this type today
        if not self.can_publish_more(publish_type):
            return {
                "scheduled": False,
                "reason": "Daily limit reached for this content type",
                "evaluation": evaluation
            }
            
        # Create content item
        publish_time = datetime.strptime(evaluation["publish_time"], "%H:%M").time()
        content_item = ContentItem(
            content=content,
            score=evaluation["score"],
            publish_time=publish_time,
            publish_type=publish_type
        )
        
        # Add to appropriate queue
        self.queue.add_content(content_item)
        
        # Update daily stats
        if publish_type == PublishType.FULL_ARTICLE:
            self.daily_stats["articles"] += 1
        elif publish_type == PublishType.SUMMARY:
            self.daily_stats["summaries"] += 1
        elif publish_type == PublishType.SOCIAL:
            self.daily_stats["social"] += 1
            
        return {
            "scheduled": True,
            "publish_time": publish_time.strftime("%H:%M"),
            "content_type": content_type.value,
            "publish_type": publish_type.value,
            "score": evaluation["score"],
            "priority": evaluation["recommendation"]["priority"]
        }
        
    def get_publishing_schedule(self) -> Dict[str, List[Dict]]:
        """Get the current publishing schedule for all content types."""
        schedule = {
            "articles": [],
            "summaries": [],
            "social": []
        }
        
        # Get all scheduled articles
        while True:
            article = self.queue.get_next_article()
            if not article:
                break
            schedule["articles"].append({
                "time": article.publish_time.strftime("%H:%M"),
                "score": article.score,
                "content": article.content
            })
            
        # Get all scheduled summaries
        while True:
            summary = self.queue.get_next_summary()
            if not summary:
                break
            schedule["summaries"].append({
                "time": summary.publish_time.strftime("%H:%M"),
                "score": summary.score,
                "content": summary.content
            })
            
        # Get all scheduled social posts
        while True:
            social = self.queue.get_next_social()
            if not social:
                break
            schedule["social"].append({
                "time": social.publish_time.strftime("%H:%M"),
                "score": social.score,
                "content": social.content
            })
            
        return schedule
        
    def get_daily_stats(self) -> Dict:
        """Get current daily publishing statistics."""
        self.reset_daily_stats()
        return {
            "date": self.daily_stats["date"].strftime("%Y-%m-%d"),
            "articles_published": self.daily_stats["articles"],
            "articles_remaining": self.scorer.max_daily_articles - self.daily_stats["articles"],
            "summaries_published": self.daily_stats["summaries"],
            "summaries_remaining": self.scorer.max_daily_articles - self.daily_stats["summaries"],
            "social_published": self.daily_stats["social"],
            "social_remaining": self.scorer.max_daily_social - self.daily_stats["social"]
        } 