#!/usr/bin/env python3
"""
Download Mistral 7B model for WeedGo AI Budtender
Handles permissions and progress better than shell script
"""

import os
import sys
import requests
from tqdm import tqdm
import hashlib

def download_with_progress(url, filename, expected_size_gb=None):
    """Download file with progress bar"""
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    filepath = os.path.join("models", filename)
    
    # Check if already exists
    if os.path.exists(filepath):
        print(f"✅ {filename} already exists!")
        return True
    
    print(f"📥 Downloading {filename}...")
    if expected_size_gb:
        print(f"   Expected size: ~{expected_size_gb}GB")
    
    try:
        # Start download
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get total file size
        total_size = int(response.headers.get('content-length', 0))
        
        # Download with progress bar
        with open(filepath, 'wb') as file:
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=filename) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = file.write(chunk)
                    pbar.update(size)
        
        print(f"✅ Successfully downloaded {filename}")
        
        # Set proper permissions
        os.chmod(filepath, 0o644)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        # Clean up partial file
        if os.path.exists(filepath):
            os.remove(filepath)
        return False
    except KeyboardInterrupt:
        print("\n⚠️ Download cancelled by user")
        # Clean up partial file
        if os.path.exists(filepath):
            os.remove(filepath)
        sys.exit(1)

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     WeedGo Model Downloader - Mistral 7B               ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    models = {
        "1": {
            "name": "Mistral 7B Instruct v0.2 (Recommended)",
            "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "size": 4.1
        },
        "2": {
            "name": "Mistral 7B Instruct v0.1",
            "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            "filename": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            "size": 4.1
        },
        "3": {
            "name": "Mistral 7B OpenOrca (Fine-tuned)",
            "url": "https://huggingface.co/TheBloke/Mistral-7B-OpenOrca-GGUF/resolve/main/mistral-7b-openorca.Q4_K_M.gguf",
            "filename": "mistral-7b-openorca.Q4_K_M.gguf",
            "size": 4.1
        }
    }
    
    print("Available Mistral models:")
    for key, model in models.items():
        print(f"{key}. {model['name']} (~{model['size']}GB)")
    
    print("\nWhich model would you like to download?")
    choice = input("Enter choice (1-3) or 'all' for all models: ").strip()
    
    if choice == 'all':
        for model in models.values():
            success = download_with_progress(
                model['url'],
                model['filename'],
                model['size']
            )
            if not success:
                print(f"⚠️ Failed to download {model['name']}")
                break
    elif choice in models:
        model = models[choice]
        success = download_with_progress(
            model['url'],
            model['filename'],
            model['size']
        )
        if success:
            print(f"""
    ✅ Download Complete!
    
    Model: {model['name']}
    Location: models/{model['filename']}
    
    To use this model:
    1. Update multi_model_budtender.py if using different version
    2. Run: python3 multi-model-api.py
    3. The model will load automatically
            """)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    # Show all downloaded models
    print("\n📊 Downloaded models:")
    if os.path.exists("models"):
        for file in os.listdir("models"):
            if file.endswith(".gguf"):
                size = os.path.getsize(os.path.join("models", file)) / (1024**3)
                print(f"  • {file} ({size:.1f}GB)")

if __name__ == "__main__":
    # Check if tqdm is installed
    try:
        import tqdm
    except ImportError:
        print("Installing required package: tqdm")
        os.system("pip3 install tqdm --quiet")
        print("Please run the script again")
        sys.exit(1)
    
    main()