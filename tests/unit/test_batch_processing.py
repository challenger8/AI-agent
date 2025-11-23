"""
tests/unit/test_batch_processing.py
-----------------------------------
Unit tests for batch processing
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from services.moe.moe_orchestrator import MoEOrchestrator
from services.moe.expert_ensemble import EnsembleResult


class TestBatchProcessing:
    """Tests for batch processing functionality"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_orchestrator_has_batch_method(self, orchestrator):
        """Test orchestrator has batch processing method"""
        assert hasattr(orchestrator, 'process_batch')
        assert hasattr(orchestrator, 'process_batch_sync')

    @pytest.mark.asyncio
    async def test_batch_process_single_query(self, orchestrator):
        """Test batch processing with single query"""
        queries = [{'query': 'test query'}]

        with patch.object(orchestrator, 'process', new_callable=AsyncMock) as mock_process:
            mock_result = MagicMock(spec=EnsembleResult)
            mock_process.return_value = mock_result

            results = await orchestrator.process_batch(queries)

            assert len(results) == 1
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_process_multiple_queries(self, orchestrator):
        """Test batch processing with multiple queries"""
        queries = [
            {'query': 'query 1'},
            {'query': 'query 2'},
            {'query': 'query 3'}
        ]

        with patch.object(orchestrator, 'process', new_callable=AsyncMock) as mock_process:
            mock_result = MagicMock(spec=EnsembleResult)
            mock_process.return_value = mock_result

            results = await orchestrator.process_batch(queries)

            assert len(results) == 3
            assert mock_process.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_process_with_context(self, orchestrator):
        """Test batch processing with context"""
        queries = [
            {'query': 'deal query', 'context': {'deal_id': 123}},
            {'query': 'sentiment query', 'context': {'type': 'feedback'}}
        ]

        with patch.object(orchestrator, 'process', new_callable=AsyncMock) as mock_process:
            mock_result = MagicMock(spec=EnsembleResult)
            mock_process.return_value = mock_result

            results = await orchestrator.process_batch(queries)

            assert len(results) == 2
            # Check contexts were passed
            calls = mock_process.call_args_list
            assert calls[0][0][1] == {'deal_id': 123}
            assert calls[1][0][1] == {'type': 'feedback'}

    @pytest.mark.asyncio
    async def test_batch_process_sequential(self, orchestrator):
        """Test sequential batch processing"""
        queries = [
            {'query': 'query 1'},
            {'query': 'query 2'}
        ]

        with patch.object(orchestrator, 'process', new_callable=AsyncMock) as mock_process:
            mock_result = MagicMock(spec=EnsembleResult)
            mock_process.return_value = mock_result

            results = await orchestrator.process_batch(queries, parallel=False)

            assert len(results) == 2

    def test_batch_process_sync(self, orchestrator):
        """Test synchronous batch processing"""
        queries = [{'query': 'test query'}]

        with patch.object(orchestrator, 'process', new_callable=AsyncMock) as mock_process:
            mock_result = MagicMock(spec=EnsembleResult)
            mock_process.return_value = mock_result

            results = orchestrator.process_batch_sync(queries)

            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_batch_handles_exceptions(self, orchestrator):
        """Test batch processing handles exceptions"""
        queries = [
            {'query': 'good query'},
            {'query': 'bad query'},
        ]

        async def mock_process(query, context):
            if 'bad' in query:
                raise Exception("Test error")
            return MagicMock(spec=EnsembleResult)

        with patch.object(orchestrator, 'process', side_effect=mock_process):
            results = await orchestrator.process_batch(queries)

            assert len(results) == 2
            # Second result should be error result
            assert results[1].combined_data.get('error') == "Test error"

    @pytest.mark.asyncio
    async def test_batch_empty_queries(self, orchestrator):
        """Test batch processing with empty queries list"""
        queries = []

        results = await orchestrator.process_batch(queries)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_batch_preserves_order(self, orchestrator):
        """Test batch processing preserves order"""
        queries = [
            {'query': f'query {i}'}
            for i in range(5)
        ]

        call_order = []

        async def mock_process(query, context):
            call_order.append(query)
            result = MagicMock(spec=EnsembleResult)
            result.query = query
            return result

        with patch.object(orchestrator, 'process', side_effect=mock_process):
            results = await orchestrator.process_batch(queries, parallel=False)

            # Results should be in same order as input
            for i, result in enumerate(results):
                assert result.query == f'query {i}'


class TestBatchProcessingIntegration:
    """Integration tests for batch processing"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_real_batch_processing(self, orchestrator):
        """Test real batch processing (no mocks)"""
        queries = [
            {'query': 'analyze deal'},
            {'query': 'sentiment check'},
        ]

        results = orchestrator.process_batch_sync(queries)

        assert len(results) == 2
        for result in results:
            assert hasattr(result, 'combined_data')
            assert hasattr(result, 'combined_confidence')
