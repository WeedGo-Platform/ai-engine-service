# AI Personality Voice - Multi-Model Architecture (FINAL)

## Executive Summary

Complete voice system with **multiple local and cloud TTS models** with manual switching, similar to the existing LLM model router.

---

## Multi-Model Voice Architecture

### Available Models

```
┌────────────────────────────────────────────────────────────────┐
│                    VOICE MODEL ROUTER                          │
│            (Manual Switching like LLM Router)                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  LOCAL MODELS (CPU dev, GPU prod)                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🔥 XTTS v2 (Coqui)                                      │ │
│  │     • Zero-shot voice cloning (6-30s sample)             │ │
│  │     • 17+ languages                                      │ │
│  │     • High quality, expressive                           │ │
│  │     • GPU: 2-5s | CPU: 20-30s                            │ │
│  │     • Model size: ~2GB                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ⚡ StyleTTS2                                            │ │
│  │     • SOTA voice cloning (3-10s sample)                  │ │
│  │     • 20+ languages                                      │ │
│  │     • Best quality, most natural                         │ │
│  │     • GPU: 1-3s | CPU: 15-25s                            │ │
│  │     • Model size: ~1.5GB                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🎵 Piper TTS (Existing)                                 │ │
│  │     • Pre-made voices only                               │ │
│  │     • 50+ languages, 200+ voices                         │ │
│  │     • Fast, lightweight                                  │ │
│  │     • CPU: <1s                                           │ │
│  │     • Model size: ~60MB per voice                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  CLOUD MODELS (Free Tiers)                                    │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ☁️  Google Cloud TTS                                    │ │
│  │     • Free: 1M chars/month (Standard)                    │ │
│  │     • Free: 100k chars/month (Neural2/WaveNet)           │ │
│  │     • 40+ languages, 380+ voices                         │ │
│  │     • Latency: ~1s                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🌐 IBM Watson TTS                                       │ │
│  │     • Free: 10k chars/month                              │ │
│  │     • 27+ languages                                      │ │
│  │     • Good quality                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  🔊 Azure TTS                                            │ │
│  │     • Free: 500k chars/month                             │ │
│  │     • 140+ languages/variants                            │ │
│  │     • Neural voices                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## Voice Model Router Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     VoiceModelRouter                             │
│                  (Like LLMModelRouter)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Configuration:                                                  │
│  • Active model: "xtts_v2" | "styletts2" | "piper" | "google"  │
│  • Fallback chain: [primary, secondary, tertiary]               │
│  • Model-specific settings                                      │
│  • Language preferences                                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  generate_speech(text, personality, language)              │ │
│  │                                                             │ │
│  │  1. Get active model from settings                         │ │
│  │  2. Check if model supports language                       │ │
│  │  3. Try primary model                                      │ │
│  │  4. On failure → try fallback chain                        │ │
│  │  5. Return audio + metadata                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Providers:                                                      │
│  ├── XTTSv2Service                                              │
│  ├── StyleTTS2Service                                           │
│  ├── PiperTTSService (existing)                                 │
│  ├── GoogleTTSService                                           │
│  ├── IBMWatsonTTSService                                        │
│  └── AzureTTSService                                            │
│                                                                  │
│  Stats Tracking:                                                │
│  • Requests per model                                           │
│  • Success/failure rates                                        │
│  • Average latency                                              │
│  • Characters generated                                         │
│  • Cache hit rates                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Updated ai_personalities.voice_config

```sql
{
  -- Provider selection (manual switching)
  "active_provider": "xtts_v2",  -- Current active model
  "providers": {
    "xtts_v2": {
      "enabled": true,
      "voice_sample_url": "https://.../sample.wav",
      "voice_sample_duration": 15.2,
      "settings": {
        "temperature": 0.75,
        "length_penalty": 1.0,
        "repetition_penalty": 5.0,
        "top_k": 50,
        "top_p": 0.85,
        "speed": 1.0
      },
      "supported_languages": ["en", "es", "fr", "de", ...]
    },
    "styletts2": {
      "enabled": true,
      "voice_sample_url": "https://.../sample.wav",
      "voice_sample_duration": 8.5,
      "settings": {
        "temperature": 0.7,
        "diffusion_steps": 10,
        "embedding_scale": 1.0
      },
      "supported_languages": ["en", "es", "fr", ...]
    },
    "piper": {
      "enabled": true,
      "voice_id": "en_US-ryan-medium",
      "settings": {
        "speed": 1.0,
        "speaker_id": 0
      }
    },
    "google_tts": {
      "enabled": false,
      "voice_name": "en-US-Neural2-D",
      "settings": {
        "pitch": 0,
        "speaking_rate": 1.0
      }
    }
  },

  -- Fallback chain
  "fallback_chain": ["xtts_v2", "styletts2", "piper", "google_tts"],

  -- Multi-language support
  "languages": {
    "primary": "en",
    "supported": ["en", "es", "fr", "de", "zh", "ja", "ko", ...]
  },

  -- Voice sample management
  "voice_samples": [
    {
      "id": "sample_1",
      "url": "https://.../sample1.wav",
      "duration": 15.2,
      "language": "en",
      "quality_score": 0.95,
      "uploaded_at": "2025-10-20T18:00:00Z",
      "notes": "Clean studio recording, neutral tone"
    }
  ],

  -- Usage stats per provider
  "stats": {
    "xtts_v2": {
      "total_generations": 1234,
      "total_characters": 567890,
      "avg_latency_ms": 2500,
      "failures": 5,
      "last_used": "2025-10-20T18:30:00Z"
    },
    "styletts2": {...},
    "piper": {...}
  }
}
```

---

## Voice Sample Quality Requirements

### Recording Specifications

**For Best Results:**

```
Audio Format:
  • File type: WAV (preferred) or high-quality MP3
  • Sample rate: 22050 Hz or 48000 Hz
  • Bit depth: 16-bit minimum
  • Channels: Mono (stereo will be converted)

