"""
Knowledge Retrieval System (RAG) for AGI
Implements document processing, embedding, and retrieval-augmented generation
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document in the knowledge base"""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any]
    created_at: datetime
    chunk_ids: List[str] = None


@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None


class EmbeddingModel:
    """
    Handles text embedding generation
    Uses sentence transformers for now, can be extended to use OpenAI/other APIs
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model"""
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Default for MiniLM

    async def initialize(self):
        """Load the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model {self.model_name} with dimension {self.dimension}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using simple hash embedding")
            self.model = None

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.model:
            # Use sentence transformer
            embedding = self.model.encode(text)
            return embedding.tolist()
        else:
            # Fallback: Simple hash-based embedding
            return self._simple_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.model:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        else:
            return [self._simple_embedding(text) for text in texts]

    def _simple_embedding(self, text: str) -> List[float]:
        """Create a simple deterministic embedding from text hash"""
        # Hash the text
        hash_obj = hashlib.sha384(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float vector
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            # Convert 4 bytes to float between -1 and 1
            value = int.from_bytes(hash_bytes[i:i+4], 'big')
            normalized = (value / (2**32 - 1)) * 2 - 1
            embedding.append(normalized)

        # Pad or truncate to dimension
        if len(embedding) < self.dimension:
            embedding.extend([0.0] * (self.dimension - len(embedding)))
        else:
            embedding = embedding[:self.dimension]

        return embedding


class VectorStore:
    """
    Manages vector storage and similarity search
    Uses PostgreSQL with JSONB for simplicity (avoiding pgvector dependency)
    """

    def __init__(self):
        """Initialize vector store"""
        self.db_manager = None
        self.config = get_config()

    async def initialize(self):
        """Initialize database connection"""
        self.db_manager = await get_db_manager()

    async def store_embedding(
        self,
        chunk_id: str,
        embedding: List[float],
        metadata: Dict[str, Any] = None
    ):
        """Store embedding in database"""
        query = """
        INSERT INTO agi.document_embeddings (chunk_id, embedding, metadata)
        VALUES ($1, $2, $3)
        ON CONFLICT (chunk_id) DO UPDATE
        SET embedding = $2, metadata = $3, updated_at = NOW()
        """

        await self.db_manager.execute(
            query,
            chunk_id,
            json.dumps(embedding),
            json.dumps(metadata or {})
        )

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar embeddings
        Returns list of (chunk_id, similarity_score, metadata)
        """
        # Get all embeddings from database
        query = """
        SELECT chunk_id, embedding, metadata
        FROM agi.document_embeddings
        """

        results = await self.db_manager.fetch(query)

        # Calculate similarities
        query_vec = np.array(query_embedding)
        similarities = []

        for row in results:
            chunk_id = row['chunk_id']
            embedding = json.loads(row['embedding'])
            metadata = json.loads(row['metadata'])

            # Cosine similarity
            doc_vec = np.array(embedding)
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8
            )

            if similarity >= threshold:
                similarities.append((chunk_id, float(similarity), metadata))

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    async def delete_embeddings(self, document_id: str):
        """Delete all embeddings for a document"""
        query = """
        DELETE FROM agi.document_embeddings
        WHERE metadata->>'document_id' = $1
        """
        await self.db_manager.execute(query, document_id)


