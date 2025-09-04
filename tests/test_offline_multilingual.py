#!/usr/bin/env python3
"""
Comprehensive Test Suite for Offline Multilingual AI System
Tests all 6 languages without any external API dependencies
"""

import os
import sys
import time
import json
import asyncio
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
import colorama
from colorama import Fore, Back, Style

# Add services to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our services
from services.offline_language_detector import OfflineLanguageDetector
from services.offline_inference_engine import (
    OfflineInferenceEngine,
    InferenceConfig,
    ModelSize,
    QuantizationType
)
from services.semantic_cache import SemanticCache
from services.cannabis_terminology import CannabisTerminologyProcessor
from services.language_preprocessors import MultilingualPreprocessor
from services.lora_adapter_manager import LoRAAdapterManager
from services.quality_validator import QualityValidator, ValidationConfig
from services.performance_monitor import PerformanceMonitor

# Initialize colorama for colored output
colorama.init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Test case for multilingual testing"""
    language: str
    prompt: str
    expected_keywords: List[str]
    description: str

class OfflineMultilingualTester:
    """
    Comprehensive tester for offline multilingual AI system
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the tester
        
        Args:
            model_path: Path to GGUF model
        """
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Offline Multilingual AI System Test{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        # Set default model path
        if not model_path:
            # Try production model first
            if os.path.exists("models/gguf/qwen-14b-chat-q4_k_m.gguf"):
                model_path = "models/gguf/qwen-14b-chat-q4_k_m.gguf"
                model_size = ModelSize.MEDIUM
            # Fallback to test model
            elif os.path.exists("models/gguf/qwen-1_8b-chat-q4_k_m.gguf"):
                model_path = "models/gguf/qwen-1_8b-chat-q4_k_m.gguf"
                model_size = ModelSize.TINY
            else:
                print(f"{Fore.RED}No model found! Please run setup script first.{Style.RESET_ALL}")
                sys.exit(1)
        
        print(f"Using model: {Fore.GREEN}{model_path}{Style.RESET_ALL}\n")
        
        # Initialize components
        self._initialize_components(model_path)
        
        # Create test cases
        self.test_cases = self._create_test_cases()
        
        # Results storage
        self.results = {
            'passed': 0,
            'failed': 0,
            'languages': {},
            'performance': {},
            'errors': []
        }
    
    def _initialize_components(self, model_path: str):
        """Initialize all components"""
        
        print(f"{Fore.YELLOW}Initializing components...{Style.RESET_ALL}")
        
        try:
            # 1. Language Detector
            print("  - Language Detector...", end="")
            self.language_detector = OfflineLanguageDetector()
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 2. Preprocessor
            print("  - Multilingual Preprocessor...", end="")
            self.preprocessor = MultilingualPreprocessor()
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 3. Cannabis Terminology
            print("  - Cannabis Terminology Processor...", end="")
            self.terminology = CannabisTerminologyProcessor()
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 4. LoRA Adapter Manager
            print("  - LoRA Adapter Manager...", end="")
            self.adapter_manager = LoRAAdapterManager()
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 5. Semantic Cache
            print("  - Semantic Cache...", end="")
            self.cache = SemanticCache(
                similarity_threshold=0.92,
                max_cache_size=1000
            )
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 6. Quality Validator
            print("  - Quality Validator...", end="")
            self.validator = QualityValidator(
                ValidationConfig(min_score=0.6)
            )
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 7. Performance Monitor
            print("  - Performance Monitor...", end="")
            self.monitor = PerformanceMonitor()
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            # 8. Inference Engine (this takes longest)
            print("  - Inference Engine (loading model)...", end="", flush=True)
            config = InferenceConfig(
                model_path=model_path,
                model_size=ModelSize.MEDIUM,
                quantization=QuantizationType.Q4_K_M,
                n_ctx=4096,
                n_gpu_layers=-1,  # Use all GPU layers if available
                temperature=0.7,
                max_tokens=256
            )
            self.inference_engine = OfflineInferenceEngine(config)
            print(f" {Fore.GREEN}✓{Style.RESET_ALL}")
            
            print(f"\n{Fore.GREEN}All components initialized successfully!{Style.RESET_ALL}\n")
            
        except Exception as e:
            print(f"\n{Fore.RED}Initialization failed: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def _create_test_cases(self) -> List[TestCase]:
        """Create test cases for all languages"""
        
        return [
            # English
            TestCase(
                language='en',
                prompt="What are the effects of Blue Dream strain?",
                expected_keywords=['blue dream', 'effects', 'hybrid', 'euphoria'],
                description="English cannabis strain query"
            ),
            TestCase(
                language='en',
                prompt="Recommend edibles for first-time users",
                expected_keywords=['edibles', 'beginner', 'low', 'dose', 'mg'],
                description="English product recommendation"
            ),
            
            # Spanish
            TestCase(
                language='es',
                prompt="¿Cuáles son los efectos de la cepa Blue Dream?",
                expected_keywords=['blue dream', 'efectos', 'híbrida', 'euforia'],
                description="Spanish cannabis strain query"
            ),
            TestCase(
                language='es',
                prompt="Recomienda comestibles para principiantes",
                expected_keywords=['comestibles', 'principiantes', 'dosis', 'baja'],
                description="Spanish product recommendation"
            ),
            
            # French
            TestCase(
                language='fr',
                prompt="Quels sont les effets de la variété Blue Dream?",
                expected_keywords=['blue dream', 'effets', 'hybride', 'euphorie'],
                description="French cannabis strain query"
            ),
            TestCase(
                language='fr',
                prompt="Recommandez des produits comestibles pour débutants",
                expected_keywords=['comestibles', 'débutants', 'dose', 'faible'],
                description="French product recommendation"
            ),
            
            # Portuguese
            TestCase(
                language='pt',
                prompt="Quais são os efeitos da cepa Blue Dream?",
                expected_keywords=['blue dream', 'efeitos', 'híbrida', 'euforia'],
                description="Portuguese cannabis strain query"
            ),
            TestCase(
                language='pt',
                prompt="Recomende comestíveis para iniciantes",
                expected_keywords=['comestíveis', 'iniciantes', 'dose', 'baixa'],
                description="Portuguese product recommendation"
            ),
            
            # Chinese
            TestCase(
                language='zh',
                prompt="蓝梦品种有什么效果？",
                expected_keywords=['蓝梦', '效果', '混合', '欣快'],
                description="Chinese cannabis strain query"
            ),
            TestCase(
                language='zh',
                prompt="为初次使用者推荐食用产品",
                expected_keywords=['食用', '初次', '剂量', '低'],
                description="Chinese product recommendation"
            ),
            
            # Arabic
            TestCase(
                language='ar',
                prompt="ما هي تأثيرات سلالة بلو دريم؟",
                expected_keywords=['بلو دريم', 'تأثيرات', 'هجين', 'نشوة'],
                description="Arabic cannabis strain query"
            ),
            TestCase(
                language='ar',
                prompt="أوصي بالمنتجات الصالحة للأكل للمبتدئين",
                expected_keywords=['صالحة للأكل', 'مبتدئين', 'جرعة', 'منخفضة'],
                description="Arabic product recommendation"
            )
        ]
    
    async def test_language_detection(self):
        """Test language detection for all languages"""
        
        print(f"\n{Fore.CYAN}Testing Language Detection{Style.RESET_ALL}")
        print("="*40)
        
        for test_case in self.test_cases:
            result = self.language_detector.detect(test_case.prompt)
            
            success = result.primary_language == test_case.language
            symbol = f"{Fore.GREEN}✓{Style.RESET_ALL}" if success else f"{Fore.RED}✗{Style.RESET_ALL}"
            
            print(f"  {symbol} {test_case.language.upper()}: ", end="")
            print(f"Detected={result.primary_language} ", end="")
            print(f"(Confidence={result.confidence:.2f})")
            
            if not success:
                self.results['errors'].append(
                    f"Language detection failed for {test_case.language}"
                )
    
    async def test_preprocessing(self):
        """Test text preprocessing for all languages"""
        
        print(f"\n{Fore.CYAN}Testing Text Preprocessing{Style.RESET_ALL}")
        print("="*40)
        
        for test_case in self.test_cases:
            processed = self.preprocessor.preprocess(
                test_case.prompt,
                test_case.language
            )
            
            print(f"  {test_case.language.upper()}:")
            print(f"    Tokens: {processed.token_count}")
            print(f"    Direction: {processed.direction.value}")
            
            # Store for results
            if test_case.language not in self.results['languages']:
                self.results['languages'][test_case.language] = {}
            
            self.results['languages'][test_case.language]['preprocessing'] = {
                'token_count': processed.token_count,
                'direction': processed.direction.value
            }
    
    async def test_inference(self):
        """Test inference for all languages"""
        
        print(f"\n{Fore.CYAN}Testing Inference Engine{Style.RESET_ALL}")
        print("="*40)
        
        for test_case in self.test_cases:
            print(f"\n  {Fore.YELLOW}{test_case.description}{Style.RESET_ALL}")
            print(f"  Language: {test_case.language.upper()}")
            print(f"  Prompt: {test_case.prompt[:50]}...")
            
            # Get adapter stack
            adapter_stack = self.adapter_manager.get_adapter_stack(
                language=test_case.language,
                domain='cannabis'
            )
            
            # Record start
            request_context = self.monitor.record_request_start(
                request_id=f"test_{test_case.language}_{time.time()}",
                language=test_case.language,
                operation='inference'
            )
            
            try:
                # Check cache first
                cached = self.cache.get(
                    test_case.prompt,
                    test_case.language
                )
                
                if cached:
                    print(f"  {Fore.CYAN}Cache hit!{Style.RESET_ALL}")
                    response_text = cached['response']
                    cache_hit = True
                else:
                    # Generate response
                    result = await self.inference_engine.generate_async(
                        prompt=test_case.prompt,
                        language=test_case.language,
                        max_tokens=256,
                        adapter_name=adapter_stack.adapters[0].name if adapter_stack.adapters else None
                    )
                    
                    response_text = result.text
                    cache_hit = False
                    
                    # Cache the response
                    self.cache.set(
                        query=test_case.prompt,
                        response=response_text,
                        language=test_case.language
                    )
                    
                    print(f"  Tokens/sec: {result.tokens_per_second:.1f}")
                    print(f"  Time: {result.time_taken:.2f}s")
                
                # Validate response
                validation = self.validator.validate(
                    response=response_text,
                    language=test_case.language,
                    prompt=test_case.prompt
                )
                
                # Record end
                metrics = self.monitor.record_request_end(
                    request_context=request_context,
                    tokens_processed=len(response_text.split()),
                    cache_hit=cache_hit,
                    quality_score=validation.overall_score
                )
                
                # Display results
                print(f"  Response: {response_text[:100]}...")
                print(f"  Quality: {validation.quality_level.value} ({validation.overall_score:.2f})")
                
                # Check for expected keywords
                response_lower = response_text.lower()
                keywords_found = sum(
                    1 for keyword in test_case.expected_keywords
                    if keyword.lower() in response_lower
                )
                keyword_coverage = keywords_found / len(test_case.expected_keywords)
                
                print(f"  Keywords: {keywords_found}/{len(test_case.expected_keywords)} found")
                
                # Determine success
                success = validation.passed and keyword_coverage >= 0.5
                
                if success:
                    print(f"  {Fore.GREEN}✓ PASSED{Style.RESET_ALL}")
                    self.results['passed'] += 1
                else:
                    print(f"  {Fore.RED}✗ FAILED{Style.RESET_ALL}")
                    self.results['failed'] += 1
                    if validation.issues:
                        print(f"  Issues: {', '.join(validation.issues[:3])}")
                
                # Store results
                if test_case.language not in self.results['languages']:
                    self.results['languages'][test_case.language] = {}
                
                self.results['languages'][test_case.language]['inference'] = {
                    'quality_score': validation.overall_score,
                    'keyword_coverage': keyword_coverage,
                    'cache_hit': cache_hit,
                    'passed': success
                }
                
            except Exception as e:
                print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}")
                self.results['failed'] += 1
                self.results['errors'].append(f"{test_case.language}: {str(e)}")
                
                # Record error
                self.monitor.record_request_end(
                    request_context=request_context,
                    tokens_processed=0,
                    error=str(e)
                )
    
    async def test_caching(self):
        """Test semantic caching"""
        
        print(f"\n{Fore.CYAN}Testing Semantic Cache{Style.RESET_ALL}")
        print("="*40)
        
        # Test with similar queries
        test_queries = [
            ("What are the effects of Blue Dream?", "en"),
            ("Tell me about Blue Dream effects", "en"),  # Similar
            ("Blue Dream strain effects?", "en"),  # Similar
            ("What is CBD?", "en")  # Different
        ]
        
        for i, (query, lang) in enumerate(test_queries):
            # First query should miss, similar ones should hit
            cached = self.cache.get(query, lang)
            
            if cached:
                print(f"  Query {i+1}: {Fore.GREEN}Cache HIT{Style.RESET_ALL} ", end="")
                print(f"(Similarity: {cached.get('similarity', 0):.2f})")
            else:
                print(f"  Query {i+1}: {Fore.YELLOW}Cache MISS{Style.RESET_ALL}")
                # Add to cache for testing
                self.cache.set(
                    query=query,
                    response=f"Response for: {query}",
                    language=lang
                )
        
        # Display cache metrics
        cache_metrics = self.cache.get_metrics()
        print(f"\n  Cache Statistics:")
        print(f"    Hit Rate: {cache_metrics['hit_rate']:.1%}")
        print(f"    Total Queries: {cache_metrics['total_queries']}")
        print(f"    Cache Sizes: {cache_metrics['cache_sizes']}")
    
    async def test_performance(self):
        """Test and display performance metrics"""
        
        print(f"\n{Fore.CYAN}Performance Analysis{Style.RESET_ALL}")
        print("="*40)
        
        summary = self.monitor.get_performance_summary()
        
        print(f"\n  Overall Metrics:")
        print(f"    Total Requests: {summary['current_metrics']['total_requests']}")
        print(f"    Avg Response Time: {summary['current_metrics']['avg_response_time']:.2f}s")
        print(f"    Avg Tokens/sec: {summary['current_metrics']['avg_tokens_per_second']:.1f}")
        print(f"    Cache Hit Rate: {summary['cache_hit_rate']:.1%}")
        print(f"    Error Rate: {summary['error_rate']:.1%}")
        
        print(f"\n  Language Performance:")
        for lang, stats in summary['language_stats'].items():
            if stats:
                print(f"    {lang.upper()}:")
                print(f"      Avg Duration: {stats['avg_duration']:.2f}s")
                print(f"      Avg Quality: {stats.get('avg_quality_score', 0):.2f}")
        
        print(f"\n  Resource Usage:")
        resources = summary['resource_usage']
        print(f"    CPU: {resources['cpu_percent']:.1f}%")
        print(f"    Memory: {resources['memory_percent']:.1f}% ", end="")
        print(f"({resources['memory_used_gb']:.2f} GB used)")
        
        if resources['gpu_percent'] is not None:
            print(f"    GPU: {resources['gpu_percent']:.1f}%")
            print(f"    GPU Memory: {resources['gpu_memory_used_gb']:.2f} GB")
        
        # Get optimization suggestions
        suggestions = self.monitor.get_optimization_suggestions()
        if suggestions:
            print(f"\n  {Fore.YELLOW}Optimization Suggestions:{Style.RESET_ALL}")
            for suggestion in suggestions:
                print(f"    • {suggestion}")
    
    async def run_all_tests(self):
        """Run all tests"""
        
        start_time = time.time()
        
        # Run tests
        await self.test_language_detection()
        await self.test_preprocessing()
        await self.test_inference()
        await self.test_caching()
        await self.test_performance()
        
        # Display final results
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Test Results Summary{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        total_tests = self.results['passed'] + self.results['failed']
        success_rate = (self.results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n  Total Tests: {total_tests}")
        print(f"  {Fore.GREEN}Passed: {self.results['passed']}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Failed: {self.results['failed']}{Style.RESET_ALL}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Language summary
        print(f"\n  Language Support Status:")
        for lang in ['en', 'es', 'fr', 'pt', 'zh', 'ar']:
            if lang in self.results['languages']:
                lang_data = self.results['languages'][lang]
                if 'inference' in lang_data:
                    status = "✓" if lang_data['inference'].get('passed', False) else "✗"
                    quality = lang_data['inference'].get('quality_score', 0)
                    color = Fore.GREEN if status == "✓" else Fore.RED
                    print(f"    {lang.upper()}: {color}{status}{Style.RESET_ALL} ", end="")
                    print(f"(Quality: {quality:.2f})")
        
        # Errors
        if self.results['errors']:
            print(f"\n  {Fore.RED}Errors:{Style.RESET_ALL}")
            for error in self.results['errors'][:5]:
                print(f"    • {error}")
        
        # Export results
        results_file = f"test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n  Results exported to: {Fore.GREEN}{results_file}{Style.RESET_ALL}")
        
        # Export performance metrics
        metrics_file = self.monitor.export_metrics()
        print(f"  Metrics exported to: {Fore.GREEN}{metrics_file}{Style.RESET_ALL}")
        
        elapsed_time = time.time() - start_time
        print(f"\n  Total test time: {elapsed_time:.2f} seconds")
        
        # Final status
        if success_rate >= 80:
            print(f"\n{Fore.GREEN}✓ All systems operational!{Style.RESET_ALL}")
        elif success_rate >= 60:
            print(f"\n{Fore.YELLOW}⚠ System partially operational{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}✗ System needs attention{Style.RESET_ALL}")

def main():
    """Main entry point"""
    
    # Parse arguments
    model_path = None
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    
    # Create tester
    tester = OfflineMultilingualTester(model_path)
    
    # Run tests
    try:
        asyncio.run(tester.run_all_tests())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Test failed with error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()