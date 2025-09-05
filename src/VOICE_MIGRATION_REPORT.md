# V5 Voice Feature Migration Report

## Executive Summary

After a comprehensive analysis of the V3/V4 voice implementation, this report provides a detailed migration plan for integrating state-of-the-art offline voice capabilities into V5, following industry best practices and modern architectural patterns.

## Current V3/V4 Voice Implementation Analysis

### Architecture Overview
The legacy implementation uses a modular, offline-first approach with:

1. **Speech Recognition (STT)**
   - Primary: OpenAI Whisper (whisper.cpp for offline)
   - Fallback: Vosk for real-time streaming
   - Languages: 100+ with automatic detection
   - Models: Base (74MB) and Small (244MB) variants

2. **Text-to-Speech (TTS)**
   - Primary: Piper TTS (15-30MB per voice)
   - Multiple voice profiles per domain
   - SSML support for prosody control
   - Emotion-aware synthesis

3. **Voice Activity Detection (VAD)**
   - Silero VAD (1MB model)
   - Energy-based fallback
   - Configurable thresholds

4. **Wake Word Detection**
   - OpenWakeWord framework
   - Custom wake words per domain
   - Low false-positive rates

### Key Strengths
- ✅ Completely offline operation
- ✅ Multi-language support
- ✅ Domain-specific voice personalities
- ✅ Configurable via YAML
- ✅ WebSocket streaming support
- ✅ Emotion detection and adaptation
- ✅ Natural conversation management

### Identified Gaps
- ❌ No dependency management in requirements.txt
- ❌ Mock implementations in some handlers
- ❌ Missing model quantization for efficiency
- ❌ No telemetry/monitoring
- ❌ Limited error recovery
- ❌ No voice authentication/biometrics

## V5 Voice Architecture Design

### Core Principles
1. **Industry Standards Compliance**
   - OpenAI Whisper API compatibility
   - W3C Web Speech API alignment
   - SSML 1.1 specification support

2. **Security First**
   - Audio sanitization
   - Rate limiting on voice endpoints
   - Encrypted audio transmission
   - Voice biometric privacy protection

3. **Performance Optimization**
   - Model quantization (INT8/INT4)
   - Streaming processing pipeline
   - Response caching
   - GPU acceleration when available

4. **Enterprise Features**
   - Multi-tenant support
   - Audit logging
   - Compliance modes (HIPAA, PCI)
   - Analytics and insights

### Proposed V5 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   V5 Voice Module                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐   │
│  │            Voice Pipeline Manager                 │   │
│  │  - Orchestration                                 │   │
│  │  - State Management                              │   │
│  │  - Error Recovery                                │   │
│  └──────────────────────────────────────────────────┘   │
│                           ▼                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  STT Engine  │  │  Processing  │  │  TTS Engine  │ │
│  │              │  │              │  │              │ │
│  │ - Whisper    │  │ - V5 AI Core │  │ - Piper      │ │
│  │ - Vosk       │  │ - Tools      │  │ - Coqui      │ │
│  │ - SpeechBrain│  │ - Context    │  │ - Edge-TTS   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                           ▲                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Supporting Services                       │   │
│  │  - VAD        - Wake Word    - Echo Cancel       │   │
│  │  - Emotion    - Diarization  - Enhancement       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Create V5 Voice Module Structure
```python
V5/
├── voice/
│   ├── __init__.py
│   ├── core/
│   │   ├── pipeline.py         # Main orchestrator
│   │   ├── audio_processor.py  # Audio utilities
│   │   └── state_manager.py    # Conversation state
│   ├── engines/
│   │   ├── stt/
│   │   │   ├── whisper_engine.py
│   │   │   ├── vosk_engine.py
│   │   │   └── base_engine.py
│   │   └── tts/
│   │       ├── piper_engine.py
│   │       ├── coqui_engine.py
│   │       └── base_engine.py
│   ├── services/
│   │   ├── vad_service.py
│   │   ├── wake_word_service.py
│   │   └── emotion_service.py
│   └── config/
│       └── voice_config.py
```

