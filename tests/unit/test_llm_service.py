"""
Unit Tests for LLM Service
Tests model loading, generation, and fallback mechanisms
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile

from services.llm_service import (
    LLMService,
    LLMModel,
    ModelConfig,
    ModelType,
    GenerationResult
)

# Test fixtures

@pytest.fixture
def mock_model_config():
    """Create a mock model configuration"""
    return ModelConfig(
        name="test-model",
        path=Path("/tmp/test-model.gguf"),
        model_type=ModelType.LLAMA2_7B,
        context_length=2048,
        n_threads=4,
        temperature=0.7,
        max_tokens=256
    )

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service"""
    service = LLMService()
    service._initialized = False
    return service

@pytest.fixture
async def initialized_llm_service(mock_llm_service):
    """Create an initialized LLM service with mocked models"""
    with patch('services.llm_service.LLMModel') as MockModel:
        mock_model = AsyncMock()
        mock_model.load = AsyncMock(return_value=True)
        mock_model.is_loaded = True
        mock_model.config = mock_model_config()
        MockModel.return_value = mock_model
        
        mock_llm_service.models['test-model'] = mock_model
        mock_llm_service.primary_model = 'test-model'
        mock_llm_service._initialized = True
        
        return mock_llm_service

# LLMModel Tests

class TestLLMModel:
    """Test LLMModel class"""
    
    @pytest.mark.asyncio
    async def test_model_initialization(self, mock_model_config):
        """Test model initialization"""
        model = LLMModel(mock_model_config)
        
        assert model.config == mock_model_config
        assert model.model is None
        assert model.langchain_llm is None
        assert not model.is_loaded
    
    @pytest.mark.asyncio
    async def test_model_load_success(self, mock_model_config):
        """Test successful model loading"""
        # Create temporary model file
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            mock_model_config.path = tmp_path
            
            model = LLMModel(mock_model_config)
            
            with patch('llama_cpp.Llama') as MockLlama:
                MockLlama.return_value = MagicMock()
                
                with patch('langchain.llms.LlamaCpp') as MockLlamaCpp:
                    MockLlamaCpp.return_value = MagicMock()
                    
                    result = await model.load()
                    
                    assert result is True
                    assert model.is_loaded is True
                    assert model.model is not None
                    assert model.langchain_llm is not None
            
            # Cleanup
            tmp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_model_load_missing_file(self, mock_model_config):
        """Test model loading with missing file"""
        mock_model_config.path = Path("/nonexistent/model.gguf")
        model = LLMModel(mock_model_config)
        
        result = await model.load()
        
        assert result is False
        assert not model.is_loaded
    
    @pytest.mark.asyncio
    async def test_model_generate(self, mock_model_config):
        """Test model generation"""
        model = LLMModel(mock_model_config)
        model.is_loaded = True
        
        # Mock the model
        mock_llama = MagicMock()
        mock_llama.return_value = {
            'choices': [{'text': 'Generated text'}],
            'usage': {'completion_tokens': 10}
        }
        model.model = mock_llama
        
        result = await model.generate("Test prompt", stream=False)
        
        assert isinstance(result, GenerationResult)
        assert result.text == 'Generated text'
        assert result.model == 'test-model'
        assert result.tokens_generated == 10
    
    @pytest.mark.asyncio
    async def test_model_generate_not_loaded(self, mock_model_config):
        """Test generation with unloaded model"""
        model = LLMModel(mock_model_config)
        model.is_loaded = False
        
        with pytest.raises(RuntimeError, match="is not loaded"):
            await model.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_model_stream_generation(self, mock_model_config):
        """Test streaming generation"""
        model = LLMModel(mock_model_config)
        model.is_loaded = True
        
        # Mock streaming response
        def mock_stream(*args, **kwargs):
            yield {'choices': [{'text': 'Hello'}]}
            yield {'choices': [{'text': ' world'}]}
        
        mock_llama = MagicMock()
        mock_llama.side_effect = mock_stream
        model.model = mock_llama
        
        tokens = []
        async for token in model.generate("Test prompt", stream=True):
            tokens.append(token)
        
        assert tokens == ['Hello', ' world']
    
    @pytest.mark.asyncio
    async def test_model_unload(self, mock_model_config):
        """Test model unloading"""
        model = LLMModel(mock_model_config)
        model.model = MagicMock()
        model.langchain_llm = MagicMock()
        model.is_loaded = True
        
        await model.unload()
        
        assert model.model is None
        assert model.langchain_llm is None
        assert not model.is_loaded

