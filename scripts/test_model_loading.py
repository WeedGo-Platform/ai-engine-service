#!/usr/bin/env python3
"""
Test Model Loading and Configuration
Verifies all models are properly configured and can be loaded
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_cpp import Llama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTester:
    """Test model loading and basic functionality"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.models_dir = self.base_dir / "models"
        self.test_results = {}
        
    def discover_models(self) -> Dict[str, List[Path]]:
        """Discover all GGUF models in the models directory"""
        models = {}
        
        for category_dir in sorted(self.models_dir.iterdir()):
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
            
            gguf_files = list(category_dir.glob("*.gguf"))
            if gguf_files:
                models[category_dir.name] = gguf_files
        
        return models
    
    def test_model_loading(self, model_path: Path) -> Dict:
        """Test loading a single model"""
        result = {
            "path": str(model_path),
            "name": model_path.name,
            "category": model_path.parent.name,
            "size_gb": round(model_path.stat().st_size / (1024**3), 2),
            "loadable": False,
            "response_time_ms": None,
            "error": None,
            "capabilities": []
        }
        
        try:
            logger.info(f"📋 Testing {model_path.name}...")
            
            # Try to load with minimal memory
            start_time = time.time()
            model = Llama(
                model_path=str(model_path),
                n_ctx=512,  # Small context for testing
                n_threads=4,
                n_gpu_layers=0,  # CPU only for testing
                verbose=False
            )
            load_time = (time.time() - start_time) * 1000
            
            result["loadable"] = True
            logger.info(f"  ✓ Loaded in {load_time:.0f}ms")
            
            # Test basic inference
            test_prompt = "Hello, what languages do you speak?"
            start_time = time.time()
            response = model(
                test_prompt,
                max_tokens=50,
                temperature=0.7,
                echo=False
            )
            inference_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = round(inference_time, 0)
            
            # Analyze response for language capabilities
            response_text = response.get('choices', [{}])[0].get('text', '').lower()
            
            # Check for language mentions
            languages = {
                "en": ["english"],
                "zh": ["chinese", "mandarin", "中文"],
                "es": ["spanish", "español"],
                "fr": ["french", "français"],
                "de": ["german", "deutsch"],
                "ja": ["japanese", "日本語"],
                "ko": ["korean", "한국어"],
                "ar": ["arabic", "العربية"],
                "pt": ["portuguese", "português"],
                "ru": ["russian", "русский"],
                "hi": ["hindi", "हिंदी"],
                "it": ["italian", "italiano"]
            }
            
            detected_langs = []
            for lang_code, patterns in languages.items():
                if any(p in response_text for p in patterns):
                    detected_langs.append(lang_code)
            
            result["capabilities"] = detected_langs
            
            logger.info(f"  ✓ Inference in {inference_time:.0f}ms")
            logger.info(f"  ✓ Detected language capabilities: {', '.join(detected_langs) if detected_langs else 'Not specified'}")
            
            # Clean up
            del model
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"  ✗ Failed: {e}")
        
        return result
    
    def test_multilingual_capabilities(self, model_path: Path) -> Dict:
        """Test multilingual capabilities of a model"""
        logger.info(f"🌍 Testing multilingual capabilities for {model_path.name}...")
        
        multilingual_tests = {
            "en": "Hello, how are you?",
            "es": "Hola, ¿cómo estás?",
            "zh": "你好，你好吗？",
            "fr": "Bonjour, comment allez-vous?",
            "de": "Hallo, wie geht es dir?",
            "ja": "こんにちは、元気ですか？",
            "ar": "مرحبا، كيف حالك؟",
            "pt": "Olá, como você está?",
            "ru": "Привет, как дела?",
            "ko": "안녕하세요, 어떻게 지내세요?"
        }
        
        results = {"model": model_path.name, "languages": {}}
        
        try:
            # Load model once
            model = Llama(
                model_path=str(model_path),
                n_ctx=1024,
                n_threads=4,
                n_gpu_layers=0,
                verbose=False
            )
            
            for lang_code, prompt in multilingual_tests.items():
                try:
                    start_time = time.time()
                    response = model(
                        prompt,
                        max_tokens=30,
                        temperature=0.7,
                        echo=False
                    )
                    response_time = (time.time() - start_time) * 1000
                    
                    response_text = response.get('choices', [{}])[0].get('text', '')
                    
                    # Simple heuristic: if response is not empty and reasonably coherent
                    is_supported = len(response_text.strip()) > 5
                    
                    results["languages"][lang_code] = {
                        "supported": is_supported,
                        "response_time_ms": round(response_time, 0),
                        "sample_response": response_text[:50] if response_text else None
                    }
                    
                    status = "✓" if is_supported else "✗"
                    logger.info(f"  {status} {lang_code}: {response_time:.0f}ms")
                    
                except Exception as e:
                    results["languages"][lang_code] = {
                        "supported": False,
                        "error": str(e)
                    }
                    logger.error(f"  ✗ {lang_code}: {e}")
            
            # Clean up
            del model
            
        except Exception as e:
            logger.error(f"Failed to test multilingual capabilities: {e}")
            results["error"] = str(e)
        
        return results
    
    def run_all_tests(self):
        """Run all model tests"""
        logger.info("🚀 Starting Model Testing Suite")
        logger.info("="*60)
        
        # Discover models
        models = self.discover_models()
        
        if not models:
            logger.error("No models found!")
            return
        
        total_models = sum(len(files) for files in models.values())
        logger.info(f"Found {total_models} models in {len(models)} categories")
        logger.info("")
        
        # Test each model
        all_results = {}
        
        for category, model_files in models.items():
            logger.info(f"\n📂 Testing {category} models ({len(model_files)} models)")
            logger.info("-"*40)
            
            category_results = []
            
            for model_path in model_files:
                # Skip empty files
                if model_path.stat().st_size < 1000:
                    logger.warning(f"⚠️ Skipping {model_path.name} (empty file)")
                    continue
                
                # Test loading
                result = self.test_model_loading(model_path)
                category_results.append(result)
                
                # Test multilingual for key models
                if category == "multilingual" and result["loadable"]:
                    if "qwen" in model_path.name.lower() or "aya" in model_path.name.lower():
                        multilingual_result = self.test_multilingual_capabilities(model_path)
                        result["multilingual_test"] = multilingual_result
            
            all_results[category] = category_results
        
        # Save results
        self._save_results(all_results)
        
        # Print summary
        self._print_summary(all_results)
    
    def _save_results(self, results: Dict):
        """Save test results to file"""
        output_file = self.models_dir / "model_test_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n📄 Test results saved to {output_file}")
    
    def _print_summary(self, results: Dict):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*60)
        
        total_tested = 0
        total_loaded = 0
        multilingual_models = []
        
        for category, models in results.items():
            loaded = sum(1 for m in models if m["loadable"])
            total = len(models)
            total_tested += total
            total_loaded += loaded
            
            logger.info(f"\n{category.upper()}:")
            logger.info(f"  Tested: {total}")
            logger.info(f"  Loaded: {loaded}")
            logger.info(f"  Success Rate: {(loaded/total*100):.0f}%" if total > 0 else "N/A")
            
            for model in models:
                if model["loadable"]:
                    status = "✓"
                    info = f"{model['response_time_ms']:.0f}ms"
                    
                    if "multilingual_test" in model:
                        lang_count = sum(1 for l in model["multilingual_test"]["languages"].values() 
                                       if l.get("supported"))
                        info += f", {lang_count} languages"
                        if lang_count > 5:
                            multilingual_models.append(model["name"])
                else:
                    status = "✗"
                    info = "Failed to load"
                
                logger.info(f"    {status} {model['name']} ({model['size_gb']}GB) - {info}")
        
        logger.info("\n" + "-"*60)
        logger.info(f"OVERALL: {total_loaded}/{total_tested} models loaded successfully")
        
        if multilingual_models:
            logger.info(f"\n🌍 Multilingual Models (5+ languages):")
            for model in multilingual_models:
                logger.info(f"  • {model}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        
        if total_loaded < total_tested:
            logger.info("  ⚠️ Some models failed to load. Check error logs.")
        
        if not any("qwen" in m["name"].lower() and m["loadable"] 
                  for models in results.values() for m in models):
            logger.info("  ⚠️ No Qwen models loaded - primary multilingual support missing")
        
        if total_loaded == total_tested:
            logger.info("  ✅ All models loaded successfully!")
        
        logger.info("")

def main():
    tester = ModelTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()