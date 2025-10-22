# Personality Management API Documentation

**Base URL:** `/api/personalities`

**Purpose:** Manage AI personalities with voice sample uploads and tier-based limits

---

## Endpoints

### 1. Upload Personality Voice Sample

**`POST /api/personalities/{personality_id}/voice`**

Upload a voice sample for voice cloning.

**Request:**
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Path Parameters:**
  - `personality_id` (UUID) - Personality identifier

- **Form Data:**
  - `audio` (File) - Voice sample audio file (WAV format)

**Audio Requirements:**
- **Format:** WAV (required)
- **Duration:** 5-30 seconds (optimal: 15-20s for XTTS v2)
- **Sample Rate:** 16000Hz minimum (recommended: 22050Hz or 44100Hz)
- **Bit Depth:** 16-bit minimum (24-bit recommended)
- **Channels:** Mono or Stereo
- **File Size:** Maximum 10MB
- **Quality:** Quiet environment, clear speech, no background music

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/personalities/{personality_id}/voice" \
  -F "audio=@marcel_voice_sample.wav"
```

**Example (Python):**
```python
import requests

personality_id = "550e8400-e29b-41d4-a716-446655440000"
files = {"audio": open("marcel_voice.wav", "rb")}

response = requests.post(
    f"http://localhost:8000/api/personalities/{personality_id}/voice",
    files=files
)

