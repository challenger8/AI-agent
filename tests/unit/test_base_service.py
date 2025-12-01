"""
tests/unit/test_base_service.py
-------------------------------
Tests for BaseService functionality
"""

import pytest
from unittest.mock import AsyncMock, Mock
from services.base_service import BaseService
from utils.exceptions import ServiceError


class MockService(BaseService):
    """Mock service for testing"""
    
    def __init__(self):
        super().__init__(repositories=None)
        self.initialized = False
    
    async def _do_init_success(self):
        """Mock successful initialization"""
        self.initialized = True
    
    async def _do_init_failure(self):
        """Mock failed initialization"""
        raise ValueError("Initialization failed")


@pytest.mark.asyncio
class TestBaseServiceInitialize:
    """Test _safe_initialize helper"""
    
    async def test_safe_initialize_success(self):
        """Test successful initialization"""
        service = MockService()
        
        result = await service._safe_initialize(
            service._do_init_success,
            service_name="Test"
        )
        
        assert result is True
        assert service.initialized is True
    
    async def test_safe_initialize_failure(self):
        """Test failed initialization returns False"""
        service = MockService()
        
        result = await service._safe_initialize(
            service._do_init_failure,
            service_name="Test"
        )
        
        assert result is False  # Should not raise
        assert service.initialized is False
    
    async def test_safe_initialize_logs_error(self):
        """Test that errors are logged"""
        service = MockService()
        
        # Patch logger to verify it's called
        service.logger.error = Mock()
        
        await service._safe_initialize(
            service._do_init_failure,
            service_name="Test"
        )
        
        # Verify error was logged
        service.logger.error.assert_called_once()
        assert "initialization failed" in str(service.logger.error.call_args)