#!/bin/bash
# RAG System Quick Setup Script
# Run this to initialize the complete RAG system

set -e  # Exit on error

echo "🚀 WeedGo RAG System - Quick Setup"
echo "=================================="
echo ""

# Change to Backend directory
cd "$(dirname "$0")/../Backend"

# Step 1: Check PostgreSQL
echo "📊 Step 1: Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL CLI found"
else
    echo "❌ PostgreSQL CLI (psql) not found. Please install PostgreSQL first."
    exit 1
fi

# Step 2: Check Python dependencies
echo ""
echo "📦 Step 2: Checking Python dependencies..."
python3 -c "import sentence_transformers" 2>/dev/null && echo "✅ sentence-transformers installed" || echo "⚠️  sentence-transformers not found"
python3 -c "import faiss" 2>/dev/null && echo "✅ faiss-cpu installed" || echo "⚠️  faiss-cpu not found"
python3 -c "import pgvector" 2>/dev/null && echo "✅ pgvector installed" || echo "⚠️  pgvector not found"
python3 -c "import nltk" 2>/dev/null && echo "✅ nltk installed" || echo "⚠️  nltk not found"
python3 -c "import spacy" 2>/dev/null && echo "✅ spacy installed" || echo "⚠️  spacy not found"

# Step 3: Run database migration (optional - prompt user)
echo ""
echo "📊 Step 3: Database Migration"
read -p "Do you want to run the database migration now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running migration..."
    read -p "Enter database name (default: weedgo): " DB_NAME
    DB_NAME=${DB_NAME:-weedgo}
    
    read -p "Enter database user (default: postgres): " DB_USER
    DB_USER=${DB_USER:-postgres}
    
    echo "Executing migration..."
    psql -U "$DB_USER" -d "$DB_NAME" -f migrations/create_rag_schema.sql
    
    if [ $? -eq 0 ]; then
        echo "✅ Database migration completed successfully"
    else
        echo "❌ Database migration failed"
        exit 1
    fi
else
    echo "⏭️  Skipping database migration"
    echo "   Run manually: psql -U postgres -d weedgo -f migrations/create_rag_schema.sql"
fi

# Step 4: Initialize RAG system
echo ""
echo "🧠 Step 4: Initialize RAG System"
read -p "Do you want to initialize the RAG system now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Initializing RAG system..."
    python3 scripts/rag_init.py init
    
    if [ $? -eq 0 ]; then
        echo "✅ RAG system initialized successfully"
    else
        echo "❌ RAG initialization failed"
        exit 1
    fi
else
    echo "⏭️  Skipping RAG initialization"
    echo "   Run manually: python3 scripts/rag_init.py init"
fi

# Step 5: Ingest FAQs (optional)
echo ""
echo "📚 Step 5: Ingest FAQ Knowledge Base"
read -p "Do you want to ingest the FAQ knowledge base now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Ingesting FAQs..."
    python3 -c "
import asyncio
import os
os.environ['DB_HOST'] = os.getenv('DB_HOST', 'localhost')
os.environ['DB_NAME'] = os.getenv('DB_NAME', 'weedgo')
os.environ['DB_USER'] = os.getenv('DB_USER', 'postgres')
os.environ['DB_PASSWORD'] = os.getenv('DB_PASSWORD', '')

async def main():
    import asyncpg
    from services.rag.faq_ingestion import get_faq_ingestion_service
    
    pool = await asyncpg.create_pool(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    
    service = await get_faq_ingestion_service(pool)
    faq_dir = 'services/rag/knowledge_base'
    
    if os.path.exists(faq_dir):
        results = await service.ingest_all_faqs(faq_dir, access_level='public')
        total = sum(r.get('total_sections', 0) for r in results)
        ingested = sum(r.get('ingested', 0) for r in results)
        print(f'✅ Ingested {ingested}/{total} FAQ sections from {len(results)} files')
    else:
        print(f'❌ FAQ directory not found: {faq_dir}')
    
    await pool.close()

asyncio.run(main())
"
    
    if [ $? -eq 0 ]; then
        echo "✅ FAQs ingested successfully"
    else
        echo "❌ FAQ ingestion failed"
    fi
else
    echo "⏭️  Skipping FAQ ingestion"
    echo "   Run manually: python3 scripts/rag_init.py init (includes FAQ ingestion)"
fi

# Step 6: Summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo "  1. Run OCS product sync: python3 scripts/rag_init.py sync <tenant-uuid>"
echo "  2. Test RAG queries: python3 scripts/rag_init.py test"
echo "  3. Check logs: tail -f logs/rag_service.log"
echo ""
echo "📚 Documentation:"
echo "  - Setup Guide: ../RAG_SYSTEM_GUIDE.md"
echo "  - Implementation Summary: ../RAG_IMPLEMENTATION_SUMMARY.md"
echo ""
echo "✅ Your RAG system is ready to use!"
