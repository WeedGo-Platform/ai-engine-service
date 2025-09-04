#!/usr/bin/env python3
"""
Quick Model Verification
Fast check that models are valid and can be loaded
"""
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_models():
    """Quick check of all models"""
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    
    logger.info("🔍 Quick Model Check")
    logger.info("="*60)
    
    model_status = {
        "verified": [],
        "missing": [],
        "invalid": []
    }
    
    # Check each category
    for category_dir in sorted(models_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue
        
        gguf_files = list(category_dir.glob("*.gguf"))
        
        if gguf_files:
            logger.info(f"\n📂 {category_dir.name}/")
            
            for model_file in sorted(gguf_files):
                size_gb = model_file.stat().st_size / (1024**3)
                
                # Check if valid GGUF
                try:
                    with open(model_file, 'rb') as f:
                        magic = f.read(4)
                        is_valid = magic == b'GGUF'
                except:
                    is_valid = False
                
                if size_gb < 0.001:
                    status = "❌ Empty"
                    model_status["invalid"].append(str(model_file))
                elif not is_valid:
                    status = "⚠️  Invalid"
                    model_status["invalid"].append(str(model_file))
                else:
                    status = "✅ Valid"
                    model_status["verified"].append(str(model_file))
                
                logger.info(f"  {status} {model_file.name} ({size_gb:.2f}GB)")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 SUMMARY")
    logger.info(f"✅ Valid models: {len(model_status['verified'])}")
    logger.info(f"❌ Invalid/Empty: {len(model_status['invalid'])}")
    
    # Critical models check
    logger.info("\n🎯 Critical Models Status:")
    
    critical_models = {
        "Mistral 7B": "mistral-7b",
        "Qwen 2.5 (Any)": "qwen2.5",
        "TinyLlama": "tinyllama"
    }
    
    for name, pattern in critical_models.items():
        found = any(pattern in str(m).lower() for m in model_status["verified"])
        status = "✅" if found else "❌"
        logger.info(f"  {status} {name}: {'Found' if found else 'Missing'}")
    
    # Recommendations
    logger.info("\n💡 RECOMMENDATIONS:")
    
    # Check for Qwen 7B specifically
    has_qwen_7b = any("qwen2.5-7b" in str(m).lower() and m in model_status["verified"] 
                      for m in model_status["verified"])
    
    if not has_qwen_7b:
        logger.info("  ⚠️  Qwen 2.5 7B not found - Primary multilingual model missing")
        logger.info("     Run: ./scripts/download_qwen_7b.sh")
    
    # Check for any multilingual model
    multilingual_models = [m for m in model_status["verified"] 
                          if "multilingual" in str(m) or "qwen" in str(m).lower()]
    
    if len(multilingual_models) < 2:
        logger.info("  ⚠️  Limited multilingual support")
        logger.info("     Run: python scripts/download_essential_models.py --categories multilingual")
    
    if model_status["invalid"]:
        logger.info(f"  ⚠️  {len(model_status['invalid'])} invalid/empty files found")
        for file in model_status["invalid"]:
            logger.info(f"     Remove: {file}")
    
    if len(model_status["verified"]) >= 3:
        logger.info("  ✅ Minimum models available for operation")
    
    # Update registry
    registry_path = models_dir / "model_registry.json"
    registry_data = {
        "version": "1.2",
        "verified_models": len(model_status["verified"]),
        "models": {}
    }
    
    for model_path in model_status["verified"]:
        model_path = Path(model_path)
        category = model_path.parent.name
        
        registry_data["models"][f"{category}/{model_path.name}"] = {
            "path": str(model_path),
            "category": category,
            "size_gb": round(model_path.stat().st_size / (1024**3), 2),
            "status": "verified"
        }
    
    with open(registry_path, 'w') as f:
        json.dump(registry_data, f, indent=2)
    
    logger.info(f"\n✅ Registry updated: {registry_path}")
    
    return len(model_status["verified"]) > 0

if __name__ == "__main__":
    check_models()