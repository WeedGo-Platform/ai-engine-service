#!/usr/bin/env python3
"""
Download latest LLM models including Llama 3, Mistral, and others
Supports hot-swapping models at runtime
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
import requests
import json
from typing import Dict, List, Optional
from urllib.parse import urlparse
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Latest model configurations (December 2024)
LATEST_MODELS = {
    "llama3": {
        "8b": {
            "name": "llama-3.1-8b-instruct-q4_k_m.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "size": "4.9GB",
            "description": "Llama 3.1 8B - Latest from Meta, excellent reasoning",
            "capabilities": ["chat", "reasoning", "code", "multilingual"]
        },
        "70b_v33": {
            "name": "Llama-3.3-70B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF/resolve/main/Llama-3.3-70B-Instruct-Q4_K_M.gguf",
            "size": "42.5GB",
            "description": "Llama 3.3 70B - Matches 405B performance at 1/6 size!",
            "capabilities": ["chat", "reasoning", "code", "analysis", "multilingual", "tool_use"]
        }
    },
    "mistral": {
        "7b_v0.3": {
            "name": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
            "url": "https://huggingface.co/MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
            "size": "4.1GB",
            "description": "Mistral 7B v0.3 - Latest version with improved performance",
            "capabilities": ["chat", "reasoning", "function_calling"]
        },
        "mixtral_8x7b": {
            "name": "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
            "size": "26GB",
            "description": "Mixtral 8x7B - MoE architecture for efficiency",
            "capabilities": ["chat", "reasoning", "code", "multilingual", "function_calling"]
        }
    },
    "phi": {
        "3_mini": {
            "name": "Phi-3-mini-4k-instruct.Q4_K_M.gguf",
            "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
            "size": "2.3GB",
            "description": "Phi-3 Mini - Small but capable model from Microsoft",
            "capabilities": ["chat", "reasoning", "code"]
        }
    },
    "qwen": {
        "2.5_7b": {
            "name": "qwen2.5-7b-instruct-q4_k_m.gguf",
            "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
            "size": "4.4GB",
            "description": "Qwen 2.5 7B - Excellent multilingual support",
            "capabilities": ["chat", "reasoning", "multilingual", "code"]
        },
        "2.5_14b": {
            "name": "qwen2.5-14b-instruct-q4_k_m.gguf",
            "url": "https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf",
            "size": "8.9GB",
            "description": "Qwen 2.5 14B - Larger multilingual model",
            "capabilities": ["chat", "reasoning", "multilingual", "code", "analysis"]
        }
    },
    "gemma": {
        "2_9b": {
            "name": "gemma-2-9b-it.Q4_K_M.gguf",
            "url": "https://huggingface.co/google/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it.Q4_K_M.gguf",
            "size": "5.5GB",
            "description": "Gemma 2 9B - Google's efficient model",
            "capabilities": ["chat", "reasoning", "code"]
        }
    },
    "qwq": {
        "32b_preview": {
            "name": "QwQ-32B-Preview-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/QwQ-32B-Preview-GGUF/resolve/main/QwQ-32B-Preview-Q4_K_M.gguf",
            "size": "18.5GB",
            "description": "QwQ 32B - Best reasoning model, beats 70B+ models!",
            "capabilities": ["math", "reasoning", "logic", "problem_solving"]
        }
    },
    "deepseek": {
        "coder_6.7b": {
            "name": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
            "size": "4.0GB",
            "description": "DeepSeek Coder 6.7B - Specialized for code generation",
            "capabilities": ["code", "reasoning", "analysis"]
        }
    }
}

class ModelDownloader:
    def __init__(self, base_dir: str = "models"):
        self.base_dir = Path(base_dir)
        self.base_model_dir = self.base_dir / "base"
        self.multilingual_dir = self.base_dir / "multilingual"
        self.specialized_dir = self.base_dir / "specialized"
        
        # Create directories
        for dir_path in [self.base_model_dir, self.multilingual_dir, self.specialized_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, dest_path: Path, expected_size: str = None) -> bool:
        """Download a file with progress tracking"""
        try:
            logger.info(f"Downloading {dest_path.name}")
            logger.info(f"URL: {url}")
            if expected_size:
                logger.info(f"Expected size: {expected_size}")
            
            # Use wget or curl for better progress tracking
            if subprocess.run(["which", "wget"], capture_output=True).returncode == 0:
                cmd = ["wget", "-c", "-O", str(dest_path), url]
            else:
                cmd = ["curl", "-L", "-o", str(dest_path), "-C", "-", url]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd)
            
            if result.returncode == 0 and dest_path.exists():
                actual_size = dest_path.stat().st_size / (1024**3)  # GB
                logger.info(f"✓ Downloaded {dest_path.name} ({actual_size:.2f}GB)")
                return True
            else:
                logger.error(f"Failed to download {dest_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def download_model(self, model_category: str, model_variant: str) -> bool:
        """Download a specific model"""
        if model_category not in LATEST_MODELS:
            logger.error(f"Unknown model category: {model_category}")
            return False
        
        if model_variant not in LATEST_MODELS[model_category]:
            logger.error(f"Unknown variant: {model_variant}")
            return False
        
        model_info = LATEST_MODELS[model_category][model_variant]
        
        # Determine destination directory
        if "multilingual" in model_info.get("capabilities", []):
            dest_dir = self.multilingual_dir
        elif "specialized" in model_category:
            dest_dir = self.specialized_dir
        else:
            dest_dir = self.base_model_dir
        
        dest_path = dest_dir / model_info["name"]
        
        # Check if already exists
        if dest_path.exists():
            logger.info(f"✓ Model already exists: {dest_path}")
            return True
        
        # Download
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading: {model_info['description']}")
        logger.info(f"{'='*60}")
        
        success = self.download_file(
            model_info["url"],
            dest_path,
            model_info.get("size")
        )
        
        if success:
            # Create metadata file
            metadata = {
                "name": model_info["name"],
                "category": model_category,
                "variant": model_variant,
                "capabilities": model_info.get("capabilities", []),
                "description": model_info["description"],
                "path": str(dest_path),
                "downloaded_at": str(dest_path.stat().st_ctime)
            }
            
            metadata_path = dest_path.with_suffix(".json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✓ Metadata saved to {metadata_path}")
        
        return success
    
    def download_all_essential(self):
        """Download essential models for the cannabis AI system"""
        essential_models = [
            ("llama3", "8b"),      # Main reasoning model
            ("mistral", "7b_v0.3"), # Fast inference
            ("qwen", "2.5_7b"),    # Multilingual support
            ("phi", "3_mini"),     # Lightweight fallback
            ("qwq", "32b_preview"), # Math & reasoning champion
            ("deepseek", "coder_6.7b") # Specialized code generation
        ]
        
        logger.info("\n" + "="*60)
        logger.info("DOWNLOADING ESSENTIAL MODELS FOR CANNABIS AI")
        logger.info("="*60)
        
        success_count = 0
        for category, variant in essential_models:
            if self.download_model(category, variant):
                success_count += 1
        
        logger.info(f"\n✓ Downloaded {success_count}/{len(essential_models)} essential models")
        return success_count == len(essential_models)

def create_hot_swap_config():
    """Create configuration for hot-swappable models"""
    config = {
        "hot_swap": {
            "enabled": True,
            "default_model": "llama3_8b",
            "fallback_model": "phi_3_mini",
            "models": {
                "llama3_8b": {
                    "path": "models/base/llama-3.1-8b-instruct-q4_k_m.gguf",
                    "context_size": 8192,
                    "gpu_layers": 35,
                    "temperature": 0.7
                },
                "mistral_7b": {
                    "path": "models/base/mistral-7b-instruct-v0.3.Q4_K_M.gguf",
                    "context_size": 32768,
                    "gpu_layers": 35,
                    "temperature": 0.7
                },
                "qwen_7b": {
                    "path": "models/multilingual/qwen2.5-7b-instruct-q4_k_m.gguf",
                    "context_size": 32768,
                    "gpu_layers": 35,
                    "temperature": 0.7
                },
                "phi_mini": {
                    "path": "models/base/Phi-3-mini-4k-instruct.Q4_K_M.gguf",
                    "context_size": 4096,
                    "gpu_layers": 20,
                    "temperature": 0.7
                }
            },
            "swap_conditions": {
                "memory_threshold_gb": 4,
                "latency_threshold_ms": 1000,
                "error_threshold": 3
            }
        }
    }
    
    config_path = Path("config/model_hot_swap.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✓ Hot-swap configuration saved to {config_path}")
    return config_path

def main():
    logger.info("="*60)
    logger.info("CANNABIS AI MODEL UPDATER")
    logger.info("="*60)
    
    downloader = ModelDownloader()
    
    # Check available space
    import shutil
    free_gb = shutil.disk_usage("/").free / (1024**3)
    logger.info(f"Available disk space: {free_gb:.2f}GB")
    
    if free_gb < 50:
        logger.warning("⚠️  Low disk space! At least 50GB recommended for all models")
    
    # Download essential models
    if downloader.download_all_essential():
        logger.info("\n✅ Essential models downloaded successfully!")
    else:
        logger.error("\n❌ Some models failed to download")
        
    # Create hot-swap configuration
    create_hot_swap_config()
    
    logger.info("\n" + "="*60)
    logger.info("✅ MODEL SETUP COMPLETE")
    logger.info("Models are ready for hot-swapping!")
    logger.info("="*60)

if __name__ == "__main__":
    main()