# AI-Only Architecture Requirements

## Production Requirements Document

### Executive Summary

The WeedGo AI Engine operates in **AI-Only Mode**, where ALL conversation processing, intent detection, and response generation is handled exclusively by the Large Language Model (LLM). This document outlines the critical production requirements and architectural decisions.

## Core Architectural Principles

### 1. No Pattern Matching
- **CRITICAL**: The system contains ZERO pattern matching for production operations
- All intent detection is performed by the LLM
- No keyword-based fallbacks are permitted
- No regex patterns for message classification

### 2. LLM Dependency
- The system REQUIRES a functioning LLM to operate
- There are NO fallback mechanisms when the LLM is unavailable
- System fails fast and transparently when AI is offline

### 3. Pure AI Decision Making
- Every customer interaction is processed through the AI model
- Intent determination is 100% AI-driven
- Parameter extraction uses only LLM capabilities
- Response generation is entirely model-based

## System Requirements

### Startup Requirements
1. **LLM Availability Check**
   - System validates LLM presence during initialization
   - Performs health check with test query
   - Refuses to start if LLM is not responsive
   - Location: `api_server.py:235-254`

2. **Database Connectivity**
   - PostgreSQL connection for product data
   - AI personality configurations
   - Conversation history storage
   - Training data persistence

### Runtime Requirements

#### Error Handling
- When LLM is unavailable, system returns explicit error:
  ```json
  {
    "stage": "error",
    "message": "AI service is currently unavailable",
    "error": "LLM_NOT_AVAILABLE"
  }
  ```
- No degraded mode operations
- Clear user messaging about AI requirement

#### Monitoring & Metrics
The system tracks comprehensive metrics:
- Total LLM calls and success rate
- Response time percentiles
- Intent distribution
- Error types and frequencies
- Automatic metric logging every 60 seconds

#### Health Checks
Dedicated endpoint: `/api/v1/ai/health`
- Real-time LLM availability testing
- Health score calculation (0-100)
- Performance metrics reporting
- Configuration verification

## Implementation Details

### Key Files Modified

1. **services/smart_ai_engine_v3.py**
   - Pure LLM implementation
   - No pattern matching methods
   - Comprehensive metrics tracking
   - RuntimeError on LLM unavailability

2. **api_server.py**
   - Startup LLM validation
   - AI health endpoint
   - Error response handling
   - Metrics integration

3. **ai-admin-dashboard/src/components/LiveChatTestingFixed.tsx**
   - Graceful AI unavailability handling
   - Clear error messaging
   - Toast notifications for AI issues

### Removed Components
- Pattern matching for greetings (hi, hello, hey)
- Keyword detection for cart actions (buy, purchase, add)
- Fallback parameter extraction
- Default responses when LLM unavailable

## Production Deployment Checklist

### Pre-Deployment
- [ ] Verify LLM model is loaded and accessible
- [ ] Confirm database connections are established
- [ ] Test health check endpoint returns "healthy"
- [ ] Validate startup fails appropriately without LLM

### Monitoring Setup
- [ ] Configure alerts for LLM unavailability
- [ ] Set up metrics collection for AI performance
- [ ] Establish response time SLAs
- [ ] Monitor success rate thresholds (< 95% triggers alert)

### Error Response Testing
- [ ] Test frontend handles AI unavailability errors
- [ ] Verify clear user messaging when AI is offline
- [ ] Confirm no pattern matching fallbacks activate

## Training & Improvement Strategy

### Current Approach
- All improvements through model training
- No hardcoded rules or patterns
- Continuous learning from conversations
- Personality-based response variations

### Future Enhancements
1. **MCP PostgreSQL Integration**
   - Direct LLM-to-database connections
   - Eliminate intermediate search functions
   - Real-time inventory queries

2. **Enhanced Training Pipeline**
   - Automated training data collection
   - Intent classification improvements
   - Response quality optimization

## API Endpoints

### Core Endpoints
- `POST /api/v1/chat` - Main conversation endpoint
- `GET /api/v1/ai/health` - AI system health check
- `GET /api/v1/ai/personalities` - Personality configurations
- `POST /api/v1/ai/personality` - Create/update personalities

### Health Response Format
```json
{
  "status": "healthy|degraded|unhealthy",
  "ai_available": true,
  "health_score": 95.0,
  "metrics": {
    "total_llm_calls": 1000,
    "success_rate_percent": 98.5,
    "average_response_time_ms": 450
  },
  "configuration": {
    "mode": "AI_ONLY",
    "pattern_matching": "DISABLED",
    "fallback_behavior": "ERROR_ON_LLM_UNAVAILABLE"
  }
}
```

## Compliance & Security

### Data Handling
- No customer data in pattern matching rules
- All processing through secure LLM pipeline
- Audit logging of all AI decisions
- HIPAA-compliant conversation storage

### Age Verification
- Handled by IAM layer before AI processing
- AI assumes all users are pre-verified
- No age-related pattern matching in AI

## Troubleshooting Guide

### Common Issues

1. **"AI service is currently unavailable"**
   - Check LLM process is running
   - Verify model files are accessible
   - Review startup logs for initialization errors

2. **High response times (> 2s)**
   - Check model loading and memory usage
   - Verify database query performance
   - Review concurrent request handling

3. **Low success rate (< 95%)**
   - Analyze error types in metrics
   - Check for model corruption
   - Review recent training data quality

### Debug Commands
```bash
# Check AI health
curl http://localhost:8080/api/v1/ai/health

# View real-time logs
tail -f logs/ai_engine.log | grep "AI Engine Metrics"

# Test LLM directly
python3 -c "from services.smart_ai_engine_v3 import SmartAIEngineV3; 
           import asyncio; 
           engine = SmartAIEngineV3(); 
           asyncio.run(engine.initialize())"
```

## Version History

### v3.0.0 - Pure AI Implementation
- Removed ALL pattern matching
- Implemented comprehensive monitoring
- Added startup validation
- Enhanced error handling
- Created dedicated health endpoint

### Previous Versions (Deprecated)
- v2.x - Hybrid pattern/AI approach (DEPRECATED)
- v1.x - Pattern-first with AI enhancement (DEPRECATED)

## Contact & Support

For questions about the AI-only architecture:
- Technical Lead: AI Engineering Team
- Documentation: This file
- Health Monitoring: `/api/v1/ai/health`
- Metrics Dashboard: Available in AI Admin Dashboard

---

**Last Updated**: 2025-08-24
**Status**: PRODUCTION READY
**Mode**: AI_ONLY - NO PATTERN MATCHING