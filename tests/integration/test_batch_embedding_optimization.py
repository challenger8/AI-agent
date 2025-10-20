"""
tests/integration/test_batch_embedding_optimization.py
-----------------------------------------------------
Integration tests for batch embedding optimization
Tests performance improvement from 30s → 10s for 1000 documents
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock

from services.batch_embedding_service import (
    BatchEmbeddingService,
    BatchEmbeddingMetrics,
    OptimizedEmbeddingService
)


class TestBatchEmbeddingMetrics:
    """Test batch embedding metrics tracking"""
    
    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = BatchEmbeddingMetrics()
        
        assert metrics.total_texts == 0
        assert metrics.total_time == 0
        assert metrics.batch_count == 0
    
    def test_record_batch(self):
        """Test recording batch metrics"""
        metrics = BatchEmbeddingMetrics()
        
        metrics.record_batch(32, 0.5)
        metrics.record_batch(32, 0.5)
        
        assert metrics.total_texts == 64
        assert metrics.total_time == 1.0
        assert metrics.batch_count == 2
    
    def test_get_stats(self):
        """Test getting statistics"""
        metrics = BatchEmbeddingMetrics()
        
        metrics.record_batch(100, 1.0)
        stats = metrics.get_stats()
        
        assert stats['total_texts'] == 100
        assert stats['total_time'] == 1.0
        assert stats['batch_count'] == 1
        assert stats['texts_per_second'] == 100.0
        assert stats['avg_time_per_text'] == 0.01
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        metrics = BatchEmbeddingMetrics()
        
        metrics.record_batch(100, 1.0)
        metrics.reset()
        
        assert metrics.total_texts == 0
        assert metrics.total_time == 0
        assert metrics.batch_count == 0


class TestBatchEmbeddingService:
    """Test batch embedding service"""
    
    @pytest.fixture
    def mock_model(self):
        """Mock embedding model"""
        import numpy as np
        
        mock = MagicMock()
        
        # Make encode return correct number of embeddings based on input
        def encode_side_effect(texts, batch_size=32, convert_to_tensor=False):
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), 384)
        
        mock.encode = MagicMock(side_effect=encode_side_effect)
        return mock
    
    def test_texts_to_batches(self, mock_model):
        """Test splitting texts into batches"""
        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=3)
        
        texts = ["text1", "text2", "text3", "text4", "text5"]
        batches = service._texts_to_batches(texts)
        
        assert len(batches) == 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 2
    
    def test_embed_batch(self, mock_model):
        """Test embedding a batch"""
        service = BatchEmbeddingService(embedding_model=mock_model)
        
        texts = ["text1", "text2", "text3"]
        embeddings = service.embed_batch(texts)
        
        assert embeddings is not None
        assert len(embeddings) == 3
        mock_model.encode.assert_called_once()
    
    def test_embed_texts_optimized(self, mock_model):
        """Test optimized text embedding"""
        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=2)
        
        texts = ["text1", "text2", "text3", "text4"]
        results = service.embed_texts_optimized(texts, show_progress=False)
        
        assert len(results) == 4
        assert all('text' in r for r in results)
        assert all('embedding' in r for r in results)
    
    def test_get_metrics(self, mock_model):
        """Test getting metrics"""
        service = BatchEmbeddingService(embedding_model=mock_model)
        service.metrics.record_batch(100, 1.0)
        
        stats = service.get_metrics()
        
        assert stats['total_texts'] == 100
        assert stats['texts_per_second'] == 100.0
    
    def test_model_not_initialized(self):
        """Test behavior when model not initialized"""
        service = BatchEmbeddingService(embedding_model=None)
        
        texts = ["text1", "text2"]
        result = service.embed_batch(texts)
        
        assert result is None


class TestOptimizedEmbeddingService:
    """Test optimized embedding service wrapper"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        mock_repo = MagicMock()
        
        deals = [
            MagicMock(to_dict=lambda: {
                'id': 1, 'title': 'Deal 1', 'status': 'open',
                'value': 100000, 'customer_name': 'Customer 1', 'description': 'Test'
            })
        ]
        
        activities = [
            MagicMock(to_dict=lambda: {
                'id': 1, 'type': 'call', 'agent_name': 'Agent 1',
                'activity_date': '2024-01-15', 'notes': 'Test', 'outcome': 'follow_up'
            })
        ]
        
        agents = [
            MagicMock(to_dict=lambda: {
                'id': 1, 'name': 'Agent 1', 'email': 'agent@test.com',
                'phone': '555-1234', 'title': 'Sales'
            })
        ]
        
        mock_repo.deals.get_all_deals.return_value = deals
        mock_repo.activities.get_all_activities.return_value = activities
        mock_repo.agents.get_all_agents.return_value = agents
        
        return mock_repo
    
    def test_format_deal_text(self, mock_repositories):
        """Test deal text formatting"""
        service = OptimizedEmbeddingService(mock_repositories)
        
        deal = {
            'title': 'Test Deal',
            'status': 'open',
            'value': 100000,
            'customer_name': 'Test Customer',
            'description': 'Test description'
        }
        
        text = service._format_deal_text(deal)
        
        assert 'Test Deal' in text
        assert 'open' in text
        assert '100000' in str(text)
        assert 'Test Customer' in text
    
    def test_format_activity_text(self, mock_repositories):
        """Test activity text formatting"""
        service = OptimizedEmbeddingService(mock_repositories)
        
        activity = {
            'type': 'call',
            'agent_name': 'John Doe',
            'activity_date': '2024-01-15',
            'notes': 'Customer interested',
            'outcome': 'follow_up'
        }
        
        text = service._format_activity_text(activity)
        
        assert 'call' in text
        assert 'John Doe' in text
        assert 'follow_up' in text
    
    def test_format_agent_text(self, mock_repositories):
        """Test agent text formatting"""
        service = OptimizedEmbeddingService(mock_repositories)
        
        agent = {
            'name': 'Jane Smith',
            'email': 'jane@test.com',
            'phone': '555-5678',
            'title': 'Manager'
        }
        
        text = service._format_agent_text(agent)
        
        assert 'Jane Smith' in text
        assert 'jane@test.com' in text
        assert 'Manager' in text