#### 1.2 Dependencies Installation
```python
# requirements_voice.txt
whisper==20231117          # OpenAI Whisper
whisper-cpp-python==0.1.0  # Optimized C++ version
vosk==0.3.45               # Streaming STT
piper-tts==1.2.0           # Fast TTS
TTS==0.22.0                # Coqui TTS
silero-vad==4.0.0          # VAD
webrtcvad==2.0.10          # Audio processing
soundfile==0.12.1          # Audio I/O
numpy==1.24.3              # Audio arrays
torch==2.1.0               # Model runtime
onnxruntime==1.16.0        # ONNX inference
```

### Phase 2: Core Components (Week 2)

#### 2.1 STT Engine Implementation
```python
# V5/voice/engines/stt/whisper_engine.py
import whisper
import numpy as np
from typing import Dict, Optional, Any
from dataclasses import dataclass
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class WhisperConfig:
    model_size: str = "base"
    device: str = "auto"
    language: Optional[str] = None
    task: str = "transcribe"
    temperature: float = 0.0
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    condition_on_previous_text: bool = True
    quantization: Optional[str] = "int8"  # int8, int4, or None

class WhisperEngine:
    """
    Industry-standard Whisper implementation for V5
    Following OpenAI Whisper API specifications
    """
    
    def __init__(self, config: WhisperConfig):
        self.config = config
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load and optionally quantize Whisper model"""
        try:
            # Determine device
            import torch
            if self.config.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.config.device
            
            # Load model
            self.model = whisper.load_model(
                self.config.model_size,
                device=device
            )
            
            # Apply quantization if specified
            if self.config.quantization:
                self._quantize_model()
            
            logger.info(f"Whisper {self.config.model_size} loaded on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            raise
    
    def _quantize_model(self):
        """Apply INT8/INT4 quantization for performance"""
        if self.config.quantization == "int8":
            import torch
            self.model = torch.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8
            )
            logger.info("Applied INT8 quantization")
        # INT4 requires special handling
    
    async def transcribe(
        self, 
        audio: np.ndarray,
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio following OpenAI API format
        
        Returns:
        {
            "text": str,
            "segments": [...],
            "language": str,
            "duration": float,
            "tokens": [...],
            "temperature": float,
            "avg_logprob": float,
            "compression_ratio": float,
            "no_speech_prob": float
        }
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio,
            language,
            initial_prompt
        )
        return result
    
    def _transcribe_sync(
        self,
        audio: np.ndarray,
        language: Optional[str],
        initial_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Synchronous transcription"""
        options = {
            "language": language or self.config.language,
            "task": self.config.task,
            "temperature": self.config.temperature,
            "compression_ratio_threshold": self.config.compression_ratio_threshold,
            "logprob_threshold": self.config.logprob_threshold,
            "no_speech_threshold": self.config.no_speech_threshold,
            "condition_on_previous_text": self.config.condition_on_previous_text,
        }
        
        if initial_prompt:
            options["initial_prompt"] = initial_prompt
        
        result = self.model.transcribe(audio, **options)
        
        # Add performance metrics
        result["duration"] = len(audio) / 16000  # Assuming 16kHz
        
        return result
    
    async def stream_transcribe(self, audio_stream):
        """Real-time streaming transcription"""
        # Implementation for chunk-by-chunk processing
        pass
```