Duration:
  • XTTS v2: 6-30 seconds (optimal: 15-20s)
  • StyleTTS2: 3-10 seconds (optimal: 5-8s)
  • Multiple samples allowed for better quality

Environment:
  • Quiet room (no background noise)
  • No echo or reverb
  • Consistent microphone distance (6-12 inches)
  • Room temperature recording (avoid outdoor)

Content:
  • Natural conversational speech
  • Varied sentence types (questions, statements, exclamations)
  • Include different emotions if desired
  • Speak clearly but naturally (not robotic)

Quality Checks:
  • SNR (Signal-to-Noise Ratio): >20 dB
  • No clipping or distortion
  • Consistent volume throughout
  • No breathing sounds or pops
```

### Sample Recording Script (Multi-Emotion)

**Neutral/Friendly:**
```
Hi there! Welcome to [Store Name]. I'm excited to help you find
the perfect product today. Let me know what you're looking for.
```

**Enthusiastic:**
```
Oh wow, that's an awesome choice! This strain has fantastic reviews
and I think you're really going to love it. It's one of our best sellers!
```

**Calm/Professional:**
```
I'd be happy to answer any questions you have about our products.
Feel free to ask me anything, and I'll do my best to help.
```

**Empathetic/Caring:**
```
I understand what you're going through. Let's work together to find
something that can help you feel better. You're in good hands.
```

**Duration**: ~15-20 seconds total
**Result**: Captures voice across different emotional ranges

---

## Multi-Model Implementation

### 1. Voice Model Router Service

**File**: `src/Backend/services/voice_model_router.py`

```python
"""
Voice Model Router - Multi-model TTS with manual switching
Similar to LLM Model Router
"""
from typing import Optional, Dict, Any, List
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class VoiceProvider(Enum):
    """Available voice providers"""
    XTTS_V2 = "xtts_v2"
    STYLETTS2 = "styletts2"
    PIPER = "piper"
    GOOGLE_TTS = "google_tts"
    IBM_WATSON = "ibm_watson"
    AZURE_TTS = "azure_tts"