# LLMService Tests

class TestLLMService:
    """Test LLMService class"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_llm_service):
        """Test service initialization"""
        assert len(mock_llm_service.models) == 0
        assert mock_llm_service.primary_model is None
        assert mock_llm_service.fallback_model is None
        assert not mock_llm_service._initialized
    
    @pytest.mark.asyncio
    async def test_service_initialize(self, mock_llm_service):
        """Test service initialization process"""
        with patch.object(mock_llm_service, '_load_model_configs') as mock_load_configs:
            with patch.object(mock_llm_service, '_load_primary_models') as mock_load_models:
                mock_load_models.return_value = None
                
                await mock_llm_service.initialize()
                
                mock_load_configs.assert_called_once()
                mock_load_models.assert_called_once()
                assert mock_llm_service._initialized
    
    @pytest.mark.asyncio
    async def test_generate_with_primary_model(self, initialized_llm_service):
        """Test generation using primary model"""
        mock_model = initialized_llm_service.models['test-model']
        mock_result = GenerationResult(
            text="Generated response",
            model="test-model",
            tokens_generated=50,
            generation_time=1.0,
            confidence=0.9
        )
        mock_model.generate = AsyncMock(return_value=mock_result)
        
        result = await initialized_llm_service.generate(
            prompt="Test prompt",
            temperature=0.7
        )
        
        assert result == mock_result
        mock_model.generate.assert_called_once_with(
            "Test prompt",
            False,
            temperature=0.7
        )
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback(self, initialized_llm_service):
        """Test fallback to secondary model on primary failure"""
        # Add fallback model
        mock_fallback = AsyncMock()
        mock_fallback.is_loaded = True
        fallback_result = GenerationResult(
            text="Fallback response",
            model="fallback-model",
            tokens_generated=30,
            generation_time=0.8,
            confidence=0.8
        )
        mock_fallback.generate = AsyncMock(return_value=fallback_result)
        
        initialized_llm_service.models['fallback-model'] = mock_fallback
        initialized_llm_service.fallback_model = 'fallback-model'
        
        # Make primary model fail
        primary_model = initialized_llm_service.models['test-model']
        primary_model.generate = AsyncMock(side_effect=Exception("Primary failed"))
        
        result = await initialized_llm_service.generate(prompt="Test prompt")
        
        assert result == fallback_result
        mock_fallback.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_streaming(self, initialized_llm_service):
        """Test streaming generation"""
        async def mock_stream(*args, **kwargs):
            for token in ['Hello', ' ', 'world']:
                yield token
        
        mock_model = initialized_llm_service.models['test-model']
        mock_model.generate = AsyncMock(return_value=mock_stream())
        
        tokens = []
        async for token in await initialized_llm_service.generate(
            prompt="Test prompt",
            stream=True
        ):
            tokens.append(token)
        
        assert tokens == ['Hello', ' ', 'world']
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, initialized_llm_service):
        """Test getting available models"""
        models = initialized_llm_service.get_available_models()
        
        assert models == ['test-model']
    
    @pytest.mark.asyncio
    async def test_get_status(self, initialized_llm_service):
        """Test getting service status"""
        mock_model = initialized_llm_service.models['test-model']
        mock_model.config.model_type = ModelType.LLAMA2_7B
        mock_model.config.context_length = 2048
        mock_model.config.n_gpu_layers = 0
        mock_model.config.metadata = {'test': 'data'}
        
        status = initialized_llm_service.get_status()
        
        assert status['initialized'] is True
        assert status['primary_model'] == 'test-model'
        assert 'test-model' in status['models']
        assert status['models']['test-model']['loaded'] is True
    
    @pytest.mark.asyncio
    async def test_load_model_dynamically(self, initialized_llm_service, mock_model_config):
        """Test dynamic model loading"""
        with patch('services.llm_service.LLMModel') as MockModel:
            mock_new_model = AsyncMock()
            mock_new_model.load = AsyncMock(return_value=True)
            MockModel.return_value = mock_new_model
            
            result = await initialized_llm_service.load_model(
                'new-model',
                mock_model_config
            )
            
            assert result is True
            assert 'new-model' in initialized_llm_service.models
    
    @pytest.mark.asyncio
    async def test_unload_model(self, initialized_llm_service):
        """Test model unloading"""
        # Add another model so we can unload one
        mock_model2 = AsyncMock()
        mock_model2.unload = AsyncMock()
        initialized_llm_service.models['model2'] = mock_model2
        
        result = await initialized_llm_service.unload_model('model2')
        
        assert result is True
        assert 'model2' not in initialized_llm_service.models
        mock_model2.unload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, initialized_llm_service):
        """Test service cleanup"""
        mock_model = initialized_llm_service.models['test-model']
        mock_model.unload = AsyncMock()
        
        await initialized_llm_service.cleanup()
        
        assert len(initialized_llm_service.models) == 0
        assert initialized_llm_service.primary_model is None
        assert initialized_llm_service.fallback_model is None
        assert not initialized_llm_service._initialized

# Integration-like tests

class TestLLMServiceIntegration:
    """Integration-style tests for LLM service"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_generation(self):
        """Test end-to-end generation flow"""
        service = LLMService()
        
        # Mock the model loading
        with patch('services.llm_service.Path.exists', return_value=True):
            with patch('llama_cpp.Llama') as MockLlama:
                mock_llama_instance = MagicMock()
                mock_llama_instance.return_value = {
                    'choices': [{'text': 'Cannabis recommendation'}],
                    'usage': {'completion_tokens': 20}
                }
                MockLlama.return_value = mock_llama_instance
                
                with patch('langchain.llms.LlamaCpp'):
                    # Create config
                    config = ModelConfig(
                        name='test',
                        path=Path('/tmp/test.gguf'),
                        model_type=ModelType.LLAMA2_7B
                    )
                    service.model_configs['test'] = config
                    
                    # Load and generate
                    await service.load_model('test')
                    
                    result = await service.generate(
                        model='test',
                        prompt="Recommend a strain for anxiety"
                    )
                    
                    assert isinstance(result, GenerationResult)
                    assert result.text == 'Cannabis recommendation'
                    assert result.tokens_generated == 20

