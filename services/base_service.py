"""
services/base_service.py
------------------------
Base service class for common functionality
"""

from abc import ABC
from typing import Any, Dict, Optional

from utils.logging_config import get_logger
from utils.exceptions import ServiceError

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, repositories=None):
        """
        Initialize base service
        
        Args:
            repositories: Database repositories instance
        """
        self.repositories = repositories
        self.logger = get_logger(self.__class__.__name__)
        self._cache = {}
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present in data
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ServiceError: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise ServiceError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self._cache.get(key)
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self._cache[key] = value
    
    def _clear_cache(self) -> None:
        """Clear all cached values"""
        self._cache.clear()
    
    def _safe_execute(self, operation_name: str, operation_func, *args, **kwargs) -> Any:
        """
        Safely execute an operation with logging and error handling
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the operation
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            self.logger.debug(f"Starting operation: {operation_name}")
            result = operation_func(*args, **kwargs)
            self.logger.debug(f"Operation completed: {operation_name}")
            return result
        except Exception as e:
            self.logger.error(f"Operation failed: {operation_name} - {str(e)}")
            raise ServiceError(f"{operation_name} failed: {str(e)}")