class VoiceModelRouter:
    """
    Routes voice generation to selected model
    Handles fallback chain like LLM router
    """

    def __init__(self):
        self.providers = {}
        self.active_provider = None
        self.fallback_chain = []
        self.stats = {}

    async def initialize(self):
        """Initialize all voice providers"""
        from services.xtts_service import XTTSv2Service
        from services.styletts2_service import StyleTTS2Service
        from services.piper_service import PiperService
        from services.google_tts_service import GoogleTTSService
        from services.ibm_watson_service import IBMWatsonService
        from services.azure_tts_service import AzureTTSService

        # Initialize local providers
        self.providers[VoiceProvider.XTTS_V2] = XTTSv2Service()
        self.providers[VoiceProvider.STYLETTS2] = StyleTTS2Service()
        self.providers[VoiceProvider.PIPER] = PiperService()

        # Initialize cloud providers
        self.providers[VoiceProvider.GOOGLE_TTS] = GoogleTTSService()
        self.providers[VoiceProvider.IBM_WATSON] = IBMWatsonService()
        self.providers[VoiceProvider.AZURE_TTS] = AzureTTSService()

        # Initialize all in parallel
        init_tasks = [
            provider.initialize()
            for provider in self.providers.values()
        ]
        results = await asyncio.gather(*init_tasks, return_exceptions=True)

        # Log initialization results
        for provider, result in zip(self.providers.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"{provider.value} initialization failed: {result}")
            else:
                logger.info(f"✅ {provider.value} initialized")

    async def generate_speech(
        self,
        text: str,
        personality_config: Dict[str, Any],
        language: str = "en",
        force_provider: Optional[VoiceProvider] = None
    ) -> Dict[str, Any]:
        """
        Generate speech using configured provider

        Args:
            text: Text to synthesize
            personality_config: Voice configuration from personality
            language: Language code
            force_provider: Override active provider

        Returns:
            {
                "audio": bytes,
                "provider": str,
                "latency_ms": float,
                "cached": bool
            }
        """
        # Get active provider or use forced
        provider = force_provider or self._get_active_provider(personality_config)

        # Get fallback chain
        fallback_chain = self._get_fallback_chain(personality_config, provider)

        # Try each provider in chain
        for current_provider in [provider] + fallback_chain:
            try:
                logger.info(f"Attempting TTS with {current_provider.value}")

                # Check if provider supports language
                if not self._supports_language(current_provider, language):
                    logger.warning(f"{current_provider.value} doesn't support {language}")
                    continue

                # Get provider config
                provider_config = personality_config["providers"].get(current_provider.value, {})

                # Check if enabled
                if not provider_config.get("enabled", False):
                    logger.info(f"{current_provider.value} is disabled")
                    continue

                # Generate speech
                start_time = time.time()

                audio = await self.providers[current_provider].generate(
                    text=text,
                    config=provider_config,
                    language=language
                )

                latency_ms = (time.time() - start_time) * 1000

                # Track stats
                self._track_stats(current_provider, latency_ms, success=True)

                return {
                    "audio": audio,
                    "provider": current_provider.value,
                    "latency_ms": latency_ms,
                    "cached": False
                }

            except Exception as e:
                logger.error(f"{current_provider.value} failed: {e}")
                self._track_stats(current_provider, 0, success=False)
                continue

        # All providers failed
        raise RuntimeError(f"All voice providers failed for language: {language}")

    def _get_active_provider(self, config: Dict) -> VoiceProvider:
        """Get active provider from config"""
        active = config.get("active_provider", "piper")
        return VoiceProvider(active)

    def _get_fallback_chain(
        self,
        config: Dict,
        exclude_provider: VoiceProvider
    ) -> List[VoiceProvider]:
        """Get fallback provider chain"""
        chain = config.get("fallback_chain", [
            "styletts2", "xtts_v2", "piper", "google_tts"
        ])

        # Convert to enums and exclude primary
        return [
            VoiceProvider(p)
            for p in chain
            if p != exclude_provider.value
        ]

    def _supports_language(self, provider: VoiceProvider, language: str) -> bool:
        """Check if provider supports language"""
        # Check provider capabilities
        provider_languages = {
            VoiceProvider.XTTS_V2: [
                "en", "es", "fr", "de", "it", "pt", "pl", "tr",
                "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hu", "hi"
            ],
            VoiceProvider.STYLETTS2: [
                "en", "es", "fr", "de", "it", "pt", "pl", "ru",
                "nl", "ar", "zh", "ja", "ko", "hi", "bn", "ta",
                "te", "mr", "gu"
            ],
            VoiceProvider.PIPER: [
                # Piper supports 50+ languages
                # Full list: https://github.com/rhasspy/piper
                "en", "es", "fr", "de", "it", "pt", "pl", "tr",
                "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hi",
                "bn", "ta", "vi", "th", "id", "ms", "fil", "sw"
                # ... and many more
            ],
            VoiceProvider.GOOGLE_TTS: [
                # Google supports 40+ languages
                "en", "es", "fr", "de", "it", "pt", "pl", "tr",
                "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hi",
                "bn", "ta", "te", "mr", "gu", "pa", "ur", "vi",
                "th", "id", "ms", "fil", "sw", "zu", "yo", "ha"
                # ... and more
            ],
            VoiceProvider.IBM_WATSON: [
                "en", "es", "fr", "de", "it", "pt", "ar", "zh",
                "ja", "ko", "nl"
            ],
            VoiceProvider.AZURE_TTS: [
                # Azure supports 140+ languages/variants
                # All major languages supported
                "en", "es", "fr", "de", "it", "pt", "pl", "tr",
                "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hi",
                # ... comprehensive list
            ]
        }

        supported = provider_languages.get(provider, [])
        return language in supported

    def _track_stats(self, provider: VoiceProvider, latency_ms: float, success: bool):
        """Track provider statistics"""
        if provider.value not in self.stats:
            self.stats[provider.value] = {
                "requests": 0,
                "failures": 0,
                "avg_latency_ms": 0
            }

        stats = self.stats[provider.value]
        stats["requests"] += 1
        if not success:
            stats["failures"] += 1

        # Update rolling average latency
        if success:
            if stats["requests"] == 1:
                stats["avg_latency_ms"] = latency_ms
            else:
                alpha = 0.1
                stats["avg_latency_ms"] = (
                    alpha * latency_ms +
                    (1 - alpha) * stats["avg_latency_ms"]
                )

    async def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "providers": self.stats,
            "active_provider": self.active_provider.value if self.active_provider else None
        }
