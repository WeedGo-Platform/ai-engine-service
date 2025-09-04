# WeedGo AI Engine Service

Production-ready intelligent budtender service with voice interaction and self-learning capabilities.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the service
python api_server.py
```

Service runs on `http://localhost:5024`

## Key Features

- 🤖 **AI-Powered Conversations** - Natural language understanding with LLMs
- 🎙️ **Voice Interaction** - Real-time voice with <200ms latency  
- 👤 **Voice Identity** - Automatic customer recognition
- 🧠 **Self-Learning** - Improves from every interaction
- 🌍 **Multilingual** - Supports 6 languages (EN, ES, FR, PT, ZH, AR)
- 📊 **Analytics** - Built-in conversion tracking
- 🔒 **Compliance** - Age verification and purchase limits

## Documentation

- [API Documentation](docs/api/API_DOCUMENTATION.md) - Complete API reference with voice endpoints
- [Getting Started Guide](docs/guides/GETTING-STARTED.md) - Setup and configuration
- [Architecture Overview](docs/architecture/SYSTEM_OVERVIEW.md) - System design and components
- [Voice Architecture](docs/architecture/VOICE_ARCHITECTURE.md) - Voice system design

## Voice Features

### Voice Identification
The system automatically identifies returning customers by their voice print using acoustic embeddings.

### Self-Learning System
Implements true learning through:
- Pattern recognition from interactions
- Prompt evolution based on outcomes
- Knowledge graph expansion
- Behavioral modeling for predictions

### Intelligent Model Selection
Dynamically selects optimal models based on:
- Context (urgency, noise level, domain)
- Available resources (memory, CPU)
- Performance targets (<200ms latency)

## API Endpoints

### Core Endpoints
- `POST /api/v1/chat` - AI conversation
- `POST /api/v1/products/search` - Product search
- `POST /api/v1/cart` - Cart management

### Voice Endpoints
- `GET /api/voice/status` - System status
- `POST /api/voice/transcribe` - Speech-to-text with voice ID
- `POST /api/voice/synthesize` - Text-to-speech with emotion
- `POST /api/voice/conversation` - Complete voice turn
- `WS /api/voice/stream` - Real-time streaming

## Testing

```bash
# Run voice system tests
python test_voice_system.py

# Run API tests
python test_api.py
```

## Models

Download required models:
```bash
python scripts/download_voice_models.py
```

## Support

For issues or questions, please check the documentation or open an issue.