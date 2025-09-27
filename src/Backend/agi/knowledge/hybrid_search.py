"""
Hybrid Search System for RAG
Combines semantic and keyword search for better retrieval
"""

import asyncio
import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import hashlib

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with metadata"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str  # semantic, keyword, or hybrid
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search"""
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    use_reranking: bool = True
    max_results: int = 10
    min_score_threshold: float = 0.3
    use_query_expansion: bool = True
    use_cross_encoder: bool = False


class HybridSearch:
    """
    Advanced hybrid search combining semantic and keyword search
    Features: query expansion, reranking, cross-encoder scoring
    """

    def __init__(self, config: Optional[HybridSearchConfig] = None):
        self.config = config or HybridSearchConfig()
        self.embedding_model = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.documents = []
        self.document_embeddings = None
        self.index_built = False

    async def initialize(self):
        """Initialize search components"""
        try:
            # Load embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 3),
                stop_words='english',
                use_idf=True,
                smooth_idf=True
            )

            logger.info("Hybrid search system initialized")

        except Exception as e:
            logger.error(f"Failed to initialize hybrid search: {e}")
            raise

    async def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Index documents for hybrid search

        Args:
            documents: List of documents with 'content' and 'metadata'

        Returns:
            Number of documents indexed
        """
        if not self.embedding_model:
            await self.initialize()

        try:
            # Store documents
            self.documents = documents
            contents = [doc.get('content', '') for doc in documents]

            # Create semantic embeddings
            logger.info(f"Creating embeddings for {len(contents)} documents")
            self.document_embeddings = self.embedding_model.encode(
                contents,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            # Create TF-IDF matrix
            logger.info("Building TF-IDF index")
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)

            # Store in database for persistence
            await self._persist_index()

            self.index_built = True
            logger.info(f"Indexed {len(documents)} documents successfully")

            return len(documents)

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of search results
        """
        if not self.index_built:
            logger.warning("Index not built, attempting to load from database")
            await self._load_index()

        # Expand query if enabled
        if self.config.use_query_expansion:
            expanded_query = await self._expand_query(query)
        else:
            expanded_query = query

        # Perform semantic search
        semantic_results = await self._semantic_search(expanded_query, top_k * 2)

        # Perform keyword search
        keyword_results = await self._keyword_search(expanded_query, top_k * 2)

        # Combine results
        combined_results = self._combine_results(
            semantic_results,
            keyword_results,
            self.config.semantic_weight,
            self.config.keyword_weight
        )

        # Apply filters if provided
        if filters:
            combined_results = self._apply_filters(combined_results, filters)

        # Rerank if enabled
        if self.config.use_reranking:
            combined_results = await self._rerank_results(combined_results, query)

        # Apply score threshold
        combined_results = [
            r for r in combined_results
            if r.score >= self.config.min_score_threshold
        ]

        # Return top k results
        return combined_results[:top_k]

    async def _semantic_search(
        self,
        query: str,
        top_k: int
    ) -> List[SearchResult]:
        """Perform semantic similarity search"""
        if not self.document_embeddings:
            return []

        try:
            # Encode query
            query_embedding = self.embedding_model.encode(
                [query],
                show_progress_bar=False,
                convert_to_numpy=True
            )[0]

            # Calculate cosine similarities
            similarities = cosine_similarity(
                [query_embedding],
                self.document_embeddings
            )[0]

            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # Create results
            results = []
            for idx in top_indices:
                if idx < len(self.documents):
                    results.append(SearchResult(
                        id=f"sem_{idx}",
                        content=self.documents[idx].get('content', ''),
                        score=float(similarities[idx]),
                        metadata=self.documents[idx].get('metadata', {}),
                        source='semantic',
                        chunk_id=self.documents[idx].get('chunk_id'),
                        document_id=self.documents[idx].get('document_id')
                    ))

            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        top_k: int
    ) -> List[SearchResult]:
        """Perform keyword-based search using TF-IDF"""
        if self.tfidf_matrix is None:
            return []

        try:
            # Transform query
            query_vec = self.tfidf_vectorizer.transform([query])

            # Calculate similarities
            similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # Create results
            results = []
            for idx in top_indices:
                if idx < len(self.documents) and similarities[idx] > 0:
                    results.append(SearchResult(
                        id=f"key_{idx}",
                        content=self.documents[idx].get('content', ''),
                        score=float(similarities[idx]),
                        metadata=self.documents[idx].get('metadata', {}),
                        source='keyword',
                        chunk_id=self.documents[idx].get('chunk_id'),
                        document_id=self.documents[idx].get('document_id')
                    ))

            # Boost exact matches
            results = self._boost_exact_matches(results, query)

            return results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _combine_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """Combine semantic and keyword search results"""
        combined = {}

        # Process semantic results
        for result in semantic_results:
            key = self._get_result_key(result)
            if key not in combined:
                combined[key] = result
                combined[key].score *= semantic_weight
            else:
                combined[key].score += result.score * semantic_weight

        # Process keyword results
        for result in keyword_results:
            key = self._get_result_key(result)
            if key not in combined:
                combined[key] = result
                combined[key].score *= keyword_weight
            else:
                combined[key].score += result.score * keyword_weight

        # Update source for hybrid results
        for key, result in combined.items():
            if key in [self._get_result_key(r) for r in semantic_results] and \
               key in [self._get_result_key(r) for r in keyword_results]:
                result.source = 'hybrid'

        # Sort by combined score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x.score,
            reverse=True
        )

        return sorted_results

    def _get_result_key(self, result: SearchResult) -> str:
        """Get unique key for a result"""
        # Use content hash as key to identify duplicates
        content_hash = hashlib.md5(result.content.encode()).hexdigest()
        return content_hash

    async def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms"""
        # Simple query expansion - can be enhanced with WordNet or language models
        expanded = query

        # Add common variations
        expansions = {
            "search": "find locate query retrieve",
            "delete": "remove erase clear",
            "create": "make build generate construct",
            "update": "modify change edit alter",
            "analyze": "examine investigate study inspect"
        }

        for term, synonyms in expansions.items():
            if term in query.lower():
                expanded += f" {synonyms}"

        return expanded

    async def _rerank_results(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Rerank results using advanced scoring"""
        if not results:
            return results

        # Calculate additional features for reranking
        for result in results:
            # Length normalization
            length_factor = 1.0 / (1.0 + np.log(1 + len(result.content.split())))

            # Query term coverage
            query_terms = set(query.lower().split())
            content_terms = set(result.content.lower().split())
            coverage = len(query_terms & content_terms) / max(len(query_terms), 1)

            # Recency boost (if timestamp available)
            recency_boost = 1.0
            if 'timestamp' in result.metadata:
                try:
                    timestamp = datetime.fromisoformat(result.metadata['timestamp'])
                    age_days = (datetime.utcnow() - timestamp).days
                    recency_boost = 1.0 / (1.0 + age_days / 30)  # Decay over 30 days
                except:
                    pass

            # Adjust score
            result.score *= (1.0 + coverage * 0.3 + recency_boost * 0.2) * length_factor

        # Sort by new scores
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def _boost_exact_matches(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Boost results with exact query matches"""
        query_lower = query.lower()

        for result in results:
            if query_lower in result.content.lower():
                # Boost score for exact matches
                result.score *= 1.5

                # Extra boost for title/beginning matches
                if result.content.lower().startswith(query_lower):
                    result.score *= 1.2

        return results

    def _apply_filters(
        self,
        results: List[SearchResult],
        filters: Dict[str, Any]
    ) -> List[SearchResult]:
        """Apply metadata filters to results"""
        filtered = []

        for result in results:
            match = True

            for key, value in filters.items():
                if key not in result.metadata:
                    match = False
                    break

                if isinstance(value, list):
                    if result.metadata[key] not in value:
                        match = False
                        break
                else:
                    if result.metadata[key] != value:
                        match = False
                        break

            if match:
                filtered.append(result)

        return filtered

    async def _persist_index(self):
        """Persist index to database"""
        try:
            db = await get_db_manager()

            # Store document embeddings
            for i, doc in enumerate(self.documents):
                if i < len(self.document_embeddings):
                    embedding = self.document_embeddings[i].tolist()

                    await db.execute(
                        """
                        INSERT INTO agi.document_embeddings
                        (id, document_id, chunk_id, embedding, content, metadata, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = $4,
                            content = $5,
                            metadata = $6,
                            created_at = $7
                        """,
                        f"emb_{i}_{datetime.utcnow().timestamp()}",
                        doc.get('document_id', ''),
                        doc.get('chunk_id', ''),
                        embedding,
                        doc.get('content', ''),
                        doc.get('metadata', {}),
                        datetime.utcnow()
                    )

            logger.info("Index persisted to database")

        except Exception as e:
            logger.error(f"Failed to persist index: {e}")

    async def _load_index(self):
        """Load index from database"""
        try:
            db = await get_db_manager()

            # Load embeddings
            rows = await db.fetch(
                """
                SELECT * FROM agi.document_embeddings
                ORDER BY created_at DESC
                LIMIT 1000
                """
            )

            if rows:
                self.documents = []
                embeddings = []

                for row in rows:
                    self.documents.append({
                        'content': row['content'],
                        'metadata': row['metadata'],
                        'document_id': row['document_id'],
                        'chunk_id': row['chunk_id']
                    })
                    embeddings.append(row['embedding'])

                self.document_embeddings = np.array(embeddings)

                # Rebuild TF-IDF
                contents = [doc['content'] for doc in self.documents]
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)

                self.index_built = True
                logger.info(f"Loaded {len(self.documents)} documents from database")

        except Exception as e:
            logger.error(f"Failed to load index: {e}")

    async def update_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a document in the index"""
        try:
            # Find document
            doc_index = None
            for i, doc in enumerate(self.documents):
                if doc.get('document_id') == document_id:
                    doc_index = i
                    break

            if doc_index is None:
                # Add as new document
                new_doc = {
                    'document_id': document_id,
                    'content': content,
                    'metadata': metadata or {}
                }
                self.documents.append(new_doc)

                # Update embeddings
                new_embedding = self.embedding_model.encode([content])[0]
                if self.document_embeddings is not None:
                    self.document_embeddings = np.vstack([
                        self.document_embeddings,
                        new_embedding
                    ])
                else:
                    self.document_embeddings = np.array([new_embedding])

            else:
                # Update existing document
                self.documents[doc_index]['content'] = content
                if metadata:
                    self.documents[doc_index]['metadata'] = metadata

                # Update embedding
                new_embedding = self.embedding_model.encode([content])[0]
                self.document_embeddings[doc_index] = new_embedding

            # Rebuild TF-IDF
            contents = [doc['content'] for doc in self.documents]
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)

            # Persist changes
            await self._persist_index()

            return True

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index"""
        try:
            # Find document
            doc_index = None
            for i, doc in enumerate(self.documents):
                if doc.get('document_id') == document_id:
                    doc_index = i
                    break

            if doc_index is None:
                return False

            # Remove from documents
            self.documents.pop(doc_index)

            # Remove from embeddings
            if self.document_embeddings is not None:
                self.document_embeddings = np.delete(
                    self.document_embeddings,
                    doc_index,
                    axis=0
                )

            # Rebuild TF-IDF
            if self.documents:
                contents = [doc['content'] for doc in self.documents]
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)
            else:
                self.tfidf_matrix = None

            # Remove from database
            db = await get_db_manager()
            await db.execute(
                "DELETE FROM agi.document_embeddings WHERE document_id = $1",
                document_id
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get search index statistics"""
        return {
            "total_documents": len(self.documents),
            "index_built": self.index_built,
            "embedding_dimensions": self.document_embeddings.shape[1] if self.document_embeddings is not None else 0,
            "tfidf_features": self.tfidf_matrix.shape[1] if self.tfidf_matrix is not None else 0,
            "config": {
                "semantic_weight": self.config.semantic_weight,
                "keyword_weight": self.config.keyword_weight,
                "use_reranking": self.config.use_reranking,
                "use_query_expansion": self.config.use_query_expansion
            }
        }


# Global hybrid search instance
_hybrid_search: Optional[HybridSearch] = None


async def get_hybrid_search() -> HybridSearch:
    """Get singleton hybrid search instance"""
    global _hybrid_search
    if _hybrid_search is None:
        _hybrid_search = HybridSearch()
        await _hybrid_search.initialize()
    return _hybrid_search