"""
Multilingual Performance Optimizer
Optimizes the offline multilingual AI system for better performance
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Optimization strategies"""
    AGGRESSIVE = "aggressive"  # Maximum performance, may reduce quality
    BALANCED = "balanced"      # Balance between performance and quality
    QUALITY = "quality"        # Prioritize quality over performance
    MEMORY = "memory"          # Minimize memory usage
    LATENCY = "latency"        # Minimize response latency

@dataclass
class OptimizationConfig:
    """Configuration for optimization"""
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    target_latency_ms: int = 2000
    target_memory_gb: float = 8.0
    min_quality_score: float = 0.7
    enable_quantization: bool = True
    enable_caching: bool = True
    enable_batching: bool = True
    enable_adapters: bool = True
    batch_size: int = 4
    cache_similarity_threshold: float = 0.92
    max_context_length: int = 4096

@dataclass
class OptimizationResult:
    """Result of optimization"""
    strategy_used: str
    improvements: Dict[str, float]
    settings_changed: Dict[str, Any]
    estimated_speedup: float
    estimated_memory_reduction: float
    quality_impact: float
    recommendations: List[str]

class MultilingualOptimizer:
    """
    Optimizes the multilingual AI system for better performance
    """
    
    def __init__(self, config: OptimizationConfig = None):
        """
        Initialize the optimizer
        
        Args:
            config: Optimization configuration
        """
        
        self.config = config or OptimizationConfig()
        
        # Optimization parameters by strategy
        self.strategy_params = self._initialize_strategy_params()
        
        # Language-specific optimizations
        self.language_optimizations = self._initialize_language_optimizations()
        
        # Performance baselines
        self.baselines = {
            'latency_ms': 3000,
            'memory_gb': 12.0,
            'tokens_per_second': 15,
            'quality_score': 0.75
        }
        
        # Optimization history
        self.optimization_history = []
    
    def _initialize_strategy_params(self) -> Dict:
        """Initialize parameters for each optimization strategy"""
        
        return {
            OptimizationStrategy.AGGRESSIVE: {
                'quantization': 'q2_k',      # Lowest quality, fastest
                'context_length': 2048,       # Shorter context
                'batch_size': 8,              # Larger batches
                'cache_threshold': 0.85,      # More aggressive caching
                'gpu_layers': -1,             # Full GPU utilization
                'temperature': 0.5,           # Lower temperature
                'top_k': 20,                  # Fewer tokens to consider
                'adapter_rank': 4             # Smaller adapters
            },
            OptimizationStrategy.BALANCED: {
                'quantization': 'q4_k_m',     # Good balance
                'context_length': 4096,       # Standard context
                'batch_size': 4,              # Moderate batches
                'cache_threshold': 0.92,      # Standard caching
                'gpu_layers': -1,             # Full GPU if available
                'temperature': 0.7,           # Standard temperature
                'top_k': 40,                  # Standard sampling
                'adapter_rank': 8             # Standard adapters
            },
            OptimizationStrategy.QUALITY: {
                'quantization': 'q6_k',       # Higher quality
                'context_length': 8192,       # Longer context
                'batch_size': 2,              # Smaller batches
                'cache_threshold': 0.95,      # Conservative caching
                'gpu_layers': -1,             # Full GPU
                'temperature': 0.8,           # Higher temperature
                'top_k': 50,                  # More diverse sampling
                'adapter_rank': 16            # Larger adapters
            },
            OptimizationStrategy.MEMORY: {
                'quantization': 'q3_k_m',     # Lower memory usage
                'context_length': 2048,       # Shorter context
                'batch_size': 1,              # Single processing
                'cache_threshold': 0.90,      # Moderate caching
                'gpu_layers': 20,             # Partial GPU usage
                'temperature': 0.7,           # Standard
                'top_k': 30,                  # Reduced sampling
                'adapter_rank': 4,            # Smaller adapters
                'use_mmap': True,             # Memory mapping
                'use_mlock': False            # Don't lock in RAM
            },
            OptimizationStrategy.LATENCY: {
                'quantization': 'q4_k_m',     # Fast but decent quality
                'context_length': 3072,       # Moderate context
                'batch_size': 1,              # No batching for latency
                'cache_threshold': 0.88,      # Aggressive caching
                'gpu_layers': -1,             # Full GPU
                'temperature': 0.6,           # Faster generation
                'top_k': 30,                  # Faster sampling
                'adapter_rank': 8,            # Standard adapters
                'early_stopping': True        # Stop when good enough
            }
        }
    
    def _initialize_language_optimizations(self) -> Dict:
        """Initialize language-specific optimizations"""
        
        return {
            'en': {
                'token_multiplier': 1.0,
                'context_adjustment': 1.0,
                'cache_priority': 1.0,
                'preprocessing': 'minimal'
            },
            'es': {
                'token_multiplier': 1.1,
                'context_adjustment': 1.05,
                'cache_priority': 0.95,
                'preprocessing': 'standard'
            },
            'fr': {
                'token_multiplier': 1.1,
                'context_adjustment': 1.05,
                'cache_priority': 0.95,
                'preprocessing': 'standard'
            },
            'pt': {
                'token_multiplier': 1.15,
                'context_adjustment': 1.1,
                'cache_priority': 0.9,
                'preprocessing': 'standard'
            },
            'zh': {
                'token_multiplier': 2.5,
                'context_adjustment': 1.5,
                'cache_priority': 1.1,
                'preprocessing': 'advanced',
                'use_specialized_tokenizer': True
            },
            'ar': {
                'token_multiplier': 2.0,
                'context_adjustment': 1.3,
                'cache_priority': 1.05,
                'preprocessing': 'advanced',
                'use_rtl_optimization': True
            }
        }
    
    def optimize(self, performance_data: Dict) -> OptimizationResult:
        """
        Optimize system based on performance data
        
        Args:
            performance_data: Current performance metrics
            
        Returns:
            OptimizationResult with improvements and recommendations
        """
        
        # Analyze current performance
        analysis = self._analyze_performance(performance_data)
        
        # Get optimization parameters for strategy
        params = self.strategy_params[self.config.strategy]
        
        # Apply optimizations
        settings_changed = {}
        improvements = {}
        recommendations = []
        
        # 1. Model Quantization
        if self.config.enable_quantization:
            quant_improvement = self._optimize_quantization(
                analysis, params, settings_changed
            )
            improvements['quantization'] = quant_improvement
        
        # 2. Context Length
        context_improvement = self._optimize_context(
            analysis, params, settings_changed
        )
        improvements['context'] = context_improvement
        
        # 3. Caching
        if self.config.enable_caching:
            cache_improvement = self._optimize_caching(
                analysis, params, settings_changed
            )
            improvements['caching'] = cache_improvement
        
        # 4. Batching
        if self.config.enable_batching:
            batch_improvement = self._optimize_batching(
                analysis, params, settings_changed
            )
            improvements['batching'] = batch_improvement
        
        # 5. Language-specific optimizations
        lang_improvements = self._optimize_languages(
            analysis, settings_changed
        )
        improvements['languages'] = lang_improvements
        
        # 6. Hardware utilization
        hw_improvement = self._optimize_hardware(
            analysis, params, settings_changed
        )
        improvements['hardware'] = hw_improvement
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            analysis, improvements
        )
        
        # Calculate overall impact
        estimated_speedup = np.mean(list(improvements.values()))
        estimated_memory_reduction = self._estimate_memory_reduction(settings_changed)
        quality_impact = self._estimate_quality_impact(settings_changed)
        
        # Store optimization history
        result = OptimizationResult(
            strategy_used=self.config.strategy.value,
            improvements=improvements,
            settings_changed=settings_changed,
            estimated_speedup=estimated_speedup,
            estimated_memory_reduction=estimated_memory_reduction,
            quality_impact=quality_impact,
            recommendations=recommendations
        )
        
        self.optimization_history.append({
            'timestamp': time.time(),
            'result': result
        })
        
        return result
    
    def _analyze_performance(self, performance_data: Dict) -> Dict:
        """Analyze current performance metrics"""
        
        analysis = {
            'bottlenecks': [],
            'underutilized': [],
            'language_issues': [],
            'quality_issues': []
        }
        
        # Check for bottlenecks
        if performance_data.get('avg_latency_ms', 0) > self.config.target_latency_ms:
            analysis['bottlenecks'].append('latency')
        
        if performance_data.get('memory_usage_gb', 0) > self.config.target_memory_gb:
            analysis['bottlenecks'].append('memory')
        
        if performance_data.get('gpu_utilization', 0) > 90:
            analysis['bottlenecks'].append('gpu')
        
        # Check for underutilization
        if performance_data.get('cpu_utilization', 0) < 30:
            analysis['underutilized'].append('cpu')
        
        if performance_data.get('gpu_utilization', 0) < 50:
            analysis['underutilized'].append('gpu')
        
        # Check language-specific issues
        language_stats = performance_data.get('language_stats', {})
        for lang, stats in language_stats.items():
            if stats.get('avg_latency_ms', 0) > self.config.target_latency_ms * 1.5:
                analysis['language_issues'].append(lang)
            
            if stats.get('quality_score', 1.0) < self.config.min_quality_score:
                analysis['quality_issues'].append(lang)
        
        return analysis
    
    def _optimize_quantization(self, analysis: Dict, params: Dict, settings: Dict) -> float:
        """Optimize model quantization"""
        
        improvement = 0.0
        
        if 'memory' in analysis['bottlenecks']:
            # Use more aggressive quantization
            settings['quantization'] = params['quantization']
            improvement = 0.3  # 30% memory improvement
        elif 'latency' in analysis['bottlenecks']:
            # Balance quantization for speed
            settings['quantization'] = 'q4_k_m'
            improvement = 0.15  # 15% speed improvement
        
        return improvement
    
    def _optimize_context(self, analysis: Dict, params: Dict, settings: Dict) -> float:
        """Optimize context length"""
        
        improvement = 0.0
        
        if 'memory' in analysis['bottlenecks'] or 'latency' in analysis['bottlenecks']:
            # Reduce context length
            settings['context_length'] = min(
                params['context_length'],
                self.config.max_context_length
            )
            improvement = 0.2  # 20% improvement
        
        return improvement
    
    def _optimize_caching(self, analysis: Dict, params: Dict, settings: Dict) -> float:
        """Optimize caching parameters"""
        
        improvement = 0.0
        
        if 'latency' in analysis['bottlenecks']:
            # More aggressive caching
            settings['cache_threshold'] = params['cache_threshold']
            settings['cache_size'] = 10000
            improvement = 0.25  # 25% improvement for cached queries
        
        return improvement
    
    def _optimize_batching(self, analysis: Dict, params: Dict, settings: Dict) -> float:
        """Optimize batching parameters"""
        
        improvement = 0.0
        
        if 'gpu' in analysis['underutilized'] and 'latency' not in analysis['bottlenecks']:
            # Increase batch size
            settings['batch_size'] = params['batch_size']
            improvement = 0.15  # 15% throughput improvement
        elif 'latency' in analysis['bottlenecks']:
            # Reduce or disable batching
            settings['batch_size'] = 1
            improvement = 0.1  # 10% latency improvement
        
        return improvement
    
    def _optimize_languages(self, analysis: Dict, settings: Dict) -> float:
        """Apply language-specific optimizations"""
        
        improvements = []
        
        for lang in analysis['language_issues']:
            lang_config = self.language_optimizations.get(lang, {})
            
            # Apply language-specific settings
            settings[f'{lang}_preprocessing'] = lang_config.get('preprocessing', 'standard')
            
            if lang in ['zh', 'ar']:
                # Special handling for complex scripts
                settings[f'{lang}_specialized'] = True
                improvements.append(0.2)
            else:
                improvements.append(0.1)
        
        return np.mean(improvements) if improvements else 0.0
    
    def _optimize_hardware(self, analysis: Dict, params: Dict, settings: Dict) -> float:
        """Optimize hardware utilization"""
        
        improvement = 0.0
        
        if 'gpu' in analysis['underutilized']:
            # Increase GPU utilization
            settings['gpu_layers'] = params['gpu_layers']
            improvement = 0.3  # 30% speed improvement
        
        if 'cpu' in analysis['bottlenecks']:
            # Reduce CPU threads
            settings['n_threads'] = os.cpu_count() // 2
            improvement = 0.1
        
        return improvement
    
    def _estimate_memory_reduction(self, settings: Dict) -> float:
        """Estimate memory reduction from settings"""
        
        reduction = 0.0
        
        # Quantization impact
        if 'quantization' in settings:
            quant_map = {
                'q2_k': 0.5,    # 50% reduction
                'q3_k_m': 0.4,  # 40% reduction
                'q4_k_m': 0.3,  # 30% reduction
                'q5_k_m': 0.2,  # 20% reduction
                'q6_k': 0.1     # 10% reduction
            }
            reduction += quant_map.get(settings['quantization'], 0)
        
        # Context length impact
        if 'context_length' in settings:
            original = self.config.max_context_length
            new = settings['context_length']
            reduction += (1 - new / original) * 0.2
        
        return min(reduction, 0.7)  # Cap at 70% reduction
    
    def _estimate_quality_impact(self, settings: Dict) -> float:
        """Estimate quality impact from settings"""
        
        impact = 0.0
        
        # Quantization impact on quality
        if 'quantization' in settings:
            quant_impact = {
                'q2_k': -0.3,    # 30% quality loss
                'q3_k_m': -0.15, # 15% quality loss
                'q4_k_m': -0.05, # 5% quality loss
                'q5_k_m': -0.02, # 2% quality loss
                'q6_k': -0.01    # 1% quality loss
            }
            impact += quant_impact.get(settings['quantization'], 0)
        
        # Context length impact
        if 'context_length' in settings and settings['context_length'] < 3072:
            impact -= 0.1  # 10% quality loss for very short context
        
        return impact
    
    def _generate_recommendations(self, analysis: Dict, improvements: Dict) -> List[str]:
        """Generate optimization recommendations"""
        
        recommendations = []
        
        # Hardware recommendations
        if 'gpu' in analysis['bottlenecks']:
            recommendations.append(
                "Consider upgrading GPU or using multi-GPU setup for better performance"
            )
        
        if 'memory' in analysis['bottlenecks']:
            recommendations.append(
                "Consider using more aggressive quantization or upgrading system memory"
            )
        
        # Language-specific recommendations
        if analysis['language_issues']:
            langs = ', '.join(analysis['language_issues'])
            recommendations.append(
                f"Languages {langs} need optimization. Consider language-specific LoRA adapters"
            )
        
        # Quality recommendations
        if analysis['quality_issues']:
            recommendations.append(
                "Quality scores are below threshold. Consider using larger model or adjusting temperature"
            )
        
        # Caching recommendations
        if improvements.get('caching', 0) < 0.1:
            recommendations.append(
                "Cache hit rate is low. Consider pre-warming cache with common queries"
            )
        
        # No issues found
        if not recommendations:
            recommendations.append(
                "System is performing well. Continue monitoring for changes in usage patterns"
            )
        
        return recommendations
    
    def auto_optimize(self, performance_data: Dict) -> Dict:
        """
        Automatically apply optimizations based on performance
        
        Args:
            performance_data: Current performance metrics
            
        Returns:
            Applied settings
        """
        
        # Run optimization
        result = self.optimize(performance_data)
        
        # Apply settings if improvement is significant
        if result.estimated_speedup > 0.1 and result.quality_impact > -0.1:
            logger.info(f"Applying optimizations: {result.strategy_used}")
            logger.info(f"Expected speedup: {result.estimated_speedup:.1%}")
            logger.info(f"Quality impact: {result.quality_impact:.1%}")
            
            return result.settings_changed
        else:
            logger.info("No significant optimizations found")
            return {}
    
    def export_optimization_config(self, filepath: str = "optimization_config.json"):
        """
        Export current optimization configuration
        
        Args:
            filepath: Path to save configuration
        """
        
        config_data = {
            'strategy': self.config.strategy.value,
            'parameters': self.strategy_params[self.config.strategy],
            'language_optimizations': self.language_optimizations,
            'thresholds': {
                'target_latency_ms': self.config.target_latency_ms,
                'target_memory_gb': self.config.target_memory_gb,
                'min_quality_score': self.config.min_quality_score
            },
            'history': self.optimization_history[-10:]  # Last 10 optimizations
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        logger.info(f"Exported optimization config to {filepath}")
    
    def get_best_settings_for_language(self, language: str) -> Dict:
        """
        Get optimal settings for a specific language
        
        Args:
            language: Language code
            
        Returns:
            Optimal settings dictionary
        """
        
        base_params = self.strategy_params[self.config.strategy].copy()
        lang_config = self.language_optimizations.get(language, {})
        
        # Adjust for language
        settings = {
            **base_params,
            'max_tokens': int(base_params.get('max_tokens', 512) * lang_config.get('token_multiplier', 1.0)),
            'context_length': int(base_params['context_length'] * lang_config.get('context_adjustment', 1.0)),
            'preprocessing': lang_config.get('preprocessing', 'standard')
        }
        
        # Special handling
        if language == 'zh':
            settings['use_chinese_tokenizer'] = True
            settings['adapter'] = 'chinese_enhanced'
        elif language == 'ar':
            settings['use_rtl_optimization'] = True
            settings['adapter'] = 'arabic_enhanced'
        
        return settings