"""
tests/unit/test_batch_embedding_service.py
-------------------------------------------
Unit tests for BatchEmbeddingService and OptimizedEmbeddingService
Tests batch processing, metrics tracking, and optimized embedding workflows
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from services.batch_embedding_service import (
    BatchEmbeddingMetrics,
    BatchEmbeddingService,
    OptimizedEmbeddingService
)
from utils.exceptions import ServiceError


class TestBatchEmbeddingMetrics:
    """Test BatchEmbeddingMetrics class"""

    def test_init(self):
        """Test metrics initialization"""
        metrics = BatchEmbeddingMetrics()

        assert metrics.total_texts == 0
        assert metrics.total_time == 0
        assert metrics.batch_count == 0

    def test_record_batch(self):
        """Test recording batch metrics"""
        metrics = BatchEmbeddingMetrics()

        metrics.record_batch(text_count=10, processing_time=0.5)
        metrics.record_batch(text_count=15, processing_time=0.7)

        assert metrics.total_texts == 25
        assert metrics.total_time == 1.2
        assert metrics.batch_count == 2

    def test_get_stats(self):
        """Test getting statistics"""
        metrics = BatchEmbeddingMetrics()
        metrics.record_batch(100, 5.0)
        metrics.record_batch(50, 2.5)

        stats = metrics.get_stats()

        assert stats['total_texts'] == 150
        assert stats['total_time'] == 7.5
        assert stats['batch_count'] == 2
        assert stats['avg_time_per_text'] == 0.05  # 7.5 / 150
        assert stats['texts_per_second'] == 20.0  # 150 / 7.5
        assert stats['avg_batch_size'] == 75.0  # 150 / 2

    def test_get_stats_with_zero_values(self):
        """Test get_stats with no data (avoid division by zero)"""
        metrics = BatchEmbeddingMetrics()

        stats = metrics.get_stats()

        assert stats['avg_time_per_text'] == 0
        assert stats['texts_per_second'] == 0
        assert stats['avg_batch_size'] == 0

    def test_reset(self):
        """Test resetting metrics"""
        metrics = BatchEmbeddingMetrics()
        metrics.record_batch(50, 2.0)

        metrics.reset()

        assert metrics.total_texts == 0
        assert metrics.total_time == 0
        assert metrics.batch_count == 0


class TestBatchEmbeddingServiceInitialization:
    """Test BatchEmbeddingService initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        service = BatchEmbeddingService()

        assert service.model is None
        assert service.batch_size == 32
        assert service.show_progress is True
        assert isinstance(service.metrics, BatchEmbeddingMetrics)

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(
            embedding_model=mock_model,
            batch_size=64,
            show_progress=False
        )

        assert service.model is mock_model
        assert service.batch_size == 64
        assert service.show_progress is False

    @pytest.mark.asyncio
    async def test_initialize_model_success(self):
        """Test successful model initialization"""
        service = BatchEmbeddingService()

        with patch('services.batch_embedding_service.SentenceTransformer') as mock_st, \
             patch('services.batch_embedding_service.ModelLoader') as mock_loader:
            mock_loader.check_already_loaded.return_value = False
            mock_model = MagicMock()
            mock_st.return_value = mock_model

            result = await service.initialize_model()

            assert result is True
            assert service.model is mock_model
            mock_st.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_model_already_loaded(self):
        """Test model initialization when model already loaded"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(embedding_model=mock_model)

        with patch('services.batch_embedding_service.ModelLoader') as mock_loader:
            mock_loader.check_already_loaded.return_value = True

            result = await service.initialize_model()

            assert result is True

    @pytest.mark.asyncio
    async def test_initialize_model_failure(self):
        """Test model initialization failure"""
        service = BatchEmbeddingService()

        with patch('services.batch_embedding_service.SentenceTransformer', side_effect=Exception("Load error")), \
             patch('services.batch_embedding_service.ModelLoader') as mock_loader:
            mock_loader.check_already_loaded.return_value = False

            with pytest.raises(ServiceError):
                await service.initialize_model()


class TestBatchOperations:
    """Test batch processing operations"""

    def test_texts_to_batches(self):
        """Test splitting texts into batches"""
        service = BatchEmbeddingService(batch_size=3)
        texts = ['text1', 'text2', 'text3', 'text4', 'text5']

        batches = service._texts_to_batches(texts)

        assert len(batches) == 2
        assert batches[0] == ['text1', 'text2', 'text3']
        assert batches[1] == ['text4', 'text5']

    def test_texts_to_batches_exact_fit(self):
        """Test batching when texts fit exactly"""
        service = BatchEmbeddingService(batch_size=5)
        texts = ['t1', 't2', 't3', 't4', 't5']

        batches = service._texts_to_batches(texts)

        assert len(batches) == 1
        assert batches[0] == texts

    def test_texts_to_batches_empty(self):
        """Test batching with empty list"""
        service = BatchEmbeddingService()
        batches = service._texts_to_batches([])

        assert batches == []

    def test_embed_batch_success(self):
        """Test successful batch embedding"""
        mock_model = MagicMock()
        mock_embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_model.encode.return_value = mock_embeddings

        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=2)
        texts = ['text1', 'text2']

        result = service.embed_batch(texts)

        assert result == mock_embeddings
        mock_model.encode.assert_called_once_with(
            texts,
            convert_to_tensor=False,
            batch_size=2
        )

    def test_embed_batch_with_tensor_conversion(self):
        """Test embed_batch converts tensors to lists"""
        mock_model = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.tolist.return_value = [[0.1], [0.2]]
        mock_model.encode.return_value = mock_tensor

        service = BatchEmbeddingService(embedding_model=mock_model)

        result = service.embed_batch(['text'])

        assert result == [[0.1], [0.2]]
        mock_tensor.tolist.assert_called_once()

    def test_embed_batch_no_model(self):
        """Test embed_batch when model not initialized"""
        service = BatchEmbeddingService()

        result = service.embed_batch(['text'])

        assert result is None

    def test_embed_batch_error(self):
        """Test embed_batch handles errors"""
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Encoding error")

        service = BatchEmbeddingService(embedding_model=mock_model)

        result = service.embed_batch(['text'])

        assert result is None


class TestOptimizedEmbedding:
    """Test optimized embedding operations"""

    def test_embed_texts_optimized_success(self):
        """Test successful optimized text embedding"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=2)

        texts = ['text1', 'text2', 'text3']
        mock_embeddings_batch1 = [[0.1, 0.2], [0.3, 0.4]]
        mock_embeddings_batch2 = [[0.5, 0.6]]

        service.embed_batch = MagicMock(side_effect=[
            mock_embeddings_batch1,
            mock_embeddings_batch2
        ])

        result = service.embed_texts_optimized(texts, show_progress=False)

        assert len(result) == 3
        assert result[0] == {'text': 'text1', 'embedding': [0.1, 0.2]}
        assert result[1] == {'text': 'text2', 'embedding': [0.3, 0.4]}
        assert result[2] == {'text': 'text3', 'embedding': [0.5, 0.6]}

    def test_embed_texts_optimized_no_model(self):
        """Test embed_texts_optimized when model not initialized"""
        service = BatchEmbeddingService()

        result = service.embed_texts_optimized(['text'])

        assert result == []

    def test_embed_texts_optimized_with_progress(self):
        """Test embed_texts_optimized shows progress messages"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=2)
        service.embed_batch = MagicMock(return_value=[[0.1]])

        with patch.object(service.logger, 'info') as mock_log:
            result = service.embed_texts_optimized(['text'], show_progress=True)

            # Verify progress messages were logged
            assert mock_log.call_count >= 2  # Start and complete messages
            assert any('Starting batch embedding' in str(call) for call in mock_log.call_args_list)

    def test_embed_texts_optimized_records_metrics(self):
        """Test that embed_texts_optimized records metrics"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(embedding_model=mock_model)
        service.embed_batch = MagicMock(return_value=[[0.1], [0.2]])

        service.embed_texts_optimized(['text1', 'text2'], show_progress=False)

        stats = service.get_metrics()
        assert stats['total_texts'] == 2
        assert stats['batch_count'] == 1

    def test_embed_texts_optimized_handles_none_batch(self):
        """Test embed_texts_optimized skips None batches"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=1)
        service.embed_batch = MagicMock(side_effect=[None, [[0.1]]])

        result = service.embed_texts_optimized(['text1', 'text2'], show_progress=False)

        # Only second batch succeeded
        assert len(result) == 1

    def test_embed_texts_optimized_error(self):
        """Test embed_texts_optimized raises ServiceError on failure"""
        mock_model = MagicMock()
        service = BatchEmbeddingService(embedding_model=mock_model)
        service.embed_batch = MagicMock(side_effect=Exception("Batch error"))

        with pytest.raises(ServiceError):
            service.embed_texts_optimized(['text'])


class TestMetricsManagement:
    """Test metrics management"""

    def test_get_metrics(self):
        """Test getting metrics"""
        service = BatchEmbeddingService()
        service.metrics.record_batch(10, 1.0)

        metrics = service.get_metrics()

        assert metrics['total_texts'] == 10
        assert metrics['total_time'] == 1.0

    def test_reset_metrics(self):
        """Test resetting metrics"""
        service = BatchEmbeddingService()
        service.metrics.record_batch(10, 1.0)

        service.reset_metrics()
        metrics = service.get_metrics()

        assert metrics['total_texts'] == 0
        assert metrics['total_time'] == 0


class TestOptimizedEmbeddingService:
    """Test OptimizedEmbeddingService wrapper"""

    def test_init(self):
        """Test initialization"""
        mock_repos = MagicMock()
        service = OptimizedEmbeddingService(repositories=mock_repos, batch_size=64)

        assert service.repositories is mock_repos
        assert service.batch_size == 64
        assert service.model is None
        assert service.batch_service is None

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful initialization"""
        service = OptimizedEmbeddingService()

        with patch('services.batch_embedding_service.BatchEmbeddingService') as mock_batch:
            mock_batch_instance = AsyncMock()
            mock_batch_instance.initialize_model = AsyncMock()
            mock_batch_instance.model = MagicMock()
            mock_batch.return_value = mock_batch_instance

            result = await service.initialize()

            assert result is True
            assert service.batch_service is mock_batch_instance
            mock_batch_instance.initialize_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test initialization failure"""
        service = OptimizedEmbeddingService()

        with patch('services.batch_embedding_service.BatchEmbeddingService', side_effect=Exception("Init error")):
            result = await service.initialize()

            assert result is False

    def test_format_deal_text(self):
        """Test formatting deal text delegates to EmbeddingTextFormatter"""
        service = OptimizedEmbeddingService()
        deal = {'title': 'Test Deal', 'value': 1000}

        with patch('services.batch_embedding_service.EmbeddingTextFormatter.format_deal') as mock_format:
            mock_format.return_value = "Formatted deal text"

            result = service._format_deal_text(deal)

            assert result == "Formatted deal text"
            mock_format.assert_called_once_with(deal)

    def test_format_activity_text(self):
        """Test formatting activity text delegates to EmbeddingTextFormatter"""
        service = OptimizedEmbeddingService()
        activity = {'title': 'Call', 'note': 'Follow up'}

        with patch('services.batch_embedding_service.EmbeddingTextFormatter.format_activity') as mock_format:
            mock_format.return_value = "Formatted activity"

            result = service._format_activity_text(activity)

            assert result == "Formatted activity"
            mock_format.assert_called_once_with(activity)

    def test_format_agent_text(self):
        """Test formatting agent text delegates to EmbeddingTextFormatter"""
        service = OptimizedEmbeddingService()
        agent = {'name': 'John Doe', 'title': 'Sales'}

        with patch('services.batch_embedding_service.EmbeddingTextFormatter.format_agent') as mock_format:
            mock_format.return_value = "Formatted agent"

            result = service._format_agent_text(agent)

            assert result == "Formatted agent"
            mock_format.assert_called_once_with(agent)

    def test_get_metadata_for_deal(self):
        """Test getting metadata for deal entity"""
        service = OptimizedEmbeddingService()
        deal_mock = MagicMock()
        deal_mock.to_dict.return_value = {
            'id': '123',
            'title': 'Test Deal',
            'status': 'open',
            'value': 1000
        }

        metadata = service._get_metadata('deal', '123', [deal_mock])

        assert metadata == {'title': 'Test Deal', 'status': 'open', 'value': 1000}

    def test_get_metadata_for_activity(self):
        """Test getting metadata for activity entity"""
        service = OptimizedEmbeddingService()
        activity_mock = MagicMock()
        activity_mock.to_dict.return_value = {
            'id': '456',
            'type': 'call',
            'agent_name': 'John'
        }

        metadata = service._get_metadata('activity', '456', [activity_mock])

        assert metadata == {'type': 'call', 'agent': 'John'}

    def test_get_metadata_for_agent(self):
        """Test getting metadata for agent entity"""
        service = OptimizedEmbeddingService()
        agent_mock = MagicMock()
        agent_mock.to_dict.return_value = {
            'id': '789',
            'name': 'Jane Doe',
            'title': 'Manager'
        }

        metadata = service._get_metadata('agent', '789', [agent_mock])

        assert metadata == {'name': 'Jane Doe', 'title': 'Manager'}

    def test_get_metadata_not_found(self):
        """Test getting metadata when entity not found"""
        service = OptimizedEmbeddingService()

        metadata = service._get_metadata('deal', 'nonexistent', [])

        assert metadata == {}

    def test_embed_with_metadata_empty_list(self):
        """Test embed_with_metadata with empty list"""
        service = OptimizedEmbeddingService()
        service.batch_service = MagicMock()

        result = service._embed_with_metadata([], 'deal', [])

        assert result == []

    def test_embed_with_metadata_success(self):
        """Test successful embedding with metadata"""
        service = OptimizedEmbeddingService()
        mock_batch_service = MagicMock()
        service.batch_service = mock_batch_service

        texts_with_ids = [('d1', 'Deal 1 text'), ('d2', 'Deal 2 text')]
        mock_batch_service.embed_texts_optimized.return_value = [
            {'text': 'Deal 1 text', 'embedding': [0.1, 0.2]},
            {'text': 'Deal 2 text', 'embedding': [0.3, 0.4]}
        ]

        deal1 = MagicMock()
        deal1.to_dict.return_value = {'id': 'd1', 'title': 'Deal 1', 'status': 'open', 'value': 100}
        deal2 = MagicMock()
        deal2.to_dict.return_value = {'id': 'd2', 'title': 'Deal 2', 'status': 'won', 'value': 200}

        result = service._embed_with_metadata(texts_with_ids, 'deal', [deal1, deal2])

        assert len(result) == 2
        assert result[0]['id'] == 'd1'
        assert result[0]['type'] == 'deal'
        assert result[0]['embedding'] == [0.1, 0.2]
        assert result[0]['metadata']['title'] == 'Deal 1'
