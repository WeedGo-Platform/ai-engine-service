"""
Mock Voice Handler for Testing
Provides simple voice processing without requiring actual models
"""
import numpy as np
import asyncio
import time
import random
from typing import Dict, Any, Optional

class MockVoiceHandler:
    """Mock voice handler for testing without models"""
    
    def __init__(self):
        self.responses = [
            "I recommend our Purple Kush for excellent sleep support. It's an indica-dominant strain with sedating effects.",
            "For pain relief, try our high-CBD strains like ACDC or Harlequin. They provide relief without intense psychoactive effects.",
            "Our Blue Dream is perfect for daytime use. It offers a balanced, uplifting experience that enhances creativity.",
            "Looking for something potent? Our Ghost Train Haze tests at 28% THC and delivers a powerful cerebral experience.",
            "For beginners, I suggest starting with a balanced hybrid like Blue Dream or a CBD-rich strain for a gentler experience."
        ]
        
        self.multilingual_responses = {
            "es": "Te recomiendo Purple Kush para dormir mejor. Es una cepa índica con efectos sedantes.",
            "fr": "Je recommande Purple Kush pour un excellent soutien au sommeil. C'est une variété à dominance indica.",
            "zh": "我推荐Purple Kush来帮助睡眠。这是一种具有镇静作用的印度大麻品种。",
            "pt": "Recomendo Purple Kush para um excelente suporte ao sono. É uma variedade predominantemente indica.",
            "ar": "أوصي بـ Purple Kush لدعم النوم الممتاز. إنها سلالة إنديكا مهدئة."
        }
    
    async def process_audio(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Mock audio processing"""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate mock transcription
        sample_texts = [
            "What do you recommend for sleep?",
            "I need something for pain relief",
            "What's good for creativity?",
            "Show me your strongest strains",
            "I'm new to cannabis, what should I try?"
        ]
        
        text = random.choice(sample_texts)
        
        return {
            "status": "success",
            "transcription": {
                "text": text,
                "confidence": 0.95,
                "language": "en"
            },
            "metadata": {
                "duration_ms": len(audio_array) / 16,  # Assuming 16kHz
                "detected_intent": "product_recommendation"
            }
        }
    
    async def generate_speech(self, text: str, override_settings: Dict = None) -> np.ndarray:
        """Mock speech generation"""
        # Simulate TTS processing
        await asyncio.sleep(0.3)
        
        # Generate mock audio (1 second of sine wave)
        sample_rate = 22050
        duration = min(len(text) * 0.05, 5.0)  # Approximate duration based on text length
        samples = int(sample_rate * duration)
        
        # Generate a simple sine wave as mock audio
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        return audio.astype(np.float32)
    
    async def calibrate_for_environment(self) -> Dict[str, Any]:
        """Mock environment calibration"""
        await asyncio.sleep(0.2)
        
        return {
            "noise_level": random.uniform(0.05, 0.15),
            "echo_present": False,
            "optimal_gain": 1.1
        }
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get mock configuration value"""
        config = {
            "tts.default_speed": 1.0,
            "tts.default_pitch": 0.0,
            "conversation.enable_interruption_detection": True,
            "conversation.enable_backchanneling": True
        }
        return config.get(key, default)
    
    def update_config_value(self, key: str, value: Any):
        """Update mock configuration"""
        pass  # Just accept the update
    
    async def switch_domain(self, domain: str):
        """Switch domain context"""
        self.current_domain = domain
        
    async def detect_language(self, audio_array: np.ndarray) -> str:
        """Mock language detection"""
        # Randomly return a language for testing
        languages = ["en", "es", "fr", "pt", "zh", "ar"]
        return random.choice(languages)
    
    async def identify_speaker(self, audio_array: np.ndarray) -> Optional[str]:
        """Mock speaker identification"""
        # Randomly identify or not
        if random.random() > 0.5:
            return f"voice_user_{random.randint(100, 999)}"
        return None

# Singleton instance
_mock_handler = None

def get_mock_handler():
    """Get or create mock handler instance"""
    global _mock_handler
    if _mock_handler is None:
        _mock_handler = MockVoiceHandler()
    return _mock_handler