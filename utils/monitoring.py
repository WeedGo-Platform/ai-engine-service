"""
Monitoring Utilities - Metrics collection
Tracks performance and business metrics
"""

import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

class MetricsCollector:
    """
    Singleton metrics collector for application monitoring
    Collects and aggregates performance metrics
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize metrics collector"""
        if self._initialized:
            return
        
        self.metrics = {
            "requests": defaultdict(int),
            "response_times": defaultdict(list),
            "model_usage": defaultdict(int),
            "errors": defaultdict(int),
            "cache_hits": 0,
            "cache_misses": 0,
            "start_time": datetime.now()
        }
        self._initialized = True
    
    def record_request(self, endpoint: str, method: str, status: int, duration: float):
        """Record API request metrics"""
        key = f"{method}:{endpoint}"
        self.metrics["requests"][key] += 1
        self.metrics["response_times"][key].append(duration)
        
        if status >= 400:
            self.metrics["errors"][key] += 1
    
    def record_chat(self, customer_id: str, model: str, response_time: float):
        """Record chat interaction metrics"""
        self.metrics["model_usage"][model] += 1
        self.metrics["response_times"]["chat"].append(response_time)
    
    def record_cache(self, hit: bool):
        """Record cache hit/miss"""
        if hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        
        uptime = (datetime.now() - self.metrics["start_time"]).total_seconds()
        
        # Calculate averages
        avg_response_times = {}
        for endpoint, times in self.metrics["response_times"].items():
            if times:
                avg_response_times[endpoint] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        
        # Calculate cache hit rate
        total_cache = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (
            self.metrics["cache_hits"] / total_cache * 100
            if total_cache > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "total_requests": sum(self.metrics["requests"].values()),
            "requests_by_endpoint": dict(self.metrics["requests"]),
            "response_times": avg_response_times,
            "model_usage": dict(self.metrics["model_usage"]),
            "errors": dict(self.metrics["errors"]),
            "cache_hit_rate": cache_hit_rate,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        self.__init__()
        self._initialized = True

# Global metrics instance
metrics_collector = MetricsCollector()