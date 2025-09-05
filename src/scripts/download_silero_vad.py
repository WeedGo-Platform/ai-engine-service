#!/usr/bin/env python3
"""
Download Silero VAD model for Voice Activity Detection
"""
import os
import ssl
import torch
import logging
import urllib.request
from pathlib import Path

# Handle SSL certificate issues
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_silero_vad():
    """Download Silero VAD model"""
    models_dir = Path("models/voice/silero")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Downloading Silero VAD model...")
    
    try:
        # Download the Silero VAD model
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=True  # Use ONNX for better performance
        )
        
        # Save the model
        model_path = models_dir / "silero_vad.onnx"
        
        # The model is already in ONNX format when loaded with onnx=True
        # Just need to save the ONNX file that was downloaded
        cache_dir = Path.home() / '.cache' / 'torch' / 'hub'
        onnx_files = list(cache_dir.rglob("*.onnx"))
        
        if onnx_files:
            # Copy the ONNX file to our models directory
            import shutil
            shutil.copy(onnx_files[0], model_path)
            logger.info(f"✅ Successfully saved Silero VAD model to {model_path}")
            
            # Log model size
            size_mb = model_path.stat().st_size / (1024 * 1024)
            logger.info(f"   Model size: {size_mb:.1f} MB")
        else:
            logger.warning("Could not find ONNX file, saving PyTorch model instead")
            torch.save(model, models_dir / "silero_vad.pt")
            
        # Also save the utils for later use
        logger.info("Saving VAD utilities...")
        (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
        
        # Create a simple test to verify the model works
        logger.info("Testing VAD model...")
        test_audio = torch.randn(16000)  # 1 second of random audio at 16kHz
        
        # Test with the model
        speech_timestamps = get_speech_timestamps(
            test_audio,
            model,
            sampling_rate=16000,
            threshold=0.5
        )
        
        logger.info(f"✅ VAD model test successful! Detected {len(speech_timestamps)} speech segments in test audio")
        
    except Exception as e:
        logger.error(f"❌ Failed to download Silero VAD: {e}")
        raise

if __name__ == "__main__":
    download_silero_vad()