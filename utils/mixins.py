"""
utils/mixins.py
---------------
Reusable mixins for common functionality

DRY: Eliminates duplicate code patterns across base classes
"""

from typing import Any, Optional
import logging


class CacheableMixin:
    """
    Mixin for cache operations.

    DRY: Eliminates duplicate _get_from_cache, _set_cache, _clear_cache
    methods that were duplicated in BaseService and BaseExpert.

    CONSOLIDATION: Replaces 2 identical implementations with 1 mixin.

    Usage:
        class MyService(CacheableMixin, OtherBase):
            def __init__(self):
                super().__init__()
                # _cache dict is automatically available
    """

    def __init__(self, *args, **kwargs):
        """Initialize cache storage"""
        super().__init__(*args, **kwargs)
        if not hasattr(self, '_cache'):
            self._cache = {}

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        return self._cache.get(key)

    def _set_cache(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        self._cache[key] = value

    def _clear_cache(self) -> None:
        """Clear all cached values"""
        if hasattr(self, '_cache'):
            self._cache.clear()

    def _has_cache(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not hasattr(self, '_cache'):
            return False
        return key in self._cache


class LoggableMixin:
    """
    Mixin for logging functionality.

    Provides consistent logger setup across classes.

    Usage:
        class MyService(LoggableMixin):
            def __init__(self):
                super().__init__()
                self.logger.info("Service initialized")
    """

    def __init__(self, *args, **kwargs):
        """Initialize logger"""
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'logger'):
            from utils.logging_config import get_logger
            self.logger = get_logger(self.__class__.__name__)


class ValidatableMixin:
    """
    Mixin for common validation operations.

    Provides field validation helpers.
    """

    def _validate_required_fields(self, data: dict, required_fields: list) -> None:
        """
        Validate that required fields are present.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [
            field for field in required_fields
            if field not in data or data[field] is None
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_field_types(self, data: dict, field_types: dict) -> None:
        """
        Validate field types.

        Args:
            data: Data dictionary
            field_types: Dict mapping field names to expected types

        Raises:
            TypeError: If field types don't match
        """
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    raise TypeError(
                        f"Field '{field}' must be {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
