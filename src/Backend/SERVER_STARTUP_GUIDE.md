# 🚨 IMPORTANT: Server Startup Guide

## ✅ THE CORRECT WAY TO START THE SERVER

### Quick Start
```bash
./start_server.sh
```

### Manual Start
```bash
python3 api_server.py
```

### Background Start (with logging)
```bash
nohup python3 api_server.py > server.log 2>&1 &
```

## ⚠️ DO NOT RUN THESE FILES

| File | Why NOT to run it |
|------|-------------------|
| `agi/api/_deprecated_agi_only_server.py` | Only has AGI endpoints, missing WeedGo API |
| Any file in `agi/` directory | These are modules imported by main server |
| `mcp_servers/*` | These are MCP protocol servers, not HTTP servers |

## 🎯 The ONLY Server You Need

**`api_server.py`** is the ONLY server file you should run. It includes:

- ✅ All WeedGo API endpoints (stores, products, cart, etc.)
- ✅ AGI Dashboard and AI services
- ✅ Chat WebSocket support
- ✅ Voice streaming support
- ✅ Authentication endpoints
- ✅ All database connections

## 🔍 How to Verify Server is Running Correctly

1. Check the process:
```bash
ps aux | grep python | grep api_server
```

2. Test WeedGo endpoints:
```bash
curl http://localhost:5024/api/stores/tenant/ce2d57bc-b3ba-4801-b229-889a9fe9626d
```

3. Test AGI endpoints:
```bash
curl http://localhost:5024/api/agi/stats
```

4. Check Swagger docs:
```bash
open http://localhost:5024/docs
```

## 📱 Mobile App Connection

The mobile app expects the server on port 5024 with these endpoints:
- `/api/stores/tenant/{tenant_id}`
- `/api/search/products`
- `/api/products/search`
- `/chat/ws` (WebSocket)
- `/api/voice/ws/stream` (WebSocket)

## 🛑 Troubleshooting

### "Port 5024 already in use"
```bash
# Find and kill the process
lsof -i :5024
kill <PID>
```

### "Mobile app can't connect"
You're probably running the wrong server. Kill all Python processes and restart:
```bash
pkill -f python
./start_server.sh
```

### "Store endpoints return 404"
Make sure you're running `api_server.py`, NOT the deprecated AGI-only server.

---

## 📌 Remember

**ALWAYS use `api_server.py`** - it's the complete, combined server with everything the mobile app needs!