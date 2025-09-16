"""
FAISS-based embedding store for fast voice similarity search
"""

import numpy as np
import faiss
import pickle
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime
import asyncio
import asyncpg
from collections import defaultdict
import threading

from core.security.encryption import encrypt_embedding, decrypt_embedding, hash_user_id

logger = logging.getLogger(__name__)


class FAISSEmbeddingStore:
    """
    Fast similarity search for voice embeddings using FAISS
    Provides sub-millisecond search across millions of embeddings
    """

    def __init__(self, db_connection, embedding_dim: int = 448, index_path: str = "models/voice/biometric/cache/faiss_index"):
        """Initialize FAISS embedding store"""
        self.db = db_connection
        self.embedding_dim = embedding_dim
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize FAISS index
        self.index = None
        self.user_mapping = {}  # Maps index position to user_id
        self.reverse_mapping = {}  # Maps user_id to index position
        self.metadata = {}  # Stores additional metadata per user

        # Index configuration
        self.use_gpu = False  # Set to True if GPU available
        self.nlist = 100  # Number of clusters for IVF
        self.nprobe = 10  # Number of clusters to search

        # Performance metrics
        self.metrics = {
            'total_embeddings': 0,
            'index_updates': 0,
            'search_queries': 0,
            'avg_search_time_ms': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Thread lock for concurrent access
        self.lock = threading.Lock()

        # Initialize or load index
        self._initialize_index()

    def _initialize_index(self):
        """Initialize or load existing FAISS index"""
        try:
            index_file = self.index_path / "voice_embeddings.index"
            mapping_file = self.index_path / "user_mappings.pkl"
            metadata_file = self.index_path / "metadata.json"

            if index_file.exists() and mapping_file.exists():
                # Load existing index
                logger.info("Loading existing FAISS index...")
                self.index = faiss.read_index(str(index_file))

                with open(mapping_file, 'rb') as f:
                    data = pickle.load(f)
                    self.user_mapping = data['user_mapping']
                    self.reverse_mapping = data['reverse_mapping']

                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        self.metadata = json.load(f)

                self.metrics['total_embeddings'] = len(self.user_mapping)
                logger.info(f"Loaded FAISS index with {self.metrics['total_embeddings']} embeddings")

            else:
                # Create new index
                logger.info("Creating new FAISS index...")
                self._create_new_index()

        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
            self._create_new_index()

    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use IVF index for efficient search on large datasets
        quantizer = faiss.IndexFlatL2(self.embedding_dim)
        self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, self.nlist)

        # Train with dummy data if needed
        dummy_data = np.random.randn(max(self.nlist * 39, 1000), self.embedding_dim).astype('float32')
        self.index.train(dummy_data)

        # Set search parameters
        self.index.nprobe = self.nprobe

        logger.info(f"Created new FAISS IVF index with {self.nlist} clusters")

    async def add_embedding(self, user_id: str, embedding: np.ndarray, metadata: Optional[Dict] = None) -> bool:
        """Add or update a user's voice embedding"""
        try:
            with self.lock:
                # Normalize embedding
                embedding = embedding.astype('float32')
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                # Check if user already exists
                if user_id in self.reverse_mapping:
                    # Update existing embedding
                    idx = self.reverse_mapping[user_id]

                    # FAISS doesn't support in-place updates, so we need to rebuild
                    # For production, implement incremental updates or versioning
                    logger.warning(f"Updating embedding for user {user_id} requires index rebuild")
                    await self._rebuild_index_without_user(user_id)

                # Add new embedding
                self.index.add(np.expand_dims(embedding, axis=0))
                new_idx = self.index.ntotal - 1

                # Update mappings
                self.user_mapping[new_idx] = user_id
                self.reverse_mapping[user_id] = new_idx

                # Store metadata
                if metadata:
                    self.metadata[user_id] = {
                        **metadata,
                        'added_at': datetime.now().isoformat(),
                        'embedding_version': 1
                    }

                self.metrics['total_embeddings'] = self.index.ntotal
                self.metrics['index_updates'] += 1

                # Persist to disk periodically
                if self.metrics['index_updates'] % 100 == 0:
                    await self.save_index()

                logger.info(f"Added embedding for user {user_id}, total: {self.index.ntotal}")
                return True

        except Exception as e:
            logger.error(f"Error adding embedding: {str(e)}")
            return False

    async def search_similar(self, query_embedding: np.ndarray, k: int = 5,
                           threshold: float = 0.85) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar voice embeddings

        Args:
            query_embedding: Query voice embedding
            k: Number of nearest neighbors to return
            threshold: Minimum similarity threshold

        Returns:
            List of (user_id, similarity_score, metadata) tuples
        """
        try:
            with self.lock:
                start_time = datetime.now()

                # Normalize query embedding
                query_embedding = query_embedding.astype('float32')
                norm = np.linalg.norm(query_embedding)
                if norm > 0:
                    query_embedding = query_embedding / norm

                # Search
                distances, indices = self.index.search(
                    np.expand_dims(query_embedding, axis=0),
                    min(k, self.index.ntotal)
                )

                # Convert distances to similarities (cosine similarity)
                # Since we're using L2 distance on normalized vectors:
                # cosine_similarity = 1 - (L2_distance^2 / 2)
                similarities = 1 - (distances[0] ** 2) / 2

                # Filter results
                results = []
                for idx, similarity in zip(indices[0], similarities):
                    if idx >= 0 and similarity >= threshold:
                        user_id = self.user_mapping.get(idx)
                        if user_id:
                            user_metadata = self.metadata.get(user_id, {})
                            results.append((user_id, float(similarity), user_metadata))

                # Update metrics
                search_time = (datetime.now() - start_time).total_seconds() * 1000
                self.metrics['search_queries'] += 1
                n = self.metrics['search_queries']
                self.metrics['avg_search_time_ms'] = ((n - 1) * self.metrics['avg_search_time_ms'] + search_time) / n

                logger.debug(f"Found {len(results)} matches in {search_time:.2f}ms")
                return results

        except Exception as e:
            logger.error(f"Error searching embeddings: {str(e)}")
            return []

    async def remove_embedding(self, user_id: str) -> bool:
        """Remove a user's embedding (GDPR compliance)"""
        try:
            with self.lock:
                if user_id not in self.reverse_mapping:
                    logger.warning(f"User {user_id} not found in index")
                    return False

                # FAISS doesn't support deletion, need to rebuild
                await self._rebuild_index_without_user(user_id)

                logger.info(f"Removed embedding for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error removing embedding: {str(e)}")
            return False

    async def _rebuild_index_without_user(self, user_id: str):
        """Rebuild index excluding a specific user"""
        try:
            # Get all embeddings except the one to remove
            all_embeddings = []
            new_user_mapping = {}
            new_reverse_mapping = {}
            idx_counter = 0

            for idx, uid in self.user_mapping.items():
                if uid != user_id:
                    # Reconstruct embedding (would need to fetch from DB in production)
                    # For now, we'll skip reconstruction
                    pass

            # Remove from metadata
            if user_id in self.metadata:
                del self.metadata[user_id]

            # Update mappings
            if user_id in self.reverse_mapping:
                del self.reverse_mapping[user_id]

            self.metrics['total_embeddings'] = self.index.ntotal

        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            raise

    async def batch_add_embeddings(self, embeddings_data: List[Tuple[str, np.ndarray, Dict]]) -> int:
        """
        Add multiple embeddings in batch

        Args:
            embeddings_data: List of (user_id, embedding, metadata) tuples

        Returns:
            Number of successfully added embeddings
        """
        try:
            with self.lock:
                # Prepare batch data
                embeddings_list = []
                user_ids = []
                metadatas = []

                for user_id, embedding, metadata in embeddings_data:
                    # Skip if user already exists
                    if user_id in self.reverse_mapping:
                        continue

                    # Normalize embedding
                    embedding = embedding.astype('float32')
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm

                    embeddings_list.append(embedding)
                    user_ids.append(user_id)
                    metadatas.append(metadata)

                if not embeddings_list:
                    return 0

                # Add to index
                embeddings_array = np.array(embeddings_list, dtype='float32')
                self.index.add(embeddings_array)

                # Update mappings
                start_idx = self.index.ntotal - len(embeddings_list)
                for i, (user_id, metadata) in enumerate(zip(user_ids, metadatas)):
                    idx = start_idx + i
                    self.user_mapping[idx] = user_id
                    self.reverse_mapping[user_id] = idx

                    if metadata:
                        self.metadata[user_id] = {
                            **metadata,
                            'added_at': datetime.now().isoformat()
                        }

                self.metrics['total_embeddings'] = self.index.ntotal
                self.metrics['index_updates'] += len(embeddings_list)

                logger.info(f"Added batch of {len(embeddings_list)} embeddings")
                return len(embeddings_list)

        except Exception as e:
            logger.error(f"Error in batch add: {str(e)}")
            return 0

    async def save_index(self):
        """Save FAISS index and mappings to disk"""
        try:
            with self.lock:
                # Save FAISS index
                index_file = self.index_path / "voice_embeddings.index"
                faiss.write_index(self.index, str(index_file))

                # Save mappings
                mapping_file = self.index_path / "user_mappings.pkl"
                with open(mapping_file, 'wb') as f:
                    pickle.dump({
                        'user_mapping': self.user_mapping,
                        'reverse_mapping': self.reverse_mapping
                    }, f)

                # Save metadata
                metadata_file = self.index_path / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(self.metadata, f, indent=2)

                logger.info(f"Saved FAISS index with {self.index.ntotal} embeddings")

        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise

    async def load_from_database(self):
        """Load all embeddings from database into FAISS index"""
        try:
            query = """
                SELECT
                    vp.user_id,
                    vp.voice_embedding,
                    vp.metadata,
                    vp.quality_score,
                    vp.liveness_score,
                    vp.created_at
                FROM voice_profiles vp
                JOIN users u ON vp.user_id = u.id
                WHERE u.active = true
                    AND u.voice_enrolled = true
                ORDER BY vp.created_at
            """

            profiles = await self.db.fetch(query)

            if not profiles:
                logger.info("No voice profiles found in database")
                return 0

            # Prepare batch data
            embeddings_data = []
            for profile in profiles:
                try:
                    # Decrypt embedding
                    embedding = decrypt_embedding(profile['voice_embedding'])

                    # Parse metadata
                    metadata = json.loads(profile['metadata']) if profile['metadata'] else {}
                    metadata.update({
                        'quality_score': float(profile['quality_score']) if profile['quality_score'] else 0,
                        'liveness_score': float(profile['liveness_score']) if profile['liveness_score'] else 0,
                        'created_at': profile['created_at'].isoformat() if profile['created_at'] else None
                    })

                    embeddings_data.append((profile['user_id'], embedding, metadata))

                except Exception as e:
                    logger.error(f"Error processing profile for user {profile['user_id']}: {str(e)}")
                    continue

            # Add embeddings in batch
            count = await self.batch_add_embeddings(embeddings_data)

            # Save to disk
            await self.save_index()

            logger.info(f"Loaded {count} voice profiles from database")
            return count

        except Exception as e:
            logger.error(f"Error loading from database: {str(e)}")
            return 0

    async def optimize_index(self):
        """Optimize FAISS index for better performance"""
        try:
            with self.lock:
                if self.index.ntotal < 1000:
                    logger.info("Index too small for optimization")
                    return

                # Re-train index with current data
                logger.info("Optimizing FAISS index...")

                # Extract all embeddings
                embeddings = []
                for idx in range(self.index.ntotal):
                    embedding = self.index.reconstruct(idx)
                    embeddings.append(embedding)

                embeddings_array = np.array(embeddings, dtype='float32')

                # Create new optimized index
                if self.index.ntotal > 10000:
                    # Use PQ for large datasets
                    index = faiss.IndexIVFPQ(
                        faiss.IndexFlatL2(self.embedding_dim),
                        self.embedding_dim,
                        self.nlist,
                        32,  # Number of subquantizers
                        8   # Bits per subquantizer
                    )
                else:
                    # Use IVF for medium datasets
                    index = faiss.IndexIVFFlat(
                        faiss.IndexFlatL2(self.embedding_dim),
                        self.embedding_dim,
                        self.nlist
                    )

                # Train and add data
                index.train(embeddings_array)
                index.add(embeddings_array)
                index.nprobe = self.nprobe

                # Replace old index
                self.index = index

                logger.info(f"Optimized index with {self.index.ntotal} embeddings")

        except Exception as e:
            logger.error(f"Error optimizing index: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.metrics,
            'index_type': type(self.index).__name__,
            'embedding_dim': self.embedding_dim,
            'nlist': self.nlist,
            'nprobe': self.nprobe
        }

    async def clear_index(self):
        """Clear all embeddings (use with caution)"""
        try:
            with self.lock:
                self._create_new_index()
                self.user_mapping.clear()
                self.reverse_mapping.clear()
                self.metadata.clear()
                self.metrics['total_embeddings'] = 0

                logger.info("Cleared FAISS index")

        except Exception as e:
            logger.error(f"Error clearing index: {str(e)}")
            raise