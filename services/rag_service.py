"""
RAG (Retrieval-Augmented Generation) Service
Integrates with Milvus vector database for document retrieval and reranking
"""

import asyncio
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from pymilvus import (
    connections,
    Collection,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    MilvusException
)

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Milvus
from langchain.schema import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor, EmbeddingsFilter
from sentence_transformers import CrossEncoder

from services.llm_service import get_llm_service, GenerationResult
from config import settings
from utils.cache import CacheManager
from utils.monitoring import MetricsCollector

logger = logging.getLogger(__name__)

class RetrievalStrategy(Enum):
    """Retrieval strategies for RAG"""
    SIMILARITY = "similarity"
    MMR = "mmr"  # Maximum Marginal Relevance
    HYBRID = "hybrid"  # Combine multiple strategies
    CONTEXTUAL = "contextual"  # With context compression

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    # Milvus settings
    collection_name: str = "cannabis_products"
    embedding_collection: str = "product_embeddings"
    host: str = "localhost"
    port: int = 19530
    
    # Embedding settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    
    # Retrieval settings
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    top_k: int = 10
    similarity_threshold: float = 0.7
    rerank_top_k: int = 5
    
    # Reranking model
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Chunking settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600

@dataclass
class RetrievalResult:
    """Result from document retrieval"""
    documents: List[Document]
    scores: List[float]
    query: str
    strategy: str
    retrieval_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RAGResult:
    """Result from RAG pipeline"""
    response: str
    retrieved_documents: List[Document]
    retrieval_scores: List[float]
    query: str
    total_time: float
    model_used: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class MilvusManager:
    """Manages Milvus vector database connections and operations"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.connected = False
        self.collections: Dict[str, Collection] = {}
        
    async def connect(self) -> bool:
        """Connect to Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.config.host,
                port=self.config.port
            )
            self.connected = True
            logger.info(f"Connected to Milvus at {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            self.connected = False
            return False
    
    async def ensure_collection(self, collection_name: str, dim: int) -> bool:
        """Ensure collection exists with proper schema"""
        try:
            if utility.has_collection(collection_name):
                self.collections[collection_name] = Collection(collection_name)
                logger.info(f"Using existing collection: {collection_name}")
                return True
            
            # Create collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
                FieldSchema(name="metadata", dtype=DataType.JSON)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description=f"Cannabis product embeddings for {collection_name}"
            )
            
            # Create collection
            collection = Collection(
                name=collection_name,
                schema=schema
            )
            
            # Create index for vector field
            index_params = {
                "metric_type": "IP",  # Inner Product for similarity
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            self.collections[collection_name] = collection
            logger.info(f"Created new collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {str(e)}")
            return False
    
    async def insert_embeddings(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """Insert documents with embeddings into Milvus"""
        try:
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return False
            
            collection = self.collections[collection_name]
            
            # Prepare data for insertion
            data = {
                "document_id": [doc.get("id", str(i)) for i, doc in enumerate(documents)],
                "content": [doc.get("content", "") for doc in documents],
                "embedding": embeddings,
                "metadata": [json.dumps(doc.get("metadata", {})) for doc in documents]
            }
            
            # Insert data
            collection.insert(data)
            collection.flush()
            
            logger.info(f"Inserted {len(documents)} documents into {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert embeddings: {str(e)}")
            return False
    
    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None
    ) -> Tuple[List[Dict], List[float]]:
        """Search for similar documents in Milvus"""
        try:
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return [], []
            
            collection = self.collections[collection_name]
            collection.load()
            
            # Prepare search parameters
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
            
            # Perform search
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filters,
                output_fields=["document_id", "content", "metadata"]
            )
            
            # Extract results
            documents = []
            scores = []
            
            for hits in results:
                for hit in hits:
                    doc = {
                        "id": hit.entity.get("document_id"),
                        "content": hit.entity.get("content"),
                        "metadata": json.loads(hit.entity.get("metadata", "{}"))
                    }
                    documents.append(doc)
                    scores.append(hit.score)
            
            return documents, scores
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return [], []
    
    async def disconnect(self):
        """Disconnect from Milvus"""
        try:
            connections.disconnect("default")
            self.connected = False
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Error disconnecting from Milvus: {str(e)}")