print(response.json())
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Voice sample uploaded successfully",
  "personality_id": "550e8400-e29b-41d4-a716-446655440000",
  "voice_config": {
    "sample_path": "/data/voices/personalities/550e8400-marcel-a3b2c1d4e5f6.wav",
    "sample_metadata": {
      "duration": 18.5,
      "sample_rate": 44100,
      "channels": 1,
      "bit_depth": 16,
      "file_size_mb": 1.42,
      "uploaded_at": "2025-10-20T19:30:00.000Z"
    },
    "provider": "xtts_v2",
    "fallback_chain": ["xtts_v2", "google_tts", "piper"]
  },
  "validation": {
    "valid": true,
    "duration": 18.5,
    "channels": 1,
    "sample_rate": 44100,
    "bit_depth": 16,
    "file_size_mb": 1.42,
    "format": "wav"
  },
  "file_path": "/data/voices/personalities/550e8400-marcel-a3b2c1d4e5f6.wav"
}
```

**Errors:**
- `400` - Invalid audio format or validation failed
- `404` - Personality not found
- `500` - Server error

---

### 2. Get Personality Voice Configuration

**`GET /api/personalities/{personality_id}/voice`**

Retrieve voice configuration for a personality.

**Request:**
- **Method:** GET
- **Path Parameters:**
  - `personality_id` (UUID) - Personality identifier

**Example:**
```bash
curl "http://localhost:8000/api/personalities/{personality_id}/voice"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "personality_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "marcel",
  "has_voice_sample": true,
  "voice_config": {
    "sample_path": "/data/voices/personalities/550e8400-marcel-a3b2c1d4e5f6.wav",
    "sample_metadata": {
      "duration": 18.5,
      "sample_rate": 44100,
      "channels": 1,
      "bit_depth": 16,
      "uploaded_at": "2025-10-20T19:30:00.000Z"
    },
    "provider": "xtts_v2",
    "fallback_chain": ["xtts_v2", "google_tts", "piper"]
  }
}
```

---

### 3. Delete Personality Voice Sample

**`DELETE /api/personalities/{personality_id}/voice`**

Remove voice sample for a personality.

**Request:**
- **Method:** DELETE
- **Path Parameters:**
  - `personality_id` (UUID) - Personality identifier

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/personalities/{personality_id}/voice"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Voice sample deleted successfully",
  "personality_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4. List Personalities

**`GET /api/personalities`**

List all personalities for a tenant.

**Request:**
- **Method:** GET
- **Query Parameters:**
  - `tenant_id` (UUID, optional) - Filter by tenant
  - `include_defaults` (boolean, default: true) - Include default personalities

**Example:**
```bash
curl "http://localhost:8000/api/personalities?tenant_id={tenant_id}&include_defaults=true"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "personalities": [
    {
      "id": "default-marcel-uuid",
      "tenant_id": "tenant-uuid",
      "name": "marcel",
      "description": "Professional and knowledgeable cannabis expert",
      "traits": {
        "tone": "professional",
        "expertise": "high"
      },
      "is_default": true,
      "has_voice_sample": false,
      "voice_provider": "piper",
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-01T00:00:00.000Z"
    },
    {
      "id": "custom-personality-uuid",
      "tenant_id": "tenant-uuid",
      "name": "custom_budtender",
      "description": "Custom friendly budtender",
      "traits": {
        "tone": "casual",
        "expertise": "medium"
      },
      "is_default": false,
      "has_voice_sample": true,
      "voice_provider": "xtts_v2",
      "created_at": "2025-10-15T10:00:00.000Z",
      "updated_at": "2025-10-20T19:30:00.000Z"
    }
  ],
  "count": 2
}
```

---

### 5. Get Personality Limits

**`GET /api/personalities/limits/{tenant_id}`**

Get subscription tier-based personality limits.

**Request:**
- **Method:** GET
- **Path Parameters:**
  - `tenant_id` (UUID) - Tenant identifier

**Example:**
```bash
curl "http://localhost:8000/api/personalities/limits/{tenant_id}"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "tenant_id": "tenant-uuid",
  "subscription_tier": "professional",
  "limits": {
    "default_personalities": 3,
    "custom_personalities_allowed": 3,
    "custom_personalities_used": 1,
    "custom_personalities_remaining": 2,
    "can_create_more": true
  },
  "tier_details": {
    "free": {
      "custom": 0,
      "description": "3 default personalities only"
    },
    "small_business": {
      "custom": 2,
      "description": "3 defaults + 2 custom"
    },
    "professional": {
      "custom": 3,
      "description": "3 defaults + 3 custom"
    },
    "enterprise": {
      "custom": 5,
      "description": "3 defaults + 5 custom"
    }
  }
}
```

---

### 6. Validate Voice Sample

**`POST /api/personalities/validate-voice`**

Validate voice sample without saving (client-side preview).

**Request:**
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Form Data:**
  - `audio` (File) - Voice sample audio file

**Example:**
```bash
curl -X POST "http://localhost:8000/api/personalities/validate-voice" \
  -F "audio=@test_voice.wav"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "validation": {
    "valid": true,
    "duration": 18.5,
    "channels": 1,
    "sample_rate": 44100,
    "bit_depth": 16,
    "file_size_mb": 1.42,
    "format": "wav"
  },
  "quality": {
    "score": 95,
    "rating": "excellent",
    "warnings": []
  },
  "recommendations": [
    "Record in a quiet environment (minimal background noise)",
    "Keep consistent distance from microphone (6-12 inches)",
    "Speak naturally with varied intonation",
    "Avoid music, echo, or other speakers in the recording",
    "Use WAV format at 22050Hz or 44100Hz, 16-bit or higher"
  ]
}
```

**Quality Ratings:**
- `excellent` (90-100): Optimal for voice cloning
- `good` (70-89): Will work well
- `acceptable` (50-69): May have quality issues
- `poor` (<50): Not recommended

---

## Subscription Tier Limits

| Tier | Default Personalities | Custom Personalities | Total |
|------|----------------------|----------------------|-------|
| **Free** | 3 (marcel, shanté, zac) | 0 | 3 |
| **Small Business** | 3 | +2 | 5 |
| **Professional** | 3 | +3 | 6 |
| **Enterprise** | 3 | +5 | 8 |

**Default personalities are:**
1. **marcel** - Professional and knowledgeable
2. **shanté** - Friendly and approachable
3. **zac** - Casual and laid-back

These are hardcoded and read-only (cannot be edited or deleted).

---

## Voice Sample Guidelines

### Optimal Recording Settings

| Parameter | Recommended | Minimum | Notes |
|-----------|-------------|---------|-------|
| **Duration** | 15-20 seconds | 5 seconds | XTTS v2 optimal: 15-20s, StyleTTS2: 5-8s |
| **Format** | WAV | WAV | Only WAV supported |
| **Sample Rate** | 44100Hz | 16000Hz | Higher is better |
| **Bit Depth** | 24-bit | 16-bit | Professional quality |
| **Channels** | Mono | Mono/Stereo | Mono preferred |
| **File Size** | 1-3 MB | - | Maximum 10MB |

### Recording Best Practices

✅ **Do:**
- Record in a quiet room with minimal echo
- Speak naturally with varied intonation
- Keep consistent microphone distance (6-12 inches)
- Include varied sentences (not monotone)
- Use clear, professional-quality microphone

❌ **Don't:**
- Record with background music or TV
- Use heavily compressed audio (MP3)
- Include other people speaking
- Record in reverberant spaces (bathroom, empty room)
- Speak in a monotone voice

### Example Recording Script

For best voice cloning results, record yourself saying:

> "Hello, welcome to WeedGo! I'm here to help you find the perfect cannabis products for your needs. Whether you're looking for relaxation, pain relief, or creative inspiration, I can guide you through our selection. What brings you in today? Let me know how I can help."

**Duration:** ~15-18 seconds
**Content:** Natural conversational tone with question

---

## Integration with VoiceModelRouter

After uploading a voice sample, the system:

1. **Validates** audio format and quality
2. **Saves** file to `/data/voices/personalities/{uuid}-{name}-{hash}.wav`
3. **Updates** personality `voice_config` in database
4. **Loads** voice sample into VoiceModelRouter cache (XTTS v2, StyleTTS2)

### Voice Synthesis Usage

```python
from core.voice.voice_model_router import (
    VoiceModelRouter,
    VoiceQuality,
    SynthesisContext
)

