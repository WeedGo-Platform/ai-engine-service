# WeedGo AI Engine - Quick Reference

## 🚀 Start Service
```bash
python3 api_server.py
```
Service runs on **http://localhost:8080** (changed from 8000 to avoid Docker conflicts)

## 📌 Test API is Running
```bash
# Check service status
curl http://localhost:8080/

# View all endpoints
curl http://localhost:8080/api/v1

# Check health
curl http://localhost:8080/health
```

## 📍 Key Endpoints

### Chat (Main AI Interface)
```bash
POST /api/v1/chat
{
  "message": "I need help sleeping",
  "customer_id": "user_123"
}
```

### Product Search
```bash
POST /api/v1/products/search
{
  "intent": "sleep",
  "category": "Flower",
  "limit": 5
}
```

### Age Verification (Required)
```bash
POST /api/v1/compliance/verify-age
{
  "customer_id": "user_123",
  "birth_date": "1995-06-15",
  "verification_method": "manual"
}
```

### Cart Management
```bash
POST /api/v1/cart
{
  "action": "add",
  "customer_id": "user_123",
  "product_id": 234,
  "quantity": 1
}
```

## 🔍 Health Check
```bash
GET /health
```

## 📚 Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🎯 Customer Intents
- `sleep` - Sedating products
- `energy` - Uplifting options
- `pain` - Pain relief
- `anxiety` - Calming effects
- `creativity` - Creative enhancement
- `focus` - Concentration
- `appetite` - Munchies
- `social` - Party vibes

## ⚡ Performance Tips
```bash
# Enable GPU acceleration (M3 Max)
export MODEL_N_GPU_LAYERS=32

# Monitor performance
curl http://localhost:8000/api/v1/analytics/performance
```

## 🛠️ Troubleshooting
```bash
# Check service health
curl http://localhost:8000/health | jq

# View logs
tail -f logs/ai_engine.log

# Clear cache if needed
curl -X POST http://localhost:8000/api/v1/admin/cache/clear

# Test database connection
psql -h localhost -p 5434 -U weedgo -d ai_engine -c "SELECT COUNT(*) FROM products;"
```

## 📝 Common Issues

| Issue | Solution |
|-------|----------|
| Models not loading | Check `models/` directory has .gguf files |
| Slow responses | Enable GPU: `MODEL_N_GPU_LAYERS=32` |
| Database errors | Check PostgreSQL is running on port 5434 |
| Cache misses | Ensure Redis is running on port 6379 |

## 🔧 Configuration (.env)
```bash
# Essential settings
DB_HOST=localhost
DB_PORT=5434
REDIS_HOST=localhost
REDIS_PORT=6379
MODEL_N_GPU_LAYERS=32  # For GPU acceleration
MODEL_MAX_TOKENS=150    # Response length
```

## 📊 Monitoring
```bash
# Real-time performance
watch -n 1 'curl -s http://localhost:8000/api/v1/analytics/performance | jq'

# Cache stats
curl http://localhost:8000/api/v1/analytics/cache | jq

# Error status
curl http://localhost:8000/api/v1/admin/errors | jq
```

---
**Port**: 8000 | **Version**: 2.0.0 | **Docs**: `/api/docs`