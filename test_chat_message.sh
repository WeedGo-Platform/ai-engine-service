#!/bin/bash
curl -X POST http://localhost:5024/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"hey","user_id":"user123","session_id":"sess123"}'
