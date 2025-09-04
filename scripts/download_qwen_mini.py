#!/usr/bin/env python3
"""
Download script for Qwen2.5-3B-Instruct (smaller version for testing)
This is a more manageable model size for quick testing
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_qwen_mini():
    """Download Qwen2.5-3B-Instruct GGUF (smaller, faster model)"""
    
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models" / "multilingual"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Qwen2.5-3B is smaller and faster for testing
    # Using Q4_K_M quantization for balance of quality and size
    models = {
        "qwen2.5-3b": {
            "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
            "size": "~2GB"
        },
        "qwen2.5-1.5b": {
            "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf", 
            "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "size": "~1GB"
        },
        "qwen2.5-0.5b": {
            "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
            "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
            "size": "~400MB"
        }
    }
    
    print("\n🌏 Qwen Model Downloader")
    print("=" * 50)
    print("\nAvailable models:")
    print("1. Qwen2.5-3B (2GB) - Good quality, moderate size")
    print("2. Qwen2.5-1.5B (1GB) - Balanced")
    print("3. Qwen2.5-0.5B (400MB) - Smallest, fastest")
    
    choice = input("\nSelect model to download (1-3): ").strip()
    
    if choice == "1":
        model_key = "qwen2.5-3b"
    elif choice == "2":
        model_key = "qwen2.5-1.5b"
    elif choice == "3":
        model_key = "qwen2.5-0.5b"
    else:
        print("Invalid choice")
        return False
    
    model_info = models[model_key]
    output_path = models_dir / model_info["filename"]
    
    if output_path.exists():
        logger.info(f"Model already exists: {output_path}")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            return True
    
    print(f"\n📥 Downloading {model_key} ({model_info['size']})...")
    print(f"URL: {model_info['url']}")
    print(f"Destination: {output_path}")
    
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
        
        print(f"\n✅ Successfully downloaded: {output_path}")
        
        # Update the config to use this model
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
                "context_size": 2048,  # Smaller for mini models
                "gpu_layers": 20,  # Less layers for smaller model
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
    
    print(f"📝 Updated config: {config_path}")

def test_chinese_generation():
    """Quick test of Chinese generation"""
    try:
        from llama_cpp import Llama
        import json
        
        base_dir = Path(__file__).parent.parent
        config_path = base_dir / "config" / "multilingual_models.json"
        
        if not config_path.exists():
            print("Config not found")
            return
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        model_path = base_dir / config["models"]["qwen"]["path"]
        
        if not model_path.exists():
            print(f"Model not found: {model_path}")
            return
        
        print("\n🧪 Testing Chinese generation...")
        print(f"Loading model: {model_path}")
        
        model = Llama(
            model_path=str(model_path),
            n_ctx=1024,
            n_threads=4,
            n_gpu_layers=0,  # CPU only for testing
            verbose=False
        )
        
        # Test query
        query = "最高THC含量的产品是什么？"
        
        prompt = f"""<|im_start|>system
你是一个大麻产品顾问。用中文回答问题。
<|im_end|>
<|im_start|>user
{query}
<|im_end|>
<|im_start|>assistant
"""
        
        print(f"\n💬 Query: {query}")
        print("🤖 Generating response...")
        
        response = model(
            prompt,
            max_tokens=128,
            temperature=0.7,
            stop=["<|im_end|>"],
            echo=False
        )
        
        answer = response['choices'][0]['text'].strip()
        print(f"\n✅ Response: {answer}")
        
        return True
        
    except ImportError:
        print("⚠️  llama-cpp-python not installed")
        print("Install with: pip install llama-cpp-python")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = download_qwen_mini()
    
    if success:
        print("\n" + "=" * 50)
        test = input("\nTest Chinese generation? (y/n): ").strip().lower()
        if test == 'y':
            test_chinese_generation()
        
        print("\n📌 Next steps:")
        print("1. Restart the AI service: pkill -f 'python api_server.py' && python api_server.py")
        print("2. Test Chinese queries through the API")
        print("3. Check the admin dashboard chat interface")
    else:
        print("\n❌ Download failed. Please check your internet connection and try again.")