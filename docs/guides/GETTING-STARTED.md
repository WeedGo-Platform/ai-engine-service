# Getting Started - WeedGo AI Engine Services

## Quick Start Guide

### Prerequisites

1. **Development Environment**
   ```bash
   # Required software
   - .NET 9 SDK
   - Python 3.11+
   - Docker & Docker Compose
   - Git
   
   # Optional (for GPU acceleration)
   - NVIDIA Docker runtime
   - CUDA 12.1+
   ```

2. **Hardware Requirements**
   ```bash
   # Minimum (Development)
   - 16GB RAM
   - 4 CPU cores
   - 50GB disk space
   
   # Recommended (Production)
   - 64GB RAM
   - 16 CPU cores
   - 1 NVIDIA GPU (T4 or better)
   - 500GB SSD storage
   ```

### Setup Instructions

#### 1. Clone and Initialize
```bash
# Clone repository
git clone <repository-url>
cd ai-engine-services

# Install dependencies
make install

# Setup development environment
make dev-env
```

#### 2. Load Canadian Cannabis Data
```bash
# Download strain database (you'll need to provide this)
# Place your canadian_strains.json file in data/datasets/

# Load data into system
make load-data

# Verify data loading
make validate-data
```

#### 3. Start Services
```bash
# Start all services
make up

# Or start individually
make run-dotnet    # .NET API only
make run-python    # Python ML service only
```

#### 4. Verify Installation
```bash
# Check service status
make status

# Run health checks
curl http://localhost:5100/health

# View logs
make logs
```

## Service Endpoints

### .NET API Service
- **REST API**: http://localhost:5100
- **gRPC**: http://localhost:5101
- **Health Check**: http://localhost:5100/health
- **Swagger UI**: http://localhost:5100/swagger

### Python ML Service  
- **gRPC**: http://localhost:50051
- **Metrics**: http://localhost:8501
- **Jupyter Lab**: http://localhost:8888 (token: weedgo)

### Infrastructure Services
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Milvus**: localhost:19530
- **MLflow**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/admin)

## Development Workflow

### 1. Code Changes
```bash
# .NET development
cd src/dotnet/WeedGo.AI.Api
dotnet watch run

# Python development  
cd src/python
python -m ml_service.server
```

### 2. Testing
```bash
# Run all tests
make test

# Run specific tests
make test-unit
make test-integration
make test-load
```

### 3. Code Quality
```bash
# Format code
make format

# Run linters
make lint

# Security scan
make security-scan
```

## API Usage Examples

### 1. Virtual Budtender Chat
```bash
curl -X POST http://localhost:5100/api/v1/budtender/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need something for creativity without anxiety",
    "language": "en",
    "customerId": "customer-123",
    "tenantId": "store-abc"
  }'
```

### 2. Product Recommendations
```bash
curl -X POST http://localhost:5100/api/v1/budtender/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "customer-123",
    "preferences": {
      "thcRange": [15, 25],
      "strainType": "Hybrid",
      "effects": ["Creative", "Relaxed"]
    },
    "count": 5
  }'
```

### 3. Customer Recognition
```bash
# Upload image for recognition
curl -X POST http://localhost:5100/api/v1/recognition/identify \
  -H "Content-Type: multipart/form-data" \
  -F "image=@customer_photo.jpg" \
  -F "tenantId=store-abc"
```

### 4. Identity Verification
```bash
curl -X POST http://localhost:5100/api/v1/identity/verify \
  -H "Content-Type: application/json" \
  -d '{
    "idCardImage": "base64_encoded_id_image",
    "selfieImage": "base64_encoded_selfie",
    "documentType": "driver_license",
    "tenantId": "store-abc"
  }'
```

### 5. Pricing Optimization
```bash
curl -X POST http://localhost:5100/api/v1/pricing/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "product-123",
    "currentPrice": 25.99,
    "strategy": "dynamic",
    "inventoryLevel": 0.6,
    "targetMargin": 0.3
  }'
```

## Configuration

### Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit configuration
vim .env
```

### Key Configuration Options
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_DB=weedgo_ai
POSTGRES_USER=weedgo
POSTGRES_PASSWORD=weedgo123

# ML Service
MODEL_PATH=/models
GRPC_PORT=50051
CUDA_VISIBLE_DEVICES=0

# Security
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Languages
SUPPORTED_LANGUAGES=en,fr,pt,es,ar,zh
DEFAULT_LANGUAGE=en

# Features
ENABLE_AGE_VERIFICATION=true
MINIMUM_AGE=19
ENABLE_FACE_RECOGNITION=true
```

## Data Management

### Adding New Strain Data
```bash
# Format: JSON array of strain objects
{
  "strains": [
    {
      "name": "Blue Dream",
      "thc_percentage": 18.5,
      "cbd_percentage": 0.2,
      "strain_type": "Hybrid",
      "terpene_profile": {
        "myrcene": 0.8,
        "pinene": 0.3,
        "limonene": 0.5
      },
      "effects": ["Creative", "Euphoric", "Relaxed"],
      "medical_uses": ["Stress", "Depression", "Pain"],
      "brand": "Canopy Growth",
      "price": 12.50,
      "source": "OCS"
    }
  ]
}

# Load into system
python scripts/load_strain_data.py --file data/datasets/my_strains.json
```

### Backup and Restore
```bash
# Backup all data
make backup-data

# Restore from backup
make restore-data
```

## Model Management

### Training New Models
```bash
# Train recommendation model
python scripts/train_recommendation_model.py

# Train face recognition model
python scripts/train_face_recognition.py

# Train pricing model
python scripts/train_pricing_model.py

# Train all models
make train-models
```

### Model Deployment
```bash
# Export models
make export-models

# Deploy to production
kubectl apply -f deployment/kubernetes/production/
```

## Monitoring

### Metrics Dashboard
```bash
# Open Grafana
open http://localhost:3000

# Username: admin
# Password: admin
```

### Key Metrics to Monitor
- **API Response Time**: <200ms p99
- **Model Inference Time**: <100ms average
- **Face Recognition Accuracy**: >95%
- **Recommendation Relevance**: >80%
- **System Memory Usage**: <80%
- **GPU Utilization**: 60-80%

### Logs
```bash
# View all logs
make logs

# View specific service
docker-compose logs ai-api
docker-compose logs ai-ml

# Follow logs
docker-compose logs -f
```

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   ```bash
   # Check NVIDIA runtime
   docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
   
   # If not working, install nvidia-docker2
   sudo apt-get install nvidia-docker2
   sudo systemctl restart docker
   ```

2. **Out of Memory Errors**
   ```bash
   # Reduce batch size in config
   MODEL_BATCH_SIZE=8
   
   # Or allocate more memory to containers
   docker-compose up --scale ai-ml=1 -m 8g
   ```

3. **Slow Model Loading**
   ```bash
   # Preload models in background
   python scripts/preload_models.py
   
   # Or use model caching
   ENABLE_MODEL_CACHE=true
   ```

4. **Connection Refused Errors**
   ```bash
   # Check service health
   make status
   
   # Restart specific service
   docker-compose restart ai-api
   
   # Check network connectivity
   docker-compose exec ai-api ping ai-ml
   ```

### Getting Help
```bash
# Check service health
curl http://localhost:5100/health

# View system status
make status

# Generate diagnostic report
python scripts/diagnostics.py

# Check logs for errors
make logs | grep ERROR
```

## Next Steps

1. **Add Your Cannabis Data**
   - Prepare strain database in JSON format
   - Load using `make load-data`
   - Verify with test API calls

2. **Configure Languages**
   - Test each supported language
   - Add custom cannabis terminology
   - Train language-specific models

3. **Customize Models**
   - Fine-tune with your data
   - Adjust confidence thresholds
   - Test with real customer data

4. **Production Deployment**
   - Setup Kubernetes cluster
   - Configure monitoring
   - Setup CI/CD pipeline

5. **Integration**
   - Connect to your POS system
   - Setup customer enrollment
   - Configure pricing rules

For detailed implementation guides, see the `/docs` directory.

---

🚀 **Ready to build the future of cannabis retail!**