# Error handling tests

class TestErrorHandling:
    """Test error handling in LLM service"""
    
    @pytest.mark.asyncio
    async def test_generate_without_initialization(self, mock_llm_service):
        """Test generation without initialization"""
        mock_llm_service._initialized = False
        
        with patch.object(mock_llm_service, 'initialize') as mock_init:
            mock_init.return_value = None
            mock_llm_service.primary_model = 'test'
            mock_llm_service.models['test'] = AsyncMock()
            
            await mock_llm_service.generate(prompt="Test")
            
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_all_models_fail(self, initialized_llm_service):
        """Test when all models fail"""
        primary_model = initialized_llm_service.models['test-model']
        primary_model.generate = AsyncMock(side_effect=Exception("All failed"))
        
        with pytest.raises(Exception, match="All failed"):
            await initialized_llm_service.generate(prompt="Test prompt")
    
    @pytest.mark.asyncio
    async def test_invalid_model_request(self, initialized_llm_service):
        """Test requesting non-existent model"""
        mock_model = initialized_llm_service.models['test-model']
        mock_model.generate = AsyncMock(return_value=GenerationResult(
            text="Default",
            model="test-model",
            tokens_generated=10,
            generation_time=0.5,
            confidence=0.8
        ))
        
        # Request non-existent model, should use primary
        result = await initialized_llm_service.generate(
            model="nonexistent",
            prompt="Test"
        )
        
        assert result.model == "test-model"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])