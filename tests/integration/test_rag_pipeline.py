"""
Integration Tests for RAG Pipeline
Tests document retrieval, reranking, and generation with context
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import numpy as np

from services.rag_service import (
    RAGService,
    RAGConfig,
    RetrievalStrategy,
    RetrievalResult,
    RAGResult,
    MilvusManager
)
from langchain.schema import Document
from services.llm_service import GenerationResult

# Test fixtures

@pytest.fixture
def mock_rag_config():
    """Create a mock RAG configuration"""
    return RAGConfig(
        collection_name="test_products",
        embedding_collection="test_embeddings",
        host="localhost",
        port=19530,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dim=384,
        retrieval_strategy=RetrievalStrategy.HYBRID,
        top_k=5,
        similarity_threshold=0.7,
        rerank_top_k=3
    )

@pytest.fixture
def mock_documents():
    """Create mock documents for testing"""
    return [
        Document(
            page_content="Blue Dream is a sativa-dominant hybrid with high THC content.",
            metadata={"id": "1", "type": "product", "name": "Blue Dream", "thc_content": 18}
        ),
        Document(
            page_content="OG Kush is an indica strain known for relaxation.",
            metadata={"id": "2", "type": "product", "name": "OG Kush", "thc_content": 20}
        ),
        Document(
            page_content="CBD oil tincture with no THC for medical use.",
            metadata={"id": "3", "type": "product", "name": "CBD Oil", "thc_content": 0}
        )
    ]

@pytest.fixture
async def mock_rag_service(mock_rag_config):
    """Create a mock RAG service"""
    service = RAGService(mock_rag_config)
    
    # Mock Milvus manager
    service.milvus_manager = AsyncMock(spec=MilvusManager)
    service.milvus_manager.connect = AsyncMock(return_value=True)
    service.milvus_manager.ensure_collection = AsyncMock(return_value=True)
    
    # Mock embeddings
    with patch('services.rag_service.HuggingFaceEmbeddings') as MockEmbeddings:
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query = MagicMock(return_value=[0.1] * 384)
        mock_embeddings.embed_documents = MagicMock(return_value=[[0.1] * 384] * 3)
        MockEmbeddings.return_value = mock_embeddings
        service.embeddings = mock_embeddings
    
    # Mock reranker
    with patch('services.rag_service.CrossEncoder') as MockReranker:
        mock_reranker = MagicMock()
        mock_reranker.predict = MagicMock(return_value=np.array([0.9, 0.7, 0.5]))
        MockReranker.return_value = mock_reranker
        service.reranker = mock_reranker
    
    service._initialized = True
    
    return service

# RAGService Tests

class TestRAGService:
    """Test RAG service functionality"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_rag_config):
        """Test RAG service initialization"""
        service = RAGService(mock_rag_config)
        
        assert service.config == mock_rag_config
        assert not service._initialized
        
        # Mock dependencies
        with patch.object(service.milvus_manager, 'connect', return_value=True):
            with patch.object(service.milvus_manager, 'ensure_collection', return_value=True):
                with patch('services.rag_service.HuggingFaceEmbeddings'):
                    with patch('services.rag_service.CrossEncoder'):
                        await service.initialize()
                        
                        assert service._initialized
                        assert service.embeddings is not None
                        assert service.reranker is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_similarity_strategy(self, mock_rag_service, mock_documents):
        """Test document retrieval with similarity strategy"""
        # Mock Milvus search
        mock_rag_service.milvus_manager.search = AsyncMock(return_value=(
            [
                {"id": "1", "content": mock_documents[0].page_content, "metadata": mock_documents[0].metadata},
                {"id": "2", "content": mock_documents[1].page_content, "metadata": mock_documents[1].metadata}
            ],
            [0.9, 0.8]
        ))
        
        result = await mock_rag_service.retrieve(
            query="What strains are good for relaxation?",
            strategy=RetrievalStrategy.SIMILARITY
        )
        
        assert isinstance(result, RetrievalResult)
        assert len(result.documents) == 2
        assert result.scores == [0.9, 0.8]
        assert result.strategy == "similarity"
    
    @pytest.mark.asyncio
    async def test_retrieve_mmr_strategy(self, mock_rag_service, mock_documents):
        """Test retrieval with Maximum Marginal Relevance"""
        # Mock Milvus search with more candidates
        mock_rag_service.milvus_manager.search = AsyncMock(return_value=(
            [
                {"id": str(i), "content": f"Document {i}", "metadata": {"id": str(i)}}
                for i in range(10)
            ],
            [0.9 - i * 0.05 for i in range(10)]
        ))
        
        # Mock embedding for MMR calculation
        mock_rag_service.embeddings.embed_query = MagicMock(
            side_effect=lambda x: np.random.rand(384).tolist()
        )
        
        result = await mock_rag_service.retrieve(
            query="Find diverse cannabis products",
            strategy=RetrievalStrategy.MMR
        )
        
        assert isinstance(result, RetrievalResult)
        assert len(result.documents) <= mock_rag_service.config.top_k
        assert result.strategy == "mmr"
    
    @pytest.mark.asyncio
    async def test_retrieve_hybrid_strategy(self, mock_rag_service):
        """Test hybrid retrieval strategy"""
        # Mock searches for hybrid approach
        mock_rag_service.milvus_manager.search = AsyncMock(return_value=(
            [{"id": "1", "content": "Content 1", "metadata": {}}],
            [0.85]
        ))
        
        result = await mock_rag_service.retrieve(
            query="Best products for pain relief",
            strategy=RetrievalStrategy.HYBRID
        )
        
        assert isinstance(result, RetrievalResult)
        assert result.strategy == "hybrid"
    
    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, mock_rag_service):
        """Test retrieval with filters"""
        filters = {
            "category": "flower",
            "thc_content": {"min": 15, "max": 25}
        }
        
        mock_rag_service.milvus_manager.search = AsyncMock(return_value=(
            [{"id": "1", "content": "Filtered content", "metadata": {"category": "flower"}}],
            [0.9]
        ))
        
        result = await mock_rag_service.retrieve(
            query="High THC flowers",
            filters=filters
        )
        
        assert isinstance(result, RetrievalResult)
        assert result.metadata["filters"] == filters
    
    @pytest.mark.asyncio
    async def test_reranking(self, mock_rag_service):
        """Test document reranking"""
        # Setup mock documents
        docs = [
            {"id": str(i), "content": f"Document {i}", "metadata": {}}
            for i in range(5)
        ]
        scores = [0.9, 0.85, 0.8, 0.75, 0.7]
        
        # Mock reranker predictions
        mock_rag_service.reranker.predict = MagicMock(
            return_value=np.array([0.6, 0.95, 0.7, 0.5, 0.8])
        )
        
        reranked_docs, reranked_scores = await mock_rag_service._rerank_documents(
            "Test query",
            docs,
            scores
        )
        
        # Check reranking happened
        assert len(reranked_docs) <= mock_rag_service.config.rerank_top_k
        # Scores should be combined and reordered
        assert reranked_scores[0] > reranked_scores[-1]
    
    @pytest.mark.asyncio
    async def test_generate_with_context(self, mock_rag_service, mock_documents):
        """Test RAG generation with retrieved context"""
        # Mock retrieval
        mock_rag_service.retrieve = AsyncMock(return_value=RetrievalResult(
            documents=mock_documents,
            scores=[0.9, 0.8, 0.7],
            query="What's good for anxiety?",
            strategy="similarity",
            retrieval_time=0.5
        ))
        
        # Mock LLM service
        with patch('services.rag_service.get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=GenerationResult(
                text="Based on the context, CBD oil would be best for anxiety.",
                model="test-model",
                tokens_generated=20,
                generation_time=1.0,
                confidence=0.9
            ))
            mock_get_llm.return_value = mock_llm
            
            result = await mock_rag_service.generate_with_context(
                query="What's good for anxiety?",
                context="Customer has mild anxiety"
            )
            
            assert isinstance(result, RAGResult)
            assert "CBD" in result.response
            assert len(result.retrieved_documents) == 3
            assert result.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_streaming_generation(self, mock_rag_service, mock_documents):
        """Test streaming RAG generation"""
        # Mock retrieval
        mock_rag_service.retrieve = AsyncMock(return_value=RetrievalResult(
            documents=mock_documents,
            scores=[0.9],
            query="Test",
            strategy="similarity",
            retrieval_time=0.5
        ))
        
        # Mock streaming LLM
        async def mock_stream():
            for token in ["Cannabis ", "recommendation ", "here"]:
                yield token
        
        with patch('services.rag_service.get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=mock_stream())
            mock_get_llm.return_value = mock_llm
            
            result = await mock_rag_service.generate_with_context(
                query="Test query",
                stream=True
            )
            
            # Collect streamed tokens
            tokens = []
            async for token in result:
                tokens.append(token)
            
            assert tokens == ["Cannabis ", "recommendation ", "here"]
    
    @pytest.mark.asyncio
    async def test_index_documents(self, mock_rag_service):
        """Test document indexing"""
        documents = [
            {"id": "1", "content": "Test content 1", "metadata": {"type": "product"}},
            {"id": "2", "content": "Test content 2", "metadata": {"type": "product"}}
        ]
        
        mock_rag_service.milvus_manager.insert_embeddings = AsyncMock(return_value=True)
        
        result = await mock_rag_service.index_documents(documents, batch_size=2)
        
        assert result is True
        mock_rag_service.milvus_manager.insert_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_contextual_search(self, mock_rag_service):
        """Test contextual search with query expansion"""
        # Mock LLM for query expansion
        with patch('services.rag_service.get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=GenerationResult(
                text="- cannabis for sleep\n- indica strains\n- nighttime relief",
                model="test",
                tokens_generated=15,
                generation_time=0.5,
                confidence=0.8
            ))
            mock_get_llm.return_value = mock_llm
            
            # Mock search results
            mock_rag_service.milvus_manager.search = AsyncMock(return_value=(
                [{"id": "1", "content": "Indica for sleep", "metadata": {}}],
                [0.9]
            ))
            
            result = await mock_rag_service.retrieve(
                query="Help me sleep better",
                strategy=RetrievalStrategy.CONTEXTUAL
            )
            
            assert isinstance(result, RetrievalResult)
            assert result.strategy == "contextual"
            # Should have called search multiple times for expanded queries
            assert mock_rag_service.milvus_manager.search.call_count >= 1

