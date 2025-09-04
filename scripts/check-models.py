#!/usr/bin/env python3
"""
Check status of downloaded models
"""

import os
import time

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}TB"

def check_models():
    """Check status of all models"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     WeedGo AI Models Status                            ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    models_info = {
        "llama-2-7b-chat.Q4_K_M.gguf": {
            "name": "Llama 2 7B Chat",
            "expected_size": 3.8 * 1024**3,  # 3.8GB
            "purpose": "General conversation, reasoning"
        },
        "mistral-7b-instruct-v0.2.Q4_K_M.gguf": {
            "name": "Mistral 7B Instruct",
            "expected_size": 4.1 * 1024**3,  # 4.1GB
            "purpose": "Medical queries, technical content"
        }
    }
    
    if not os.path.exists("models"):
        print("❌ Models directory not found")
        return
    
    total_size = 0
    models_found = []
    
    for filename, info in models_info.items():
        filepath = os.path.join("models", filename)
        
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size
            completion = (size / info["expected_size"]) * 100
            
            if completion >= 99:  # Allow 1% variance
                status = "✅ Ready"
                emoji = "🟢"
            elif completion > 10:
                status = f"⏳ Downloading... {completion:.1f}%"
                emoji = "🟡"
            else:
                status = "❌ Not found or corrupted"
                emoji = "🔴"
            
            models_found.append(filename)
            
            print(f"{emoji} {info['name']}")
            print(f"   File: {filename}")
            print(f"   Size: {format_size(size)} / {format_size(info['expected_size'])}")
            print(f"   Status: {status}")
            print(f"   Purpose: {info['purpose']}")
            print()
        else:
            print(f"🔴 {info['name']}")
            print(f"   Status: Not downloaded")
            print(f"   To download: python3 download-mistral.py")
            print()
    
    # Summary
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   Models installed: {len(models_found)}/2")
    print(f"   Total disk usage: {format_size(total_size)}")
    
    if len(models_found) == 2:
        print(f"   Status: ✅ All models ready!")
        print(f"\n🚀 You can now run: python3 multi-model-api.py")
    elif len(models_found) == 1:
        print(f"   Status: ⚠️ Running with single model")
        print(f"\n💡 Download Mistral for dual-model capability")
    else:
        print(f"   Status: ❌ No models found")
        print(f"\n📥 Run download scripts to get started")
    
    # Check if download is in progress
    for filename in os.listdir("models"):
        if filename.endswith(".gguf"):
            filepath = os.path.join("models", filename)
            initial_size = os.path.getsize(filepath)
            time.sleep(2)
            current_size = os.path.getsize(filepath)
            
            if current_size > initial_size:
                speed = (current_size - initial_size) / 2  # bytes per second
                print(f"\n⏬ Active download detected: {filename}")
                print(f"   Speed: {format_size(speed)}/s")
                if speed > 0:
                    remaining = (4.1 * 1024**3 - current_size) / speed
                    print(f"   ETA: {remaining/60:.1f} minutes")

if __name__ == "__main__":
    check_models()