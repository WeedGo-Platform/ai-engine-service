"""
Semantic Cache for Offline Multilingual AI
Uses embeddings to find similar queries and cache responses
"""

import os
import json
import time
import pickle
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Single cache entry"""
    query: str
    response: str
    language: str
    embedding: List[float]
    timestamp: float
    hit_count: int = 0
    quality_score: float = 1.0
    metadata: Dict = None

class SemanticCache:
    """
    Semantic caching system for multilingual queries
    Uses embeddings to find similar queries regardless of exact wording
    """
    
    def __init__(
        self,
        cache_dir: str = "cache/semantic",
        embedding_model: str = "models/embeddings/multilingual-minilm",
        similarity_threshold: float = 0.92,
        max_cache_size: int = 10000,
        ttl_hours: int = 24
    ):
        """
        Initialize semantic cache
        
        Args:
            cache_dir: Directory for cache storage
            embedding_model: Path to embedding model
            similarity_threshold: Minimum similarity for cache hit
            max_cache_size: Maximum number of cached entries
            ttl_hours: Time-to-live for cache entries
        """
        
        self.cache_dir = cache_dir
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_hours * 3600
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load embedding model
        self._load_embedding_model(embedding_model)
        
        # Initialize ChromaDB for vector storage
        self._initialize_vector_db()
        
        # Metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_similarity': 0,
            'total_time_saved': 0
        }
    
    def _load_embedding_model(self, model_path: str):
        """Load the multilingual embedding model"""
        
        try:
            if os.path.exists(model_path):
                logger.info(f"Loading embedding model from {model_path}")
                self.embedder = SentenceTransformer(model_path)
            else:
                # Fallback to downloading model
                logger.info("Downloading embedding model...")
                self.embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
                self.embedder.save(model_path)
            
            # Test embedding
            test_embedding = self.embedder.encode("test", convert_to_numpy=True)
            self.embedding_dim = len(test_embedding)
            logger.info(f"Embedding model loaded (dim={self.embedding_dim})")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _initialize_vector_db(self):
        """Initialize ChromaDB for vector similarity search"""
        
        try:
            # Configure ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=os.path.join(self.cache_dir, "chroma"),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collection for each language
            self.collections = {}
            for lang in ['en', 'es', 'fr', 'pt', 'zh', 'ar', 'mixed']:
                collection_name = f"cache_{lang}"
                try:
                    self.collections[lang] = self.chroma_client.get_collection(
                        name=collection_name
                    )
                except:
                    self.collections[lang] = self.chroma_client.create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
            
            logger.info("Vector database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector DB: {e}")
            # Fallback to in-memory cache
            self.collections = None
            self.memory_cache = {}
    
    def get(
        self,
        query: str,
        language: str,
        context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get cached response for similar query
        
        Args:
            query: User query
            language: Language code
            context: Optional context for better matching
            
        Returns:
            Cached response if found, None otherwise
        """
        
        self.metrics['total_queries'] += 1
        
        try:
            # Generate embedding for query
            query_embedding = self.embedder.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Search in appropriate collection
            collection = self.collections.get(language, self.collections.get('mixed'))
            
            if collection:
                # Search for similar queries
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=3,
                    include=['metadatas', 'documents', 'distances']
                )
                
                if results['ids'][0]:
                    # Check similarity threshold
                    best_distance = results['distances'][0][0]
                    similarity = 1 - best_distance  # Convert distance to similarity
                    
                    if similarity >= self.similarity_threshold:
                        # Check TTL
                        metadata = results['metadatas'][0][0]
                        timestamp = metadata.get('timestamp', 0)
                        
                        if time.time() - timestamp < self.ttl_seconds:
                            # Cache hit!
                            self.metrics['cache_hits'] += 1
                            self.metrics['avg_similarity'] = (
                                (self.metrics['avg_similarity'] * (self.metrics['cache_hits'] - 1) + similarity)
                                / self.metrics['cache_hits']
                            )
                            
                            # Update hit count
                            hit_count = metadata.get('hit_count', 0) + 1
                            collection.update(
                                ids=[results['ids'][0][0]],
                                metadatas=[{**metadata, 'hit_count': hit_count}]
                            )
                            
                            response = results['documents'][0][0]
                            
                            # Parse response if it's JSON
                            try:
                                response = json.loads(response)
                            except:
                                pass
                            
                            return {
                                'response': response,
                                'similarity': similarity,
                                'cache_hit': True,
                                'original_query': metadata.get('original_query', query)
                            }
            
            # Cache miss
            self.metrics['cache_misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
            return None
    
    def set(
        self,
        query: str,
        response: Any,
        language: str,
        quality_score: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Cache a query-response pair
        
        Args:
            query: User query
            response: Generated response
            language: Language code
            quality_score: Quality score of response
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        
        try:
            # Don't cache low-quality responses
            if quality_score < 0.7:
                return False
            
            # Generate embedding
            query_embedding = self.embedder.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Prepare response for storage
            if isinstance(response, dict):
                response_str = json.dumps(response)
            else:
                response_str = str(response)
            
            # Prepare metadata
            cache_metadata = {
                'timestamp': time.time(),
                'language': language,
                'quality_score': quality_score,
                'hit_count': 0,
                'original_query': query,
                **(metadata or {})
            }
            
            # Get collection
            collection = self.collections.get(language, self.collections.get('mixed'))
            
            if collection:
                # Check cache size
                count = collection.count()
                if count >= self.max_cache_size:
                    # Remove oldest entries
                    self._cleanup_old_entries(collection, keep_ratio=0.8)
                
                # Generate unique ID
                cache_id = hashlib.md5(f"{query}:{language}:{time.time()}".encode()).hexdigest()
                
                # Add to collection
                collection.add(
                    ids=[cache_id],
                    embeddings=[query_embedding.tolist()],
                    documents=[response_str],
                    metadatas=[cache_metadata]
                )
                
                logger.debug(f"Cached response for query in {language}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return False
    
    def _cleanup_old_entries(self, collection, keep_ratio: float = 0.8):
        """Remove old cache entries"""
        
        try:
            # Get all entries
            all_data = collection.get(include=['metadatas'])
            
            if not all_data['ids']:
                return
            
            # Sort by timestamp and hit count
            entries = []
            for i, (id_, metadata) in enumerate(zip(all_data['ids'], all_data['metadatas'])):
                score = metadata.get('timestamp', 0) + metadata.get('hit_count', 0) * 3600
                entries.append((id_, score))
            
            # Sort by score
            entries.sort(key=lambda x: x[1])
            
            # Remove lowest scoring entries
            num_to_remove = int(len(entries) * (1 - keep_ratio))
            ids_to_remove = [e[0] for e in entries[:num_to_remove]]
            
            if ids_to_remove:
                collection.delete(ids=ids_to_remove)
                logger.info(f"Removed {len(ids_to_remove)} old cache entries")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def get_similar_queries(
        self,
        query: str,
        language: str,
        n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get similar cached queries
        
        Args:
            query: Query to find similar ones for
            language: Language code
            n: Number of similar queries to return
            
        Returns:
            List of (query, similarity) tuples
        """
        
        try:
            # Generate embedding
            query_embedding = self.embedder.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            collection = self.collections.get(language, self.collections.get('mixed'))
            
            if collection:
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=n,
                    include=['metadatas', 'distances']
                )
                
                similar_queries = []
                for i, (metadata, distance) in enumerate(
                    zip(results['metadatas'][0], results['distances'][0])
                ):
                    original_query = metadata.get('original_query', 'Unknown')
                    similarity = 1 - distance
                    similar_queries.append((original_query, similarity))
                
                return similar_queries
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get similar queries: {e}")
            return []
    
    def clear(self, language: Optional[str] = None):
        """Clear cache for specific language or all"""
        
        try:
            if language:
                if language in self.collections:
                    self.chroma_client.delete_collection(f"cache_{language}")
                    self.collections[language] = self.chroma_client.create_collection(
                        name=f"cache_{language}",
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"Cleared cache for {language}")
            else:
                # Clear all collections
                for lang in list(self.collections.keys()):
                    self.clear(lang)
                logger.info("Cleared all caches")
                
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_metrics(self) -> Dict:
        """Get cache performance metrics"""
        
        hit_rate = (
            self.metrics['cache_hits'] / self.metrics['total_queries']
            if self.metrics['total_queries'] > 0 else 0
        )
        
        # Get cache sizes
        cache_sizes = {}
        if self.collections:
            for lang, collection in self.collections.items():
                try:
                    cache_sizes[lang] = collection.count()
                except:
                    cache_sizes[lang] = 0
        
        return {
            **self.metrics,
            'hit_rate': hit_rate,
            'cache_sizes': cache_sizes,
            'similarity_threshold': self.similarity_threshold
        }
    
    def save_to_disk(self):
        """Save cache state to disk"""
        
        try:
            metrics_path = os.path.join(self.cache_dir, "metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(self.metrics, f)
            logger.info("Cache metrics saved to disk")
        except Exception as e:
            logger.error(f"Failed to save cache state: {e}")
    
    def load_from_disk(self):
        """Load cache state from disk"""
        
        try:
            metrics_path = os.path.join(self.cache_dir, "metrics.json")
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    self.metrics = json.load(f)
                logger.info("Cache metrics loaded from disk")
        except Exception as e:
            logger.error(f"Failed to load cache state: {e}")