"""
Performance Monitoring System for Offline Multilingual AI
Tracks metrics, resource usage, and optimization opportunities
"""

import os
import time
import json
import psutil
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
import numpy as np

try:
    import GPUtil
    gpu_available = True
except ImportError:
    gpu_available = False

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    request_id: str
    language: str
    operation: str
    duration: float
    tokens_processed: int
    tokens_per_second: float
    memory_used_mb: float
    cpu_percent: float
    gpu_percent: Optional[float] = None
    gpu_memory_mb: Optional[float] = None
    cache_hit: bool = False
    adapter_used: Optional[str] = None
    quality_score: Optional[float] = None
    error: Optional[str] = None

@dataclass
class ResourceUsage:
    """System resource usage"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    gpu_percent: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_temperature: Optional[float] = None
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float

class PerformanceMonitor:
    """
    Monitors and tracks performance of multilingual AI system
    """
    
    def __init__(
        self,
        metrics_dir: str = "metrics",
        max_history: int = 10000,
        monitoring_interval: float = 1.0
    ):
        """
        Initialize performance monitor
        
        Args:
            metrics_dir: Directory to store metrics
            max_history: Maximum metrics to keep in memory
            monitoring_interval: Resource monitoring interval in seconds
        """
        
        self.metrics_dir = metrics_dir
        self.max_history = max_history
        self.monitoring_interval = monitoring_interval
        
        # Create metrics directory
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Metrics storage
        self.metrics_history = deque(maxlen=max_history)
        self.language_metrics = defaultdict(list)
        self.operation_metrics = defaultdict(list)
        
        # Real-time metrics
        self.current_metrics = {
            'active_requests': 0,
            'total_requests': 0,
            'total_tokens': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'avg_response_time': 0,
            'avg_tokens_per_second': 0
        }
        
        # Resource monitoring
        self.resource_history = deque(maxlen=1000)
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # Performance thresholds
        self.thresholds = {
            'max_response_time': 5.0,  # seconds
            'min_tokens_per_second': 10,
            'max_memory_percent': 80,
            'max_cpu_percent': 90,
            'max_gpu_percent': 95,
            'min_quality_score': 0.6
        }
        
        # Start resource monitoring
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start background resource monitoring"""
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Started resource monitoring")
    
    def stop_monitoring(self):
        """Stop background resource monitoring"""
        
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped resource monitoring")
    
    def _monitor_resources(self):
        """Background thread for resource monitoring"""
        
        while not self.stop_monitoring.is_set():
            try:
                usage = self._get_resource_usage()
                self.resource_history.append(usage)
                
                # Check for threshold violations
                self._check_thresholds(usage)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
            
            self.stop_monitoring.wait(self.monitoring_interval)
    
    def _get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Disk
        disk = psutil.disk_usage('/')
        
        # Network
        net_io = psutil.net_io_counters()
        
        # GPU (if available)
        gpu_percent = None
        gpu_memory = None
        gpu_temp = None
        
        if gpu_available:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    gpu_percent = gpu.load * 100
                    gpu_memory = gpu.memoryUsed / 1024  # Convert to GB
                    gpu_temp = gpu.temperature
            except Exception as e:
                logger.debug(f"GPU monitoring failed: {e}")
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            gpu_percent=gpu_percent,
            gpu_memory_used_gb=gpu_memory,
            gpu_temperature=gpu_temp,
            disk_usage_percent=disk.percent,
            network_sent_mb=net_io.bytes_sent / (1024**2),
            network_recv_mb=net_io.bytes_recv / (1024**2)
        )
    
    def record_request_start(self, request_id: str, language: str, operation: str) -> Dict:
        """Record start of a request"""
        
        self.current_metrics['active_requests'] += 1
        self.current_metrics['total_requests'] += 1
        
        return {
            'request_id': request_id,
            'language': language,
            'operation': operation,
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss / (1024**2)  # MB
        }
    
    def record_request_end(
        self,
        request_context: Dict,
        tokens_processed: int,
        cache_hit: bool = False,
        adapter_used: Optional[str] = None,
        quality_score: Optional[float] = None,
        error: Optional[str] = None
    ) -> PerformanceMetrics:
        """Record end of a request"""
        
        end_time = time.time()
        duration = end_time - request_context['start_time']
        end_memory = psutil.Process().memory_info().rss / (1024**2)
        memory_used = end_memory - request_context['start_memory']
        
        # Calculate tokens per second
        tokens_per_second = tokens_processed / duration if duration > 0 else 0
        
        # Get current CPU usage
        cpu_percent = psutil.cpu_percent(interval=0)
        
        # Get GPU usage if available
        gpu_percent = None
        gpu_memory = None
        if gpu_available:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_percent = gpus[0].load * 100
                    gpu_memory = gpus[0].memoryUsed
            except:
                pass
        
        # Create metrics record
        metrics = PerformanceMetrics(
            timestamp=end_time,
            request_id=request_context['request_id'],
            language=request_context['language'],
            operation=request_context['operation'],
            duration=duration,
            tokens_processed=tokens_processed,
            tokens_per_second=tokens_per_second,
            memory_used_mb=memory_used,
            cpu_percent=cpu_percent,
            gpu_percent=gpu_percent,
            gpu_memory_mb=gpu_memory,
            cache_hit=cache_hit,
            adapter_used=adapter_used,
            quality_score=quality_score,
            error=error
        )
        
        # Update metrics
        self._update_metrics(metrics)
        
        # Store metrics
        self.metrics_history.append(metrics)
        self.language_metrics[request_context['language']].append(metrics)
        self.operation_metrics[request_context['operation']].append(metrics)
        
        # Update current metrics
        self.current_metrics['active_requests'] -= 1
        self.current_metrics['total_tokens'] += tokens_processed
        
        if cache_hit:
            self.current_metrics['cache_hits'] += 1
        else:
            self.current_metrics['cache_misses'] += 1
        
        if error:
            self.current_metrics['errors'] += 1
        
        return metrics
    
    def _update_metrics(self, metrics: PerformanceMetrics):
        """Update running metrics"""
        
        # Update average response time
        total_requests = self.current_metrics['total_requests']
        if total_requests > 0:
            prev_avg = self.current_metrics['avg_response_time']
            self.current_metrics['avg_response_time'] = (
                (prev_avg * (total_requests - 1) + metrics.duration) / total_requests
            )
            
            # Update average tokens per second
            prev_tps = self.current_metrics['avg_tokens_per_second']
            self.current_metrics['avg_tokens_per_second'] = (
                (prev_tps * (total_requests - 1) + metrics.tokens_per_second) / total_requests
            )
    
    def _check_thresholds(self, usage: ResourceUsage):
        """Check for threshold violations"""
        
        warnings = []
        
        if usage.cpu_percent > self.thresholds['max_cpu_percent']:
            warnings.append(f"High CPU usage: {usage.cpu_percent:.1f}%")
        
        if usage.memory_percent > self.thresholds['max_memory_percent']:
            warnings.append(f"High memory usage: {usage.memory_percent:.1f}%")
        
        if usage.gpu_percent and usage.gpu_percent > self.thresholds['max_gpu_percent']:
            warnings.append(f"High GPU usage: {usage.gpu_percent:.1f}%")
        
        if warnings:
            logger.warning(" | ".join(warnings))
    
    def get_language_stats(self, language: str) -> Dict:
        """Get statistics for a specific language"""
        
        if language not in self.language_metrics:
            return {}
        
        metrics_list = self.language_metrics[language]
        if not metrics_list:
            return {}
        
        durations = [m.duration for m in metrics_list]
        tokens_per_sec = [m.tokens_per_second for m in metrics_list]
        quality_scores = [m.quality_score for m in metrics_list if m.quality_score]
        
        return {
            'total_requests': len(metrics_list),
            'avg_duration': np.mean(durations),
            'min_duration': np.min(durations),
            'max_duration': np.max(durations),
            'avg_tokens_per_second': np.mean(tokens_per_sec),
            'avg_quality_score': np.mean(quality_scores) if quality_scores else None,
            'error_rate': sum(1 for m in metrics_list if m.error) / len(metrics_list),
            'cache_hit_rate': sum(1 for m in metrics_list if m.cache_hit) / len(metrics_list)
        }
    
    def get_operation_stats(self, operation: str) -> Dict:
        """Get statistics for a specific operation"""
        
        if operation not in self.operation_metrics:
            return {}
        
        metrics_list = self.operation_metrics[operation]
        if not metrics_list:
            return {}
        
        durations = [m.duration for m in metrics_list]
        memory_used = [m.memory_used_mb for m in metrics_list]
        
        return {
            'total_calls': len(metrics_list),
            'avg_duration': np.mean(durations),
            'p50_duration': np.percentile(durations, 50),
            'p95_duration': np.percentile(durations, 95),
            'p99_duration': np.percentile(durations, 99),
            'avg_memory_mb': np.mean(memory_used),
            'max_memory_mb': np.max(memory_used)
        }
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        
        # Calculate cache hit rate
        total_cache_ops = self.current_metrics['cache_hits'] + self.current_metrics['cache_misses']
        cache_hit_rate = (
            self.current_metrics['cache_hits'] / total_cache_ops
            if total_cache_ops > 0 else 0
        )
        
        # Calculate error rate
        error_rate = (
            self.current_metrics['errors'] / self.current_metrics['total_requests']
            if self.current_metrics['total_requests'] > 0 else 0
        )
        
        # Get current resource usage
        current_resources = self._get_resource_usage()
        
        # Language distribution
        language_distribution = {
            lang: len(metrics)
            for lang, metrics in self.language_metrics.items()
        }
        
        return {
            'current_metrics': self.current_metrics,
            'cache_hit_rate': cache_hit_rate,
            'error_rate': error_rate,
            'resource_usage': asdict(current_resources),
            'language_distribution': language_distribution,
            'language_stats': {
                lang: self.get_language_stats(lang)
                for lang in self.language_metrics.keys()
            },
            'thresholds': self.thresholds
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get performance optimization suggestions"""
        
        suggestions = []
        
        # Analyze recent metrics
        if len(self.metrics_history) >= 100:
            recent_metrics = list(self.metrics_history)[-100:]
            
            # Check response times
            avg_duration = np.mean([m.duration for m in recent_metrics])
            if avg_duration > self.thresholds['max_response_time']:
                suggestions.append(
                    f"Response times are high ({avg_duration:.2f}s avg). "
                    "Consider: reducing model size, enabling more GPU layers, "
                    "or increasing cache similarity threshold."
                )
            
            # Check tokens per second
            avg_tps = np.mean([m.tokens_per_second for m in recent_metrics])
            if avg_tps < self.thresholds['min_tokens_per_second']:
                suggestions.append(
                    f"Token generation is slow ({avg_tps:.1f} t/s). "
                    "Consider: using smaller quantization, reducing context size, "
                    "or upgrading hardware."
                )
            
            # Check cache effectiveness
            cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
            cache_rate = cache_hits / len(recent_metrics)
            if cache_rate < 0.2:
                suggestions.append(
                    f"Low cache hit rate ({cache_rate:.1%}). "
                    "Consider: lowering similarity threshold or pre-warming cache "
                    "with common queries."
                )
            
            # Check quality scores
            quality_scores = [m.quality_score for m in recent_metrics if m.quality_score]
            if quality_scores:
                avg_quality = np.mean(quality_scores)
                if avg_quality < self.thresholds['min_quality_score']:
                    suggestions.append(
                        f"Quality scores are low ({avg_quality:.2f} avg). "
                        "Consider: using larger model, adjusting temperature, "
                        "or fine-tuning with LoRA adapters."
                    )
        
        # Check resource usage
        if self.resource_history:
            recent_resources = list(self.resource_history)[-10:]
            avg_cpu = np.mean([r.cpu_percent for r in recent_resources])
            avg_memory = np.mean([r.memory_percent for r in recent_resources])
            
            if avg_cpu > 80:
                suggestions.append(
                    f"High CPU usage ({avg_cpu:.1f}% avg). "
                    "Consider: reducing thread count or enabling GPU acceleration."
                )
            
            if avg_memory > 70:
                suggestions.append(
                    f"High memory usage ({avg_memory:.1f}% avg). "
                    "Consider: using memory mapping, reducing batch size, "
                    "or clearing cache more frequently."
                )
        
        # Language-specific suggestions
        for lang, metrics in self.language_metrics.items():
            if len(metrics) >= 10:
                lang_durations = [m.duration for m in metrics[-10:]]
                lang_avg = np.mean(lang_durations)
                
                if lang in ['zh', 'ar'] and lang_avg > avg_duration * 1.5:
                    suggestions.append(
                        f"{lang.upper()} processing is slow. "
                        f"Consider: using specialized tokenizer or "
                        f"language-specific LoRA adapter."
                    )
        
        return suggestions if suggestions else ["System performing within normal parameters."]
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export metrics to JSON file"""
        
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.metrics_dir, f"metrics_{timestamp}.json")
        
        metrics_data = {
            'timestamp': time.time(),
            'summary': self.get_performance_summary(),
            'recent_metrics': [
                asdict(m) for m in list(self.metrics_history)[-1000:]
            ],
            'optimization_suggestions': self.get_optimization_suggestions()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)
        
        logger.info(f"Exported metrics to {filepath}")
        return filepath
    
    def reset_metrics(self):
        """Reset all metrics"""
        
        self.metrics_history.clear()
        self.language_metrics.clear()
        self.operation_metrics.clear()
        self.resource_history.clear()
        
        self.current_metrics = {
            'active_requests': 0,
            'total_requests': 0,
            'total_tokens': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'avg_response_time': 0,
            'avg_tokens_per_second': 0
        }
        
        logger.info("Reset all metrics")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_monitoring()