#### 2.2 TTS Engine Implementation
```python
# V5/voice/engines/tts/piper_engine.py
import numpy as np
from typing import Dict, Optional, Any
import piper
import asyncio
import logging

logger = logging.getLogger(__name__)

class PiperEngine:
    """
    High-performance TTS engine for V5
    """
    
    def __init__(self, voice_model: str, config: Dict[str, Any]):
        self.voice_model = voice_model
        self.config = config
        self.synthesizer = None
        self._load_model()
    
    def _load_model(self):
        """Load Piper voice model"""
        self.synthesizer = piper.PiperVoice(
            model_path=self.voice_model,
            config_path=f"{self.voice_model}.json",
            use_cuda=self.config.get("use_cuda", False)
        )
    
    async def synthesize(
        self,
        text: str,
        voice_params: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Synthesize speech from text
        
        Args:
            text: Input text (supports SSML)
            voice_params: Speed, pitch, volume adjustments
            
        Returns:
            Audio array at specified sample rate
        """
        params = voice_params or {}
        
        # Parse SSML if present
        if text.startswith("<speak>"):
            text = self._parse_ssml(text)
        
        # Apply voice parameters
        speed = params.get("speed", 1.0)
        pitch = params.get("pitch", 0)
        
        # Generate audio
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
            speed,
            pitch
        )
        
        return audio
    
    def _synthesize_sync(self, text: str, speed: float, pitch: int) -> np.ndarray:
        """Synchronous synthesis"""
        audio = self.synthesizer.synthesize(
            text,
            speaker_id=0,
            length_scale=1.0/speed,
            noise_scale=0.667,
            noise_w=0.8
        )
        return np.array(audio, dtype=np.float32)
    
    def _parse_ssml(self, ssml: str) -> str:
        """Parse SSML markup for Piper"""
        # Simplified SSML parsing
        import re
        text = re.sub(r'<[^>]+>', '', ssml)
        return text
```

### Phase 3: Integration with V5 Core (Week 3)

#### 3.1 Voice Service for V5
```python
# V5/voice/voice_service.py
from typing import Dict, Any, Optional
import numpy as np
import asyncio
from dataclasses import dataclass

from V5.services.smart_ai_engine_v5 import SmartAIEngineV5
from V5.core.authentication import get_current_user
from V5.core.rate_limiter import rate_limit
from .engines.stt.whisper_engine import WhisperEngine, WhisperConfig
from .engines.tts.piper_engine import PiperEngine
from .services.vad_service import VADService

@dataclass
class VoiceSession:
    """Voice session state"""
    session_id: str
    user_id: str
    domain: str = "default"
    language: str = "en"
    context: Dict[str, Any] = None
    is_active: bool = True

class V5VoiceService:
    """
    Main voice service for V5
    Integrates with V5 AI Engine and security features
    """
    
    def __init__(self, ai_engine: SmartAIEngineV5):
        self.ai_engine = ai_engine
        self.sessions: Dict[str, VoiceSession] = {}
        
        # Initialize engines
        self.stt_engine = WhisperEngine(WhisperConfig())
        self.tts_engine = PiperEngine(
            "models/piper/en_US-amy-medium.onnx",
            {"use_cuda": False}
        )
        self.vad = VADService()
        
    async def process_audio(
        self,
        audio: np.ndarray,
        session_id: str,
        user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main audio processing pipeline
        
        Args:
            audio: Input audio array
            session_id: Session identifier
            user: Authenticated user from V5 auth
            
        Returns:
            Response with transcription and synthesis
        """
        
        # Get or create session
        session = self._get_session(session_id, user["user_id"])
        
        # 1. Voice Activity Detection
        if not self.vad.is_speech(audio):
            return {"status": "no_speech"}
        
        # 2. Transcribe audio
        transcription = await self.stt_engine.transcribe(
            audio,
            language=session.language
        )
        
        # 3. Process through V5 AI Engine
        ai_response = await self.ai_engine.process_message(
            message=transcription["text"],
            context={
                "user_id": user["user_id"],
                "session_id": session_id,
                "input_mode": "voice",
                "language": transcription["language"]
            },
            session_id=session_id
        )
        
        # 4. Generate voice response
        voice_audio = await self.tts_engine.synthesize(
            ai_response["response"],
            voice_params=self._get_voice_params(session.domain)
        )
        
        return {
            "transcription": transcription,
            "ai_response": ai_response,
            "voice_audio": voice_audio.tolist(),  # Convert for JSON
            "session_id": session_id,
            "metadata": {
                "duration_ms": len(audio) * 1000 / 16000,
                "language": transcription["language"],
                "domain": session.domain
            }
        }
    
    def _get_session(self, session_id: str, user_id: str) -> VoiceSession:
        """Get or create voice session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = VoiceSession(
                session_id=session_id,
                user_id=user_id
            )
        return self.sessions[session_id]
    
    def _get_voice_params(self, domain: str) -> Dict:
        """Get domain-specific voice parameters"""
        domain_voices = {
            "dispensary": {"speed": 0.95, "pitch": -1},
            "healthcare": {"speed": 0.9, "pitch": 0},
            "legal": {"speed": 0.85, "pitch": -2}
        }
        return domain_voices.get(domain, {"speed": 1.0, "pitch": 0})
```

