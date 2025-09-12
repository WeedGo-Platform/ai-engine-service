# Voice API Documentation

## Overview
The Voice API provides comprehensive text-to-speech (TTS) and speech-to-text (STT) capabilities for the WeedGo AI Engine.

## Base URL
```
http://localhost:5024/api/voice
```

## Interactive Documentation
- **Swagger UI**: http://localhost:5024/docs
- **ReDoc**: http://localhost:5024/redoc

## Endpoints

### 1. Voice Selection and Configuration

#### GET /api/voice/voices
Get list of available TTS voices with current selection.

**Response:**
```json
{
  "status": "success",
  "voices": ["en-US-Standard-A", "en-US-Wavenet-D", ...],
  "current_voice": "en-US-Standard-A"
}
```

#### POST /api/voice/voice
Set the current TTS voice for the session.

**Request:**
```
voice_id: string (required) - Voice identifier
voice_settings: string (optional) - JSON string with settings
```

**Example:**
```bash
curl -X POST http://localhost:5024/api/voice/voice \
  -F "voice_id=en-US-Wavenet-D" \
  -F 'voice_settings={"speed": 1.2, "pitch": 5, "volume": 0.9}'
```

**Response:**
```json
{
  "status": "success",
  "message": "Voice changed to en-US-Wavenet-D",
  "voice_id": "en-US-Wavenet-D",
  "settings": {
    "speed": 1.2,
    "pitch": 5,
    "volume": 0.9
  }
}
```

#### GET /api/voice/voice
Get the current voice configuration.

**Response:**
```json
{
  "status": "success",
  "current_voice": "en-US-Wavenet-D",
  "settings": {
    "speed": 1.2,
    "pitch": 5,
    "volume": 0.9
  },
  "available_settings": {
    "speed": "Speech rate (0.5-2.0)",
    "pitch": "Voice pitch adjustment (-20 to 20)",
    "volume": "Volume level (0.0-1.0)",
    "emotion": "Emotional tone (neutral, happy, sad, etc.)"
  }
}
```

### 2. Speech Processing

#### POST /api/voice/transcribe
Transcribe audio to text.

**Parameters:**
- `audio`: Audio file (WAV, MP3, etc.)
- `language`: Language code (optional)
- `mode`: Processing mode (manual, auto_vad, continuous)

#### POST /api/voice/synthesize
Convert text to speech.

**Parameters:**
- `text`: Text to synthesize
- `voice`: Voice ID (optional, uses current if not specified)
- `language`: Language code (optional)
- `speed`: Speech rate (0.5-2.0)
- `format`: Audio format (wav, mp3)

#### POST /api/voice/detect_speech
Detect speech segments in audio using VAD.

**Parameters:**
- `audio`: Audio file
- `threshold`: Detection threshold (0.0-1.0)

### 3. Unified Processing

#### POST /api/voice/process
Unified endpoint for voice processing.

**Parameters:**
- `audio`: Audio file (optional)
- `audio_base64`: Base64 encoded audio (optional)
- `text`: Text for synthesis (optional)
- `action`: Action to perform (transcribe, synthesize, detect)
- `language`: Language code (optional)
- `voice`: Voice for synthesis (optional)
- `domain`: Domain context (general, healthcare, budtender, legal)

### 4. Status and Metrics

#### GET /api/voice/status
Get voice system status.

**Response:**
```json
{
  "status": "success",
  "initialized": true,
  "components": {
    "stt": {
      "state": "ready",
      "model": "whisper-base"
    },
    "tts": {
      "state": "ready"
    },
    "vad": {
      "state": "ready"
    }
  },
  "session": {
    "id": "session-123",
    "domain": "general"
  }
}
```

#### GET /api/voice/metrics
Get voice pipeline performance metrics.

**Response:**
```json
{
  "status": "success",
  "metrics": {
    "transcriptions": 150,
    "synthesis_requests": 75,
    "avg_transcription_time": 250,
    "avg_synthesis_time": 180
  }
}
```

## Voice Settings Configuration

### Available Voice Settings

| Setting | Type | Range | Description |
|---------|------|-------|-------------|
| speed | float | 0.5-2.0 | Speech rate multiplier |
| pitch | int | -20 to 20 | Voice pitch adjustment in semitones |
| volume | float | 0.0-1.0 | Volume level |
| emotion | string | varies | Emotional tone (neutral, happy, sad, angry, excited) |

### Example Usage Scenarios

#### 1. Fast-paced Assistant
```json
{
  "speed": 1.3,
  "pitch": 2,
  "emotion": "excited"
}
```

#### 2. Calm Medical Advisor
```json
{
  "speed": 0.9,
  "pitch": -2,
  "emotion": "calm",
  "volume": 0.8
}
```

#### 3. Professional Customer Service
```json
{
  "speed": 1.0,
  "pitch": 0,
  "emotion": "neutral",
  "volume": 0.95
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing the issue"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (voice not found)
- `500`: Internal Server Error

## Notes

- The voice selection persists for the duration of the session
- If no voice is specified for synthesis, the current voice is used
- Voice settings are optional and have sensible defaults
- The system supports multiple languages based on the TTS/STT engine capabilities