```

### 2. StyleTTS2 Service

**File**: `src/Backend/services/styletts2_service.py`

```python
"""
StyleTTS2 Service - State-of-the-art voice cloning
"""
import torch
import torchaudio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class StyleTTS2Service:
    """StyleTTS2 voice cloning service"""

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"StyleTTS2 will use device: {self.device}")

    async def initialize(self):
        """Load StyleTTS2 model"""
        try:
            logger.info("Loading StyleTTS2 model...")

            # Load StyleTTS2 checkpoint
            from styletts2 import tts_cli

            self.model = tts_cli.StyleTTS2(
                config_path="models/voice/styletts2/config.yml",
                checkpoint_path="models/voice/styletts2/checkpoint.pth",
                device=self.device
            )

            logger.info("✅ StyleTTS2 model loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load StyleTTS2: {e}")
            return False

    async def generate(
        self,
        text: str,
        config: Dict[str, Any],
        language: str = "en"
    ) -> bytes:
        """
        Generate speech with StyleTTS2

        Args:
            text: Text to synthesize
            config: Provider configuration
            language: Language code

        Returns:
            WAV audio bytes
        """
        # Get voice sample
        sample_url = config.get("voice_sample_url")
        if not sample_url:
            raise ValueError("StyleTTS2 requires voice sample")

        sample_audio = await self._download_voice_sample(sample_url)

        # Get settings
        settings = config.get("settings", {})

        # Generate speech
        wav = self.model.inference(
            text=text,
            ref_s=sample_audio,  # Reference speaker
            alpha=settings.get("temperature", 0.7),
            beta=settings.get("diffusion_steps", 10),
            diffusion_steps=settings.get("diffusion_steps", 10),
            embedding_scale=settings.get("embedding_scale", 1.0)
        )

        # Convert to bytes
        buffer = io.BytesIO()
        wav_tensor = torch.FloatTensor(wav).unsqueeze(0)
        torchaudio.save(buffer, wav_tensor, 24000, format="wav")
        buffer.seek(0)

        return buffer.read()
