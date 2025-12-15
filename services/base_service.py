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

    def _handle_error(
        self,
        operation: str,
        error: Exception,
        return_dict: bool = True,
        raise_error: bool = False
    ) -> Any:
        """
        DRY: Consolidated error handling for all services.

        Eliminates duplicate try-except-log-return patterns across services.

        Args:
            operation: Operation description (e.g., "analyzing sentiment")
            error: Exception that occurred
            return_dict: If True, return {"error": str(error)} dict
            raise_error: If True, raise ServiceError instead of returning

        Returns:
            Error dict if return_dict=True, None otherwise

        Raises:
            ServiceError: If raise_error=True

        Usage:
            try:
                result = do_something()
            except Exception as e:
                return self._handle_error("doing something", e)
        """
        self.logger.error(f"Error {operation}: {error}")

        if raise_error:
            raise ServiceError(f"{operation} failed: {error}")

        if return_dict:
            return {"error": str(error)}

        return None
    async def _safe_initialize(
        self,
        init_func,
        service_name: str = None,
        *args,
        raise_on_error: bool = False,
        **kwargs
    ) -> bool:
        """
        Safely execute async initialization with logging and error handling.
        
        DRY helper to eliminate duplicate try-except-logging in initialize() methods.
        
        Args:
            init_func: Async function to execute for initialization
            service_name: Name of service (defaults to class name)
            *args: Positional arguments to pass to init_func
            raise_on_error: Whether to raise ServiceError on failure (default: False)
            **kwargs: Keyword arguments to pass to init_func
            
        Returns:
            True on success, False on failure (if raise_on_error=False)
            
        Raises:
            ServiceError: If initialization fails and raise_on_error=True
            
        Usage:
            async def initialize(self):
                await self._safe_initialize(
                    self._do_initialize,
                    service_name="Embedding"
                )
            
            async def _do_initialize(self):
                # Actual initialization code here
                self.model = load_model()
        """
        service_name = service_name or self.__class__.__name__
        
        try:
            self.logger.info(f"Initializing {service_name}...")
            await init_func(*args, **kwargs)
            self.logger.info(f"{service_name} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"{service_name} initialization failed: {e}")
            if raise_on_error:
                raise ServiceError(f"{service_name} initialization failed: {e}")
            return False