#### 3.2 Voice API Endpoints for V5
```python
# V5/api/voice_endpoints.py
from fastapi import APIRouter, Depends, UploadFile, File, WebSocket
from fastapi.responses import StreamingResponse
import numpy as np
import base64
import json

from V5.core.authentication import get_current_user
from V5.core.rate_limiter import rate_limit
from V5.voice.voice_service import V5VoiceService

router = APIRouter(prefix="/api/v5/voice", tags=["voice"])

# Initialize voice service (will be injected)
voice_service = None

@router.post("/transcribe")
@rate_limit(resource="voice", requests=30, seconds=60)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    user: Dict = Depends(get_current_user)
):
    """
    Transcribe audio to text
    OpenAI Whisper API compatible
    """
    # Read audio file
    audio_data = await audio_file.read()
    
    # Convert to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    # Transcribe
    result = await voice_service.stt_engine.transcribe(audio_array)
    
    return {
        "text": result["text"],
        "language": result["language"],
        "duration": result["duration"],
        "segments": result.get("segments", [])
    }

@router.post("/synthesize")
@rate_limit(resource="voice", requests=20, seconds=60)
async def synthesize_speech(
    text: str,
    voice: str = "default",
    user: Dict = Depends(get_current_user)
):
    """
    Convert text to speech
    Returns audio stream
    """
    # Generate speech
    audio = await voice_service.tts_engine.synthesize(text)
    
    # Convert to WAV format
    import io
    import wave
    
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(22050)
        wav.writeframes((audio * 32767).astype(np.int16).tobytes())
    
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=speech.wav"}
    )

@router.websocket("/stream")
async def voice_stream(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time voice streaming
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_bytes()
            
            # Process audio
            audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Get user from session
            user = {"user_id": "websocket_user"}  # Get from session in production
            
            # Process through voice service
            result = await voice_service.process_audio(
                audio_array,
                session_id,
                user
            )
            
            # Send response
            await websocket.send_json(result)
            
    except Exception as e:
        await websocket.close(code=1000)
```

### Phase 4: Advanced Features (Week 4)

#### 4.1 Conversation Management
```python
# V5/voice/services/conversation_manager.py
class ConversationManager:
    """
    Natural conversation flow management
    """
    
    def __init__(self):
        self.turn_history = []
        self.interruption_handler = InterruptionHandler()
        self.backchannel_generator = BackchannelGenerator()
    
    async def manage_turn(self, audio_energy: float, is_ai_speaking: bool):
        """Handle turn-taking in conversation"""
        
        if is_ai_speaking and audio_energy > 0.7:
            # User interruption detected
            return {"action": "yield_turn", "confidence": 0.9}
        
        if not is_ai_speaking and self.should_backchannel():
            # Generate backchannel response
            return {"action": "backchannel", "response": "uh-huh"}
        
        return {"action": "continue"}
```

#### 4.2 Multi-Language Support
```python
# V5/voice/services/language_detector.py
class LanguageDetector:
    """
    Automatic language detection service
    """
    
    def detect(self, audio: np.ndarray) -> str:
        """Detect language from audio"""
        # Use Whisper's language detection
        pass
```

## Testing Strategy

### Unit Tests
```python
# V5/tests/test_voice.py
import pytest
import numpy as np
from V5.voice.engines.stt.whisper_engine import WhisperEngine

@pytest.mark.asyncio
async def test_whisper_transcription():
    """Test Whisper transcription"""
    engine = WhisperEngine(WhisperConfig(model_size="tiny"))
    
    # Generate test audio (silence)
    audio = np.zeros(16000, dtype=np.float32)
    
    result = await engine.transcribe(audio)
    
    assert "text" in result
    assert "language" in result
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_voice_pipeline():
    """Test complete voice pipeline"""
    service = V5VoiceService(mock_ai_engine)
    
    # Test audio processing
    audio = generate_test_audio("Hello, world")
    result = await service.process_audio(
        audio,
        "test_session",
        {"user_id": "test_user"}
    )
    
    assert result["status"] != "error"
    assert "transcription" in result
    assert "voice_audio" in result
```

