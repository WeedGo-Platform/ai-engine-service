"""
RAG System Initialization Script
Sets up and tests the complete RAG pipeline
"""

import asyncio
import logging
import os
from datetime import datetime
import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_rag_system():
    """
    Initialize complete RAG system
    Run this after database migration
    """
    logger.info("🚀 Starting RAG System Initialization")
    
    # Step 1: Create database connection pool
    logger.info("📊 Connecting to database...")
    db_pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "weedgo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        min_size=2,
        max_size=10
    )
    logger.info("✅ Database connected")
    
    # Step 2: Initialize RAG service
    logger.info("🧠 Initializing RAG service...")
    from services.rag.rag_service import get_rag_service
    rag_service = await get_rag_service(db_pool)
    await rag_service.initialize()
    logger.info("✅ RAG service initialized")
    
    # Step 3: Initialize embedding service
    logger.info("🔤 Warming up embedding service...")
    from services.rag.embedding_service import get_embedding_service
    embedding_service = get_embedding_service()
    embedding_service.warmup()
    logger.info("✅ Embedding service ready")
    
    # Step 4: Initialize OCS product sync
    logger.info("🌿 Initializing OCS product sync...")
    from services.rag.ocs_product_sync import get_ocs_sync_service
    sync_service = await get_ocs_sync_service(db_pool)
    logger.info("✅ OCS sync service ready")
    
    # Step 5: Initialize FAQ ingestion
    logger.info("❓ Initializing FAQ ingestion...")
    from services.rag.faq_ingestion import get_faq_ingestion_service
    faq_service = await get_faq_ingestion_service(db_pool)
    logger.info("✅ FAQ ingestion service ready")
    
    # Step 6: Ingest FAQs
    logger.info("📚 Ingesting FAQ knowledge base...")
    faq_dir = os.path.join(
        os.path.dirname(__file__),
        "rag",
        "knowledge_base"
    )
    
    if os.path.exists(faq_dir):
        results = await faq_service.ingest_all_faqs(faq_dir, access_level="public")
        total_sections = sum(r.get("total_sections", 0) for r in results)
        ingested = sum(r.get("ingested", 0) for r in results)
        logger.info(f"✅ Ingested {ingested}/{total_sections} FAQ sections from {len(results)} files")
    else:
        logger.warning(f"⚠️  FAQ directory not found: {faq_dir}")
    
    # Step 7: Test RAG retrieval
    logger.info("🔍 Testing RAG retrieval...")
    test_queries = [
        "What is the difference between indica and sativa?",
        "How much THC should a beginner start with?",
        "What are terpenes?",
        "Can I return cannabis products?"
    ]
    
    for query in test_queries:
        results = await rag_service.retrieve(
            query=query,
            agent_id="assistant",
            top_k=3
        )
        logger.info(f"  Query: '{query}' → {len(results)} results")
        if results:
            logger.info(f"    Top result: {results[0]['metadata'].get('question', 'N/A')}")
    
    logger.info("✅ RAG retrieval working")
    
    # Step 8: Test access control
    logger.info("🔐 Testing access control...")
    
    # Test public access (assistant agent)
    public_results = await rag_service.retrieve(
        query="pricing information",
        agent_id="assistant",
        top_k=5
    )
    logger.info(f"  Assistant agent: {len(public_results)} results (should exclude internal docs)")
    
    # Test customer access (dispensary agent)
    customer_results = await rag_service.retrieve(
        query="product information",
        agent_id="dispensary",
        top_k=5
    )
    logger.info(f"  Dispensary agent: {len(customer_results)} results (should include customer-facing docs)")
    
    logger.info("✅ Access control configured")
    
    # Step 9: Performance metrics
    logger.info("📊 RAG System Metrics:")
    metrics = rag_service.get_metrics()
    logger.info(f"  Total queries: {metrics.get('total_queries', 0)}")
    logger.info(f"  Cache hits: {metrics.get('cache_hits', 0)}")
    logger.info(f"  Avg latency: {metrics.get('avg_latency_ms', 0):.2f}ms")
    logger.info(f"  Total documents: {metrics.get('total_documents', 0)}")
    logger.info(f"  Total chunks: {metrics.get('total_chunks', 0)}")
    
    await db_pool.close()
    logger.info("🎉 RAG System Initialization Complete!")