# MilvusManager Tests

class TestMilvusManager:
    """Test Milvus manager functionality"""
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_rag_config):
        """Test Milvus connection"""
        manager = MilvusManager(mock_rag_config)
        
        with patch('services.rag_service.connections.connect') as mock_connect:
            result = await manager.connect()
            
            assert result is True
            assert manager.connected is True
            mock_connect.assert_called_once_with(
                alias="default",
                host=mock_rag_config.host,
                port=mock_rag_config.port
            )
    
    @pytest.mark.asyncio
    async def test_ensure_collection_exists(self, mock_rag_config):
        """Test ensuring collection exists"""
        manager = MilvusManager(mock_rag_config)
        
        with patch('services.rag_service.utility.has_collection', return_value=True):
            with patch('services.rag_service.Collection') as MockCollection:
                mock_collection = MagicMock()
                MockCollection.return_value = mock_collection
                
                result = await manager.ensure_collection("test_collection", 384)
                
                assert result is True
                assert "test_collection" in manager.collections
    
    @pytest.mark.asyncio
    async def test_ensure_collection_create_new(self, mock_rag_config):
        """Test creating new collection"""
        manager = MilvusManager(mock_rag_config)
        
        with patch('services.rag_service.utility.has_collection', return_value=False):
            with patch('services.rag_service.Collection') as MockCollection:
                mock_collection = MagicMock()
                MockCollection.return_value = mock_collection
                
                result = await manager.ensure_collection("new_collection", 384)
                
                assert result is True
                assert "new_collection" in manager.collections
                mock_collection.create_index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search(self, mock_rag_config):
        """Test vector search"""
        manager = MilvusManager(mock_rag_config)
        
        # Setup mock collection
        mock_collection = MagicMock()
        mock_hits = [
            MagicMock(
                entity={"document_id": "1", "content": "Test", "metadata": "{}"},
                score=0.9
            )
        ]
        mock_collection.search.return_value = [mock_hits]
        manager.collections["test"] = mock_collection
        
        docs, scores = await manager.search(
            "test",
            [0.1] * 384,
            top_k=5
        )
        
        assert len(docs) == 1
        assert scores == [0.9]
        mock_collection.load.assert_called_once()
        mock_collection.search.assert_called_once()

