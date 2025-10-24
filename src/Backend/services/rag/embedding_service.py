"""
Embedding Service for RAG
Handles text embedding generation using sentence-transformers
"""

import numpy as np
import logging
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
from pathlib import Path
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Manages text embeddings using sentence-transformers
    Optimized for semantic search and retrieval
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        Initialize embedding service
        
        Args:
            model_name: Name of sentence-transformers model
                - all-MiniLM-L6-v2: Fast, 384 dim (default)
                - paraphrase-multilingual-MiniLM-L12-v2: Multilingual, 384 dim
                - multi-qa-mpnet-base-dot-v1: Better quality, 768 dim
            cache_dir: Directory to cache models
            device: Device to run model on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = device
        
        # Set cache directory
        if cache_dir:
            cache_path = Path(cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            self.cache_dir = str(cache_path)
        else:
            self.cache_dir = "models/embeddings"
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self.model = None
        self.embedding_dim = None
        self._load_model()
        
        # Performance metrics
        self.metrics = {
            "embeddings_generated": 0,
            "total_texts_embedded": 0,
            "cache_hits": 0,
            "average_batch_size": 0
        }
        
        logger.info(f"EmbeddingService initialized with model: {model_name}")
        logger.info(f"Embedding dimension: {self.embedding_dim}")
        logger.info(f"Device: {self.device}")
    
    def _load_model(self):
        """Load sentence-transformers model"""
        try:
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir,
                device=self.device
            )
            
            # Get embedding dimension
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"✅ Loaded embedding model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length
            
        Returns:
            Numpy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if not self.model:
            raise ValueError("Model not loaded")
        
        # Convert single string to list
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )
            
            # Update metrics
            self.metrics["embeddings_generated"] += 1
            self.metrics["total_texts_embedded"] += len(texts)
            
            # Return single embedding if input was single string
            if is_single:
                return embeddings[0]
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def encode_async(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Async wrapper for embedding generation
        Runs encoding in thread pool to avoid blocking
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.encode(texts, batch_size=batch_size, normalize=normalize)
        )
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[np.ndarray]:
        """
        Encode texts in batches and return as list
        Useful for large datasets
        """
        embeddings = self.encode(texts, batch_size=batch_size)
        return [emb for emb in embeddings]
    
    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = "cosine"
    ) -> float:
        """
        Calculate similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric ('cosine', 'dot', 'euclidean')
            
        Returns:
            Similarity score
        """
        if metric == "cosine":
            # Cosine similarity (assumes normalized embeddings)
            return float(np.dot(embedding1, embedding2))
        
        elif metric == "dot":
            # Dot product
            return float(np.dot(embedding1, embedding2))
        
        elif metric == "euclidean":
            # Euclidean distance (lower is more similar)
            return float(np.linalg.norm(embedding1 - embedding2))
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        metric: str = "cosine"
    ) -> np.ndarray:
        """
        Calculate similarity between query and multiple embeddings
        
        Args:
            query_embedding: Query embedding (1D array)
            embeddings: Array of embeddings (2D array)
            metric: Similarity metric
            
        Returns:
            Array of similarity scores
        """
        if metric == "cosine":
            # Assumes normalized embeddings
            return np.dot(embeddings, query_embedding)
        
        elif metric == "dot":
            return np.dot(embeddings, query_embedding)
        
        elif metric == "euclidean":
            return np.linalg.norm(embeddings - query_embedding, axis=1)
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    def get_metrics(self) -> dict:
        """Get performance metrics"""
        return {
            **self.metrics,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "device": self.device
        }
    
    def warmup(self, sample_texts: Optional[List[str]] = None):
        """
        Warm up model with sample texts
        Useful for reducing first-query latency
        """
        if sample_texts is None:
            sample_texts = [
                "What are your store hours?",
                "Tell me about your products",
                "How do I sign up?"
            ]
        
        logger.info("Warming up embedding model...")
        self.encode(sample_texts, show_progress=False)
        logger.info("✅ Model warmed up")


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    model_name: str = "all-MiniLM-L6-v2",
    device: str = "cpu"
) -> EmbeddingService:
    """
    Get singleton embedding service instance
    
    Args:
        model_name: Model to use
        device: Device to run on
        
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            model_name=model_name,
            device=device
        )
        # Warm up the model
        _embedding_service.warmup()
    
    return _embedding_service
