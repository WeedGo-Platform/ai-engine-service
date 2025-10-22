# AI Personality Voice Implementation - Local-First Architecture

## Executive Summary

This document outlines the **revised** voice implementation using a **local-first** approach with free cloud fallback, matching the existing model router pattern.

---

## Current State Assessment

### ✅ Already Implemented

**Voice Pipeline** (`core/voice/voice_pipeline.py`):
- **Piper TTS** (PiperTTSHandler) - Local neural TTS with ONNX models
- **Whisper STT** (WhisperSTTHandler) - Local speech-to-text
- **Silero VAD** (SileroVADHandler) - Voice activity detection
- **Wake Word** (WhisperWakeWordHandler) - Custom wake word support

**Existing Voices** (`models/voice/piper/`):
- en_US-ryan-medium (male)
- en_US-amy-medium (female)
- en_US-joe-medium (male)
- en_US-kristin-medium (female)
- en_GB-alan-medium (male)
- en_GB-alba-medium (female)
- es_ES-davefx-medium (Spanish)
- es_MX-ald-medium (Mexican Spanish)

**API Endpoints** (`api/voice_endpoints.py`):
- `POST /api/voice/synthesize` - Text-to-speech
- `POST /api/voice/transcribe` - Speech-to-text
- `GET /api/voice/voices` - List available voices

---

## Revised Architecture: Local Voice Cloning + Piper TTS

### Strategy Overview

```
┌─────────────────────────────────────────────────────────────┐
│               VOICE GENERATION ROUTER                        │
│                                                              │
│  Priority 1: Custom Voice (XTTS v2 Local)  ← IF TRAINED    │
│  Priority 2: Default Voice (Piper TTS)      ← FALLBACK     │
│  Priority 3: Cloud TTS (Google Free Tier)   ← EMERGENCY    │
└─────────────────────────────────────────────────────────────┘
```

**Similar to your LLM router**: Local model first, cloud fallback if needed.

---

## Local Voice Cloning: XTTS v2 (Coqui TTS)

### Why XTTS v2?

**✅ Advantages:**
- **Zero-shot voice cloning** from 6-30 seconds of audio
- **Open source** and **free** (no API costs)
- **Multi-lingual** (17+ languages)
- **Emotional** and **expressive** voices
- **Local deployment** (GPU or CPU)
- **High quality** (comparable to commercial solutions)
- **Fast inference** on GPU (~2-5 seconds for 10s of audio)

**❌ Trade-offs:**
- Requires **GPU for best performance** (CPU is slow but works)
- ~2GB model size
- Slower than Piper TTS (~3-5x)

**Cost:**
- Hardware: Can run on existing GPU infrastructure
- No per-character costs
- One-time setup

### Technical Specifications

**Model:** `tts_models/multilingual/multi-dataset/xtts_v2`

**Hardware Requirements:**
- **Minimum**: 4GB RAM, CPU (slow, ~30s per sentence)
- **Recommended**: NVIDIA GPU with 4GB+ VRAM (fast, ~2-5s per sentence)
- **Optimal**: NVIDIA GPU with 8GB+ VRAM (very fast, ~1-2s per sentence)

**Voice Cloning Process:**
1. User uploads 6-30 seconds of clean audio
2. XTTS v2 uses audio as reference (no training needed)
3. Generates speech in the reference voice instantly
4. Can adjust emotion, speed, pitch

---

## Alternative: StyleTTS2 (Even Better Quality)

**Why StyleTTS2?**
- **State-of-the-art** open-source TTS (better than XTTS v2)
- **Voice cloning** with minimal samples
- **More natural** prosody and emotion
- **Faster** than XTTS v2

**Trade-offs:**
- Newer, less mature ecosystem
- Slightly more complex setup
- GPU required for good performance

---

## System Architecture

### High-Level Flow

