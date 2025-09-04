#!/usr/bin/env python3
"""
Download Qwen 2.5 7B model for multilingual support
Handles Chinese, Arabic, Japanese, Korean excellently
"""
import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm
import hashlib

def download_file(url: str, dest_path: Path, expected_size: int = None):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    if expected_size and total_size != expected_size:
        print(f"Warning: File size mismatch. Expected {expected_size}, got {total_size}")
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dest_path, 'wb') as file:
        with tqdm(total=total_size, unit='iB', unit_scale=True, desc=dest_path.name) as pbar:
            for data in response.iter_content(chunk_size=1024*1024):
                size = file.write(data)
                pbar.update(size)
    
    return dest_path

def verify_checksum(file_path: Path, expected_checksum: str = None):
    """Verify file checksum"""
    if not expected_checksum:
        return True
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual = sha256_hash.hexdigest()
    if actual != expected_checksum:
        print(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual}")
        return False
    return True

def main():
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models" / "multilingual"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Qwen 2.5 7B Instruct Q4_K_M (Best balance of quality and size)
    models = [
        {
            "name": "Qwen 2.5 7B Instruct (Q4_K_M)",
            "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
            "size": 4_920_000_000,  # ~4.9GB
            "languages": ["Chinese", "Arabic", "Japanese", "Korean", "English", "Spanish", "French", "Portuguese"],
            "description": "Excellent multilingual support, especially for Asian languages"
        },
        {
            "name": "Qwen 2.5 3B Instruct (Q4_K_M) - Smaller Alternative",
            "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
            "size": 2_020_000_000,  # ~2GB
            "languages": ["Chinese", "Arabic", "Japanese", "Korean", "English"],
            "description": "Smaller but still capable multilingual model"
        }
    ]
    
    print("🌍 Qwen 2.5 Multilingual Model Downloader")
    print("=" * 50)
    
    for i, model in enumerate(models, 1):
        print(f"\n{i}. {model['name']}")
        print(f"   Size: {model['size'] / 1_000_000_000:.1f} GB")
        print(f"   Languages: {', '.join(model['languages'])}")
        print(f"   Description: {model['description']}")
    
    print("\n0. Download all")
    print("q. Quit")
    
    choice = input("\nSelect model to download (1-2, 0 for all, q to quit): ").strip()
    
    if choice.lower() == 'q':
        return
    
    if choice == '0':
        selected_models = models
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected_models = [models[idx]]
            else:
                print("Invalid selection")
                return
        except ValueError:
            print("Invalid input")
            return
    
    for model in selected_models:
        dest_path = models_dir / model['filename']
        
        if dest_path.exists():
            print(f"\n✓ {model['filename']} already exists")
            overwrite = input("Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                continue
        
        print(f"\n📥 Downloading {model['name']}...")
        print(f"URL: {model['url']}")
        print(f"Destination: {dest_path}")
        
        try:
            download_file(model['url'], dest_path, model['size'])
            print(f"✅ Successfully downloaded {model['filename']}")
            
            # Update configuration
            update_config(model['filename'])
            
        except Exception as e:
            print(f"❌ Error downloading {model['filename']}: {e}")
            if dest_path.exists():
                dest_path.unlink()  # Clean up partial download

def update_config(model_filename: str):
    """Update the multilingual configuration to use the new model"""
    config_path = Path(__file__).parent.parent / "config" / "multilingual_models.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    
    config = {
        "models": {
            "qwen": {
                "path": f"models/multilingual/{model_filename}",
                "languages": ["zh", "ar", "ja", "ko"],
                "context_size": 4096,
                "gpu_layers": 35,
                "threads": 8
            },
            "mistral": {
                "path": "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                "languages": ["en", "es", "fr", "pt"],
                "context_size": 4096,
                "gpu_layers": 35,
                "threads": 8
            }
        },
        "language_routing": {
            "en": "mistral",
            "es": "mistral",
            "fr": "mistral",
            "pt": "mistral",
            "zh": "qwen",
            "ar": "qwen",
            "ja": "qwen",
            "ko": "qwen"
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Updated configuration to use {model_filename}")

if __name__ == "__main__":
    main()