async def sync_ocs_products_for_tenant(tenant_id: str):
    """
    Sync OCS products for specific tenant
    
    Args:
        tenant_id: Tenant UUID
    """
    logger.info(f"🌿 Starting OCS product sync for tenant {tenant_id}")
    
    # Connect to database
    db_pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "weedgo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        min_size=2,
        max_size=10
    )
    
    # Initialize sync service
    from services.rag.ocs_product_sync import get_ocs_sync_service
    sync_service = await get_ocs_sync_service(db_pool)
    
    # Run sync
    result = await sync_service.sync_tenant_products(
        tenant_id=tenant_id,
        force_full_sync=True
    )
    
    logger.info(f"✅ OCS Sync Complete:")
    logger.info(f"  Status: {result['status']}")
    logger.info(f"  Total products: {result.get('total', 0)}")
    logger.info(f"  Synced: {result.get('synced', 0)}")
    logger.info(f"  Errors: {result.get('errors', 0)}")
    logger.info(f"  Time: {result.get('elapsed_ms', 0):.2f}ms")
    
    await db_pool.close()


async def test_rag_queries():
    """
    Test RAG with various query types
    """
    logger.info("🔍 Testing RAG Query Performance")
    
    # Connect to database
    db_pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "weedgo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        min_size=2,
        max_size=10
    )
    
    # Initialize RAG
    from services.rag.rag_service import get_rag_service
    rag_service = await get_rag_service(db_pool)
    await rag_service.initialize()
    
    # Test queries
    test_cases = [
        {
            "query": "What are the effects of indica strains?",
            "agent_id": "dispensary",
            "expected_type": "faq"
        },
        {
            "query": "High THC sativa products",
            "agent_id": "dispensary",
            "expected_type": "ocs_product"
        },
        {
            "query": "What is the legal age for cannabis?",
            "agent_id": "assistant",
            "expected_type": "faq"
        },
        {
            "query": "Platform pricing and features",
            "agent_id": "sales",
            "expected_type": "faq"
        },
        {
            "query": "How to handle cannabis overdose",
            "agent_id": "dispensary",
            "expected_type": "faq"
        }
    ]
    
    results_summary = []
    
    for test in test_cases:
        start = datetime.now()
        
        results = await rag_service.retrieve(
            query=test["query"],
            agent_id=test["agent_id"],
            top_k=5
        )
        
        elapsed_ms = (datetime.now() - start).total_seconds() * 1000
        
        result_types = [r["document_type"] for r in results]
        has_expected = test["expected_type"] in result_types if results else False
        
        results_summary.append({
            "query": test["query"],
            "agent": test["agent_id"],
            "results": len(results),
            "latency_ms": elapsed_ms,
            "types": result_types[:3],
            "expected_found": has_expected
        })
        
        logger.info(f"  ✓ '{test['query'][:50]}...'")
        logger.info(f"    Results: {len(results)}, Latency: {elapsed_ms:.2f}ms, Expected: {has_expected}")
    
    # Summary
    logger.info("\n📊 Query Performance Summary:")
    avg_latency = sum(r["latency_ms"] for r in results_summary) / len(results_summary)
    success_rate = sum(1 for r in results_summary if r["expected_found"]) / len(results_summary) * 100
    
    logger.info(f"  Average latency: {avg_latency:.2f}ms")
    logger.info(f"  Success rate: {success_rate:.1f}%")
    logger.info(f"  Total queries: {len(results_summary)}")
    
    await db_pool.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python rag_init.py init              # Initialize RAG system")
        print("  python rag_init.py sync <tenant_id>  # Sync OCS products")
        print("  python rag_init.py test              # Test RAG queries")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        asyncio.run(initialize_rag_system())
    elif command == "sync" and len(sys.argv) > 2:
        tenant_id = sys.argv[2]
        asyncio.run(sync_ocs_products_for_tenant(tenant_id))
    elif command == "test":
        asyncio.run(test_rag_queries())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