```
User creates personality
   ↓
Uploads voice sample (optional)
   ↓
System stores sample in blob storage
   ↓
--- Voice Generation (during conversation) ---
   ↓
Check personality.voice_config
   ↓
┌──────────────────────────────────────────┐
│  Has custom voice sample?                │
├──────────────────────────────────────────┤
│  YES → Use XTTS v2 (local GPU)           │
│  NO  → Use Piper TTS (local CPU)         │
│  FAIL → Use Google TTS (cloud free tier) │
└──────────────────────────────────────────┘
   ↓
Cache generated audio (24h)
   ↓
Return audio URL to frontend
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   VoiceRouter Service                        │
│  (New component, similar to model router)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  route_voice_generation(text, personality_config)           │
│      ↓                                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Check personality.voice_config                       │  │
│  └──────────────────────────────────────────────────────┘  │
│      ↓                                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Priority 1: XTTS v2 (if voice_sample exists)        │  │
│  │  Priority 2: Piper TTS (default voice)               │  │
│  │  Priority 3: Google TTS Free (fallback)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
             ↓                 ↓                 ↓
   ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
   │  XTTS v2        │  │  Piper TTS   │  │  Google TTS  │
   │  Local (GPU)    │  │  Local (CPU) │  │  Cloud (Free)│
   │  ~2-5s latency  │  │  <1s latency │  │  ~1s latency │
   └─────────────────┘  └──────────────┘  └──────────────┘
```

---

## Database Schema (Updated)

```sql
-- ai_personalities.voice_config (JSONB column)
{
  "provider": "xtts_v2",  -- or "piper", "google_tts"
  "mode": "custom",       -- "custom" or "default"

  -- For custom voices (XTTS v2)
  "voice_sample_url": "https://storage.../voices/uuid/sample.wav",
  "voice_sample_duration": 15.5,  -- seconds
  "uploaded_at": "2025-10-20T17:00:00Z",

  -- Voice generation settings
  "settings": {
    "temperature": 0.75,   -- XTTS v2 creativity
    "length_penalty": 1.0, -- XTTS v2 speech rate
    "repetition_penalty": 5.0,
    "top_k": 50,
    "top_p": 0.85,
    "speed": 1.0,          -- Piper TTS speed
    "emotion": "neutral"   -- Future: happy, sad, excited
  },

  -- Fallback configuration
  "fallback": {
    "provider": "piper",
    "voice_id": "en_US-ryan-medium"  -- Piper voice model
  },

  -- Usage stats
  "stats": {
    "total_generations": 1234,
    "total_seconds": 5678.9,
    "average_latency_ms": 2500,
    "cache_hit_rate": 0.45
  }
}
```

---

## Implementation Details

### 1. Voice Router Service

**New file:** `src/Backend/services/voice_router_service.py`

