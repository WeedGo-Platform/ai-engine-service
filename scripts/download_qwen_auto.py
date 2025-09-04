#!/usr/bin/env python3
"""
Automated download script for Qwen2.5 models
Non-interactive version for direct model download
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_qwen_model(model_size="0.5b"):
    """Download Qwen model automatically"""
    
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models" / "multilingual"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Model configurations
    models = {
        "0.5b": {
            "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
            "size": "~400MB"
        },
        "1.5b": {
            "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "size": "~1GB"
        },
        "3b": {
            "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
            "size": "~2GB"
        }
    }
    
    if model_size not in models:
        logger.error(f"Invalid model size: {model_size}. Choose from: {list(models.keys())}")
        return False
    
    model_info = models[model_size]
    output_path = models_dir / model_info["filename"]
    
    if output_path.exists():
        logger.info(f"Model already exists: {output_path}")
        return True
    
    logger.info(f"📥 Downloading Qwen2.5-{model_size.upper()} ({model_info['size']})")
    logger.info(f"URL: {model_info['url']}")
    logger.info(f"Destination: {output_path}")
    
    try:
        response = requests.get(model_info['url'], stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc="Downloading") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"✅ Successfully downloaded: {output_path}")
        
        # Update the config
        update_config(model_info["filename"])
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return False
    except KeyboardInterrupt:
        logger.info("\nDownload cancelled by user")
        if output_path.exists():
            output_path.unlink()
        return False

def update_config(model_filename: str):
    """Update the multilingual config to use the downloaded model"""
    import json
    
    base_dir = Path(__file__).parent.parent
    config_dir = base_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / "multilingual_models.json"
    
    config = {
        "models": {
            "qwen": {
                "path": f"models/multilingual/{model_filename}",
                "languages": ["zh", "ar", "ja", "ko"],
                "context_size": 2048,
                "gpu_layers": 20,
                "threads": 4,
                "temperature": 0.7,
                "max_tokens": 256
            },
            "mistral": {
                "path": "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                "languages": ["en", "es", "fr", "pt"],
                "context_size": 4096,
                "gpu_layers": 35,
                "threads": 8,
                "temperature": 0.7,
                "max_tokens": 512
            }
        },
        "language_routing": {
            "zh": "qwen",
            "zh-cn": "qwen",
            "zh-tw": "qwen",
            "ar": "qwen",
            "ja": "qwen",
            "ko": "qwen",
            "en": "mistral",
            "es": "mistral",
            "fr": "mistral",
            "pt": "mistral"
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📝 Updated config: {config_path}")

def main():
    parser = argparse.ArgumentParser(description='Download Qwen multilingual model')
    parser.add_argument('--size', choices=['0.5b', '1.5b', '3b'], default='0.5b',
                        help='Model size to download (default: 0.5b)')
    args = parser.parse_args()
    
    print("\n🌏 Qwen Model Downloader")
    print("=" * 50)
    
    success = download_qwen_model(args.size)
    
    if success:
        print("\n✅ Download complete!")
        print("\n📌 Next steps:")
        print("1. Restart the AI service to load the new model")
        print("2. Test Chinese queries through the API")
    else:
        print("\n❌ Download failed. Please check your internet connection and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()