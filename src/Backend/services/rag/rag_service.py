"""
RAG Service - Retrieval Augmented Generation
Hybrid PostgreSQL (pgvector) + FAISS implementation
Multilingual support with tenant/store partitioning
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import asyncpg
import faiss
import pickle
from pathlib import Path
import hashlib
import json

from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    Hybrid RAG with PostgreSQL + FAISS
    - PostgreSQL: Persistent storage with metadata filtering
    - FAISS: Fast in-memory vector search
    - Real-time updates with smart caching
    """
    
    def __init__(
        self,
        db_pool: asyncpg.Pool,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
        faiss_index_path: str = "models/rag/faiss_index",
        cache_ttl: int = 3600  # 1 hour cache
    ):
        """
        Initialize RAG service
        
        Args:
            db_pool: PostgreSQL connection pool
            embedding_model: Multilingual model for all languages
            faiss_index_path: Path to store FAISS index
            cache_ttl: Cache time-to-live in seconds
        """
        self.db_pool = db_pool
        self.cache_ttl = cache_ttl
        
        # Initialize embedding service
        self.embedding_service = get_embedding_service(
            model_name=embedding_model,
            device="cpu"
        )
        self.embedding_dim = self.embedding_service.embedding_dim
        
        # FAISS index setup
        self.faiss_index_path = Path(faiss_index_path)
        self.faiss_index_path.mkdir(parents=True, exist_ok=True)
        self.faiss_index = None
        self.chunk_id_mapping = {}  # Maps FAISS index position to chunk_id
        self.reverse_mapping = {}  # Maps chunk_id to FAISS index position
        
        # Cache for frequently accessed chunks
        self.chunk_cache = {}  # chunk_id -> chunk_data
        self.query_cache = {}  # query_hash -> results
        
        # Metrics
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "faiss_searches": 0,
            "postgres_queries": 0,
            "average_latency_ms": 0
        }
        
        logger.info(f"✅ RAG Service initialized")
        logger.info(f"   Embedding model: {embedding_model}")
        logger.info(f"   Embedding dimension: {self.embedding_dim}")
    
    async def initialize(self):
        """Initialize FAISS index from PostgreSQL"""
        logger.info("Initializing RAG service...")
        
        # Load FAISS index if exists
        await self._load_faiss_index()
        
        # If no index, build from PostgreSQL
        if self.faiss_index is None:
            await self._build_faiss_index()
        
        logger.info(f"✅ RAG Service ready with {len(self.chunk_id_mapping)} chunks")
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        tenant_id: Optional[str] = None,
        store_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        rerank: bool = True,
        final_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for query
        
        Args:
            query: User query
            top_k: Initial retrieval count (before re-ranking)
            tenant_id: Filter by tenant (for multi-tenancy)
            store_id: Filter by store (for store-specific info)
            agent_id: Agent making request (for access control)
            document_types: Filter by document types
            rerank: Whether to re-rank results
            final_k: Final number of results after re-ranking
            
        Returns:
            List of relevant chunks with metadata
        """
        import time
        start_time = time.time()
        self.metrics["total_queries"] += 1
        
        # Check query cache
        cache_key = self._get_cache_key(
            query, top_k, tenant_id, store_id, document_types
        )
        
        if cache_key in self.query_cache:
            cache_entry = self.query_cache[cache_key]
            if (datetime.now(timezone.utc) - cache_entry["timestamp"]).seconds < self.cache_ttl:
                self.metrics["cache_hits"] += 1
                logger.info(f"🎯 Cache hit for query: {query[:50]}...")
                return cache_entry["results"]
        
        # Generate query embedding
        query_embedding = await self.embedding_service.encode_async(query)
        
        # Step 1: Fast FAISS search (top_k candidates)
        faiss_results = await self._faiss_search(query_embedding, top_k * 2)
        self.metrics["faiss_searches"] += 1
        
        # Step 2: Filter by metadata in PostgreSQL
        filtered_chunks = await self._filter_chunks(
            faiss_results,
            tenant_id=tenant_id,
            store_id=store_id,
            agent_id=agent_id,
            document_types=document_types,
            limit=top_k
        )
        self.metrics["postgres_queries"] += 1
        
        # Step 3: Re-rank if requested (cross-encoder would go here)
        if rerank and len(filtered_chunks) > final_k:
            filtered_chunks = self._rerank_results(
                query, filtered_chunks, final_k
            )
        else:
            filtered_chunks = filtered_chunks[:final_k]
        
        # Update metrics
        latency_ms = (time.time() - start_time) * 1000
        self._update_average_latency(latency_ms)
        
        # Cache results
        self.query_cache[cache_key] = {
            "results": filtered_chunks,
            "timestamp": datetime.now(timezone.utc)
        }
        
        logger.info(f"✅ Retrieved {len(filtered_chunks)} chunks in {latency_ms:.2f}ms")
        
        return filtered_chunks
    
    async def _faiss_search(
        self,
        query_embedding: np.ndarray,
        k: int
    ) -> List[Tuple[str, float]]:
        """
        Search FAISS index for similar vectors
        
        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        if self.faiss_index is None or len(self.chunk_id_mapping) == 0:
            return []
        
        # Reshape for FAISS
        query_vector = query_embedding.reshape(1, -1).astype('float32')
        
        # Search
        k = min(k, len(self.chunk_id_mapping))
        distances, indices = self.faiss_index.search(query_vector, k)
        
        # Convert to chunk_ids with scores
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self.chunk_id_mapping:
                chunk_id = self.chunk_id_mapping[idx]
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + dist)
                results.append((chunk_id, float(similarity)))
        
        return results
    
    async def _filter_chunks(
        self,
        faiss_results: List[Tuple[str, float]],
        tenant_id: Optional[str],
        store_id: Optional[str],
        agent_id: Optional[str],
        document_types: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Filter and enrich chunks from PostgreSQL
        Apply access control and metadata filtering
        """
        if not faiss_results:
            return []
        
        chunk_ids = [chunk_id for chunk_id, _ in faiss_results]
        scores = {chunk_id: score for chunk_id, score in faiss_results}
        
        # Build query with filters
        query = """
            SELECT 
                c.chunk_id,
                c.document_id,
                c.content,
                c.chunk_index,
                c.metadata,
                d.title,
                d.document_type,
                d.tenant_id,
                d.store_id,
                d.source_table,
                d.access_level
            FROM knowledge_chunks c
            JOIN knowledge_documents d ON c.document_id = d.document_id
            WHERE c.chunk_id = ANY($1)
        """
        
        params = [chunk_ids]
        param_idx = 2
        
        # Add filters
        if tenant_id:
            query += f" AND (d.tenant_id = ${param_idx} OR d.tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if store_id:
            query += f" AND (d.store_id = ${param_idx} OR d.store_id IS NULL)"
            params.append(store_id)
            param_idx += 1
        
        if document_types:
            query += f" AND d.document_type = ANY(${param_idx})"
            params.append(document_types)
            param_idx += 1
        
        # Access control by agent
        if agent_id:
            access_filter = self._get_access_filter(agent_id)
            if access_filter:
                query += f" AND {access_filter}"
        
        query += f" ORDER BY array_position($1, c.chunk_id) LIMIT {limit}"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        # Format results
        results = []
        for row in rows:
            chunk_id = row['chunk_id']
            results.append({
                "chunk_id": chunk_id,
                "document_id": row['document_id'],
                "content": row['content'],
                "title": row['title'],
                "document_type": row['document_type'],
                "tenant_id": row['tenant_id'],
                "store_id": row['store_id'],
                "source_table": row['source_table'],
                "chunk_index": row['chunk_index'],
                "metadata": row['metadata'],
                "similarity_score": scores.get(chunk_id, 0.0),
                "access_level": row['access_level']
            })
        
        return results
    
    def _get_access_filter(self, agent_id: str) -> Optional[str]:
        """
        Get SQL filter for agent access control
        
        Dispensary agents: No sensitive info (pricing, internal docs)
        Sales agents: Platform info only, no customer-specific data
        Assistant: General FAQs only
        """
        access_rules = {
            "dispensary": "d.access_level IN ('public', 'customer')",
            "sales": "d.access_level IN ('public', 'platform')",
            "assistant": "d.access_level = 'public'",
            # Admin agents get everything
            "admin": None
        }
        
        return access_rules.get(agent_id, "d.access_level = 'public'")
    
    def _rerank_results(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        final_k: int
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results using simple scoring
        In production, use cross-encoder for better quality
        """
        # For now, use weighted combination of:
        # - FAISS similarity score (70%)
        # - Recency (20%)
        # - Document type priority (10%)
        
        type_priority = {
            "ocs_product": 1.0,  # Highest priority - source of truth
            "faq": 0.9,
            "compliance": 0.85,
            "platform_docs": 0.8,
            "store_info": 0.75
        }
        
        for chunk in chunks:
            base_score = chunk["similarity_score"]
            type_score = type_priority.get(chunk["document_type"], 0.5)
            
            # Weighted final score
            chunk["final_score"] = (
                base_score * 0.7 +
                type_score * 0.3
            )
        
        # Sort by final score
        chunks.sort(key=lambda x: x["final_score"], reverse=True)
        
        return chunks[:final_k]
    
    async def add_document(
        self,
        content: str,
        document_type: str,
        title: str,
        tenant_id: Optional[str] = None,
        store_id: Optional[str] = None,
        source_table: Optional[str] = None,
        metadata: Optional[Dict] = None,
        access_level: str = "public"
    ) -> str:
        """
        Add new document to knowledge base
        Automatically chunks and indexes
        
        Returns:
            document_id
        """
        from .document_chunker import DocumentChunker
        
        chunker = DocumentChunker()
        chunks = chunker.chunk_document(content, metadata=metadata)
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Insert document
                document_id = await conn.fetchval("""
                    INSERT INTO knowledge_documents (
                        title, document_type, tenant_id, store_id,
                        source_table, access_level, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING document_id
                """, title, document_type, tenant_id, store_id, source_table,
                    access_level, json.dumps(metadata or {}), datetime.now(timezone.utc))
                
                # Insert chunks with embeddings
                for idx, chunk in enumerate(chunks):
                    embedding = await self.embedding_service.encode_async(chunk["text"])
                    
                    await conn.execute("""
                        INSERT INTO knowledge_chunks (
                            document_id, content, chunk_index, 
                            embedding, metadata, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """, document_id, chunk["text"], idx,
                        embedding.tolist(), json.dumps(chunk.get("metadata", {})),
                        datetime.now(timezone.utc))
        
        # Rebuild FAISS index
        await self._rebuild_faiss_index()
        
        logger.info(f"✅ Added document: {title} ({len(chunks)} chunks)")
        
        return document_id
    
    async def _build_faiss_index(self):
        """Build FAISS index from PostgreSQL embeddings"""
        logger.info("Building FAISS index from PostgreSQL...")
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT chunk_id, embedding
                FROM knowledge_chunks
                ORDER BY chunk_id
            """)
        
        if not rows:
            logger.warning("No chunks found in database")
            self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
            return
        
        # Create FAISS index
        embeddings = []
        chunk_ids = []
        
        for row in rows:
            chunk_ids.append(row['chunk_id'])
            embeddings.append(np.array(row['embedding'], dtype='float32'))
        
        embeddings_array = np.vstack(embeddings)
        
        # Initialize FAISS index (IVF for faster search)
        quantizer = faiss.IndexFlatL2(self.embedding_dim)
        nlist = min(100, len(embeddings) // 10)  # Number of clusters
        self.faiss_index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, max(nlist, 1))
        
        # Train and add vectors
        if len(embeddings) >= nlist:
            self.faiss_index.train(embeddings_array)
        self.faiss_index.add(embeddings_array)
        
        # Build mappings
        self.chunk_id_mapping = {i: chunk_id for i, chunk_id in enumerate(chunk_ids)}
        self.reverse_mapping = {chunk_id: i for i, chunk_id in enumerate(chunk_ids)}
        
        # Save index
        await self._save_faiss_index()
        
        logger.info(f"✅ FAISS index built with {len(chunk_ids)} chunks")
    
    async def _rebuild_faiss_index(self):
        """Rebuild FAISS index after updates"""
        await self._build_faiss_index()
        self.query_cache.clear()  # Clear cache after rebuild
    
    async def _save_faiss_index(self):
        """Save FAISS index and mappings to disk"""
        if self.faiss_index is None:
            return
        
        index_file = self.faiss_index_path / "rag.index"
        mapping_file = self.faiss_index_path / "mappings.pkl"
        
        # Save FAISS index
        faiss.write_index(self.faiss_index, str(index_file))
        
        # Save mappings
        with open(mapping_file, 'wb') as f:
            pickle.dump({
                'chunk_id_mapping': self.chunk_id_mapping,
                'reverse_mapping': self.reverse_mapping
            }, f)
        
        logger.info(f"💾 Saved FAISS index to {index_file}")
    
    async def _load_faiss_index(self):
        """Load FAISS index from disk"""
        index_file = self.faiss_index_path / "rag.index"
        mapping_file = self.faiss_index_path / "mappings.pkl"
        
        if not index_file.exists() or not mapping_file.exists():
            logger.info("No existing FAISS index found")
            return
        
        try:
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(index_file))
            
            # Load mappings
            with open(mapping_file, 'rb') as f:
                data = pickle.load(f)
                self.chunk_id_mapping = data['chunk_id_mapping']
                self.reverse_mapping = data['reverse_mapping']
            
            logger.info(f"✅ Loaded FAISS index with {len(self.chunk_id_mapping)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self.faiss_index = None
    
    def _get_cache_key(
        self,
        query: str,
        top_k: int,
        tenant_id: Optional[str],
        store_id: Optional[str],
        document_types: Optional[List[str]]
    ) -> str:
        """Generate cache key for query"""
        key_parts = [
            query,
            str(top_k),
            tenant_id or "",
            store_id or "",
            ",".join(sorted(document_types or []))
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_average_latency(self, latency_ms: float):
        """Update rolling average latency"""
        current_avg = self.metrics["average_latency_ms"]
        total_queries = self.metrics["total_queries"]
        
        self.metrics["average_latency_ms"] = (
            (current_avg * (total_queries - 1) + latency_ms) / total_queries
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_hit_rate = 0
        if self.metrics["total_queries"] > 0:
            cache_hit_rate = (
                self.metrics["cache_hits"] / self.metrics["total_queries"] * 100
            )
        
        return {
            **self.metrics,
            "cache_hit_rate_pct": round(cache_hit_rate, 2),
            "total_chunks": len(self.chunk_id_mapping),
            "cache_size": len(self.query_cache)
        }


# Singleton instance
_rag_service: Optional[RAGService] = None


async def get_rag_service(db_pool: asyncpg.Pool) -> RAGService:
    """Get singleton RAG service instance"""
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService(db_pool)
        await _rag_service.initialize()
    
    return _rag_service
