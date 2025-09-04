# WeedGo AI Engine - Intelligent Budtender Service

An industry-standard, production-ready AI service that powers intelligent cannabis recommendations through natural conversation, driving sales through personalized customer experiences.

## Features

### Core Capabilities
- **🤖 Intelligent Conversation**: LLM-powered natural language understanding (Llama 2, Mistral)
- **🎯 Sales-Focused Flow**: 6-stage sales funnel with purchase intent detection
- **🧬 Scientific Recommendations**: Terpene and cannabinoid-based effect matching
- **🛒 Cart Management**: Intelligent upselling and cross-selling
- **⚡ Performance Optimized**: Redis caching, sub-5 second responses
- **📊 Analytics Ready**: Conversion tracking and A/B testing framework
- **🌍 Multi-language**: Support for 6 languages
- **🔒 Secure**: Environment-based configuration, JWT authentication ready

## Architecture

```
┌─────────────────────────────────────────┐
│         Frontend Applications            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Unified Budtender Service (8000)     │
│  ┌────────────────────────────────────┐ │
│  │  • Chat Endpoint                   │ │
│  │  • Product Search                  │ │
│  │  • Cart Management                 │ │
│  │  • Recommendations                 │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Service Components               │
│  ┌─────────────┐  ┌──────────────┐     │
│  │Model Manager│  │Sales Engine  │     │
│  │(LLMs)       │  │(SPIN Selling)│     │
│  └─────────────┘  └──────────────┘     │
│  ┌─────────────┐  ┌──────────────┐     │
│  │Knowledge    │  │Cache Manager │     │
│  │Graph        │  │(Redis)       │     │
│  └─────────────┘  └──────────────┘     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│           Data Layer                     │
│  PostgreSQL │ Redis │ Embeddings        │
└─────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis (optional, for caching)
- 8GB+ RAM for LLM models
- Apple Silicon or NVIDIA GPU (optional, for acceleration)

### Installation

1. Clone the repository:
```bash
git clone <repository>
cd microservices/ai-engine-service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Download LLM models (if not present):
```bash
# Llama 2 7B Chat (3.8GB)
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -P models/

# Mistral 7B Instruct (4.1GB)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -P models/
```

5. Set up database:
```bash
# Load OCS product data
DB_HOST=localhost DB_PORT=5434 DB_NAME=ai_engine DB_USER=weedgo DB_PASSWORD=weedgo123 \
  python scripts/process_ocs_data.py

# Generate embeddings
DB_HOST=localhost DB_PORT=5434 DB_NAME=ai_engine DB_USER=weedgo DB_PASSWORD=weedgo123 \
  python scripts/generate_embeddings.py

# Build knowledge graph
DB_HOST=localhost DB_PORT=5434 DB_NAME=ai_engine DB_USER=weedgo DB_PASSWORD=weedgo123 \
  python scripts/build_cannabis_knowledge_graph.py
```

6. Start the unified API server:
```bash
python api_server.py
```

The service will be available at `http://localhost:8000`

## API Endpoints

The service runs on a single unified port (8000) with all endpoints organized by function. API documentation is available at `http://localhost:8000/api/docs`

### Endpoint Organization

```
BASE URL: http://localhost:8000

/api/v1/
├── chat/                  # Conversation & AI interactions
│   ├── POST /             # Main chat endpoint
│   └── GET /history/{id}  # Chat history
├── products/              # Product catalog & search
│   ├── POST /search       # Advanced search
│   ├── GET /              # List products
│   ├── GET /{id}          # Product details
│   ├── GET /categories    # Product categories
│   └── GET /recommendations/{intent}  # Intent-based recommendations
├── cart/                  # Cart management
│   ├── POST /             # Manage cart (add/remove/checkout)
│   └── GET /{id}          # Get cart status
├── compliance/            # Age verification & compliance
│   ├── POST /verify-age   # Age verification
│   └── GET /{id}          # Compliance status
├── analytics/             # Metrics & analytics
│   ├── POST /             # Custom analytics
│   ├── GET /performance   # Performance metrics
│   └── GET /cache         # Cache statistics
└── admin/                 # Administrative functions
    ├── POST /cache/clear  # Clear cache
    └── GET /errors        # Error reports
```

### Core Endpoints

#### 🤖 Chat Endpoint
**POST** `/api/v1/chat`

Intelligent conversation with sales optimization and LLM enhancement.

```json
{
  "message": "I need something for sleep",
  "customer_id": "customer_123",
  "session_id": "session_456",
  "language": "en",
  "optimization_strategy": "balanced"
}
```

