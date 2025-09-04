#!/usr/bin/env python3
"""
WeedGo RAG-Enhanced LLM Service
Combines Llama 2 with Retrieval Augmented Generation for accurate product recommendations
"""

import os
import json
import time
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import asyncio
import hashlib

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LLM imports
from llama_cpp import Llama

# Vector database imports
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)

# Embeddings
from sentence_transformers import SentenceTransformer

# Database
import asyncpg
import redis

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WeedGo RAG-LLM Service", version="4.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm = None
embedder = None
milvus_collection = None
redis_client = None
db_pool = None

# Cannabis product schema
class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    strain_type: str
    thc_content: float
    cbd_content: float
    terpenes: List[str]
    effects: List[str]
    medical_uses: List[str]
    description: str
    price: float
    inventory: int

class RAGQuery(BaseModel):
    message: str
    session_id: str
    use_rag: Optional[bool] = True
    top_k: Optional[int] = 5
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

# Sample products for demo
SAMPLE_PRODUCTS = [
    {
        "id": "prod_001",
        "name": "Blue Dream",
        "brand": "WeedGo Premium",
        "category": "Flower",
        "strain_type": "Hybrid",
        "thc_content": 18.5,
        "cbd_content": 0.2,
        "terpenes": ["Myrcene", "Pinene", "Caryophyllene"],
        "effects": ["Euphoric", "Creative", "Relaxed", "Happy"],
        "medical_uses": ["Stress", "Depression", "Pain", "Fatigue"],
        "description": "Blue Dream is a sativa-dominant hybrid with balanced effects. Sweet berry aroma from Blueberry parent.",
        "price": 45.00,
        "inventory": 50
    },
    {
        "id": "prod_002",
        "name": "OG Kush",
        "brand": "WeedGo Classic",
        "category": "Flower",
        "strain_type": "Indica",
        "thc_content": 22.0,
        "cbd_content": 0.1,
        "terpenes": ["Limonene", "Myrcene", "Caryophyllene"],
        "effects": ["Relaxed", "Happy", "Sleepy", "Hungry"],
        "medical_uses": ["Insomnia", "Pain", "Anxiety", "Appetite Loss"],
        "description": "OG Kush is a classic indica with strong sedating effects. Earthy pine scent with woody undertones.",
        "price": 50.00,
        "inventory": 30
    },
    {
        "id": "prod_003",
        "name": "Charlotte's Web",
        "brand": "WeedGo Medical",
        "category": "Flower",
        "strain_type": "CBD",
        "thc_content": 0.3,
        "cbd_content": 17.0,
        "terpenes": ["Pinene", "Myrcene", "Caryophyllene"],
        "effects": ["Calm", "Focused", "Clear-headed", "Relaxed"],
        "medical_uses": ["Seizures", "Inflammation", "Anxiety", "Pain"],
        "description": "Charlotte's Web is a high-CBD strain with minimal psychoactive effects. Perfect for medical use.",
        "price": 55.00,
        "inventory": 25
    },
    {
        "id": "prod_004",
        "name": "Sour Diesel",
        "brand": "WeedGo Energy",
        "category": "Flower",
        "strain_type": "Sativa",
        "thc_content": 20.0,
        "cbd_content": 0.2,
        "terpenes": ["Limonene", "Caryophyllene", "Myrcene"],
        "effects": ["Energetic", "Uplifted", "Creative", "Focused"],
        "medical_uses": ["Depression", "Fatigue", "Stress", "ADD/ADHD"],
        "description": "Sour Diesel is an energizing sativa with a pungent diesel aroma. Great for daytime use.",
        "price": 48.00,
        "inventory": 40
    },
    {
        "id": "prod_005",
        "name": "Northern Lights",
        "brand": "WeedGo Night",
        "category": "Flower",
        "strain_type": "Indica",
        "thc_content": 18.0,
        "cbd_content": 0.1,
        "terpenes": ["Myrcene", "Caryophyllene", "Limonene"],
        "effects": ["Sleepy", "Relaxed", "Happy", "Euphoric"],
        "medical_uses": ["Insomnia", "Pain", "Stress", "Depression"],
        "description": "Northern Lights is a legendary indica known for its fast-acting, dreamy effects.",
        "price": 42.00,
        "inventory": 35
    }
]

