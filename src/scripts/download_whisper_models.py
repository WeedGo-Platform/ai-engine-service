#!/usr/bin/env python3
"""
Download Whisper models for offline use
"""
import os
import sys
import ssl
import urllib.request
import whisper
import logging
from pathlib import Path

# Handle SSL certificate issues
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_whisper_models():
    """Download Whisper models to local directory"""
    models_to_download = ["tiny", "base", "small"]
    models_dir = Path("models/voice/whisper")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Set cache directory to our models directory
    os.environ['XDG_CACHE_HOME'] = str(models_dir.parent.parent.parent.absolute())
    
    for model_name in models_to_download:
        logger.info(f"Downloading Whisper {model_name} model...")
        try:
            # This will download the model to the cache directory
            model = whisper.load_model(model_name, download_root=str(models_dir.absolute()))
            logger.info(f"✅ Successfully downloaded {model_name} model")
            
            # Get model info
            n_params = sum(p.numel() for p in model.parameters())
            logger.info(f"   Model parameters: {n_params:,}")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {model_name}: {e}")
            sys.exit(1)
    
    # List downloaded files
    logger.info("\n📁 Downloaded model files:")
    for file in models_dir.rglob("*.pt"):
        size_mb = file.stat().st_size / (1024 * 1024)
        logger.info(f"   {file.name}: {size_mb:.1f} MB")

if __name__ == "__main__":
    download_whisper_models()