```python
"""
Voice Router Service - Routes TTS requests to optimal provider
Similar pattern to model router
"""
from typing import Optional, Dict, Any
import logging
import time
from pathlib import Path

from core.voice.piper_tts import PiperTTSHandler
from services.xtts_service import XTTSService
from services.google_tts_service import GoogleTTSService

logger = logging.getLogger(__name__)

class VoiceRouter:
    """Routes voice generation to optimal provider"""

    def __init__(self):
        self.piper = PiperTTSHandler()  # Existing Piper handler
        self.xtts = XTTSService()       # New XTTS v2 handler
        self.google = GoogleTTSService() # New Google TTS fallback

        self.providers = {
            "xtts_v2": self.xtts,
            "piper": self.piper,
            "google_tts": self.google
        }

        # Performance tracking
        self.stats = {
            "xtts_v2": {"requests": 0, "failures": 0, "avg_latency": 0},
            "piper": {"requests": 0, "failures": 0, "avg_latency": 0},
            "google_tts": {"requests": 0, "failures": 0, "avg_latency": 0}
        }

    async def initialize(self):
        """Initialize all providers"""
        await self.piper.initialize()
        await self.xtts.initialize()
        await self.google.initialize()
        logger.info("Voice router initialized")

    async def generate_speech(
        self,
        text: str,
        voice_config: Dict[str, Any],
        cache_key: Optional[str] = None
    ) -> bytes:
        """
        Generate speech using optimal provider

        Priority:
        1. XTTS v2 if voice_sample exists
        2. Piper TTS for default voices
        3. Google TTS as emergency fallback
        """
        provider = voice_config.get("provider", "piper")
        mode = voice_config.get("mode", "default")

        # Route based on mode
        if mode == "custom" and voice_config.get("voice_sample_url"):
            # Try XTTS v2 first for custom voices
            try:
                return await self._generate_with_xtts(text, voice_config)
            except Exception as e:
                logger.warning(f"XTTS v2 failed, falling back: {e}")
                # Fall through to Piper

        # Try Piper TTS (fast and reliable)
        try:
            return await self._generate_with_piper(text, voice_config)
        except Exception as e:
            logger.warning(f"Piper TTS failed, falling back: {e}")

        # Last resort: Google TTS (free tier)
        try:
            return await self._generate_with_google(text, voice_config)
        except Exception as e:
            logger.error(f"All TTS providers failed: {e}")
            raise

    async def _generate_with_xtts(
        self,
        text: str,
        config: Dict[str, Any]
    ) -> bytes:
        """Generate with XTTS v2"""
        start = time.time()

        # Get voice sample
        sample_url = config["voice_sample_url"]
        sample_audio = await self._download_voice_sample(sample_url)

        # Generate speech
        audio = await self.xtts.generate(
            text=text,
            speaker_wav=sample_audio,
            language="en",  # From personality config
            temperature=config["settings"].get("temperature", 0.75),
            length_penalty=config["settings"].get("length_penalty", 1.0),
            repetition_penalty=config["settings"].get("repetition_penalty", 5.0),
            top_k=config["settings"].get("top_k", 50),
            top_p=config["settings"].get("top_p", 0.85)
        )

        # Track stats
        latency = (time.time() - start) * 1000
        self._update_stats("xtts_v2", latency, success=True)

        return audio

    async def _generate_with_piper(
        self,
        text: str,
        config: Dict[str, Any]
    ) -> bytes:
        """Generate with Piper TTS (existing implementation)"""
        start = time.time()

        # Use fallback voice or default
        voice_id = config.get("fallback", {}).get("voice_id", "en_US-ryan-medium")

        audio = await self.piper.synthesize(
            text=text,
            voice=voice_id,
            speed=config["settings"].get("speed", 1.0)
        )

        latency = (time.time() - start) * 1000
        self._update_stats("piper", latency, success=True)

        return audio

    async def _generate_with_google(
        self,
        text: str,
        config: Dict[str, Any]
    ) -> bytes:
        """Generate with Google TTS Free Tier"""
        start = time.time()

        audio = await self.google.synthesize(
            text=text,
            language_code="en-US",
            voice_name="en-US-Neural2-D"  # Free tier voice
        )

        latency = (time.time() - start) * 1000
        self._update_stats("google_tts", latency, success=True)

        return audio

    def _update_stats(self, provider: str, latency_ms: float, success: bool):
        """Update provider statistics"""
        stats = self.stats[provider]
        stats["requests"] += 1
        if not success:
            stats["failures"] += 1

        # Update rolling average latency
        if stats["requests"] == 1:
            stats["avg_latency"] = latency_ms
        else:
            alpha = 0.1  # Exponential moving average factor
            stats["avg_latency"] = (alpha * latency_ms) + ((1 - alpha) * stats["avg_latency"])
```

### 2. XTTS v2 Service

**New file:** `src/Backend/services/xtts_service.py`

