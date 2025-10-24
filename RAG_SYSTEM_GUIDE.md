# RAG System - Complete Setup Guide

## Overview

This RAG (Retrieval-Augmented Generation) system provides factual grounding for AI agents using a hybrid PostgreSQL + FAISS architecture with multilingual support.

### Architecture

- **Embedding Model**: `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, 25+ languages)
- **Storage**: Hybrid PostgreSQL (pgvector) + FAISS for performance + persistence
- **Cache**: 1-hour TTL with query hash-based keys (target >70% hit rate)
- **Performance**: Balanced mode (~50ms target latency)
- **Access Control**: Agent-based filtering (public, customer, platform, internal)
- **Data Partitioning**: By tenant_id and store_id

### Components

```
Backend/
├── services/rag/
│   ├── embedding_service.py      # Text → vector embeddings
│   ├── rag_service.py             # Core RAG orchestrator (hybrid storage)
│   ├── document_chunker.py        # Semantic chunking (512 tokens, overlap)
│   ├── ocs_product_sync.py        # Sync ocs_product_catalog (67 cols)
│   ├── faq_ingestion.py           # Load FAQs into knowledge base
│   └── knowledge_base/
│       └── cannabis_platform_faqs.md  # 50+ Q&As
├── migrations/
│   └── create_rag_schema.sql      # PostgreSQL + pgvector schema
└── scripts/
    └── rag_init.py                # Initialization & testing
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `sentence-transformers==2.2.2` (embedding model)
- `faiss-cpu==1.7.4` (vector search)
- `pgvector==0.2.4` (PostgreSQL vector extension)
- `nltk==3.8.1` (text processing)
- `spacy==3.7.2` (NLP)
- `asyncpg` (async PostgreSQL)

### 2. Download NLP Models

```bash
# NLTK data
python -c "import nltk; nltk.download('punkt')"

# Spacy model
python -m spacy download en_core_web_sm
```

### 3. Enable PostgreSQL pgvector Extension

```bash
# Connect to your database
psql -U postgres -d weedgo

# Enable extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Run Database Migration

```bash
psql -U postgres -d weedgo -f src/Backend/migrations/create_rag_schema.sql
```

This creates:
- `knowledge_documents` - Document metadata with access control
- `knowledge_chunks` - Chunked text with 384-dim embeddings (pgvector)
- `knowledge_sync_status` - Sync tracking for source tables
- `rag_query_analytics` - Query performance metrics

### 5. Initialize RAG System

```bash
cd src/Backend
python scripts/rag_init.py init
```

This will:
- Initialize embedding service (download model ~80MB)
- Warm up FAISS index
- Ingest FAQs from knowledge base
- Test retrieval and access control

## Usage

### Initialize RAG System

```python
from services.rag.rag_service import get_rag_service
import asyncpg

# Create database pool
db_pool = await asyncpg.create_pool(
    host="localhost",
    database="weedgo",
    user="postgres",
    password=""
)

# Initialize RAG
rag_service = await get_rag_service(db_pool)
await rag_service.initialize()
```

### Retrieve Knowledge

```python
# Basic retrieval
results = await rag_service.retrieve(
    query="What is the difference between indica and sativa?",
    agent_id="dispensary",  # Access control
    top_k=5  # Number of results
)

# With filtering
results = await rag_service.retrieve(
    query="High THC products",
    agent_id="dispensary",
    tenant_id="tenant-uuid",
    store_id="store-uuid",
    document_types=["ocs_product"],  # Only products
    top_k=10
)

# Result format
for result in results:
    print(result["text"])  # Chunk text
    print(result["similarity"])  # Similarity score
    print(result["document_type"])  # ocs_product, faq, etc.
    print(result["metadata"])  # Custom metadata
```

### Sync OCS Products

```bash
# Sync all products for tenant
python scripts/rag_init.py sync <tenant-uuid>
```

Or programmatically:

```python
from services.rag.ocs_product_sync import get_ocs_sync_service