class RAGSystem:
    """
    Main RAG (Retrieval-Augmented Generation) system
    Handles document processing, retrieval, and augmented generation
    """

    def __init__(self):
        """Initialize RAG system"""
        self.config = get_config()
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        self.db_manager = None
        self.chunk_size = 500  # Characters per chunk
        self.chunk_overlap = 50  # Overlap between chunks

    async def initialize(self):
        """Initialize all components"""
        await self.embedding_model.initialize()
        await self.vector_store.initialize()
        self.db_manager = await get_db_manager()

        # Create tables if needed
        await self._create_tables()

        logger.info("RAG system initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS agi.documents (
                id VARCHAR(255) PRIMARY KEY,
                title VARCHAR(500),
                content TEXT,
                source VARCHAR(500),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi.document_chunks (
                id VARCHAR(255) PRIMARY KEY,
                document_id VARCHAR(255) REFERENCES agi.documents(id) ON DELETE CASCADE,
                content TEXT,
                chunk_index INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi.document_embeddings (
                chunk_id VARCHAR(255) PRIMARY KEY,
                embedding JSONB,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id
            ON agi.document_chunks(document_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_embeddings_metadata
            ON agi.document_embeddings USING GIN (metadata)
            """
        ]

        for query in queries:
            await self.db_manager.execute(query)

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap
        """
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        # Add overlap
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0 and len(chunks[i-1]) > self.chunk_overlap:
                # Add end of previous chunk to beginning
                overlap = chunks[i-1][-self.chunk_overlap:]
                chunk = overlap + " " + chunk
            overlapped_chunks.append(chunk)

        return overlapped_chunks

    async def index_document(
        self,
        title: str,
        content: str,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> Document:
        """
        Index a document - chunk it, embed chunks, and store
        """
        # Generate document ID
        doc_id = hashlib.sha256(f"{title}_{source}_{datetime.now()}".encode()).hexdigest()[:16]

        # Store document
        doc_query = """
        INSERT INTO agi.documents (id, title, content, source, metadata)
        VALUES ($1, $2, $3, $4, $5)
        """

        await self.db_manager.execute(
            doc_query,
            doc_id,
            title,
            content,
            source,
            json.dumps(metadata or {})
        )

        # Chunk the document
        chunks = self._chunk_text(content)
        chunk_ids = []

        for i, chunk_text in enumerate(chunks):
            # Generate chunk ID
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)

            # Store chunk
            chunk_query = """
            INSERT INTO agi.document_chunks (id, document_id, content, chunk_index, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """

            chunk_metadata = {
                "document_id": doc_id,
                "document_title": title,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }

            await self.db_manager.execute(
                chunk_query,
                chunk_id,
                doc_id,
                chunk_text,
                i,
                json.dumps(chunk_metadata)
            )

            # Generate and store embedding
            embedding = await self.embedding_model.embed_text(chunk_text)
            await self.vector_store.store_embedding(
                chunk_id,
                embedding,
                chunk_metadata
            )

        logger.info(f"Indexed document {doc_id} with {len(chunks)} chunks")

        return Document(
            id=doc_id,
            title=title,
            content=content,
            source=source,
            metadata=metadata or {},
            created_at=datetime.now(),
            chunk_ids=chunk_ids
        )

    async def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks
        """
        # Generate query embedding
        query_embedding = await self.embedding_model.embed_text(query)

        # Search similar chunks
        similar_chunks = await self.vector_store.search_similar(
            query_embedding,
            limit=limit,
            threshold=threshold
        )

        # Fetch chunk contents
        results = []
        for chunk_id, similarity, metadata in similar_chunks:
            chunk_query = """
            SELECT c.content, c.chunk_index, d.title, d.source
            FROM agi.document_chunks c
            JOIN agi.documents d ON c.document_id = d.id
            WHERE c.id = $1
            """

            chunk_data = await self.db_manager.fetchrow(chunk_query, chunk_id)

            if chunk_data:
                results.append({
                    "chunk_id": chunk_id,
                    "content": chunk_data['content'],
                    "document_title": chunk_data['title'],
                    "document_source": chunk_data['source'],
                    "chunk_index": chunk_data['chunk_index'],
                    "similarity": similarity,
                    "metadata": metadata
                })

        return results

    async def generate_augmented_response(
        self,
        query: str,
        context_limit: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a response augmented with retrieved context
        """
        # Search for relevant context
        relevant_chunks = await self.search(
            query,
            limit=context_limit,
            threshold=0.6
        )

        # Build context from relevant chunks
        context_parts = []
        sources = set()

        for chunk in relevant_chunks:
            context_parts.append(chunk['content'])
            sources.add(chunk['document_title'])

        context = "\n\n".join(context_parts) if context_parts else ""

        # Create augmented prompt
        augmented_prompt = self._create_augmented_prompt(query, context)

        return {
            "query": query,
            "context": context,
            "sources": list(sources),
            "relevant_chunks": relevant_chunks,
            "augmented_prompt": augmented_prompt
        }

    def _create_augmented_prompt(self, query: str, context: str) -> str:
        """Create prompt with retrieved context"""
        if context:
            return f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer based on the context provided. If the context doesn't contain relevant information, say so."""
        else:
            return query

    async def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all indexed documents"""
        query = """
        SELECT id, title, source, metadata, created_at
        FROM agi.documents
        ORDER BY created_at DESC
        LIMIT $1
        """

        results = await self.db_manager.fetch(query, limit)

        documents = []
        for row in results:
            documents.append({
                "id": row['id'],
                "title": row['title'],
                "source": row['source'],
                "metadata": json.loads(row['metadata']),
                "created_at": row['created_at'].isoformat()
            })

        return documents

    async def delete_document(self, document_id: str):
        """Delete a document and all its chunks/embeddings"""
        # Delete embeddings
        await self.vector_store.delete_embeddings(document_id)

        # Delete document (chunks will cascade)
        query = "DELETE FROM agi.documents WHERE id = $1"
        await self.db_manager.execute(query, document_id)

        logger.info(f"Deleted document {document_id}")

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document"""
        query = """
        SELECT id, title, content, source, metadata, created_at
        FROM agi.documents
        WHERE id = $1
        """

        row = await self.db_manager.fetchrow(query, document_id)

        if row:
            return {
                "id": row['id'],
                "title": row['title'],
                "content": row['content'],
                "source": row['source'],
                "metadata": json.loads(row['metadata']),
                "created_at": row['created_at'].isoformat()
            }

        return None


# Singleton instance
_rag_system: Optional[RAGSystem] = None

async def get_rag_system() -> RAGSystem:
    """Get singleton RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
        await _rag_system.initialize()
    return _rag_system