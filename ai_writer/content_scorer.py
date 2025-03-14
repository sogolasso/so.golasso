from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, time
import math

class ContentType(Enum):
    MATCH_RESULT = "match_result"
    TRANSFER_NEWS = "transfer_news"
    TACTICAL_ANALYSIS = "tactical_analysis"
    TEAM_UPDATE = "team_update"
    RUMOR = "rumor"

class PublishType(Enum):
    FULL_ARTICLE = "full_article"  # Score 8-10
    SUMMARY = "summary"            # Score 6-7.9
    SOCIAL = "social"             # Score 4-5.9
    DISCARD = "discard"           # Score < 4

class TimeSlot(Enum):
    MORNING = "morning"     # 8AM - 12PM
    AFTERNOON = "afternoon" # 12PM - 6PM
    EVENING = "evening"     # 6PM - 12AM

class ContentScorer:
    def __init__(self, max_daily_articles: int = 10, max_daily_social: int = 5):
        self.max_daily_articles = max_daily_articles
        self.max_daily_social = max_daily_social
        
        # News importance base scores
        self.news_importance_scores = {
            ContentType.MATCH_RESULT: 10,        # Major match results
            ContentType.TRANSFER_NEWS: 8,        # Breaking transfer news
            ContentType.TACTICAL_ANALYSIS: 6,    # Tactical analysis & previews
            ContentType.TEAM_UPDATE: 4,          # General updates
            ContentType.RUMOR: 2                 # Minor rumors
        }
        
        # Engagement thresholds
        self.engagement_thresholds = {
            "high": {"score": 10, "min_engagement": 10000},
            "medium": {"score": 6, "min_engagement": 1000},
            "low": {"score": 2, "min_engagement": 0}
        }
        
        # Trend scores
        self.trend_scores = {
            "trending": 10,    # Top trending
            "engaging": 6,     # Some engagement
            "none": 2         # Not trending
        }

    def calculate_daily_volume(self, 
                             content_volume: int,
                             engagement_score: float,
                             trend_score: float,
                             time_sensitivity: int) -> int:
        """
        Calculate how many articles/posts to generate per day.
        
        Args:
            content_volume (int): Number of newsworthy pieces available
            engagement_score (float): Historical engagement score (0-10)
            trend_score (float): Current trending score (0-10)
            time_sensitivity (int): Urgency score (1-10)
            
        Returns:
            int: Recommended number of articles/posts for the day
        """
        score = (
            (content_volume * 0.4) +
            (engagement_score * 0.3) +
            (trend_score * 0.2) +
            (time_sensitivity * 0.1)
        ) / 10
        
        return min(math.ceil(score), self.max_daily_articles)

    def get_engagement_score(self, engagement_count: int) -> float:
        """Calculate engagement score based on likes/shares."""
        if engagement_count >= self.engagement_thresholds["high"]["min_engagement"]:
            return self.engagement_thresholds["high"]["score"]
        elif engagement_count >= self.engagement_thresholds["medium"]["min_engagement"]:
            return self.engagement_thresholds["medium"]["score"]
        return self.engagement_thresholds["low"]["score"]

    def get_trend_score(self, is_trending: bool, has_engagement: bool) -> float:
        """Calculate trend score based on social media presence."""
        if is_trending:
            return self.trend_scores["trending"]
        elif has_engagement:
            return self.trend_scores["engaging"]
        return self.trend_scores["none"]

    def calculate_content_score(self,
                              content_type: ContentType,
                              engagement_count: int,
                              is_trending: bool,
                              has_engagement: bool) -> float:
        """
        Calculate the final score for a piece of content.
        
        Args:
            content_type (ContentType): Type of content
            engagement_count (int): Number of likes/shares
            is_trending (bool): Whether the topic is trending
            has_engagement (bool): Whether there's some engagement
            
        Returns:
            float: Content score (0-10)
        """
        news_score = self.news_importance_scores[content_type]
        engagement_score = self.get_engagement_score(engagement_count)
        trend_score = self.get_trend_score(is_trending, has_engagement)
        
        final_score = (
            (news_score * 0.5) +
            (engagement_score * 0.3) +
            (trend_score * 0.2)
        )
        
        return round(final_score, 1)

    def determine_publish_type(self, score: float) -> PublishType:
        """Determine how content should be published based on score."""
        if score >= 8:
            return PublishType.FULL_ARTICLE
        elif score >= 6:
            return PublishType.SUMMARY
        elif score >= 4:
            return PublishType.SOCIAL
        return PublishType.DISCARD

    def get_optimal_time_slot(self, content_type: ContentType) -> TimeSlot:
        """Determine the optimal time slot for publishing."""
        time_slots = {
            ContentType.TACTICAL_ANALYSIS: TimeSlot.MORNING,
            ContentType.TRANSFER_NEWS: TimeSlot.MORNING,
            ContentType.TEAM_UPDATE: TimeSlot.AFTERNOON,
            ContentType.MATCH_RESULT: TimeSlot.EVENING,
            ContentType.RUMOR: TimeSlot.AFTERNOON
        }
        return time_slots.get(content_type, TimeSlot.AFTERNOON)

    def get_publish_time(self, time_slot: TimeSlot) -> time:
        """Get specific publish time within a time slot."""
        time_ranges = {
            TimeSlot.MORNING: (time(8, 0), time(12, 0)),
            TimeSlot.AFTERNOON: (time(12, 0), time(18, 0)),
            TimeSlot.EVENING: (time(18, 0), time(23, 59))
        }
        
        start, end = time_ranges[time_slot]
        # For simplicity, we'll use the middle of the time slot
        hours = (start.hour + end.hour) // 2
        return time(hours, 0)

    def evaluate_content(self,
                        content_type: ContentType,
                        engagement_count: int,
                        is_trending: bool,
                        has_engagement: bool) -> Dict:
        """
        Evaluate content and provide publishing recommendations.
        
        Args:
            content_type (ContentType): Type of content
            engagement_count (int): Number of likes/shares
            is_trending (bool): Whether the topic is trending
            has_engagement (bool): Whether there's some engagement
            
        Returns:
            Dict: Publishing recommendations
        """
        score = self.calculate_content_score(
            content_type, engagement_count, is_trending, has_engagement
        )
        
        publish_type = self.determine_publish_type(score)
        time_slot = self.get_optimal_time_slot(content_type)
        publish_time = self.get_publish_time(time_slot)
        
        return {
            "score": score,
            "publish_type": publish_type.value,
            "time_slot": time_slot.value,
            "publish_time": publish_time.strftime("%H:%M"),
            "recommendation": {
                "should_publish": publish_type != PublishType.DISCARD,
                "format": publish_type.value,
                "priority": "high" if score >= 8 else "medium" if score >= 6 else "low"
            }
        } 