sync_service = await get_ocs_sync_service(db_pool)

result = await sync_service.sync_tenant_products(
    tenant_id="tenant-uuid",
    store_id="store-uuid",  # Optional
    force_full_sync=True
)
```

### Ingest FAQs

```python
from services.rag.faq_ingestion import get_faq_ingestion_service

faq_service = await get_faq_ingestion_service(db_pool)

# Single file
result = await faq_service.ingest_faq_file(
    file_path="knowledge_base/cannabis_platform_faqs.md",
    access_level="public"
)

# Entire directory
results = await faq_service.ingest_all_faqs(
    faq_directory="knowledge_base/",
    access_level="public"
)
```

### Add Custom Documents

```python
await rag_service.add_document(
    text="Your document text here...",
    metadata={"source": "custom", "author": "Admin"},
    document_type="platform_docs",
    tenant_id="tenant-uuid",
    store_id=None,  # Global to tenant
    source_table="custom_docs",
    source_id="doc-123",
    access_level="customer"  # public, customer, platform, internal
)
```

## Access Control

### Access Levels

- **public**: All agents can access
- **customer**: Customer-facing agents (dispensary, assistant)
- **platform**: Sales and platform agents
- **internal**: Admin agents only

### Agent Filtering

```python
# Dispensary agent - gets public + customer
results = await rag_service.retrieve(
    query="product information",
    agent_id="dispensary"
)

# Sales agent - gets public + platform
results = await rag_service.retrieve(
    query="platform features",
    agent_id="sales"
)

# Assistant agent - gets public only
results = await rag_service.retrieve(
    query="general info",
    agent_id="assistant"
)
```

## Data Sources

### 1. OCS Product Catalog (Primary)

The **ocs_product_catalog** is the "bible" - source of truth for all cannabis information.

**67 columns** including:
- Product info: name, brand, producer, category
- Potency: thc_min, thc_max, cbd_min, cbd_max
- Characteristics: strain_type, genetics, flavour_profile, aroma
- Effects: effects, medical_effects, side_effects
- Terpenes: terpene profiles and concentrations

**Sync frequency**: Real-time + hourly batch (configurable)

**Chunking strategy**: 
- Overview chunk (important fields)
- Effects chunk (all effects data)
- Potency chunk (THC, CBD, terpenes)
- Details chunk (genetics, flavour, aroma)
- Info chunk (description, producer, brand)

### 2. FAQs

Comprehensive Q&A covering:
- **Cannabis Basics**: Strains, cannabinoids, terpenes, consumption methods
- **Product Information**: OCS catalog, THC/CBD content, storage
- **Compliance & Legal**: Age requirements, possession limits, driving rules
- **Platform Features**: Pricing, AI agents, integrations, analytics
- **Customer Support**: Accounts, orders, payments, returns
- **Cannabis Effects**: Dosing, side effects, medical uses, safety

**Access level**: Public

**Format**: Markdown with H2 categories and H3 questions

### 3. Compliance Documents (Future)

CRSA regulations, age verification, packaging requirements

### 4. Training Materials (Future)

Staff training, product knowledge, customer service

## Performance Optimization

### Target Metrics

- **Query latency**: <50ms (embedding + FAISS search)
- **Re-ranking**: +20ms
- **Total overhead**: <100ms
- **Cache hit rate**: >70%

### Monitoring

```python
# Get performance metrics
metrics = rag_service.get_metrics()

print(f"Total queries: {metrics['total_queries']}")
print(f"Cache hits: {metrics['cache_hits']}")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Avg latency: {metrics['avg_latency_ms']:.2f}ms")
print(f"Total documents: {metrics['total_documents']}")
print(f"Total chunks: {metrics['total_chunks']}")
```

### Query Analytics

```sql
-- Top queries
SELECT query_text, COUNT(*) as count, AVG(latency_ms) as avg_latency
FROM rag_query_analytics
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY query_text
ORDER BY count DESC
LIMIT 20;