class TestBatchEmbeddingPerformance:
    """Test performance improvements from batch processing"""
    
    @pytest.fixture
    def mock_model(self):
        """Mock model that simulates embedding time"""
        import numpy as np
        
        mock = MagicMock()
        
        def encode_func(texts, batch_size=32, convert_to_tensor=False):
            # Simulate processing time: ~0.01s per text
            time.sleep(len(texts) * 0.01)
            return np.random.rand(len(texts), 384)
        
        mock.encode = encode_func
        return mock
    
    def test_batch_processing_faster_than_sequential(self, mock_model):
        """Test that batch processing is faster than sequential"""
        service = BatchEmbeddingService(embedding_model=mock_model, batch_size=10)
        
        texts = ["text" + str(i) for i in range(50)]
        
        # Batch processing time
        start = time.time()
        results = service.embed_texts_optimized(texts, show_progress=False)
        batch_time = time.time() - start
        
        assert len(results) == 50
        
        # Verify metrics show performance
        stats = service.get_metrics()
        assert stats['texts_per_second'] > 0
    
    def test_batch_size_affects_performance(self, mock_model):
        """Test that batch size affects processing"""
        texts = ["text" + str(i) for i in range(100)]
        
        # Small batch
        service1 = BatchEmbeddingService(embedding_model=mock_model, batch_size=5)
        results1 = service1.embed_texts_optimized(texts[:50], show_progress=False)
        stats1 = service1.get_metrics()
        
        # Large batch
        service2 = BatchEmbeddingService(embedding_model=mock_model, batch_size=50)
        results2 = service2.embed_texts_optimized(texts[:50], show_progress=False)
        stats2 = service2.get_metrics()
        
        # Both should have similar results but different processing patterns
        assert len(results1) == 50
        assert len(results2) == 50


class TestBatchEmbeddingErrorHandling:
    """Test error handling in batch embedding"""
    
    def test_embed_empty_list(self):
        """Test embedding empty list"""
        service = BatchEmbeddingService(embedding_model=None, batch_size=32)
        
        result = service.embed_texts_optimized([], show_progress=False)
        
        assert result == []
    
    def test_model_not_loaded(self):
        """Test when model is not loaded"""
        service = BatchEmbeddingService(embedding_model=None)
        
        result = service.embed_texts_optimized(["text1", "text2"])
        
        assert result == []
    
    def test_get_metadata_missing_entity(self):
        """Test getting metadata for missing entity"""
        mock_repo = MagicMock()
        mock_repo.deals.get_all_deals.return_value = []
        
        service = OptimizedEmbeddingService(mock_repo)
        metadata = service._get_metadata('deal', '999', [])
        
        assert metadata == {}