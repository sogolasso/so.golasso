from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import json
from collections import defaultdict
import random

class ABTest:
    def __init__(self, name: str, variants: List[str], min_samples: int = 100):
        self.name = name
        self.variants = variants
        self.min_samples = min_samples
        self.start_time = datetime.now()
        self.results = {
            variant: {
                "impressions": 0,
                "clicks": 0,
                "shares": 0,
                "comments": 0,
                "avg_time_spent": 0.0,
                "total_time_spent": 0.0
            }
            for variant in variants
        }
        
    def add_result(self, 
                  variant: str, 
                  metrics: Dict[str, float]):
        """Add a new result for a variant."""
        if variant not in self.results:
            return
            
        self.results[variant]["impressions"] += 1
        self.results[variant]["clicks"] += metrics.get("clicks", 0)
        self.results[variant]["shares"] += metrics.get("shares", 0)
        self.results[variant]["comments"] += metrics.get("comments", 0)
        
        time_spent = metrics.get("time_spent", 0.0)
        total_time = self.results[variant]["total_time_spent"] + time_spent
        self.results[variant]["total_time_spent"] = total_time
        self.results[variant]["avg_time_spent"] = total_time / self.results[variant]["impressions"]
        
    def get_stats(self) -> Dict:
        """Calculate statistical significance and return test results."""
        stats_data = {
            "test_name": self.name,
            "duration": (datetime.now() - self.start_time).days,
            "total_samples": sum(v["impressions"] for v in self.results.values()),
            "variants": {},
            "winner": None,
            "confidence": None
        }
        
        # Calculate metrics for each variant
        for variant, data in self.results.items():
            if data["impressions"] == 0:
                continue
                
            ctr = data["clicks"] / data["impressions"] if data["impressions"] > 0 else 0
            engagement_rate = (data["shares"] + data["comments"]) / data["impressions"] if data["impressions"] > 0 else 0
            
            stats_data["variants"][variant] = {
                "impressions": data["impressions"],
                "ctr": ctr,
                "engagement_rate": engagement_rate,
                "avg_time_spent": data["avg_time_spent"]
            }
            
        # Determine if we have enough samples
        if stats_data["total_samples"] < self.min_samples:
            stats_data["status"] = "collecting_data"
            return stats_data
            
        # Find winner based on engagement metrics
        best_variant = None
        best_score = -1
        
        for variant, data in stats_data["variants"].items():
            score = (data["ctr"] * 0.4 + 
                    data["engagement_rate"] * 0.4 + 
                    (data["avg_time_spent"] / 300) * 0.2)  # Normalize time spent (5 min = 1.0)
            
            if score > best_score:
                best_score = score
                best_variant = variant
                
        # Calculate statistical significance
        if best_variant and len(stats_data["variants"]) > 1:
            control_data = stats_data["variants"][self.variants[0]]
            test_data = stats_data["variants"][best_variant]
            
            # Perform chi-square test for engagement
            control_engaged = control_data["impressions"] * control_data["engagement_rate"]
            test_engaged = test_data["impressions"] * test_data["engagement_rate"]
            
            chi2, p_value = stats.chi2_contingency([
                [control_engaged, control_data["impressions"] - control_engaged],
                [test_engaged, test_data["impressions"] - test_engaged]
            ])[0:2]
            
            confidence = (1 - p_value) * 100
            
            stats_data["winner"] = best_variant
            stats_data["confidence"] = confidence
            stats_data["status"] = "completed"
            
        return stats_data

class ABTestManager:
    def __init__(self):
        self.active_tests = {}
        self.completed_tests = {}
        self.test_history = []
        
    def create_test(self, 
                   name: str,
                   variants: List[str],
                   min_samples: int = 100) -> Dict:
        """Create a new A/B test."""
        if name in self.active_tests:
            return {"error": "Test already exists"}
            
        test = ABTest(name, variants, min_samples)
        self.active_tests[name] = test
        
        return {
            "status": "created",
            "test_name": name,
            "variants": variants,
            "min_samples": min_samples
        }
        
    def record_result(self,
                     test_name: str,
                     variant: str,
                     metrics: Dict[str, float]) -> Dict:
        """Record a result for an active test."""
        if test_name not in self.active_tests:
            return {"error": "Test not found"}
            
        test = self.active_tests[test_name]
        test.add_result(variant, metrics)
        
        # Check if test is complete
        stats = test.get_stats()
        if stats.get("status") == "completed":
            self.completed_tests[test_name] = test
            del self.active_tests[test_name]
            self.test_history.append(stats)
            
        return {"status": "recorded", "test_stats": stats}
        
    def get_test_stats(self, test_name: str) -> Optional[Dict]:
        """Get current statistics for a test."""
        if test_name in self.active_tests:
            return self.active_tests[test_name].get_stats()
        elif test_name in self.completed_tests:
            return self.completed_tests[test_name].get_stats()
        return None
        
    def get_all_active_tests(self) -> List[Dict]:
        """Get statistics for all active tests."""
        return [
            test.get_stats()
            for test in self.active_tests.values()
        ]
        
    def get_test_history(self) -> List[Dict]:
        """Get history of completed tests."""
        return self.test_history
        
    def select_variant(self, test_name: str) -> Optional[str]:
        """Select a variant for a new user in an active test."""
        if test_name not in self.active_tests:
            return None
            
        test = self.active_tests[test_name]
        
        # Simple random selection for now
        # Could be enhanced with multi-armed bandit algorithms
        return random.choice(test.variants) 