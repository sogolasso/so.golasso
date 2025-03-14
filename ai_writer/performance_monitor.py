from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import json

class ContentMetrics:
    def __init__(self):
        self.views = 0
        self.unique_visitors = set()
        self.shares = 0
        self.comments = 0
        self.avg_time_spent = 0.0
        self.total_time_spent = 0.0
        self.bounce_rate = 0.0
        self.bounces = 0
        self.social_interactions = defaultdict(int)
        
    def update(self,
              user_id: str,
              time_spent: float = 0.0,
              bounced: bool = False,
              shared: bool = False,
              commented: bool = False,
              social_platform: Optional[str] = None):
        """Update metrics with new interaction data."""
        self.views += 1
        self.unique_visitors.add(user_id)
        
        if bounced:
            self.bounces += 1
        
        if shared:
            self.shares += 1
            
        if commented:
            self.comments += 1
            
        if social_platform:
            self.social_interactions[social_platform] += 1
            
        self.total_time_spent += time_spent
        self.avg_time_spent = self.total_time_spent / self.views
        self.bounce_rate = self.bounces / self.views if self.views > 0 else 0
        
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary format."""
        return {
            "views": self.views,
            "unique_visitors": len(self.unique_visitors),
            "shares": self.shares,
            "comments": self.comments,
            "avg_time_spent": round(self.avg_time_spent, 2),
            "total_time_spent": round(self.total_time_spent, 2),
            "bounce_rate": round(self.bounce_rate * 100, 2),
            "social_interactions": dict(self.social_interactions)
        }

class PerformanceMonitor:
    def __init__(self, retention_days: int = 30):
        self.retention_period = timedelta(days=retention_days)
        self.content_metrics = {}  # content_id -> ContentMetrics
        self.daily_metrics = defaultdict(lambda: defaultdict(int))  # date -> metric -> value
        self.hourly_metrics = defaultdict(lambda: defaultdict(int))  # hour -> metric -> value
        self.style_metrics = defaultdict(lambda: ContentMetrics())  # style -> ContentMetrics
        
    def track_interaction(self,
                         content_id: str,
                         user_id: str,
                         style: str,
                         metrics: Dict):
        """Track a content interaction."""
        # Initialize content metrics if needed
        if content_id not in self.content_metrics:
            self.content_metrics[content_id] = ContentMetrics()
            
        # Update content metrics
        self.content_metrics[content_id].update(
            user_id=user_id,
            time_spent=metrics.get("time_spent", 0.0),
            bounced=metrics.get("bounced", False),
            shared=metrics.get("shared", False),
            commented=metrics.get("commented", False),
            social_platform=metrics.get("social_platform")
        )
        
        # Update style metrics
        self.style_metrics[style].update(
            user_id=user_id,
            time_spent=metrics.get("time_spent", 0.0),
            bounced=metrics.get("bounced", False),
            shared=metrics.get("shared", False),
            commented=metrics.get("commented", False),
            social_platform=metrics.get("social_platform")
        )
        
        # Update daily metrics
        today = datetime.now().date().isoformat()
        self.daily_metrics[today]["views"] += 1
        self.daily_metrics[today]["shares"] += 1 if metrics.get("shared") else 0
        self.daily_metrics[today]["comments"] += 1 if metrics.get("commented") else 0
        
        # Update hourly metrics
        hour = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_metrics[hour]["views"] += 1
        self.hourly_metrics[hour]["shares"] += 1 if metrics.get("shared") else 0
        self.hourly_metrics[hour]["comments"] += 1 if metrics.get("commented") else 0
        
    def cleanup_old_data(self):
        """Remove data older than retention period."""
        cutoff_date = datetime.now() - self.retention_period
        
        # Clean daily metrics
        self.daily_metrics = {
            date: metrics
            for date, metrics in self.daily_metrics.items()
            if datetime.fromisoformat(date) > cutoff_date
        }
        
        # Clean hourly metrics
        self.hourly_metrics = {
            hour: metrics
            for hour, metrics in self.hourly_metrics.items()
            if datetime.strptime(hour, "%Y-%m-%d %H:00") > cutoff_date
        }
        
    def get_content_performance(self, content_id: str) -> Optional[Dict]:
        """Get performance metrics for specific content."""
        if content_id in self.content_metrics:
            return self.content_metrics[content_id].to_dict()
        return None
        
    def get_style_performance(self, style: str) -> Optional[Dict]:
        """Get performance metrics for a writing style."""
        if style in self.style_metrics:
            return self.style_metrics[style].to_dict()
        return None
        
    def get_daily_summary(self, days: int = 7) -> Dict:
        """Get daily performance summary."""
        self.cleanup_old_data()
        
        dates = sorted(self.daily_metrics.keys())[-days:]
        return {
            date: self.daily_metrics[date]
            for date in dates
        }
        
    def get_hourly_summary(self, hours: int = 24) -> Dict:
        """Get hourly performance summary."""
        self.cleanup_old_data()
        
        hours_list = sorted(self.hourly_metrics.keys())[-hours:]
        return {
            hour: self.hourly_metrics[hour]
            for hour in hours_list
        }
        
    def get_top_performing_content(self, metric: str = "views", limit: int = 10) -> List[Dict]:
        """Get top performing content based on specified metric."""
        content_list = []
        
        for content_id, metrics in self.content_metrics.items():
            metrics_dict = metrics.to_dict()
            if metric in metrics_dict:
                content_list.append({
                    "content_id": content_id,
                    "metric": metric,
                    "value": metrics_dict[metric]
                })
                
        # Sort by metric value
        content_list.sort(key=lambda x: x["value"], reverse=True)
        return content_list[:limit]
        
    def get_style_comparison(self) -> Dict:
        """Compare performance across different writing styles."""
        return {
            style: metrics.to_dict()
            for style, metrics in self.style_metrics.items()
        }
        
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data."""
        self.cleanup_old_data()
        
        return {
            "overview": {
                "total_views": sum(m["views"] for m in self.daily_metrics.values()),
                "total_shares": sum(m["shares"] for m in self.daily_metrics.values()),
                "total_comments": sum(m["comments"] for m in self.daily_metrics.values())
            },
            "daily_summary": self.get_daily_summary(),
            "hourly_summary": self.get_hourly_summary(),
            "top_content": {
                "by_views": self.get_top_performing_content("views"),
                "by_shares": self.get_top_performing_content("shares"),
                "by_comments": self.get_top_performing_content("comments")
            },
            "style_comparison": self.get_style_comparison()
        } 