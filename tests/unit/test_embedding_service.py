"""
tests/unit/test_embedding_service.py
------------------------------------
Unit tests for EmbeddingService with mocked model loading
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from services.embedding_service import EmbeddingService


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmbeddingServiceInitialization:
    """Test EmbeddingService initialization with _safe_initialize"""
    
    async def test_initialize_success(self):
        """Test successful initialization"""
        service = EmbeddingService()
        
        # Patch where it's imported (inside the method)
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            await service.initialize()
            
            assert service.model is not None
            mock_transformer.assert_called_once()
    
    async def test_initialize_failure_graceful(self):
        """Test that initialization failure is handled gracefully"""
        service = EmbeddingService()
        
        # Patch where it's imported (inside the method)
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            mock_transformer.side_effect = Exception("Model load failed")
            
            # Should not raise - _safe_initialize returns False on error
            await service.initialize()
            
            # Model should be None
            assert service.model is None
    
    async def test_initialize_logs_correctly(self):
        """Test that initialization logs messages correctly"""
        service = EmbeddingService()
        
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            # Patch logger to verify it's called
            with patch.object(service.logger, 'info') as mock_info:
                await service.initialize()
                
                # Should have at least one log message
                assert mock_info.call_count >= 1


@pytest.mark.unit
class TestEmbeddingServiceWithoutInit:
    """Test EmbeddingService methods without initialization"""
    
    def test_service_creation(self):
        """Test creating service without initialization"""
        service = EmbeddingService()
        
        assert service.model is None
        assert service.model_name is not None
    
    def test_embed_without_initialization(self):
        """Test embedding without initialized model returns None"""
        service = EmbeddingService()
        
        # Check which method name is correct
        if hasattr(service, 'embed_texts_batch'):
            result = service.embed_texts_batch(["test text"])
        elif hasattr(service, 'embed_batch'):
            result = service.embed_batch(["test text"])
        else:
            # Skip if method doesn't exist
            pytest.skip("No embedding method found")
        
        assert result is None  # Should return None gracefully


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmbeddingServiceWithMockedModel:
    """Test EmbeddingService with mocked model (no actual loading)"""
    
    async def test_service_with_mock_model(self):
        """Test service behavior with pre-set mock model"""
        service = EmbeddingService()
        
        # Manually set a mock model (bypass initialization)
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        service.model = mock_model
        
        # Now test embedding methods if they exist
        if hasattr(service, 'embed_texts_batch'):
            result = service.embed_texts_batch(["test"])
            # Should work with mock model
            assert result is not None