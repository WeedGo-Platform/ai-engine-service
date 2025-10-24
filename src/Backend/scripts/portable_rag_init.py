#!/usr/bin/env python3
"""
Portable RAG Initialization Script
No PostgreSQL required - uses SQLite + FAISS
"""

import asyncio
import sys
import os
from pathlib import Path

# Add Backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag.portable_rag_service import get_portable_rag_service
from services.rag.faq_ingestion import get_faq_ingestion_service


async def init_rag(data_dir: str = "data/rag"):
    """Initialize portable RAG system"""
    print("🚀 Initializing Portable RAG System")
    print("=" * 50)
    print(f"Data directory: {data_dir}")
    print()
    
    # Get RAG service
    print("📦 Loading RAG service...")
    rag_service = await get_portable_rag_service(data_dir=data_dir)
    print("✅ RAG service initialized")
    print(f"   Total chunks: {len(rag_service.chunk_id_mapping)}")
    print()
    
    return rag_service


async def ingest_faqs(rag_service, faq_dir: str = "services/rag/knowledge_base"):
    """Ingest FAQ documents"""
    print("📚 Ingesting FAQ Knowledge Base")
    print("=" * 50)
    
    faq_path = Path(faq_dir)
    if not faq_path.exists():
        print(f"❌ FAQ directory not found: {faq_dir}")
        return
    
    # Find all markdown files
    md_files = list(faq_path.glob("*.md"))
    if not md_files:
        print(f"❌ No markdown files found in {faq_dir}")
        return
    
    print(f"Found {len(md_files)} FAQ files")
    print()
    
    total_sections = 0
    for md_file in md_files:
        print(f"Processing: {md_file.name}")
        
        # Read file
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by Q&A sections (look for "Q:" or "**Q:")
        import re
        sections = re.split(r'\n(?=\*\*Q:|\nQ:)', content)
        sections = [s.strip() for s in sections if s.strip()]
        
        # Add each Q&A as a document
        for idx, section in enumerate(sections):
            if not section:
                continue
            
            # Extract question (first line)
            lines = section.split('\n', 1)
            title = lines[0].replace('**Q:', '').replace('Q:', '').strip()
            
            # Add to RAG
            try:
                result = await rag_service.add_document(
                    title=title[:200],  # Limit title length
                    content=section,
                    document_type="faq",
                    access_level="public",
                    language="en",
                    metadata={
                        "source_file": md_file.name,
                        "section_index": idx
                    },
                    chunk_size=512,
                    chunk_overlap=50
                )
                
                if result['success']:
                    total_sections += 1
                    print(f"  ✅ Added: {title[:50]}... ({result['chunk_count']} chunks)")
                else:
                    print(f"  ❌ Failed: {title[:50]}...")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print()
    
    print(f"✅ Ingested {total_sections} FAQ sections from {len(md_files)} files")
    print()


async def test_rag(rag_service):
    """Test RAG retrieval"""
    print("🧪 Testing RAG Retrieval")
    print("=" * 50)
    
    test_queries = [
        "What is THC?",
        "What's the difference between indica and sativa?",
        "What is the legal age for cannabis?",
        "How do I store cannabis products?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        results = await rag_service.retrieve(
            query=query,
            top_k=3,
            agent_id="dispensary",
            min_similarity=0.3
        )
        
        if results:
            print(f"✅ Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title'][:60]}... (similarity: {result['similarity']:.2f})")
        else:
            print("❌ No results found")
    
    print()
    
    # Show metrics
    metrics = rag_service.get_metrics()
    print("📊 Metrics:")
    print(f"  Total queries: {metrics['total_queries']}")
    print(f"  Cache hits: {metrics['cache_hits']}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1%}")
    print(f"  Total chunks: {metrics['total_chunks']}")
    print(f"  Avg latency: {metrics['average_latency_ms']:.2f}ms")
    print()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Portable RAG Initialization")
    parser.add_argument('command', choices=['init', 'test', 'ingest'], 
                       help='Command to run')
    parser.add_argument('--data-dir', default='data/rag',
                       help='Data directory (default: data/rag)')
    parser.add_argument('--faq-dir', default='services/rag/knowledge_base',
                       help='FAQ directory (default: services/rag/knowledge_base)')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        # Full initialization
        rag_service = await init_rag(args.data_dir)
        await ingest_faqs(rag_service, args.faq_dir)
        await test_rag(rag_service)
        print("🎉 RAG system ready!")
        
    elif args.command == 'test':
        # Test only
        rag_service = await init_rag(args.data_dir)
        await test_rag(rag_service)
        
    elif args.command == 'ingest':
        # Ingest FAQs only
        rag_service = await init_rag(args.data_dir)
        await ingest_faqs(rag_service, args.faq_dir)


if __name__ == "__main__":
    asyncio.run(main())
