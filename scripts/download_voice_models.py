#!/usr/bin/env python3
"""
Download native voice models for all supported languages
"""

import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Voice model configurations
VOICE_MODELS = {
    "en-GB": "en_GB-alan-medium",
    "es-ES": "es_ES-davefx-medium",
    "fr-FR": "fr_FR-upmc-medium",
    "pt-PT": "pt_PT-tugao-medium",
    "zh-CN": "zh_CN-huayan-medium",
    "ar": "ar_JO-kareem-medium"
}

def setup_voice_models():
    """Setup voice models"""
    base_dir = Path("models/voice/piper")
    base_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Voice model directory created")
    
    for lang, model in VOICE_MODELS.items():
        logger.info(f"Voice model for {lang}: {model}")

if __name__ == "__main__":
    setup_voice_models()