-- Cache performance
SELECT 
    cache_hit,
    COUNT(*) as queries,
    AVG(latency_ms) as avg_latency,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
FROM rag_query_analytics
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY cache_hit;
```

### Tuning FAISS Index

```python
# Rebuild with different IVF list count
await rag_service._build_faiss_index(
    nlist=200  # Default: 100, increase for more data
)
```

## Testing

### Run Test Suite

```bash
python scripts/rag_init.py test
```

Tests:
- FAQ retrieval accuracy
- OCS product search
- Access control filtering
- Tenant/store partitioning
- Query performance

### Manual Testing

```python
# Test different query types
test_queries = [
    "What are the effects of indica strains?",
    "High THC sativa products",
    "Legal age for cannabis purchase",
    "Platform pricing information",
    "How to handle cannabis overdose"
]

for query in test_queries:
    results = await rag_service.retrieve(query, agent_id="dispensary", top_k=3)
    print(f"\nQuery: {query}")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['metadata'].get('question', r['text'][:100])}")
        print(f"   Similarity: {r['similarity']:.3f}")
```

## Troubleshooting

### Import Errors

```
Import "asyncpg" could not be resolved
Import "nltk" could not be resolved
```

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt')"
```

### pgvector Extension Not Found

```
ERROR: extension "vector" does not exist
```

**Solution**: Install pgvector
```bash
# PostgreSQL 12+
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Then in psql
CREATE EXTENSION vector;
```

### Slow Query Performance

**Check**:
1. FAISS index built? `await rag_service.initialize()`
2. pgvector index created? Check schema migration
3. Cache working? Check `cache_hit_rate` in metrics
4. Too many chunks? Increase `chunk_size` or reduce overlap

**Optimize**:
```python
# Reduce top_k for initial FAISS search
results = await rag_service.retrieve(query, top_k=5)  # Instead of 20

# Warm up cache with common queries
common_queries = ["indica vs sativa", "THC content", "legal age"]
for q in common_queries:
    await rag_service.retrieve(q, agent_id="assistant")
```

### Low Accuracy

**Solutions**:
1. Check document chunking - are chunks too small/large?
2. Verify metadata - are important fields indexed?
3. Test embedding quality - similar queries returning similar results?
4. Adjust re-ranking weights - increase document type priority

## Maintenance

### Daily Tasks

```bash
# None - automatic caching and sync
```

### Weekly Tasks

```bash
# Review query analytics
psql -d weedgo -c "SELECT * FROM rag_query_analytics ORDER BY created_at DESC LIMIT 100;"

# Check sync status
psql -d weedgo -c "SELECT * FROM knowledge_sync_status;"
```

### Monthly Tasks

```bash
# Rebuild FAISS index for optimization
python -c "
import asyncio
from services.rag.rag_service import get_rag_service
import asyncpg

async def rebuild():
    pool = await asyncpg.create_pool(database='weedgo')
    rag = await get_rag_service(pool)
    await rag._build_faiss_index()
    await pool.close()

asyncio.run(rebuild())
"
```

## Next Steps

1. ✅ **Install dependencies**: `pip install -r requirements.txt`
2. ✅ **Run migration**: `psql -f create_rag_schema.sql`
3. ✅ **Initialize system**: `python scripts/rag_init.py init`
4. 🔄 **Sync OCS products**: `python scripts/rag_init.py sync <tenant-id>`
5. 🔄 **Create RAG tool**: `/Backend/services/tools/rag_tool.py`
6. 🔄 **Integrate with agents**: Hook into `agent_pool_manager.py`
7. 🔄 **Test access control**: Verify filtering works
8. 🔄 **Performance testing**: Check latency and cache hit rate

## Support

For issues or questions:
- Check logs: `tail -f logs/rag_service.log`
- Review metrics: `rag_service.get_metrics()`
- Test queries: `python scripts/rag_init.py test`