```python
"""
XTTS v2 Service - Zero-shot voice cloning
"""
import torch
import torchaudio
from TTS.api import TTS
import numpy as np
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class XTTSService:
    """XTTS v2 voice cloning service"""

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"XTTS v2 will use device: {self.device}")

    async def initialize(self):
        """Load XTTS v2 model"""
        try:
            logger.info("Loading XTTS v2 model...")
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            logger.info("✅ XTTS v2 model loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load XTTS v2: {e}")
            return False

    async def generate(
        self,
        text: str,
        speaker_wav: bytes,
        language: str = "en",
        temperature: float = 0.75,
        length_penalty: float = 1.0,
        repetition_penalty: float = 5.0,
        top_k: int = 50,
        top_p: float = 0.85
    ) -> bytes:
        """
        Generate speech with voice cloning

        Args:
            text: Text to synthesize
            speaker_wav: Reference audio (6-30 seconds)
            language: Language code (en, es, fr, etc.)
            temperature: Creativity (0.1-1.0, higher = more variation)
            length_penalty: Speech rate control
            repetition_penalty: Avoid repetition
            top_k: Sampling parameter
            top_p: Nucleus sampling

        Returns:
            WAV audio bytes
        """
        # Save speaker wav to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(speaker_wav)
            speaker_path = f.name

        try:
            # Generate speech
            wav = self.model.tts(
                text=text,
                speaker_wav=speaker_path,
                language=language,
                temperature=temperature,
                length_penalty=length_penalty,
                repetition_penalty=repetition_penalty,
                top_k=top_k,
                top_p=top_p
            )

            # Convert to bytes
            wav_tensor = torch.FloatTensor(wav).unsqueeze(0)
            buffer = io.BytesIO()
            torchaudio.save(buffer, wav_tensor, 22050, format="wav")
            buffer.seek(0)

            return buffer.read()

        finally:
            # Clean up temp file
            import os
            os.unlink(speaker_path)
```

### 3. Google TTS Free Tier Service

**New file:** `src/Backend/services/google_tts_service.py`

```python
"""
Google Cloud Text-to-Speech - Free Tier Fallback
"""
from google.cloud import texttospeech
import logging

logger = logging.getLogger(__name__)

class GoogleTTSService:
    """Google TTS for emergency fallback"""

    def __init__(self):
        self.client = None

    async def initialize(self):
        """Initialize Google TTS client"""
        try:
            # Free tier: 1M characters/month
            self.client = texttospeech.TextToSpeechClient()
            logger.info("✅ Google TTS initialized (free tier)")
            return True
        except Exception as e:
            logger.warning(f"Google TTS not available: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        language_code: str = "en-US",
        voice_name: str = "en-US-Neural2-D"
    ) -> bytes:
        """Generate speech with Google TTS"""
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content
```

---

## Voice Sample Upload & Storage

### Upload Process

```python
# New endpoint: POST /api/admin/ai-personalities/:id/voice/upload

@router.post("/{personality_id}/voice/upload")
async def upload_voice_sample(
    personality_id: str,
    audio: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant)
):
    """Upload voice sample for personality"""

    # Validate audio
    if not audio.filename.endswith(('.wav', '.mp3', '.m4a')):
        raise HTTPException(400, "Invalid audio format")

    # Read audio
    audio_data = await audio.read()

    # Validate duration (6-30 seconds)
    duration = get_audio_duration(audio_data)
    if duration < 6 or duration > 30:
        raise HTTPException(400, f"Audio must be 6-30 seconds (got {duration}s)")

    # Upload to blob storage
    sample_url = await upload_to_storage(
        audio_data,
        f"voices/{tenant_id}/{personality_id}/sample.wav"
    )

    # Update personality voice_config
    personality = await get_personality(personality_id)
    personality.voice_config = {
        "provider": "xtts_v2",
        "mode": "custom",
        "voice_sample_url": sample_url,
        "voice_sample_duration": duration,
        "uploaded_at": datetime.utcnow().isoformat(),
        "settings": {
            "temperature": 0.75,
            "length_penalty": 1.0,
            "repetition_penalty": 5.0,
            "top_k": 50,
            "top_p": 0.85
        },
        "fallback": {
            "provider": "piper",
            "voice_id": "en_US-ryan-medium"
        }
    }

    await personality.save()

    return {
        "success": True,
        "message": "Voice sample uploaded",
        "sample_url": sample_url,
        "duration": duration
    }
```

---

## Integration with Agent Flow

### Updated Agent Response Generation

```python
# In V5DispensaryAgent or conversation handler

async def generate_response_with_voice(
    text_response: str,
    personality_id: str
) -> dict:
    """Generate text + voice response"""

    # Get personality config
    personality = await get_personality(personality_id)

    # Check cache first
    cache_key = f"voice:{personality_id}:{hash(text_response)}"
    audio_url = await redis.get(cache_key)

    if not audio_url:
        # Generate audio using voice router
        audio_bytes = await voice_router.generate_speech(
            text=text_response,
            voice_config=personality.voice_config
        )

        # Upload to CDN/storage
        audio_url = await upload_audio(
            audio_bytes,
            f"generated/{uuid4()}.wav"
        )

        # Cache for 24 hours
        await redis.setex(cache_key, 86400, audio_url)

    return {
        "text": text_response,
        "audio_url": audio_url,
        "personality": personality.name,
        "voice_provider": personality.voice_config.get("provider")
    }
```