async def initialize_services():
    """Initialize all services"""
    global llm, embedder, milvus_collection, redis_client, db_pool
    
    # Initialize LLM
    logger.info("Loading LLM model...")
    try:
        llm = Llama(
            model_path="./models/llama-2-7b-chat.Q4_K_M.gguf",
            n_ctx=4096,
            n_threads=8,
            n_gpu_layers=0,
            verbose=False,
            temperature=0.7,
        )
        logger.info("✅ LLM loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load LLM: {e}")
    
    # Initialize embedder
    logger.info("Loading embedding model...")
    try:
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded")
    except Exception as e:
        logger.error(f"Failed to load embedder: {e}")
    
    # Initialize Milvus
    logger.info("Connecting to Milvus...")
    try:
        connections.connect(
            alias="default",
            host="localhost",
            port="19530"
        )
        
        # Create collection if not exists
        collection_name = "cannabis_products"
        if not utility.has_collection(collection_name):
            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=5000)
            ]
            schema = CollectionSchema(fields, "Cannabis products collection")
            milvus_collection = Collection(collection_name, schema)
            
            # Create index
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            milvus_collection.create_index("embedding", index_params)
            logger.info("✅ Created Milvus collection")
        else:
            milvus_collection = Collection(collection_name)
            milvus_collection.load()
            logger.info("✅ Loaded existing Milvus collection")
            
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
    
    # Initialize Redis
    logger.info("Connecting to Redis...")
    try:
        redis_client = redis.Redis(
            host='localhost',
            port=6381,
            decode_responses=True
        )
        redis_client.ping()
        logger.info("✅ Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    # Initialize PostgreSQL
    logger.info("Connecting to PostgreSQL...")
    try:
        db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5434,
            user='weedgo',
            password='your_password_here',
            database='ai_engine',
            min_size=1,
            max_size=10
        )
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
    
    # Load sample products into Milvus
    await load_products_to_milvus()

async def load_products_to_milvus():
    """Load sample products into Milvus"""
    if not milvus_collection or not embedder:
        return
    
    try:
        # Check if products already loaded
        if milvus_collection.num_entities > 0:
            logger.info(f"Products already loaded: {milvus_collection.num_entities} entities")
            return
        
        ids = []
        names = []
        descriptions = []
        embeddings = []
        metadatas = []
        
        for product in SAMPLE_PRODUCTS:
            # Create searchable text
            search_text = f"{product['name']} {product['brand']} {product['strain_type']} "
            search_text += f"{' '.join(product['effects'])} {' '.join(product['medical_uses'])} "
            search_text += f"{' '.join(product['terpenes'])} {product['description']}"
            
            # Generate embedding
            embedding = embedder.encode(search_text)
            
            ids.append(product['id'])
            names.append(product['name'])
            descriptions.append(product['description'])
            embeddings.append(embedding.tolist())
            metadatas.append(json.dumps(product))
        
        # Insert into Milvus
        milvus_collection.insert([ids, names, descriptions, embeddings, metadatas])
        milvus_collection.flush()
        
        logger.info(f"✅ Loaded {len(SAMPLE_PRODUCTS)} products into Milvus")
        
    except Exception as e:
        logger.error(f"Failed to load products: {e}")

async def search_products(query: str, top_k: int = 5) -> List[Dict]:
    """Search for relevant products using vector similarity"""
    if not milvus_collection or not embedder:
        return []
    
    try:
        # Generate query embedding
        query_embedding = embedder.encode(query).tolist()
        
        # Search in Milvus
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = milvus_collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["name", "description", "metadata"]
        )
        
        products = []
        for hits in results:
            for hit in hits:
                metadata = json.loads(hit.entity.get('metadata'))
                metadata['similarity_score'] = 1 / (1 + hit.distance)  # Convert distance to similarity
                products.append(metadata)
        
        return products
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

def create_rag_prompt(query: str, products: List[Dict]) -> str:
    """Create a RAG-enhanced prompt with product information"""
    
    context = "Available products matching your query:\n\n"
    for i, product in enumerate(products[:3], 1):
        context += f"{i}. {product['name']} ({product['strain_type']})\n"
        context += f"   THC: {product['thc_content']}% | CBD: {product['cbd_content']}%\n"
        context += f"   Effects: {', '.join(product['effects'])}\n"
        context += f"   Medical Uses: {', '.join(product['medical_uses'])}\n"
        context += f"   Terpenes: {', '.join(product['terpenes'])}\n"
        context += f"   Description: {product['description']}\n"
        context += f"   Price: ${product['price']} | In Stock: {product['inventory']} units\n\n"
    
    prompt = f"""<s>[INST] <<SYS>>
You are a knowledgeable budtender at WeedGo dispensary. Use the product information provided to give accurate, helpful recommendations.
Always mention specific products by name when relevant. Be friendly and educational.

{context}
<</SYS>>

Customer Question: {query}

Please provide a helpful response that references the specific products above when appropriate.
[/INST]"""
    
    return prompt

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await initialize_services()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if db_pool:
        await db_pool.close()
    if milvus_collection:
        connections.disconnect("default")