class RAGService:
    """
    Retrieval-Augmented Generation Service
    Combines document retrieval with LLM generation for enhanced responses
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.milvus_manager = MilvusManager(self.config)
        self.embeddings = None
        self.text_splitter = None
        self.reranker = None
        self.cache = CacheManager() if self.config.enable_cache else None
        self.metrics = MetricsCollector()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize RAG service components"""
        
        logger.info("Initializing RAG Service")
        
        # Connect to Milvus
        if not await self.milvus_manager.connect():
            raise RuntimeError("Failed to connect to Milvus")
        
        # Ensure collections exist
        await self.milvus_manager.ensure_collection(
            self.config.collection_name,
            self.config.embedding_dim
        )
        
        await self.milvus_manager.ensure_collection(
            self.config.embedding_collection,
            self.config.embedding_dim
        )
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize reranker
        self.reranker = CrossEncoder(self.config.reranker_model)
        
        self._initialized = True
        logger.info("RAG Service initialized successfully")
    
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        strategy: Optional[RetrievalStrategy] = None
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            filters: Optional filters for search
            strategy: Retrieval strategy to use
        
        Returns:
            RetrievalResult with documents and scores
        """
        
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        strategy = strategy or self.config.retrieval_strategy
        
        # Check cache
        if self.cache:
            cache_key = f"rag:retrieve:{query}:{strategy.value}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for retrieval: {query[:50]}...")
                return cached
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build filter expression if provided
            filter_expr = self._build_filter_expression(filters) if filters else None
            
            # Retrieve based on strategy
            if strategy == RetrievalStrategy.SIMILARITY:
                documents, scores = await self._similarity_search(
                    query_embedding, filter_expr
                )
            elif strategy == RetrievalStrategy.MMR:
                documents, scores = await self._mmr_search(
                    query, query_embedding, filter_expr
                )
            elif strategy == RetrievalStrategy.HYBRID:
                documents, scores = await self._hybrid_search(
                    query, query_embedding, filter_expr
                )
            elif strategy == RetrievalStrategy.CONTEXTUAL:
                documents, scores = await self._contextual_search(
                    query, query_embedding, filter_expr
                )
            else:
                documents, scores = await self._similarity_search(
                    query_embedding, filter_expr
                )
            
            # Rerank if configured
            if self.reranker and len(documents) > 0:
                documents, scores = await self._rerank_documents(
                    query, documents, scores
                )
            
            # Convert to Document objects
            doc_objects = [
                Document(
                    page_content=doc['content'],
                    metadata=doc.get('metadata', {})
                )
                for doc in documents
            ]
            
            result = RetrievalResult(
                documents=doc_objects,
                scores=scores,
                query=query,
                strategy=strategy.value,
                retrieval_time=time.time() - start_time,
                metadata={'filters': filters}
            )
            
            # Cache result
            if self.cache:
                await self.cache.set(cache_key, result, ttl=self.config.cache_ttl)
            
            self.metrics.record_retrieval(len(documents), result.retrieval_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}", exc_info=True)
            return RetrievalResult(
                documents=[],
                scores=[],
                query=query,
                strategy=strategy.value,
                retrieval_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def _similarity_search(
        self,
        query_embedding: List[float],
        filters: Optional[str]
    ) -> Tuple[List[Dict], List[float]]:
        """Standard similarity search"""
        
        documents, scores = await self.milvus_manager.search(
            self.config.collection_name,
            query_embedding,
            self.config.top_k,
            filters
        )
        
        # Filter by threshold
        filtered_docs = []
        filtered_scores = []
        
        for doc, score in zip(documents, scores):
            if score >= self.config.similarity_threshold:
                filtered_docs.append(doc)
                filtered_scores.append(score)
        
        return filtered_docs, filtered_scores
    
    async def _mmr_search(
        self,
        query: str,
        query_embedding: List[float],
        filters: Optional[str]
    ) -> Tuple[List[Dict], List[float]]:
        """Maximum Marginal Relevance search for diversity"""
        
        # Get initial candidates
        candidates, candidate_scores = await self.milvus_manager.search(
            self.config.collection_name,
            query_embedding,
            self.config.top_k * 2,  # Get more candidates for MMR
            filters
        )
        
        if not candidates:
            return [], []
        
        # Implement MMR algorithm
        lambda_mult = 0.5  # Balance between relevance and diversity
        selected = []
        selected_scores = []
        
        # Get embeddings for all candidates
        candidate_embeddings = [
            self.embeddings.embed_query(doc['content'])
            for doc in candidates
        ]
        
        # Select first document (most relevant)
        selected.append(candidates[0])
        selected_scores.append(candidate_scores[0])
        selected_embeddings = [candidate_embeddings[0]]
        
        # Iteratively select diverse documents
        while len(selected) < min(self.config.top_k, len(candidates)):
            mmr_scores = []
            
            for i, (doc, emb, score) in enumerate(zip(
                candidates, candidate_embeddings, candidate_scores
            )):
                if doc in selected:
                    continue
                
                # Calculate similarity to selected documents
                max_sim_to_selected = max([
                    np.dot(emb, sel_emb)
                    for sel_emb in selected_embeddings
                ])
                
                # MMR score
                mmr_score = lambda_mult * score - (1 - lambda_mult) * max_sim_to_selected
                mmr_scores.append((i, mmr_score))
            
            if not mmr_scores:
                break
            
            # Select document with highest MMR score
            best_idx = max(mmr_scores, key=lambda x: x[1])[0]
            selected.append(candidates[best_idx])
            selected_scores.append(candidate_scores[best_idx])
            selected_embeddings.append(candidate_embeddings[best_idx])
        
        return selected, selected_scores
    
    async def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        filters: Optional[str]
    ) -> Tuple[List[Dict], List[float]]:
        """Hybrid search combining multiple strategies"""
        
        # Run multiple search strategies in parallel
        similarity_task = self._similarity_search(query_embedding, filters)
        mmr_task = self._mmr_search(query, query_embedding, filters)
        
        similarity_results, mmr_results = await asyncio.gather(
            similarity_task,
            mmr_task
        )
        
        # Combine results with weighted scoring
        combined_docs = {}
        
        # Add similarity results
        for doc, score in zip(similarity_results[0], similarity_results[1]):
            doc_id = doc.get('id', doc['content'][:50])
            combined_docs[doc_id] = {
                'doc': doc,
                'similarity_score': score * 0.6,  # Weight for similarity
                'mmr_score': 0
            }
        
        # Add MMR results
        for doc, score in zip(mmr_results[0], mmr_results[1]):
            doc_id = doc.get('id', doc['content'][:50])
            if doc_id in combined_docs:
                combined_docs[doc_id]['mmr_score'] = score * 0.4  # Weight for diversity
            else:
                combined_docs[doc_id] = {
                    'doc': doc,
                    'similarity_score': 0,
                    'mmr_score': score * 0.4
                }
        
        # Calculate final scores and sort
        final_results = []
        for doc_id, data in combined_docs.items():
            final_score = data['similarity_score'] + data['mmr_score']
            final_results.append((data['doc'], final_score))
        
        # Sort by final score
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        documents = [r[0] for r in final_results[:self.config.top_k]]
        scores = [r[1] for r in final_results[:self.config.top_k]]
        
        return documents, scores
    
    async def _contextual_search(
        self,
        query: str,
        query_embedding: List[float],
        filters: Optional[str]
    ) -> Tuple[List[Dict], List[float]]:
        """Contextual search with query expansion"""
        
        # Get LLM service for query expansion
        llm_service = get_llm_service()
        
        # Expand query using LLM
        expansion_prompt = f"""Given the cannabis-related query: "{query}"
        
        Generate 3 alternative phrasings or related terms that would help find relevant products.
        Focus on cannabis strains, effects, terpenes, and medical uses.
        
        Alternative queries:"""
        
        try:
            expansion_result = await llm_service.generate(
                prompt=expansion_prompt,
                max_tokens=100,
                temperature=0.7
            )
            
            # Parse expanded queries
            expanded_queries = [query]  # Include original
            if isinstance(expansion_result, GenerationResult):
                lines = expansion_result.text.strip().split('\n')
                for line in lines[:3]:  # Take up to 3 expansions
                    cleaned = line.strip().lstrip('- ').lstrip('• ')
                    if cleaned:
                        expanded_queries.append(cleaned)
        except:
            expanded_queries = [query]  # Fallback to original only
        
        # Search with all queries
        all_documents = {}
        all_scores = {}
        
        for q in expanded_queries:
            q_embedding = self.embeddings.embed_query(q)
            docs, scores = await self._similarity_search(q_embedding, filters)
            
            for doc, score in zip(docs, scores):
                doc_id = doc.get('id', doc['content'][:50])
                if doc_id not in all_documents:
                    all_documents[doc_id] = doc
                    all_scores[doc_id] = score
                else:
                    # Take maximum score
                    all_scores[doc_id] = max(all_scores[doc_id], score)
        
        # Sort by score
        sorted_docs = sorted(
            all_documents.items(),
            key=lambda x: all_scores[x[0]],
            reverse=True
        )
        
        documents = [doc for _, doc in sorted_docs[:self.config.top_k]]
        scores = [all_scores[doc_id] for doc_id, _ in sorted_docs[:self.config.top_k]]
        
        return documents, scores
    
    async def _rerank_documents(
        self,
        query: str,
        documents: List[Dict],
        scores: List[float]
    ) -> Tuple[List[Dict], List[float]]:
        """Rerank documents using cross-encoder"""
        
        if not documents:
            return documents, scores
        
        # Prepare pairs for reranking
        pairs = [[query, doc['content']] for doc in documents]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Combine original scores with rerank scores
        combined_scores = [
            0.3 * orig + 0.7 * rerank  # Weight reranking higher
            for orig, rerank in zip(scores, rerank_scores)
        ]
        
        # Sort by combined score
        sorted_indices = np.argsort(combined_scores)[::-1]
        
        # Return top k after reranking
        top_k = min(self.config.rerank_top_k, len(documents))
        reranked_docs = [documents[i] for i in sorted_indices[:top_k]]
        reranked_scores = [combined_scores[i] for i in sorted_indices[:top_k]]
        
        return reranked_docs, reranked_scores
    
    def _build_filter_expression(self, filters: Dict[str, Any]) -> str:
        """Build Milvus filter expression from dictionary"""
        
        expressions = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                expressions.append(f'{key} == "{value}"')
            elif isinstance(value, (int, float)):
                expressions.append(f'{key} == {value}')
            elif isinstance(value, list):
                values_str = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                expressions.append(f'{key} in [{values_str}]')
            elif isinstance(value, dict):
                # Handle range queries
                if 'min' in value:
                    expressions.append(f'{key} >= {value["min"]}')
                if 'max' in value:
                    expressions.append(f'{key} <= {value["max"]}')
        
        return ' and '.join(expressions) if expressions else None
    
    async def generate_with_context(
        self,
        query: str,
        context: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> RAGResult:
        """
        Generate response using retrieved context
        
        Args:
            query: User query
            context: Optional additional context
            filters: Optional filters for retrieval
            stream: Whether to stream the response
        
        Returns:
            RAGResult with generated response and retrieved documents
        """
        
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Retrieve relevant documents
            retrieval_result = await self.retrieve(query, filters)
            
            # Build context from retrieved documents
            retrieved_context = "\n\n".join([
                f"Document {i+1}: {doc.page_content[:500]}"
                for i, doc in enumerate(retrieval_result.documents[:5])
            ])
            
            # Combine with additional context if provided
            full_context = f"{context}\n\n{retrieved_context}" if context else retrieved_context
            
            # Build RAG prompt
            rag_prompt = f"""You are a knowledgeable cannabis expert. Use the following context to answer the question.
            