```

---

## UI/UX for Model Selection

### Voice Model Selector (In Personality Form)

```
┌────────────────────────────────────────────────────────────┐
│  🎤 Voice Generation Model                                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Active Model:                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  ⚡ StyleTTS2 (Local - GPU)         [Change ▼]    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Available Models:                                    │ │
│  │                                                       │ │
│  │  LOCAL MODELS                                         │ │
│  │  ○ XTTS v2 (Coqui)                                   │ │
│  │    • Quality: ⭐⭐⭐⭐⭐                                  │ │
│  │    • Speed: 2-5s (GPU) | 20-30s (CPU)                │ │
│  │    • Languages: 17+                                   │ │
│  │    • Voice Cloning: Yes (6-30s sample)               │ │
│  │                                                       │ │
│  │  ● StyleTTS2 ← ACTIVE                                │ │
│  │    • Quality: ⭐⭐⭐⭐⭐ (Best)                           │ │
│  │    • Speed: 1-3s (GPU) | 15-25s (CPU)                │ │
│  │    • Languages: 20+                                   │ │
│  │    • Voice Cloning: Yes (3-10s sample)               │ │
│  │                                                       │ │
│  │  ○ Piper TTS                                         │ │
│  │    • Quality: ⭐⭐⭐⭐                                    │ │
│  │    • Speed: <1s (Fast)                               │ │
│  │    • Languages: 50+                                   │ │
│  │    • Voice Cloning: No (pre-made voices only)        │ │
│  │                                                       │ │
│  │  CLOUD MODELS (Free Tier)                            │ │
│  │  ○ Google Cloud TTS                                  │ │
│  │    • Quality: ⭐⭐⭐                                     │ │
│  │    • Free: 100k chars/month                          │ │
│  │    • Languages: 40+                                   │ │
│  │                                                       │ │
│  │  ○ Azure TTS                                         │ │
│  │    • Quality: ⭐⭐⭐⭐                                    │ │
│  │    • Free: 500k chars/month                          │ │
│  │    • Languages: 140+                                  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Fallback Chain:                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │  1. StyleTTS2 → 2. XTTS v2 → 3. Piper → 4. Google│   │
│  │  [Reorder]                                         │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  💡 Tip: StyleTTS2 provides the highest quality for       │
│     custom voices. Piper is fastest for default voices.   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Model Performance Dashboard

