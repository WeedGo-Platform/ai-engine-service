#!/usr/bin/env python3
"""
Download Essential Models for WeedGo AI Engine
Downloads and verifies all essential models for multilingual support
"""
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Downloads and verifies AI models"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.models_dir = self.base_dir / "models"
        self.models_catalog = self._get_models_catalog()
        
    def _get_models_catalog(self) -> Dict:
        """Define essential models to download"""
        return {
            "multilingual": [
                {
                    "name": "Qwen 2.5 7B Instruct",
                    "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
                    "url": "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
                    "size_gb": 4.5,
                    "languages": ["en", "zh", "es", "fr", "de", "ja", "ko", "pt", "ru", "ar", "hi", "vi", "th"],
                    "priority": 1
                },
                {
                    "name": "Qwen 2.5 3B Instruct",
                    "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
                    "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
                    "size_gb": 2.0,
                    "languages": ["en", "zh", "es", "fr", "de", "ja", "ko", "pt", "ru"],
                    "priority": 2
                },
                {
                    "name": "Aya 23 8B",
                    "filename": "aya-23-8b-q4_k_m.gguf",
                    "url": "https://huggingface.co/bartowski/aya-23-8B-GGUF/resolve/main/aya-23-8B-Q4_K_M.gguf",
                    "size_gb": 4.5,
                    "languages": ["multilingual", "100+ languages"],
                    "priority": 3
                }
            ],
            "base": [
                {
                    "name": "Llama 3.2 3B Instruct",
                    "filename": "llama-3.2-3b-instruct-q4_k_m.gguf",
                    "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
                    "size_gb": 2.0,
                    "languages": ["en", "es", "fr", "de", "it", "pt"],
                    "priority": 2
                }
            ],
            "small": [
                {
                    "name": "Phi-3.5 Mini Instruct",
                    "filename": "phi-3.5-mini-instruct-q4.gguf",
                    "url": "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
                    "size_gb": 2.2,
                    "languages": ["en"],
                    "priority": 3
                },
                {
                    "name": "TinyLlama 1.1B Chat",
                    "filename": "tinyllama-1.1b-chat-v1.0.q4_k_m.gguf",
                    "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                    "size_gb": 0.7,
                    "languages": ["en"],
                    "priority": 4
                }
            ],
            "embeddings": [
                {
                    "name": "BGE Small EN v1.5",
                    "filename": "bge-small-en-v1.5-q4_k_m.gguf",
                    "url": "https://huggingface.co/BAAI/bge-small-en-v1.5-GGUF/resolve/main/bge-small-en-v1.5-q4_k_m.gguf",
                    "size_gb": 0.1,
                    "languages": ["en"],
                    "priority": 3
                }
            ]
        }
    
    def download_model(self, model_info: Dict, category: str) -> bool:
        """Download a single model with progress bar"""
        target_dir = self.models_dir / category
        target_path = target_dir / model_info["filename"]
        
        # Check if already exists
        if target_path.exists():
            size_mb = target_path.stat().st_size / (1024 * 1024)
            expected_size_mb = model_info["size_gb"] * 1024
            
            if abs(size_mb - expected_size_mb) < 100:  # Within 100MB tolerance
                logger.info(f"✓ {model_info['name']} already exists")
                return True
            else:
                logger.warning(f"⚠ {model_info['name']} exists but size mismatch, re-downloading")
        
        logger.info(f"📥 Downloading {model_info['name']} ({model_info['size_gb']}GB)...")
        
        try:
            # Use wget for more reliable downloads
            cmd = [
                "wget",
                "-c",  # Continue partial downloads
                "-O", str(target_path),
                "--progress=bar:force",
                model_info["url"]
            ]
            
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                logger.info(f"✓ Downloaded {model_info['name']}")
                return True
            else:
                logger.error(f"✗ Failed to download {model_info['name']}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error downloading {model_info['name']}: {e}")
            
            # Fallback to Python requests
            try:
                response = requests.get(model_info["url"], stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(target_path, 'wb') as f:
                    with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            pbar.update(len(chunk))
                            f.write(chunk)
                
                logger.info(f"✓ Downloaded {model_info['name']}")
                return True
                
            except Exception as e2:
                logger.error(f"✗ Fallback download failed: {e2}")
                return False
    
    def verify_model(self, model_path: Path) -> bool:
        """Verify model file is valid GGUF format"""
        try:
            # Check GGUF magic bytes
            with open(model_path, 'rb') as f:
                magic = f.read(4)
                if magic == b'GGUF':
                    return True
            return False
        except Exception as e:
            logger.error(f"Error verifying {model_path}: {e}")
            return False
    
    def download_essential_models(self, categories: Optional[List[str]] = None):
        """Download all essential models"""
        
        if categories is None:
            categories = ["multilingual", "base", "small"]
        
        logger.info("🚀 Starting essential model downloads...")
        logger.info(f"📁 Models directory: {self.models_dir}")
        
        downloaded = []
        failed = []
        
        for category in categories:
            if category not in self.models_catalog:
                logger.warning(f"Unknown category: {category}")
                continue
            
            logger.info(f"\n📂 Downloading {category} models...")
            
            models = sorted(self.models_catalog[category], key=lambda x: x.get("priority", 99))
            
            for model_info in models:
                success = self.download_model(model_info, category)
                
                if success:
                    model_path = self.models_dir / category / model_info["filename"]
                    if self.verify_model(model_path):
                        downloaded.append(f"{category}/{model_info['filename']}")
                    else:
                        failed.append(f"{category}/{model_info['filename']} (invalid format)")
                else:
                    failed.append(f"{category}/{model_info['filename']}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 Download Summary:")
        logger.info(f"✓ Successfully downloaded: {len(downloaded)} models")
        
        if downloaded:
            for model in downloaded:
                logger.info(f"  ✓ {model}")
        
        if failed:
            logger.info(f"✗ Failed: {len(failed)} models")
            for model in failed:
                logger.info(f"  ✗ {model}")
        
        return len(failed) == 0
    
    def list_available_models(self):
        """List all available models in the system"""
        logger.info("\n📦 Available Models:")
        
        total_size = 0
        model_count = 0
        
        for category_dir in sorted(self.models_dir.iterdir()):
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
            
            models = list(category_dir.glob("*.gguf"))
            if models:
                logger.info(f"\n{category_dir.name}/:")
                for model_file in sorted(models):
                    size_gb = model_file.stat().st_size / (1024**3)
                    total_size += size_gb
                    model_count += 1
                    logger.info(f"  • {model_file.name} ({size_gb:.2f}GB)")
        
        logger.info(f"\n📊 Total: {model_count} models, {total_size:.2f}GB")
        
    def update_model_registry(self):
        """Update the model registry with current models"""
        registry_path = self.models_dir / "model_registry.json"
        
        registry = {
            "version": "1.1",
            "models": {},
            "total_size_gb": 0,
            "last_scan": str(Path.cwd())
        }
        
        for category_dir in self.models_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
            
            for model_file in category_dir.glob("*.gguf"):
                model_id = f"{category_dir.name}/{model_file.name}"
                size_gb = model_file.stat().st_size / (1024**3)
                
                # Find model info from catalog
                model_info = None
                if category_dir.name in self.models_catalog:
                    for m in self.models_catalog[category_dir.name]:
                        if m["filename"] == model_file.name:
                            model_info = m
                            break
                
                registry["models"][model_id] = {
                    "path": str(model_file),
                    "category": category_dir.name,
                    "filename": model_file.name,
                    "size_gb": round(size_gb, 2),
                    "languages": model_info.get("languages", ["unknown"]) if model_info else ["unknown"],
                    "verified": self.verify_model(model_file)
                }
                
                registry["total_size_gb"] += size_gb
        
        registry["total_size_gb"] = round(registry["total_size_gb"], 2)
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"✓ Updated model registry: {len(registry['models'])} models")

def main():
    downloader = ModelDownloader()
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Download essential AI models")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--categories", nargs="+", help="Categories to download", 
                       default=["multilingual", "base", "small"])
    parser.add_argument("--all", action="store_true", help="Download all categories")
    
    args = parser.parse_args()
    
    if args.list:
        downloader.list_available_models()
    else:
        categories = list(downloader.models_catalog.keys()) if args.all else args.categories
        success = downloader.download_essential_models(categories)
        
        # Update registry after downloads
        downloader.update_model_registry()
        
        # List what we have
        downloader.list_available_models()
        
        if success:
            logger.info("\n✅ All essential models ready!")
        else:
            logger.info("\n⚠️ Some downloads failed. Run again to retry.")
            sys.exit(1)

if __name__ == "__main__":
    main()