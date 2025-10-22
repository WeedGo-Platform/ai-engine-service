# Voice Implementation Architecture for AI Personalities

## Executive Summary

This document outlines the implementation approach for adding voice capabilities to AI personalities, including voice training/cloning for fully customized voices.

---

## Table of Contents

1. [Voice Implementation Options](#voice-implementation-options)
2. [Recommended Approach](#recommended-approach)
3. [Voice Training & Cloning](#voice-training--cloning)
4. [Architecture & Integration](#architecture--integration)
5. [Personality Integration into Agent Flow](#personality-integration-into-agent-flow)
6. [Cost Analysis](#cost-analysis)
7. [Implementation Phases](#implementation-phases)

---

## Voice Implementation Options

### Option 1: ElevenLabs (RECOMMENDED) ⭐

**Why ElevenLabs?**
- ✅ **Best-in-class voice cloning** from just 1-10 minutes of audio
- ✅ **Professional quality** - sounds completely natural
- ✅ **Voice customization** - adjust stability, clarity, style
- ✅ **Multiple emotions** - can convey enthusiasm, calmness, etc.
- ✅ **Streaming support** - real-time audio generation
- ✅ **Voice library** - 1000+ pre-made voices if no training
- ✅ **Multi-language** - supports 29 languages
- ✅ **API-first** - easy integration

**Pricing:**
- Free tier: 10,000 characters/month (~20 minutes audio)
- Creator: $5/month - 30,000 characters (~1 hour audio)
- Pro: $22/month - 100,000 characters (~3 hours audio)
- Scale: $99/month - 500,000 characters (~15 hours audio)
- Business: $330/month - 2M characters (~60 hours audio)

**Voice Cloning Process:**
1. Upload 1-10 minutes of clean audio samples
2. ElevenLabs trains a custom voice model (takes ~10-30 minutes)
3. Voice is available via API with unique voice_id
4. Can fine-tune with additional samples

**Integration:**
```python
from elevenlabs import generate, Voice, VoiceSettings

audio = generate(
    text="Hey! Welcome! What's bringing you in today?",
    voice=Voice(
        voice_id="marcel_custom_voice_id",
        settings=VoiceSettings(
            stability=0.75,      # More stable = less variation
            similarity_boost=0.85, # Higher = closer to training samples
            style=0.5,           # Emotional range
            use_speaker_boost=True
        )
    ),
    model="eleven_multilingual_v2"
)
```

---

### Option 2: Play.ht

**Pros:**
- ✅ Voice cloning available
- ✅ Good quality voices
- ✅ Emotion control
- ✅ SSML support for fine control

**Cons:**
- ❌ More expensive than ElevenLabs
- ❌ Less natural-sounding than ElevenLabs
- ❌ Smaller voice library

**Pricing:**
- Personal: $31.20/month - 75k characters
- Professional: $79.20/month - 300k characters

---

### Option 3: Google Cloud Text-to-Speech

**Pros:**
- ✅ WavNet/Neural2 voices sound good
- ✅ Very scalable (Google infrastructure)
- ✅ SSML support for pitch, speed, emphasis
- ✅ Pay-per-use pricing

**Cons:**
- ❌ **NO voice cloning/training** - pre-made voices only
- ❌ Less natural than ElevenLabs
- ❌ Limited emotion control

**Pricing:**
- Neural2 voices: $16 per 1 million characters
- Standard voices: $4 per 1 million characters

**Without voice cloning, we can't create "Marcel's unique voice"**

---

### Option 4: OpenAI TTS

**Pros:**
- ✅ Good quality
- ✅ Simple API
- ✅ 6 pre-made voices
- ✅ Affordable

**Cons:**
- ❌ **NO voice cloning** - only 6 voices available
- ❌ Limited customization
- ❌ No emotion control

**Pricing:**
- $15 per 1 million characters

**Cannot create custom voices**

---

### Option 5: Coqui TTS (Open Source, Self-Hosted)

**Pros:**
- ✅ Voice cloning supported
- ✅ Free (self-hosted)
- ✅ Full control over data
- ✅ Can fine-tune models

**Cons:**
- ❌ Requires GPU infrastructure ($$$)
- ❌ Lower quality than commercial solutions
- ❌ Significant engineering effort
- ❌ Voice training takes hours, not minutes
- ❌ Maintenance overhead

**Cost:**
- GPU instance: ~$500-1000/month (AWS p3.2xlarge or similar)
- Engineering time: 2-4 weeks initial setup
- Ongoing maintenance

**Not recommended unless data sovereignty is critical**

---

## Recommended Approach

### ✅ **ElevenLabs for Custom Voice Training + Google Cloud TTS as Fallback**

**Why this hybrid approach?**

1. **ElevenLabs for Premium/Custom Personalities:**
   - Tenant creates custom personality with voice training
   - Upload 1-10 min audio samples (e.g., recording "Marcel" character)
   - ElevenLabs creates unique voice_id
   - Store voice_id in `ai_personalities.voice_config`

2. **Google Cloud TTS for Default Personalities:**
   - marcel, shanté, zac use pre-selected Neural2 voices
   - More cost-effective for high-volume usage
   - Still good quality

3. **Fallback Strategy:**
   - If ElevenLabs API fails → fallback to Google Cloud TTS
   - If tenant exceeds ElevenLabs quota → switch to Google TTS
   - Graceful degradation

**Cost Optimization:**
```
Average conversation: 500 words = 3,000 characters
ElevenLabs Pro ($22/month): 100,000 chars = ~33 conversations/month
Google Cloud Neural2: $16 per 1M chars = ~333 conversations for $0.048

Strategy:
- Use ElevenLabs for custom personalities (lower volume)
- Use Google TTS for default personalities (high volume)
- Total cost: ~$30-50/month for typical tenant
```

---

## Voice Training & Cloning

### How It Works (ElevenLabs)

#### Step 1: Audio Sample Collection

**Requirements:**
- **Duration**: 1-10 minutes of audio
- **Format**: MP3, WAV, M4A (high quality)
- **Content**: Varied sentences, different emotions
- **Quality**:
  - Clear audio (no background noise)
  - Consistent volume
  - Single speaker only
  - Native language of the voice

**Sample Script for Recording:**
```
Hi there! Welcome to [Store Name]. I'm so excited to help you find the perfect product today.

Let me tell you about some of our best sellers. We have some amazing strains that our customers absolutely love.

Are you looking for something to help you relax after a long day? Or maybe you need something more energizing?

I'd be happy to answer any questions you have. Feel free to ask me anything about our products!

That's a great choice! This strain has fantastic reviews. I think you're really going to enjoy it.

Thank you so much for coming in today. Have a wonderful day, and I hope to see you again soon!
```

**Why this script?**
- ✅ Covers different emotions (excited, helpful, curious, friendly)
- ✅ Includes greetings and closings
- ✅ Product-specific language
- ✅ Questions and statements
- ✅ Natural conversational flow

#### Step 2: Upload & Training

**In the UI:**
```
┌────────────────────────────────────────────────────────┐
│  🎤 Voice Training                                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Upload 1-10 minutes of audio samples to create a     │
│  unique voice for this personality.                    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  📎 Upload Audio Samples                         ││
│  │                                                   ││
│  │  [Click to upload or drag files here]            ││
│  │                                                   ││
│  │  Accepted formats: MP3, WAV, M4A                 ││
│  │  Max file size: 10 MB per file                   ││
│  │  Max duration: 10 minutes total                  ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  Uploaded Samples:                                     │
│  ┌──────────────────────────────────────────────────┐│
│  │  🎵 marcel_voice_sample_1.mp3     [✕]           ││
│  │     Duration: 3:24 | Size: 4.2 MB               ││
│  │                                                  ││
│  │  🎵 marcel_voice_sample_2.wav     [✕]           ││
│  │     Duration: 2:15 | Size: 3.1 MB               ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  Total Duration: 5:39 / 10:00                         │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  💡 Tips for Best Results:                       ││
│  │  • Record in a quiet environment                 ││
│  │  • Speak naturally and clearly                   ││
│  │  • Include varied emotions and tones             ││
│  │  • Use the same microphone for all samples       ││
│  │  • Longer samples = better quality               ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  [Cancel]  [Train Voice (Takes ~10-30 minutes)]       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### Step 3: Training Process

**Backend Flow:**
```python
# 1. Upload audio to blob storage (S3/GCS/Azure)
audio_url = upload_to_storage(audio_file, f"voices/{personality_id}/")

# 2. Send to ElevenLabs for training
voice = elevenlabs_client.clone_voice(
    name=f"{personality_name}_voice",
    description=f"Custom voice for {personality_name} personality",
    files=[audio_url]
)

# 3. Store voice_id in database
personality.voice_config = {
    "provider": "elevenlabs",
    "voice_id": voice.voice_id,
    "voice_name": voice.name,
    "status": "training",  # → "ready" when complete
    "created_at": now(),
    "sample_urls": [audio_url],
    "settings": {
        "stability": 0.75,
        "similarity_boost": 0.85,
        "style": 0.5,
        "use_speaker_boost": True
    }
}

# 4. Poll ElevenLabs for training completion
# Training takes ~10-30 minutes
# Update status to "ready" when complete
```

#### Step 4: Voice Customization

**After training, allow fine-tuning:**
```
┌────────────────────────────────────────────────────────┐
│  🎛️ Voice Settings                                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Stability (More stable = less variation)             │
│  ●────────────○─────────────○  0.75                   │
│  0.0        0.5           1.0                          │
│                                                        │
│  Similarity Boost (Higher = closer to training)       │
│  ○────────────────────────●─○  0.85                   │
│  0.0        0.5           1.0                          │
│                                                        │
│  Style Exaggeration (More expression)                 │
│  ○────────●───────────────○  0.5                      │
│  0.0        0.5           1.0                          │
│                                                        │
│  Speaker Boost                                         │
│  ☑️ Enable (Recommended for custom voices)            │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  🔊 Test Voice                                    ││
│  │                                                   ││
│  │  Type a message to hear how it sounds:           ││
│  │  ┌─────────────────────────────────────────────┐││
│  │  │ Hey! Welcome! What's bringing you in today?│││
│  │  └─────────────────────────────────────────────┘││
│  │                                                   ││
│  │  [▶️ Play]  [⏹️ Stop]  [📥 Download Sample]      ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  [Save Settings]                                       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Architecture & Integration

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Personality Management UI                             │ │
│  │  - Upload audio samples                                │ │
│  │  - Adjust voice settings                               │ │
│  │  - Test voice output                                   │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Voice Service                                         │ │
│  │  - Upload management                                   │ │
│  │  - Voice training orchestration                        │ │
│  │  - TTS generation                                      │ │
│  │  - Audio streaming                                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Personality Service                                   │ │
│  │  - CRUD operations                                     │ │
│  │  - Voice config management                             │ │
│  │  - Integration with agent flow                         │ │
│  └───────────────────────────────────────────────────────┘ │
└──────┬──────────────────────────┬────────────────────┬─────┘
       │                          │                    │
       ↓                          ↓                    ↓
┌──────────────┐        ┌──────────────────┐   ┌─────────────┐
│  PostgreSQL  │        │  Blob Storage    │   │  Redis      │
│              │        │  (Audio Samples) │   │  (Cache)    │
│ ai_personalities│      │  S3/GCS/Azure    │   │  - Generated│
│ - voice_config │       │                  │   │    audio    │
└──────────────┘        └──────────────────┘   └─────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│              External TTS Providers                          │
│  ┌──────────────┐           ┌──────────────────┐           │
│  │  ElevenLabs  │           │  Google Cloud    │           │
│  │              │           │  Text-to-Speech  │           │
│  │  - Custom    │           │  - Default voices│           │
│  │    voices    │           │  - Fallback      │           │
│  └──────────────┘           └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema Updates

```sql
-- ai_personalities table already has voice_config JSONB column
-- Structure:
{
  "provider": "elevenlabs",  -- or "google_tts", "openai"
  "voice_id": "abc123",      -- ElevenLabs voice_id or Google voice name
  "voice_name": "Marcel Voice",
  "status": "ready",         -- "training", "ready", "failed", "none"
  "created_at": "2025-10-20T17:00:00Z",
  "sample_urls": [
    "https://storage.../voices/uuid/sample1.mp3",
    "https://storage.../voices/uuid/sample2.mp3"
  ],
  "settings": {
    "stability": 0.75,
    "similarity_boost": 0.85,
    "style": 0.5,
    "use_speaker_boost": true,
    "pitch": 0,              -- For Google TTS
    "speaking_rate": 1.0     -- For Google TTS
  },
  "fallback": {
    "provider": "google_tts",
    "voice_id": "en-US-Neural2-D"
  }
}

-- Voice usage tracking (new table)
CREATE TABLE voice_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  personality_id UUID REFERENCES ai_personalities(id),
  provider VARCHAR(50) NOT NULL,
  characters_generated INTEGER NOT NULL,
  audio_duration_seconds INTEGER,
  cost_usd DECIMAL(10, 6),
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  cached BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_voice_usage_tenant ON voice_usage(tenant_id);
CREATE INDEX idx_voice_usage_date ON voice_usage(generated_at);
```

### API Endpoints

```python
# Voice Training
POST   /api/admin/ai-personalities/:id/voice/upload
       - Upload audio samples
       - Returns: upload_id, status

POST   /api/admin/ai-personalities/:id/voice/train
       - Start voice training
       - Body: { sample_ids: [...], settings: {...} }
       - Returns: training_job_id

GET    /api/admin/ai-personalities/:id/voice/status
       - Check training status
       - Returns: { status, progress, voice_id }

# Voice Generation
POST   /api/admin/ai-personalities/:id/voice/generate
       - Generate audio from text (for testing)
       - Body: { text: "Hello...", settings: {...} }
       - Returns: audio_url

GET    /api/admin/ai-personalities/:id/voice/sample
       - Get pre-generated sample audio

# Voice Settings
PUT    /api/admin/ai-personalities/:id/voice/settings
       - Update voice settings (stability, similarity, etc.)

DELETE /api/admin/ai-personalities/:id/voice
       - Delete custom voice, revert to default

# Voice Usage
GET    /api/admin/voice/usage
       - Get voice usage statistics for tenant
```

### Voice Generation Flow

**When agent responds in conversation:**

```python
async def generate_agent_response_with_voice(
    conversation_id: str,
    user_message: str,
    personality_id: str
):
    # 1. Get personality with voice config
    personality = await get_personality(personality_id)

    # 2. Generate text response from agent
    text_response = await agent.generate_response(
        message=user_message,
        personality=personality
    )

    # 3. Check if voice is enabled
    if personality.voice_config and personality.voice_config['status'] == 'ready':
        # 4. Check cache first
        cache_key = f"voice:{personality_id}:{hash(text_response)}"
        audio_url = await redis.get(cache_key)

        if not audio_url:
            # 5. Generate audio
            audio_url = await voice_service.generate_audio(
                text=text_response,
                voice_config=personality.voice_config
            )

            # 6. Cache for 24 hours
            await redis.setex(cache_key, 86400, audio_url)

        # 7. Track usage
        await track_voice_usage(
            tenant_id=personality.tenant_id,
            personality_id=personality_id,
            characters=len(text_response),
            provider=personality.voice_config['provider']
        )

        return {
            "text": text_response,
            "audio_url": audio_url,
            "audio_duration": estimate_duration(text_response)
        }
    else:
        # Voice not configured, return text only
        return {
            "text": text_response,
            "audio_url": None
        }


# Voice Service Implementation
class VoiceService:
    def __init__(self):
        self.elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        self.google_tts_client = texttospeech.TextToSpeechClient()

    async def generate_audio(
        self,
        text: str,
        voice_config: dict
    ) -> str:
        try:
            if voice_config['provider'] == 'elevenlabs':
                return await self._generate_elevenlabs(text, voice_config)
            elif voice_config['provider'] == 'google_tts':
                return await self._generate_google_tts(text, voice_config)
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            # Fallback to default provider
            if voice_config.get('fallback'):
                return await self._generate_fallback(text, voice_config['fallback'])
            raise

    async def _generate_elevenlabs(self, text: str, config: dict) -> str:
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=config['voice_id'],
                settings=VoiceSettings(
                    stability=config['settings']['stability'],
                    similarity_boost=config['settings']['similarity_boost'],
                    style=config['settings']['style'],
                    use_speaker_boost=config['settings']['use_speaker_boost']
                )
            ),
            model="eleven_multilingual_v2"
        )

        # Upload to blob storage
        audio_url = await upload_audio_to_storage(audio, f"generated/{uuid4()}.mp3")
        return audio_url
```

---

## Personality Integration into Agent Flow

### Current Agent Flow

```python
# Current: prompts/agents/dispensary/personality/marcel.json
{
  "personality": {
    "id": "marcel",
    "name": "Marcel",
    "traits": {
      "communication_style": "energetic and enthusiastic",
      "humor_level": "high",
      ...
    },
    "greeting_prompt": "You are Marcel, an energetic...",
    "product_search_prompt": "As Marcel, enthusiastically...",
    "conversation_style": {
      "opening_phrases": [...],
      "product_transitions": [...],
      "closing_phrases": [...]
    }
  }
}
```

### Enhanced Integration

**1. Load Personality into Agent Context**

```python
class V5DispensaryAgent:
    def __init__(self, personality_id: str = None):
        self.personality = None
        if personality_id:
            self.load_personality(personality_id)

    def load_personality(self, personality_id: str):
        """Load personality from database"""
        personality = db.query(AIPersonality).filter_by(id=personality_id).first()

        if not personality:
            # Fallback to default (marcel)
            personality = self.load_default_personality("marcel")

        self.personality = {
            "id": personality.personality_name,
            "name": personality.name,
            "traits": personality.traits,  # JSONB from database
            "response_style": personality.response_style,  # JSONB
            "system_prompt": personality.system_prompt,
            "voice_config": personality.voice_config
        }

        # Build dynamic system prompt based on traits
        self.system_prompt = self.build_system_prompt()

    def build_system_prompt(self) -> str:
        """Build dynamic system prompt from personality traits"""
        traits = self.personality['traits']

        prompt = f"""You are {self.personality['name']}, a {traits['age']}-year-old {traits['gender']} budtender.

Your communication style is {traits['communication_style']}.
Your knowledge level is {traits['knowledge_level']}.
Your humor style is {traits['humor_style']} with {traits['humor_level']} humor level.
Your empathy level is {traits['empathy_level']}.
Your response length should be {traits['response_length']}.
Your jargon level is {traits['jargon_level']}.
Your sales approach is {traits['sales_approach']}.
Your formality level is {traits['formality']}.

"""

        # Add custom system prompt if provided
        if self.personality.get('system_prompt'):
            prompt += f"\n{self.personality['system_prompt']}\n"

        # Add conversation style examples
        response_style = self.personality['response_style']
        prompt += f"""
When greeting customers, use phrases like:
{chr(10).join(f"- {phrase}" for phrase in response_style['opening_phrases'])}

When transitioning to products, use phrases like:
{chr(10).join(f"- {phrase}" for phrase in response_style['product_transitions'])}

When closing conversations, use phrases like:
{chr(10).join(f"- {phrase}" for phrase in response_style['closing_phrases'])}
"""

        return prompt

    async def generate_response(
        self,
        user_message: str,
        conversation_history: list
    ) -> dict:
        """Generate response using personality traits"""

        # Build messages with personality-aware system prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            *conversation_history,
            {"role": "user", "content": user_message}
        ]

        # Generate response
        response = await self.llm.generate(messages)

        # Apply personality-specific post-processing
        response_text = self.apply_personality_style(response['text'])

        # Generate voice if enabled
        if self.personality.get('voice_config'):
            audio_url = await voice_service.generate_audio(
                text=response_text,
                voice_config=self.personality['voice_config']
            )
        else:
            audio_url = None

        return {
            "text": response_text,
            "audio_url": audio_url,
            "personality": self.personality['name']
        }

    def apply_personality_style(self, text: str) -> str:
        """Apply personality-specific formatting"""
        traits = self.personality['traits']

        # Add emoji based on personality (if defined)
        if self.personality.get('emoji'):
            # Occasionally add emoji (based on humor level)
            if traits['humor_level'] == 'high' and random.random() < 0.3:
                text += f" {self.personality['emoji']}"

        # Adjust formality
        if traits['formality'] == 'casual':
            # Could add casual language transformations
            pass

        return text
```

**2. Update Agent Initialization**

```python
# In agent initialization (api_server.py or similar)
async def initialize_agent_with_personality(
    tenant_id: str,
    personality_id: str = None
):
    # If no personality specified, get tenant's primary personality
    if not personality_id:
        personality_id = await get_primary_personality(tenant_id)

    # If still no personality, default to marcel
    if not personality_id:
        personality_id = "marcel"  # Default

    # Initialize agent with personality
    agent = V5DispensaryAgent(personality_id=personality_id)

    return agent


async def get_primary_personality(tenant_id: str) -> str:
    """Get tenant's primary/default personality"""
    # Check tenant settings for primary personality
    tenant = db.query(Tenant).filter_by(id=tenant_id).first()

    primary_id = tenant.settings.get('ai_personalities', {}).get('primary_personality_id')

    if primary_id:
        return primary_id

    # Otherwise, get first active personality
    personality = db.query(AIPersonality).filter_by(
        tenant_id=tenant_id,
        is_active=True
    ).first()

    if personality:
        return personality.id

    # Fallback to default (marcel)
    return "marcel"
```

**3. Conversation Flow with Personality**

```python
# In chat endpoint
@router.post("/chat")
async def chat(
    message: str,
    conversation_id: str = None,
    personality_id: str = None,
    tenant_id: str = Depends(get_current_tenant)
):
    # Get or create conversation
    conversation = await get_or_create_conversation(conversation_id, tenant_id)

    # Use personality from conversation, or specified, or tenant default
    if not personality_id:
        personality_id = conversation.personality_id or await get_primary_personality(tenant_id)

    # Initialize agent with personality
    agent = await initialize_agent_with_personality(tenant_id, personality_id)

    # Generate response
    response = await agent.generate_response(
        user_message=message,
        conversation_history=conversation.messages
    )

    # Save to conversation
    conversation.messages.append({
        "role": "user",
        "content": message,
        "timestamp": now()
    })
    conversation.messages.append({
        "role": "assistant",
        "content": response['text'],
        "audio_url": response['audio_url'],
        "personality": response['personality'],
        "timestamp": now()
    })

    await conversation.save()

    return {
        "text": response['text'],
        "audio_url": response['audio_url'],
        "personality": response['personality'],
        "conversation_id": conversation.id
    }
```

**4. Frontend Integration**

```typescript
// In chat component
const sendMessage = async (text: string) => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message: text,
      conversation_id: conversationId,
      personality_id: selectedPersonalityId
    })
  });

  const data = await response.json();

  // Display text message
  addMessage({
    role: 'assistant',
    text: data.text,
    personality: data.personality
  });

  // Play audio if available
  if (data.audio_url) {
    const audio = new Audio(data.audio_url);
    audio.play();
  }
};
```

---

## Cost Analysis

### Scenario: Small Business Tenant

**Assumptions:**
- 1000 conversations/month
- Average 10 messages per conversation = 10,000 messages
- Average message: 300 characters
- Total: 3,000,000 characters/month

**Option 1: ElevenLabs Only**
- Professional plan: $99/month (500k chars)
- Need: 6x Professional = $594/month
- ❌ Too expensive

**Option 2: Google Cloud TTS Only**
- Neural2: $16 per 1M characters
- Total: 3M chars × $0.000016 = $48/month
- ❌ No voice cloning

**Option 3: Hybrid (RECOMMENDED)**
- Default personalities (70% of traffic): 2.1M chars
  - Google TTS: 2.1M × $0.000016 = $33.60/month
- Custom personalities (30% of traffic): 900k chars
  - ElevenLabs Pro: $99/month (500k chars) + overage
  - Overage: 400k × $0.0003 = $120/month
- **Total: ~$153/month**

**Option 4: Hybrid with Caching (BEST)**
- Cache common phrases (greetings, closings) → 30% cache hit rate
- Effective characters: 2.1M chars (70% reduction)
- Google TTS: 1.47M × $0.000016 = $23.52/month
- ElevenLabs: 630k chars → Pro plan $99/month
- **Total: ~$123/month**

**Pricing Strategy for Tenants:**
```
Free Tier: No voice (text only)
Small Business: Google TTS voices included (default personalities)
Professional: +1 custom voice (ElevenLabs)
Enterprise: Unlimited custom voices
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Backend:**
- [ ] Create VoiceService class
- [ ] Integrate ElevenLabs API
- [ ] Integrate Google Cloud TTS API
- [ ] Add voice_usage table
- [ ] Create API endpoints for voice operations

**Frontend:**
- [ ] Add voice config section to personality form
- [ ] Add audio upload component
- [ ] Add voice training UI

**Testing:**
- [ ] Test ElevenLabs voice cloning with sample audio
- [ ] Test Google TTS with different voices

### Phase 2: Voice Training (Week 2)

**Backend:**
- [ ] Implement audio upload to blob storage
- [ ] Implement voice training orchestration
- [ ] Add polling for training status
- [ ] Add voice generation endpoint

**Frontend:**
- [ ] Complete voice training flow UI
- [ ] Add progress indicators
- [ ] Add voice testing interface

**Testing:**
- [ ] End-to-end voice training test
- [ ] Test with different audio formats
- [ ] Test error scenarios

### Phase 3: Agent Integration (Week 3)

**Backend:**
- [ ] Update V5DispensaryAgent to load personalities from DB
- [ ] Implement dynamic system prompt building
- [ ] Integrate voice generation into chat flow
- [ ] Add caching for generated audio

**Frontend:**
- [ ] Update chat interface to play audio
- [ ] Add audio controls (play, pause, stop)
- [ ] Add personality selector in chat

**Testing:**
- [ ] Test agent with different personalities
- [ ] Test voice generation in conversations
- [ ] Test caching

### Phase 4: Optimization & Polish (Week 4)

**Backend:**
- [ ] Implement audio caching strategy
- [ ] Add cost tracking and usage limits
- [ ] Add fallback logic for API failures
- [ ] Performance optimization

**Frontend:**
- [ ] Add voice settings fine-tuning UI
- [ ] Add usage statistics dashboard
- [ ] Mobile optimization

**Testing:**
- [ ] Load testing
- [ ] Cost analysis
- [ ] User acceptance testing

---

## Security Considerations

1. **Audio Sample Storage:**
   - Store in private S3 buckets (not public)
   - Add access control (only tenant can access their samples)
   - Implement file size limits (10 MB per file)

2. **Voice Cloning Abuse:**
   - Require tenant admin authentication
   - Log all voice training requests
   - Implement rate limits (1 training per hour per tenant)
   - Manual review for suspicious uploads

3. **API Key Security:**
   - Store ElevenLabs/Google API keys in environment variables
   - Rotate keys regularly
   - Monitor usage for anomalies

4. **Audio Content Moderation:**
   - Scan uploaded audio for inappropriate content
   - Reject non-speech audio (music, noise, etc.)
   - Validate audio duration and format

---

## Open Questions for Discussion

1. **Voice Training Limits:** Should there be a limit on voice training attempts per month?

2. **Audio Sample Storage:** Keep audio samples after training, or delete to save storage?

3. **Real-time Streaming:** Should we support real-time audio streaming, or always return URLs?

4. **Voice Marketplace:** Future feature - allow tenants to share/sell custom voices?

5. **Multilingual Voices:** Should custom voices support multiple languages?

6. **Voice Backup:** Allow downloading trained voices for backup/migration?

---

**Status**: 📋 **AWAITING APPROVAL** on voice implementation approach

**Next Step**: Please review and confirm:
- ✅ ElevenLabs + Google TTS hybrid approach
- ✅ Voice training process
- ✅ Personality integration into agent flow
- ✅ Cost structure acceptable
- ❓ Any changes needed?
