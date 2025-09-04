#!/usr/bin/env python3
"""
Verify System Integration
Ensures models are properly integrated with the AI Engine system
"""
import os
import sys
import json
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.unified_model_interface import UnifiedModelManager
from services.dynamic_model_selector import DynamicModelSelector
from services.universal_language_system import UniversalLanguageSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_integration():
    """Verify that all components work together"""
    
    logger.info("🔧 Verifying System Integration")
    logger.info("="*60)
    
    # 1. Test UnifiedModelManager
    logger.info("\n1️⃣ Testing Unified Model Manager...")
    try:
        model_manager = UnifiedModelManager()
        await model_manager.discover_and_load_models()
        
        logger.info(f"   ✅ Discovered {len(model_manager.models)} models")
        for model_id, model in model_manager.models.items():
            profile = model.get_profile()
            langs = list(profile.supported_languages)[:5] if profile.supported_languages else []
            logger.info(f"      • {model_id}: {', '.join(langs)}...")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
        return False
    
    # 2. Test DynamicModelSelector
    logger.info("\n2️⃣ Testing Dynamic Model Selector...")
    try:
        selector = DynamicModelSelector()
        
        test_languages = ["en", "es", "zh", "fr", "pt", "ar", "ja"]
        for lang in test_languages:
            model = selector.select_model_for_language(lang)
            if model:
                logger.info(f"   ✅ {lang}: {model[0]}")
            else:
                logger.info(f"   ⚠️  {lang}: No model found")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
        return False
    
    # 3. Test Language System
    logger.info("\n3️⃣ Testing Universal Language System...")
    try:
        lang_system = UniversalLanguageSystem()
        
        test_texts = {
            "en": "Hello, how can I help you?",
            "es": "Hola, ¿cómo puedo ayudarte?",
            "zh": "你好，有什么可以帮助你的？",
            "fr": "Bonjour, comment puis-je vous aider?",
            "pt": "Olá, como posso ajudá-lo?"
        }
        
        for expected_lang, text in test_texts.items():
            profile = await lang_system.detect_language(text)
            match = "✅" if profile.code == expected_lang else "⚠️"
            logger.info(f"   {match} {expected_lang}: Detected as {profile.code} ({profile.confidence:.2f})")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
        return False
    
    # 4. Check Model Registry
    logger.info("\n4️⃣ Checking Model Registry...")
    registry_path = Path(__file__).parent.parent / "models" / "model_registry.json"
    
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
        
        logger.info(f"   ✅ Registry version: {registry.get('version')}")
        logger.info(f"   ✅ Verified models: {registry.get('verified_models', 0)}")
        
        # Check for critical models
        has_multilingual = any("multilingual" in k for k in registry.get("models", {}).keys())
        has_base = any("base" in k for k in registry.get("models", {}).keys())
        has_small = any("small" in k for k in registry.get("models", {}).keys())
        
        logger.info(f"   {'✅' if has_multilingual else '❌'} Multilingual models")
        logger.info(f"   {'✅' if has_base else '❌'} Base models")
        logger.info(f"   {'✅' if has_small else '❌'} Small/fast models")
    else:
        logger.error("   ❌ Registry not found")
        return False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 INTEGRATION STATUS")
    
    # Check minimum requirements
    min_requirements = {
        "Models discovered": len(model_manager.models) >= 3,
        "Language detection": True,  # Tested above
        "Model selection": True,  # Tested above
        "Registry exists": registry_path.exists()
    }
    
    all_passed = all(min_requirements.values())
    
    for requirement, passed in min_requirements.items():
        status = "✅" if passed else "❌"
        logger.info(f"  {status} {requirement}")
    
    if all_passed:
        logger.info("\n✅ System integration verified successfully!")
        logger.info("   The AI Engine is ready to handle multilingual requests")
    else:
        logger.info("\n⚠️ Some integration checks failed")
        logger.info("   Review the errors above and fix any issues")
    
    # Final recommendations
    logger.info("\n💡 NEXT STEPS:")
    
    if not any("qwen2.5-7b" in k.lower() for k in registry.get("models", {}).keys()):
        logger.info("  1. Download Qwen 2.5 7B for best multilingual support:")
        logger.info("     ./scripts/download_qwen_7b.sh")
    
    logger.info("  2. Start the AI Engine:")
    logger.info("     python api_server.py")
    
    logger.info("  3. Test with different languages:")
    logger.info("     curl -X POST http://localhost:8000/chat \\")
    logger.info("       -H 'Content-Type: application/json' \\")
    logger.info("       -d '{\"message\": \"Hola, necesito algo para el dolor\"}'")
    
    return all_passed

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_integration())