```
┌────────────────────────────────────────────────────────────┐
│  📊 Voice Model Performance                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Model         Requests  Success  Avg Latency  Cache│ │
│  ├──────────────────────────────────────────────────────┤ │
│  │  StyleTTS2     1,234    99.5%    2.3s         45%   │ │
│  │  XTTS v2       456      98.2%    3.1s         42%   │ │
│  │  Piper         3,456    99.9%    0.8s         52%   │ │
│  │  Google TTS    123      100%     1.2s         38%   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Character Usage: 234,567 / ∞ (Local models)              │
│  Google Cloud: 12,345 / 100,000 (12.3% used)              │
│  Azure: 5,678 / 500,000 (1.1% used)                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Multi-Language Support

### Language Configuration

```python
# Supported languages across all models
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "es": {"name": "Spanish", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "fr": {"name": "French", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "de": {"name": "German", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "it": {"name": "Italian", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "pt": {"name": "Portuguese", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "pl": {"name": "Polish", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "tr": {"name": "Turkish", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "ru": {"name": "Russian", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "nl": {"name": "Dutch", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "cs": {"name": "Czech", "models": ["xtts_v2", "piper", "google", "azure"]},
    "ar": {"name": "Arabic", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "zh": {"name": "Chinese", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "ja": {"name": "Japanese", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "ko": {"name": "Korean", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "hi": {"name": "Hindi", "models": ["xtts_v2", "styletts2", "piper", "google", "azure"]},
    "bn": {"name": "Bengali", "models": ["styletts2", "piper", "google", "azure"]},
    "ta": {"name": "Tamil", "models": ["styletts2", "piper", "google", "azure"]},
    "te": {"name": "Telugu", "models": ["styletts2", "piper", "google", "azure"]},
    "vi": {"name": "Vietnamese", "models": ["piper", "google", "azure"]},
    "th": {"name": "Thai", "models": ["piper", "google", "azure"]},
    "id": {"name": "Indonesian", "models": ["piper", "google", "azure"]},
    "ms": {"name": "Malay", "models": ["piper", "google", "azure"]},
    "fil": {"name": "Filipino", "models": ["piper", "google", "azure"]},
    "sw": {"name": "Swahili", "models": ["piper", "google", "azure"]},
    "hu": {"name": "Hungarian", "models": ["xtts_v2", "google", "azure"]}
    # Total: 25+ languages
}
```

---

## Installation & Setup

### Local Models

**XTTS v2:**
```bash
pip install TTS
python -m TTS.download_model --model_name "tts_models/multilingual/multi-dataset/xtts_v2"
```

**StyleTTS2:**
```bash
git clone https://github.com/yl4579/StyleTTS2.git
cd StyleTTS2
pip install -r requirements.txt
# Download checkpoint
wget https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/main/Models/LibriTTS/epochs_2nd_00020.pth
```

**Piper (already installed):**
```bash
# Already have Piper models in models/voice/piper/
ls models/voice/piper/*.onnx
```

### Cloud Models

**Google Cloud TTS:**
```bash
pip install google-cloud-texttospeech
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

**Azure TTS:**
```bash
pip install azure-cognitiveservices-speech
export AZURE_SPEECH_KEY="your-key"
export AZURE_SPEECH_REGION="your-region"
```

**IBM Watson:**
```bash
pip install ibm-watson
export IBM_WATSON_API_KEY="your-key"
```

---

## Final Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

- [ ] Install XTTS v2 and StyleTTS2
- [ ] Create VoiceModelRouter service
- [ ] Implement XTTSv2Service
- [ ] Implement StyleTTS2Service
- [ ] Add Google/Azure/IBM cloud services
- [ ] Add model selection to voice_config schema
- [ ] Test all models with sample text

### Phase 2: Voice Sample Upload (Week 2)

- [ ] Add voice sample upload endpoint
- [ ] Implement audio quality validation
- [ ] Add sample management UI
- [ ] Test voice cloning with XTTS v2 and StyleTTS2
- [ ] Add multi-sample support

### Phase 3: UI Integration (Week 3)

- [ ] Add model selector to personality form
- [ ] Add fallback chain editor
- [ ] Add voice settings per model
- [ ] Add performance dashboard
- [ ] Add language selector (25+ languages)

### Phase 4: Agent Integration (Week 4)

- [ ] Integrate VoiceModelRouter with agent
- [ ] Add voice caching layer
- [ ] Add multi-language support
- [ ] Performance testing (CPU vs GPU)
- [ ] Optimize model loading

---

## Questions Answered ✅

1. ✅ GPU/CPU: CPU locally, GPU in production
2. ✅ XTTS v2 + StyleTTS2: Both with manual switching
3. ✅ CPU support: Yes for both models
4. ✅ Voice quality: Full specs provided above
5. ✅ Cloud setup: Piper local + Google/Azure/IBM cloud
6. ✅ Multi-language: 25+ languages supported

---

**READY TO IMPLEMENT!** 🚀

This gives you:
- ✅ Multiple local models (XTTS v2, StyleTTS2, Piper)
- ✅ Multiple cloud options (Google, Azure, IBM)
- ✅ Manual switching like LLM router
- ✅ 25+ language support
- ✅ CPU/GPU flexibility
- ✅ Voice cloning with quality samples
- ✅ Complete fallback chain

**Shall I begin implementation?**
