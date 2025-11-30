# models/base_repository.py (CREATE THIS FILE)
"""
Base repository with common query patterns
DRY principle: Write once, use everywhere!
"""

from typing import List, Optional, TypeVar, Generic, Callable, Any
from abc import ABC, abstractmethod
import logging

T = TypeVar('T')  # Generic type for model


class BaseRepository(Generic[T], ABC):
    """
    Base repository with common CRUD patterns.
    
    Subclasses must implement:
    - _get_table_name(): Return table name
    - _map_row_to_model(): Convert DB row to model
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the database table name"""
        pass
    
    @abstractmethod
    def _map_row_to_model(self, row: dict) -> T:
        """Convert database row to model instance"""
        pass
    
    # =========================================
    # Generic Query Methods
    # =========================================
    
    def _execute_query_list(
        self, 
        query: str, 
        params: tuple = None,
        error_context: str = "fetching records"
    ) -> List[T]:
        """
        Execute query and return list of models.
        
        Args:
            query: SQL query
            params: Query parameters
            error_context: Context for error message
            
        Returns:
            List of model instances (empty list on error)
        """
        try:
            results = self.db.execute_query(query, params)
            return [self._map_row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error {error_context}: {e}")
            return []
    
    def _execute_query_single(
        self,
        query: str,
        params: tuple = None,
        error_context: str = "fetching record"
    ) -> Optional[T]:
        """
        Execute query and return single model or None.
        
        Args:
            query: SQL query
            params: Query parameters
            error_context: Context for error message
            
        Returns:
            Model instance or None
        """
        try:
            results = self.db.execute_query(query, params)
            if results:
                return self._map_row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error {error_context}: {e}")
            return None
    
    def _execute_write(
        self,
        query: str,
        params: tuple,
        error_context: str = "writing record"
    ) -> bool:
        """
        Execute write operation (INSERT/UPDATE/DELETE).
        
        Returns:
            True on success, False on error
        """
        try:
            self.db.execute_query(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error {error_context}: {e}")
            return False
    
    # =========================================
    # Common CRUD Operations
    # =========================================
    
    def get_all(self, order_by: str = None) -> List[T]:
        """Get all records from table"""
        query = f"SELECT * FROM {self.table_name}"
        if order_by:
            query += f" ORDER BY {order_by}"
        return self._execute_query_list(query, error_context=f"fetching all {self.table_name}")
    
    def get_by_id(self, record_id: str) -> Optional[T]:
        """Get single record by ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        return self._execute_query_single(
            query, 
            (record_id,), 
            error_context=f"fetching {self.table_name} {record_id}"
        )
    
    def get_by_field(self, field: str, value: Any, order_by: str = None) -> List[T]:
        """Get records matching a field value"""
        query = f"SELECT * FROM {self.table_name} WHERE {field} = %s"
        if order_by:
            query += f" ORDER BY {order_by}"
        return self._execute_query_list(
            query,
            (value,),
            error_context=f"fetching {self.table_name} by {field}"
        )
    
    def delete_by_id(self, record_id: str) -> bool:
        """Delete record by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        return self._execute_write(
            query,
            (record_id,),
            error_context=f"deleting {self.table_name} {record_id}"
        )