# Initialize router
router = VoiceModelRouter(device="cpu")
await router.initialize()

# Synthesize with personality voice
context = SynthesisContext(
    personality_id="550e8400-e29b-41d4-a716-446655440000",  # marcel with custom voice
    language="en",
    quality=VoiceQuality.HIGH,
    speed=1.0
)

result = await router.synthesize(
    text="Welcome to WeedGo! How can I help you today?",
    context=context
)

# result.audio contains cloned voice audio
```

---

## Error Handling

### Common Errors

#### 400 - Bad Request

**Audio too short:**
```json
{
  "detail": "Audio too short: 3.2s. Must be at least 5.0s for good voice cloning quality"
}
```

**Invalid format:**
```json
{
  "detail": "Invalid WAV file: Error reading header. Please upload a valid WAV audio file"
}
```

**Sample rate too low:**
```json
{
  "detail": "Sample rate too low: 8000Hz. Must be at least 16000Hz (recommended: 22050Hz or 44100Hz)"
}
```

#### 404 - Not Found

```json
{
  "detail": "Personality 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

#### 413 - Payload Too Large

```json
{
  "detail": "File too large: 12.5MB. Maximum is 10MB"
}
```

---

## Frontend Integration Example

### React Component (Voice Upload)

```typescript
import { useState } from 'react';

const VoiceUpload = ({ personalityId }: { personalityId: string }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [validation, setValidation] = useState<any>(null);

  const validateVoice = async (audioFile: File) => {
    const formData = new FormData();
    formData.append('audio', audioFile);

    const response = await fetch('/api/personalities/validate-voice', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    setValidation(result);
    return result;
  };

  const uploadVoice = async () => {
    if (!file) return;

    setUploading(true);

    const formData = new FormData();
    formData.append('audio', file);

    try {
      const response = await fetch(`/api/personalities/${personalityId}/voice`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.status === 'success') {
        alert('Voice uploaded successfully!');
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".wav"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) {
            setFile(f);
            validateVoice(f);
          }
        }}
      />

      {validation && (
        <div>
          <h4>Quality: {validation.quality.rating}</h4>
          <p>Score: {validation.quality.score}/100</p>
          {validation.quality.warnings.map((w: string) => (
            <p key={w} style={{ color: 'orange' }}>{w}</p>
          ))}
        </div>
      )}

      <button onClick={uploadVoice} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload Voice Sample'}
      </button>
    </div>
  );
};
```

---

## Storage Structure

```
/data/voices/personalities/
├── 550e8400-marcel-a3b2c1d4e5f6.wav       # Custom marcel voice
├── 660e9500-shante-b4c3d2e1f0a9.wav      # Custom shanté voice
├── 770ea600-custom-c5d4e3f2a1b8.wav      # Custom personality voice
└── ...
```

**Filename Format:** `{personality_id}-{name}-{file_hash}.wav`

- `personality_id`: UUID of personality
- `name`: Personality name (sanitized)
- `file_hash`: First 12 chars of SHA256 hash (for uniqueness)

---

**Created:** 2025-10-20
**Version:** 1.0
**Maintainer:** WeedGo Engineering Team