@app.get("/")
async def root():
    return {
        "service": "WeedGo RAG-LLM Service",
        "version": "4.0.0",
        "components": {
            "llm": "Loaded" if llm else "Not loaded",
            "embedder": "Loaded" if embedder else "Not loaded",
            "milvus": "Connected" if milvus_collection else "Not connected",
            "redis": "Connected" if redis_client else "Not connected",
            "postgres": "Connected" if db_pool else "Not connected"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": llm is not None,
            "vector_db": milvus_collection is not None,
            "embedder": embedder is not None,
            "cache": redis_client is not None,
            "database": db_pool is not None
        }
    }

@app.post("/api/v3/budtender/rag-chat")
async def rag_chat(request: RAGQuery):
    """RAG-enhanced chat endpoint"""
    
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not available")
    
    # Check cache first
    cache_key = f"rag_chat:{hashlib.md5(request.message.encode()).hexdigest()}"
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # Search for relevant products
    products = []
    if request.use_rag:
        products = await search_products(request.message, request.top_k)
    
    # Create prompt with RAG context
    if products:
        prompt = create_rag_prompt(request.message, products)
    else:
        # Fallback to regular prompt
        prompt = f"""<s>[INST] You are a helpful budtender at WeedGo dispensary. 
Customer: {request.message}
Budtender: [/INST]"""
    
    # Generate response
    start_time = time.time()
    response = llm(
        prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        stop=["</s>", "[INST]", "Customer:"],
        echo=False
    )
    
    response_text = response['choices'][0]['text'].strip()
    generation_time = time.time() - start_time
    
    # Log to database
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_history (session_id, message, response, created_at)
                VALUES ($1, $2, $3, $4)
            """, request.session_id, request.message, response_text, datetime.now())
    
    result = {
        "response": response_text,
        "session_id": request.session_id,
        "products_found": len(products),
        "products": products[:3] if products else [],
        "generation_time": f"{generation_time:.2f}s",
        "used_rag": request.use_rag and len(products) > 0
    }
    
    # Cache the result
    if redis_client:
        redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return result

@app.post("/api/v3/products/search")
async def search_products_endpoint(query: Dict[str, Any]):
    """Search products using semantic search"""
    
    search_query = query.get("query", "")
    top_k = query.get("top_k", 5)
    
    products = await search_products(search_query, top_k)
    
    return {
        "query": search_query,
        "count": len(products),
        "products": products
    }

@app.post("/api/v3/products/add")
async def add_product(product: Product):
    """Add a new product to the vector database"""
    
    if not milvus_collection or not embedder:
        raise HTTPException(status_code=503, detail="Vector database not available")
    
    # Create searchable text
    search_text = f"{product.name} {product.brand} {product.strain_type} "
    search_text += f"{' '.join(product.effects)} {' '.join(product.medical_uses)} "
    search_text += f"{' '.join(product.terpenes)} {product.description}"
    
    # Generate embedding
    embedding = embedder.encode(search_text).tolist()
    
    # Insert into Milvus
    milvus_collection.insert(
        [[product.id], [product.name], [product.description], 
         [embedding], [json.dumps(product.dict())]]
    )
    milvus_collection.flush()
    
    return {"status": "success", "product_id": product.id}

@app.get("/api/v3/stats")
async def get_stats():
    """Get system statistics"""
    
    stats = {
        "products_indexed": 0,
        "total_chats": 0,
        "cache_size": 0
    }
    
    if milvus_collection:
        stats["products_indexed"] = milvus_collection.num_entities
    
    if db_pool:
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM chat_history")
            stats["total_chats"] = result
    
    if redis_client:
        stats["cache_size"] = redis_client.dbsize()
    
    return stats

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 WeedGo RAG-Enhanced LLM Service")
    print("="*60)
    print("📦 Components:")
    print("  • LLM: Llama 2 7B")
    print("  • Vector DB: Milvus")
    print("  • Embedder: all-MiniLM-L6-v2")
    print("  • Cache: Redis")
    print("  • Database: PostgreSQL")
    print("="*60)
    print("📍 API URL: http://localhost:8002")
    print("📚 Docs: http://localhost:8002/docs")
    print("="*60)
    print("\nStarting services...")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)