# Error Handling Tests

class TestRAGErrorHandling:
    """Test error handling in RAG pipeline"""
    
    @pytest.mark.asyncio
    async def test_retrieval_failure_fallback(self, mock_rag_service):
        """Test fallback when retrieval fails"""
        mock_rag_service.milvus_manager.search = AsyncMock(
            side_effect=Exception("Search failed")
        )
        
        result = await mock_rag_service.retrieve(
            query="Test query",
            strategy=RetrievalStrategy.SIMILARITY
        )
        
        assert isinstance(result, RetrievalResult)
        assert len(result.documents) == 0
        assert "error" in result.metadata
    
    @pytest.mark.asyncio
    async def test_generation_fallback_without_context(self, mock_rag_service):
        """Test generation fallback when retrieval fails"""
        # Make retrieval fail
        mock_rag_service.retrieve = AsyncMock(
            side_effect=Exception("Retrieval failed")
        )
        
        # Mock direct LLM generation
        with patch('services.rag_service.get_llm_service') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=GenerationResult(
                text="Fallback response without context",
                model="test",
                tokens_generated=10,
                generation_time=0.5,
                confidence=0.5
            ))
            mock_get_llm.return_value = mock_llm
            
            result = await mock_rag_service.generate_with_context(
                query="Test query"
            )
            
            assert isinstance(result, RAGResult)
            assert result.confidence == 0.25  # Reduced confidence
            assert result.metadata.get("fallback") is True
    
    @pytest.mark.asyncio
    async def test_milvus_connection_failure(self, mock_rag_config):
        """Test handling Milvus connection failure"""
        service = RAGService(mock_rag_config)
        
        with patch('services.rag_service.connections.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(RuntimeError, match="Failed to connect to Milvus"):
                await service.initialize()

# Performance Tests

class TestRAGPerformance:
    """Test RAG pipeline performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_caching(self, mock_rag_service):
        """Test result caching"""
        # Enable cache
        mock_rag_service.cache = AsyncMock()
        mock_rag_service.cache.get = AsyncMock(return_value=None)
        mock_rag_service.cache.set = AsyncMock()
        
        # Mock search
        mock_rag_service.milvus_manager.search = AsyncMock(return_value=(
            [{"id": "1", "content": "Cached", "metadata": {}}],
            [0.9]
        ))
        
        # First call - should hit database
        result1 = await mock_rag_service.retrieve("Test query")
        
        # Cache should be set
        mock_rag_service.cache.set.assert_called_once()
        
        # Setup cache hit
        mock_rag_service.cache.get = AsyncMock(return_value=result1)
        
        # Second call - should hit cache
        result2 = await mock_rag_service.retrieve("Test query")
        
        # Search should only be called once (from first call)
        assert mock_rag_service.milvus_manager.search.call_count == 1
    
    @pytest.mark.asyncio
    async def test_batch_indexing(self, mock_rag_service):
        """Test batch document indexing"""
        # Create many documents
        documents = [
            {"id": str(i), "content": f"Document {i}", "metadata": {}}
            for i in range(250)
        ]
        
        mock_rag_service.milvus_manager.insert_embeddings = AsyncMock(return_value=True)
        
        result = await mock_rag_service.index_documents(documents, batch_size=100)
        
        assert result is True
        # Should be called 3 times (100, 100, 50)
        assert mock_rag_service.milvus_manager.insert_embeddings.call_count == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])