Context:
{full_context}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain relevant information, say so.

Answer:"""
            
            # Generate response using LLM
            llm_service = get_llm_service()
            
            if stream:
                # Return streaming generator
                async def stream_response():
                    async for token in await llm_service.generate(
                        prompt=rag_prompt,
                        stream=True,
                        temperature=0.7,
                        max_tokens=512
                    ):
                        yield token
                
                return stream_response()
            else:
                generation_result = await llm_service.generate(
                    prompt=rag_prompt,
                    temperature=0.7,
                    max_tokens=512
                )
                
                total_time = time.time() - start_time
                
                result = RAGResult(
                    response=generation_result.text,
                    retrieved_documents=retrieval_result.documents,
                    retrieval_scores=retrieval_result.scores,
                    query=query,
                    total_time=total_time,
                    model_used=generation_result.model,
                    confidence=generation_result.confidence,
                    metadata={
                        'retrieval_strategy': retrieval_result.strategy,
                        'num_documents': len(retrieval_result.documents),
                        'filters': filters
                    }
                )
                
                self.metrics.record_rag_generation(
                    len(retrieval_result.documents),
                    total_time
                )
                
                return result
                
        except Exception as e:
            logger.error(f"RAG generation error: {str(e)}", exc_info=True)
            
            # Fallback to direct generation without context
            llm_service = get_llm_service()
            generation_result = await llm_service.generate(
                prompt=f"Answer this cannabis-related question: {query}",
                temperature=0.7,
                max_tokens=512
            )
            
            return RAGResult(
                response=generation_result.text,
                retrieved_documents=[],
                retrieval_scores=[],
                query=query,
                total_time=time.time() - start_time,
                model_used=generation_result.model,
                confidence=generation_result.confidence * 0.5,  # Lower confidence without context
                metadata={'error': str(e), 'fallback': True}
            )
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> bool:
        """
        Index new documents into the vector database
        
        Args:
            documents: List of documents to index
            batch_size: Batch size for processing
        
        Returns:
            Success status
        """
        
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Indexing {len(documents)} documents")
            
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Extract content for embedding
                contents = [doc.get('content', '') for doc in batch]
                
                # Generate embeddings
                embeddings = self.embeddings.embed_documents(contents)
                
                # Insert into Milvus
                success = await self.milvus_manager.insert_embeddings(
                    self.config.collection_name,
                    batch,
                    embeddings
                )
                
                if not success:
                    logger.error(f"Failed to index batch {i // batch_size}")
                    return False
                
                logger.info(f"Indexed batch {i // batch_size + 1}")
            
            logger.info("Document indexing complete")
            return True
            
        except Exception as e:
            logger.error(f"Document indexing error: {str(e)}", exc_info=True)
            return False
    
    async def cleanup(self) -> None:
        """Cleanup RAG service resources"""
        
        logger.info("Cleaning up RAG Service")
        
        await self.milvus_manager.disconnect()
        
        self.embeddings = None
        self.text_splitter = None
        self.reranker = None
        self._initialized = False
        
        logger.info("RAG Service cleanup complete")

# Singleton instance
_rag_service: Optional[RAGService] = None

def get_rag_service(config: Optional[RAGConfig] = None) -> RAGService:
    """Get singleton RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(config)
    return _rag_service