### Performance Benchmarks
```python
def benchmark_whisper_models():
    """Benchmark different Whisper models"""
    models = ["tiny", "base", "small"]
    
    for model in models:
        engine = WhisperEngine(WhisperConfig(model_size=model))
        
        # Measure transcription speed
        start = time.time()
        result = engine.transcribe(test_audio)
        duration = time.time() - start
        
        print(f"{model}: {duration:.3f}s, RTF: {duration/audio_duration:.2f}")
```

## Security Considerations

### 1. Audio Input Validation
```python
def validate_audio(audio: np.ndarray) -> bool:
    """Validate audio input for security"""
    # Check for malicious payloads
    if audio.shape[0] > 16000 * 60 * 5:  # Max 5 minutes
        raise ValueError("Audio too long")
    
    # Check for unusual patterns
    if np.abs(audio).max() > 10:  # Abnormal amplitude
        raise ValueError("Invalid audio amplitude")
    
    return True
```

### 2. Rate Limiting
- Transcription: 30 requests/minute
- Synthesis: 20 requests/minute
- Streaming: 1 concurrent connection per user

### 3. Privacy Protection
- No audio storage by default
- Anonymized transcription logging
- Voice biometric hashing only

## Performance Optimization

### 1. Model Quantization
```python
# Reduce model size by 75% with <2% accuracy loss
quantized_model = quantize_int8(whisper_model)
```

### 2. Response Caching
```python
# Cache common TTS responses
cache_key = hashlib.md5(f"{text}_{voice}_{params}".encode()).hexdigest()
if cache_key in tts_cache:
    return tts_cache[cache_key]
```

### 3. GPU Acceleration
```python
# Auto-detect and use GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
```

## Migration Timeline

| Week | Phase | Tasks | Deliverables |
|------|-------|-------|-------------|
| 1 | Infrastructure | Module setup, dependencies | V5/voice/ structure |
| 2 | Core Components | STT/TTS engines | Working transcription/synthesis |
| 3 | Integration | V5 AI engine integration | Voice-enabled API |
| 4 | Advanced Features | Conversation, languages | Complete voice system |
| 5 | Testing & Optimization | Performance, security | Production-ready |

## Success Metrics

1. **Performance**
   - Transcription RTF < 0.3 (3x faster than real-time)
   - TTS latency < 100ms
   - Memory usage < 1GB

2. **Quality**
   - Word Error Rate < 5%
   - TTS naturalness score > 4.0/5.0
   - Language detection accuracy > 95%

3. **Reliability**
   - 99.9% uptime
   - Error recovery < 1s
   - Concurrent sessions > 100

## Recommended Libraries

### Required
```python
# Core
whisper==20231117
piper-tts==1.2.0
silero-vad==4.0.0
webrtcvad==2.0.10

# Audio Processing
soundfile==0.12.1
librosa==0.10.1
numpy==1.24.3

# Performance
onnxruntime==1.16.0
torch==2.1.0
```

### Optional
```python
# Advanced Features
TTS==0.22.0         # Coqui TTS for voice cloning
vosk==0.3.45        # Streaming STT
speechbrain==1.0.0  # Speaker diarization
```

## Conclusion

The V5 voice implementation will bring enterprise-grade, offline voice capabilities with:

✅ **Industry Standards**: OpenAI Whisper API compatibility
✅ **Security**: Full integration with V5 security features  
✅ **Performance**: 3x faster with quantization
✅ **Scalability**: Support for 100+ concurrent sessions
✅ **Flexibility**: Domain-specific voices and behaviors

The modular architecture ensures easy maintenance and future enhancements while maintaining complete offline operation for privacy and compliance requirements.