---

## Hardware Requirements & Performance

### Local Deployment

**Recommended Server Specs:**
```
CPU: 8+ cores
RAM: 16GB minimum
GPU: NVIDIA with 8GB+ VRAM (optional but recommended)
Storage: 50GB for models
```

**Performance Benchmarks:**
```
XTTS v2 (GPU):   ~2-5 seconds per 10s of audio
XTTS v2 (CPU):   ~20-30 seconds per 10s of audio
Piper TTS (CPU): <1 second per 10s of audio
Google TTS:      ~1-2 seconds per 10s of audio
```

### Cost Analysis

**Zero ongoing costs** for local TTS:
- ✅ XTTS v2: Free (open source)
- ✅ Piper TTS: Free (already implemented)
- ✅ Google TTS: Free tier (1M chars/month) as fallback

**Infrastructure costs:**
- GPU instance (optional): $0-500/month depending on scale
- Can run on CPU for low-volume tenants
- Cache reduces repeated generations by ~30-50%

---

## Implementation Phases

### Phase 1: Voice Router Infrastructure (Week 1)

**Backend:**
- [ ] Create VoiceRouter service
- [ ] Integrate XTTS v2 service
- [ ] Add Google TTS fallback
- [ ] Create voice sample upload endpoint
- [ ] Add voice generation to conversation API

**Testing:**
- [ ] Test XTTS v2 voice cloning with sample audio
- [ ] Test fallback chain (XTTS → Piper → Google)
- [ ] Performance benchmarks

### Phase 2: UI Integration (Week 2)

**Frontend:**
- [ ] Add voice sample upload to personality form
- [ ] Add audio preview player
- [ ] Add voice settings sliders
- [ ] Add voice provider status indicator

**Backend:**
- [ ] Audio validation and processing
- [ ] Blob storage integration
- [ ] Update personality API

### Phase 3: Agent Integration (Week 3)

**Backend:**
- [ ] Integrate voice router with agent responses
- [ ] Add caching layer
- [ ] Add voice provider selection logic
- [ ] Performance monitoring

**Frontend:**
- [ ] Auto-play voice responses in chat
- [ ] Audio controls (play, pause, stop)
- [ ] Voice loading indicators

### Phase 4: Optimization & Polish (Week 4)

**Backend:**
- [ ] Optimize XTTS v2 inference
- [ ] Implement batch processing
- [ ] Add usage analytics
- [ ] GPU/CPU resource management

**Frontend:**
- [ ] Voice usage dashboard
- [ ] Provider performance metrics
- [ ] Mobile optimization

---

## Open Questions

1. **GPU Availability**: Do you have GPU infrastructure available for XTTS v2? If not, we can start with Piper TTS only and add XTTS later.

2. **Voice Sample Quality**: Should we require tenants to record in a specific environment, or accept any quality?

3. **Multi-language**: Should custom voices support multiple languages, or English only in V1?

4. **Fallback Strategy**: Should we allow tenants to choose their fallback provider, or automatically select?

5. **XTTS v2 vs StyleTTS2**: Should we implement both and let tenants choose, or pick one?

6. **CPU-only Mode**: Should we support XTTS v2 on CPU (slow but works), or require GPU?

---

## Next Steps (After Approval)

1. ✅ **Approve local-first architecture** (XTTS v2 + Piper + Google fallback)
2. Set up XTTS v2 on GPU server (or CPU if no GPU available)
3. Implement VoiceRouter service
4. Add voice sample upload to personality UI
5. Integrate with existing voice pipeline
6. Test end-to-end voice generation

---

**Status**: 🟡 **AWAITING APPROVAL** on revised local-first voice architecture

Does this approach align with your vision? Should I proceed with XTTS v2 implementation?