Response:
```json
{
  "message": "I'd recommend our Indica strains for deep sleep...",
  "products": [
    {
      "id": 123,
      "product_name": "Purple Kush",
      "unit_price": 45.99,
      "pitch": "Perfect for deep sleep",
      "effects": ["relaxation", "sleep"],
      "terpenes": ["myrcene", "linalool"]
    }
  ],
  "quick_replies": ["Tell me more", "Add to cart"],
  "confidence": 0.85,
  "stage": "recommendation",
  "response_time_ms": 2340
}
```

#### 🔍 Product Search
**POST** `/api/v1/products/search`

Multi-strategy product search with filters.

```json
{
  "query": "high CBD",
  "intent": "anxiety",
  "category": "Flower",
  "min_price": 20,
  "max_price": 60,
  "min_thc": 5,
  "max_thc": 15,
  "limit": 10
}
```

#### 🛒 Cart Management
**POST** `/api/v1/cart`

Cart operations with compliance checking.

```json
{
  "action": "add",
  "product_id": 123,
  "quantity": 2,
  "customer_id": "customer_123"
}
```

Actions: `add`, `remove`, `update`, `clear`, `checkout`

#### ✅ Age Verification
**POST** `/api/v1/compliance/verify-age`

Required before purchases.

```json
{
  "customer_id": "customer_123",
  "birth_date": "1995-06-15",
  "verification_method": "government_id",
  "government_id": "DL123456789"
}
```

#### 📊 Analytics
**GET** `/api/v1/analytics/performance`

Get system performance metrics including:
- Average response time
- Cache hit rate
- Under 5s response rate
- P95 latency

### Health & Status
**GET** `/health` or `/api/health`

Comprehensive health check of all components:
```json
{
  "service": "ai_engine",
  "version": "2.0.0",
  "status": "healthy",
  "components": {
    "database": {"status": "healthy", "products": 5541},
    "models": {"status": "healthy", "loaded": ["mistral-7b", "llama2-7b"]},
    "cache": {"hit_rate": "85%", "memory_used": "124MB"},
    "inference": {"avg_time": 2.3, "under_5s_rate": 0.98}
  }
}
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | localhost |
| `DB_PORT` | PostgreSQL port | 5434 |
| `REDIS_HOST` | Redis host (optional) | localhost |
| `MODEL_N_GPU_LAYERS` | GPU layers for acceleration | 0 |
| `MODEL_TEMPERATURE` | LLM creativity (0-1) | 0.7 |
| `ENABLE_CACHING` | Enable Redis caching | true |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | true |

## Performance

### Current Metrics
- **LLM Inference**: 2-5 seconds (M3 Max)
- **Cached Responses**: <100ms
- **Product Search**: <500ms
- **Knowledge Graph Query**: <200ms
- **Concurrent Users**: 100+ (single instance)

### Optimization Tips
1. Enable GPU acceleration: Set `MODEL_N_GPU_LAYERS=32`
2. Use Redis caching: Reduces repeat query time by 95%
3. Increase threads: `MODEL_N_THREADS=16` for better CPU utilization
4. Use model quantization: Q4_K_M provides best size/quality ratio

## Development

### Project Structure
```
ai-engine-service/
├── services/           # Core service implementations
│   ├── model_manager.py       # LLM management
│   ├── sales_conversation_engine.py  # Sales logic
│   ├── cache_manager.py       # Redis caching
│   └── knowledge_graph.py     # Graph queries
├── scripts/           # Data processing scripts
├── models/            # LLM model files
├── data/              # Product data and embeddings
├── unified_budtender_service.py  # Main API
└── config.py          # Configuration
```

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests
python test_integration.py

# Test specific endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "customer_id": "test"}'
```

## Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "unified_budtender_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-engine
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: budtender
        image: weedgo/ai-engine:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
```

### Monitoring
- **Prometheus metrics**: Available at `/metrics`
- **Health checks**: `/api/health`
- **Logging**: Structured JSON to stdout
- **Tracing**: OpenTelemetry compatible

## Troubleshooting

### Common Issues

1. **Models not loading**
   - Ensure model files exist in `models/` directory
   - Check file permissions
   - Verify sufficient RAM (8GB minimum)

2. **Slow responses**
   - Enable Redis caching
   - Increase `MODEL_N_THREADS`
   - Enable GPU acceleration if available

3. **Database connection errors**
   - Verify PostgreSQL is running
   - Check credentials in `.env`
   - Ensure database exists

4. **Out of memory**
   - Reduce `MODEL_N_CTX` (context window)
   - Use smaller models (Q4_0 instead of Q4_K_M)
   - Enable swap space

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Proprietary - WeedGo Technologies

## Support

For issues and questions:
- Technical: engineering@weedgo.com
- Business: sales@weedgo.com

---

Built with ❤️ for the cannabis community