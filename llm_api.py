#!/usr/bin/env python3
"""
WeedGo AI Engine with Full LLM Support
Production-ready virtual budtender powered by Llama 2
"""

import os
import json
import time
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llama_cpp import Llama
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import asyncpg
import logging

# Import our ModelRegistry for model management
from services.model_registry import ModelRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WeedGo AI Engine LLM", version="3.0.0")

# Database connection pool
db_pool = None

# Model registry for version management
model_registry = None

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Model Registry and LLM
llm = None
model_name = "Initializing..."

async def initialize_model():
    """Initialize model using ModelRegistry with base model fallback"""
    global llm, model_name, model_registry
    
    try:
        # Initialize model registry
        model_registry = ModelRegistry()
        await model_registry.initialize_db()
        
        # Ensure base model is available
        base_model = await model_registry.get_or_create_base_model()
        if not base_model:
            logger.error("No base model available. Please download a model.")
            return False
        
        # Load the model (will automatically use base model if no trained version exists)
        logger.info("Loading model through ModelRegistry...")
        llm = await model_registry.load_model()
        
        if llm:
            model_config = model_registry.get_active_model_config()
            if model_config:
                model_name = model_config.model_name
                logger.info(f"✅ Model loaded successfully: {model_name}")
            else:
                model_name = "Base Model (Fallback)"
                logger.info("✅ Base model loaded as fallback")
            return True
        else:
            logger.error("Failed to load any model")
            model_name = "No model loaded"
            return False
            
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        
        # Fallback to direct loading if registry fails
        try:
            MODEL_PATH = "./models/base/llama-2-7b-chat.Q4_K_M.gguf"
            if not os.path.exists(MODEL_PATH):
                MODEL_PATH = "./models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
            
            if os.path.exists(MODEL_PATH):
                logger.info(f"Fallback: Loading model directly from {MODEL_PATH}")
                llm = Llama(
                    model_path=MODEL_PATH,
                    n_ctx=4096,
                    n_threads=8,
                    n_gpu_layers=0,
                    verbose=False,
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    repeat_penalty=1.1,
                )
                model_name = Path(MODEL_PATH).stem
                logger.info(f"✅ Fallback model loaded: {model_name}")
                return True
        except Exception as e2:
            logger.error(f"Fallback loading also failed: {e2}")
            
        model_name = "No model loaded"
        return False

# Startup event to initialize model
@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    success = await initialize_model()
    if not success:
        logger.error("⚠️ WARNING: No model loaded. API will return errors.")

# Cannabis knowledge base
CANNABIS_KNOWLEDGE = """
You are a knowledgeable and friendly virtual budtender at WeedGo, a premium cannabis dispensary. 
Your role is to help customers find the perfect cannabis products for their needs.

Key Knowledge:
1. Cannabis Types:
   - Indica: Relaxing, sedating, good for evening use, helps with sleep and pain
   - Sativa: Energizing, uplifting, good for daytime use, helps with depression and fatigue
   - Hybrid: Balanced effects, versatile use
   - CBD: Non-psychoactive, therapeutic benefits, helps with anxiety and inflammation

2. Common Terpenes:
   - Myrcene: Sedating, muscle relaxant, found in mangoes
   - Limonene: Uplifting, anti-anxiety, citrus aroma
   - Pinene: Alertness, memory, pine scent
   - Linalool: Calming, anti-anxiety, lavender scent
   - Caryophyllene: Anti-inflammatory, spicy/peppery

3. Medical Uses:
   - Anxiety: High-CBD strains, indica-dominant hybrids
   - Insomnia: Indica strains with myrcene
   - Pain: High-THC indicas or balanced THC/CBD
   - Depression: Sativa strains with limonene
   - Inflammation: CBD-dominant strains

4. Consumption Methods:
   - Flower: Immediate effects, 1-3 hours duration
   - Edibles: Delayed onset (30-120 min), 4-8 hours duration
   - Vapes: Fast onset, 2-4 hours duration
   - Tinctures: Sublingual absorption, 15-45 min onset
   - Topicals: Localized relief, non-psychoactive

Always prioritize safety, start with low doses, and provide educational information.
Never make medical claims or diagnoses. Always suggest consulting healthcare providers for serious conditions.
"""

# Session memory storage
sessions: Dict[str, ConversationBufferMemory] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str
    timestamp: str
    model_used: str
    tokens_used: Optional[int] = None

