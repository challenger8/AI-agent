"""
tests/unit/test_base_repository.py
----------------------------------
Tests for BaseRepository functionality
"""

import pytest
from unittest.mock import Mock, MagicMock
from models.base_repository import BaseRepository
from models.deal_model import Deal


class MockDealRepository(BaseRepository[Deal]):
    """Mock repository for testing BaseRepository"""
    
    @property
    def table_name(self) -> str:
        return "deals"
    
    def _map_row_to_model(self, row: dict) -> Deal:
        """Simple mapping for test"""
        return Deal(
            Id=row.get('id'),
            Title=row.get('title', ''),
            Status=row.get('status', '')
        )


class TestBaseRepository:
    """Test BaseRepository generic methods"""
    
    def test_get_all_success(self):
        """Test get_all returns list of models"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {'id': '1', 'title': 'Deal 1', 'status': 'open'},
            {'id': '2', 'title': 'Deal 2', 'status': 'won'}
        ]
        
        repo = MockDealRepository(mock_db)
        results = repo.get_all()
        
        assert len(results) == 2
        assert results[0].Id == '1'
        assert results[1].Id == '2'
        mock_db.execute_query.assert_called_once()
    
    def test_get_all_with_order(self):
        """Test get_all with ORDER BY"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        repo = MockDealRepository(mock_db)
        repo.get_all(order_by="title DESC")
        
        call_args = mock_db.execute_query.call_args[0][0]
        assert "ORDER BY title DESC" in call_args
    
    def test_get_by_id_found(self):
        """Test get_by_id returns model"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {'id': 'test-123', 'title': 'Test Deal', 'status': 'open'}
        ]
        
        repo = MockDealRepository(mock_db)
        result = repo.get_by_id('test-123')
        
        assert result is not None
        assert result.Id == 'test-123'
        assert result.Title == 'Test Deal'
    
    def test_get_by_id_not_found(self):
        """Test get_by_id returns None when not found"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []
        
        repo = MockDealRepository(mock_db)
        result = repo.get_by_id('nonexistent')
        
        assert result is None
    
    def test_get_by_field(self):
        """Test get_by_field filters correctly"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {'id': '1', 'title': 'Deal 1', 'status': 'open'},
            {'id': '2', 'title': 'Deal 2', 'status': 'open'}
        ]
        
        repo = MockDealRepository(mock_db)
        results = repo.get_by_field('status', 'open')
        
        assert len(results) == 2
        call_args = mock_db.execute_query.call_args[0]
        assert 'WHERE status = %s' in call_args[0]
        assert call_args[1] == ('open',)
    
    def test_delete_by_id_success(self):
        """Test delete_by_id executes correctly"""
        mock_db = Mock()
        mock_db.execute_query.return_value = None
        
        repo = MockDealRepository(mock_db)
        result = repo.delete_by_id('test-123')
        
        assert result is True
        mock_db.execute_query.assert_called_once()
    
    def test_error_handling_returns_empty_list(self):
        """Test error handling returns empty list"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("Database error")
        
        repo = MockDealRepository(mock_db)
        results = repo.get_all()
        
        assert results == []  # Should return empty list, not crash
    
    def test_error_handling_returns_none(self):
        """Test error handling returns None for single queries"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("Database error")
        
        repo = MockDealRepository(mock_db)
        result = repo.get_by_id('test-123')
        
        assert result is None  # Should return None, not crash