async def get_relevant_products(query: str, limit: int = 3):
    """Fetch relevant OCS products based on query"""
    if not db_pool:
        return []
    
    try:
        async with db_pool.acquire() as conn:
            # Search for relevant products
            products = await conn.fetch("""
                SELECT 
                    product_name, brand, category, plant_type,
                    thc_max_percent, cbd_max_percent,
                    short_description, unit_price,
                    terpenes, stock_status
                FROM products
                WHERE 
                    product_name ILIKE '%' || $1 || '%'
                    OR short_description ILIKE '%' || $1 || '%'
                    OR category ILIKE '%' || $1 || '%'
                ORDER BY 
                    CASE 
                        WHEN product_name ILIKE '%' || $1 || '%' THEN 1
                        ELSE 2
                    END,
                    thc_max_percent DESC NULLS LAST
                LIMIT $2
            """, query, limit)
            
            return [dict(p) for p in products]
    except Exception as e:
        logger.error(f"Failed to fetch products: {e}")
        return []

def get_or_create_session(session_id: str) -> ConversationBufferMemory:
    """Get or create a conversation memory for a session"""
    if session_id not in sessions:
        sessions[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return sessions[session_id]

def create_prompt(message: str, context: str = "", products: list = None) -> str:
    """Create a prompt for the LLM with cannabis context and real OCS products"""
    
    product_context = ""
    if products:
        product_context = "\n\nAvailable OCS products matching your query:\n"
        for i, p in enumerate(products[:3], 1):
            product_context += f"\n{i}. {p['product_name']} by {p['brand']}"
            product_context += f"\n   Type: {p['plant_type'] or 'Unknown'} | Category: {p['category']}"
            product_context += f"\n   THC: {p['thc_max_percent'] or 0}% | CBD: {p['cbd_max_percent'] or 0}%"
            if p['short_description']:
                product_context += f"\n   Description: {p['short_description'][:100]}..."
            if p['unit_price']:
                product_context += f"\n   Price: ${p['unit_price']}"
            if p['stock_status']:
                product_context += f"\n   Stock: {p['stock_status']}"
            product_context += "\n"
    
    system_prompt = f"""<s>[INST] <<SYS>>
{CANNABIS_KNOWLEDGE}

{product_context}

Previous context: {context if context else 'This is the beginning of our conversation.'}

IMPORTANT: When recommending products, always use the specific OCS product names and details provided above.
<</SYS>>

Customer: {message}

Budtender: [/INST]"""
    return system_prompt

async def generate_response(
    prompt: str, 
    temperature: float = 0.7,
    max_tokens: int = 512,
    stream: bool = False
) -> AsyncGenerator[str, None]:
    """Generate response from LLM"""
    if not llm:
        yield "I apologize, but the AI model is currently loading. Please try again in a moment."
        return
    
    try:
        if stream:
            # Streaming response
            stream_response = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                stop=["</s>", "[INST]", "Customer:"],
                echo=False
            )
            
            for output in stream_response:
                token = output['choices'][0]['text']
                yield token
        else:
            # Non-streaming response
            response = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "[INST]", "Customer:"],
                echo=False
            )
            yield response['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        yield "I apologize, but I encountered an error. Please try rephrasing your question."

@app.get("/")
async def root():
    return {
        "message": "WeedGo AI Engine LLM API v3.0",
        "model": model_name,
        "status": "operational" if llm else "loading"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "model_loaded": llm is not None,
        "sessions_active": len(sessions),
        "memory_usage": f"{len(str(llm)) / 1024 / 1024:.2f} MB" if llm else "0 MB"
    }

@app.post("/api/v2/budtender/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """LLM-powered chat endpoint"""
    
    if not llm:
        raise HTTPException(status_code=503, detail="Model is still loading")
    
    # Get session memory
    memory = get_or_create_session(request.session_id)
    
    # Get conversation context
    messages = memory.chat_memory.messages
    context = ""
    if messages:
        # Get last 3 exchanges for context
        recent = messages[-6:] if len(messages) >= 6 else messages
        context = "\n".join([
            f"{'Customer' if isinstance(m, HumanMessage) else 'Budtender'}: {m.content}"
            for m in recent
        ])
    
    # Get relevant products from database
    products = await get_relevant_products(request.message, limit=5)
    
    # Create prompt with real products
    prompt = create_prompt(request.message, context, products)
    
    # Generate response
    start_time = time.time()
    response_text = ""
    tokens = 0
    
    async for chunk in generate_response(
        prompt, 
        request.temperature,
        request.max_tokens,
        False  # Don't stream for regular endpoint
    ):
        response_text += chunk
        tokens += 1
    
    # Clean up response
    response_text = response_text.strip()
    if not response_text:
        response_text = "I understand you're looking for cannabis guidance. Could you please tell me more about what you're looking for or what effects you're seeking?"
    
    # Store in memory
    memory.chat_memory.add_user_message(request.message)
    memory.chat_memory.add_ai_message(response_text)
    
    generation_time = time.time() - start_time
    logger.info(f"Generated response in {generation_time:.2f}s using {tokens} tokens")
    
    return ChatResponse(
        response=response_text,
        session_id=request.session_id,
        message_id=f"msg_{int(time.time()*1000)}",
        timestamp=datetime.now().isoformat(),
        model_used=model_name,
        tokens_used=tokens
    )

@app.post("/api/v2/budtender/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    
    if not llm:
        raise HTTPException(status_code=503, detail="Model is still loading")
    
    # Get session memory
    memory = get_or_create_session(request.session_id)
    
    # Get conversation context
    messages = memory.chat_memory.messages
    context = ""
    if messages:
        recent = messages[-6:] if len(messages) >= 6 else messages
        context = "\n".join([
            f"{'Customer' if isinstance(m, HumanMessage) else 'Budtender'}: {m.content}"
            for m in recent
        ])
    
    # Get relevant products from database
    products = await get_relevant_products(request.message, limit=5)
    
    # Create prompt with real products
    prompt = create_prompt(request.message, context, products)
    
    async def generate():
        """Generator for streaming response"""
        full_response = ""
        try:
            async for token in generate_response(
                prompt,
                request.temperature,
                request.max_tokens,
                True
            ):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            # Store complete response in memory
            memory.chat_memory.add_user_message(request.message)
            memory.chat_memory.add_ai_message(full_response)
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True, 'total_response': full_response})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@app.post("/api/v2/budtender/analyze")
async def analyze_request(request: Dict[str, Any]):
    """Analyze a cannabis-related query using LLM"""
    
    if not llm:
        raise HTTPException(status_code=503, detail="Model is still loading")
    
    query = request.get("query", "")
    analysis_type = request.get("type", "general")
    
    prompts = {
        "strain": f"Analyze this cannabis strain and provide detailed information: {query}",
        "medical": f"Explain the medical benefits and considerations for: {query}",
        "effects": f"Describe the effects and experience of: {query}",
        "terpenes": f"Explain the terpene profile and benefits of: {query}",
        "general": f"Provide comprehensive cannabis information about: {query}"
    }
    
    prompt = create_prompt(prompts.get(analysis_type, prompts["general"]))
    
    response_text = ""
    async for chunk in generate_response(prompt, temperature=0.5, max_tokens=1024):
        response_text += chunk
    
    return {
        "query": query,
        "type": analysis_type,
        "analysis": response_text.strip(),
        "model": model_name,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/budtender/session/{session_id}")
async def get_session(session_id: str):
    """Get session conversation history"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    memory = sessions[session_id]
    messages = memory.chat_memory.messages
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "conversation": [
            {
                "role": "customer" if isinstance(m, HumanMessage) else "budtender",
                "content": m.content
            }
            for m in messages
        ]
    }

@app.delete("/api/v2/budtender/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session's conversation history"""
    
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    
    return {"message": "Session not found"}

@app.get("/api/v2/models/status")
async def model_status():
    """Get detailed model status"""
    
    return {
        "primary_model": {
            "name": "Llama 2 7B Chat",
            "path": MODEL_PATH,
            "loaded": llm is not None and "llama" in model_name.lower(),
            "size": "4.08 GB",
            "quantization": "Q4_K_M"
        },
        "backup_model": {
            "name": "Mistral 7B Instruct",
            "path": BACKUP_MODEL_PATH,
            "loaded": llm is not None and "mistral" in model_name.lower(),
            "size": "4.37 GB",
            "quantization": "Q4_K_M"
        },
        "current_model": model_name,
        "context_length": 4096,
        "sessions_active": len(sessions),
        "ready": llm is not None
    }

@app.post("/api/v2/budtender/feedback")
async def submit_feedback(feedback: Dict[str, Any]):
    """Collect feedback for continuous improvement"""
    
    # In production, this would store in a database
    logger.info(f"Feedback received: {feedback}")
    
    return {
        "status": "success",
        "message": "Thank you for your feedback! We continuously improve our recommendations based on your input."
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    global db_pool
    
    logger.info("LLM API starting...")
    logger.info(f"Model status: {model_name}")
    
    # Connect to database
    try:
        db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5434,
            user='weedgo',
            password='your_password_here',
            database='ai_engine',
            min_size=1,
            max_size=5
        )
        logger.info("✅ Connected to PostgreSQL for OCS product data")
        
        # Count products
        async with db_pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM products")
            logger.info(f"✅ Access to {count} OCS products")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.warning("Running without product database")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_pool
    
    logger.info("LLM API shutting down...")
    
    if db_pool:
        await db_pool.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 WeedGo AI Engine with LLM Support")
    print("="*60)
    print(f"📦 Model: {model_name}")
    print(f"🔥 Status: {'Ready' if llm else 'Loading...'}")
    print(f"📍 API URL: http://localhost:8001")
    print(f"📚 Docs: http://localhost:8001/docs")
    print("="*60)
    
    if llm:
        print("\n✅ LLM is ready! Test with:")
        print('curl -X POST http://localhost:8001/api/v2/budtender/chat \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"message": "What strain helps with anxiety?", "session_id": "test"}\'')
    else:
        print("\n⚠️  No LLM model loaded. The API will use fallback responses.")
    
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)