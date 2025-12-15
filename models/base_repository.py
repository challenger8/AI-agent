# models/base_repository.py (CREATE THIS FILE)
"""
Base repository with common query patterns
DRY principle: Write once, use everywhere!
"""

from typing import List, Optional, TypeVar, Generic, Callable, Any, Dict, Tuple
from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
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

    # =========================================
    # Generic Create/Update Operations (DRY!)
    # =========================================

    def _get_model_field_mapping(self, model: T) -> Dict[str, Tuple[str, Any]]:
        """
        Extract field names and values from dataclass model.

        Returns:
            Dict mapping field_name -> (db_column_name, value)
        """
        if not is_dataclass(model):
            raise ValueError(f"Model {type(model)} is not a dataclass")

        field_map = {}
        for field in fields(model):
            value = getattr(model, field.name)
            # Convert field name to snake_case for DB column
            db_column = self._to_snake_case(field.name)
            field_map[field.name] = (db_column, value)

        return field_map

    def _to_snake_case(self, name: str) -> str:
        """
        Convert PascalCase/camelCase to snake_case.

        Examples:
            RegisterTime -> register_time
            dealid -> dealid
            Id -> id
        """
        # Handle already snake_case
        if '_' in name and name.islower():
            return name

        # Special case: single lowercase word
        if name.islower():
            return name

        # Convert PascalCase/camelCase
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _prepare_value_for_db(self, value: Any) -> Any:
        """
        Convert Python values to database-compatible format.

        Args:
            value: Python value

        Returns:
            Database-compatible value
        """
        if value is None:
            return None
        elif isinstance(value, datetime):
            return value
        elif isinstance(value, Decimal):
            return value
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float, str)):
            return value
        else:
            # For complex types, convert to string
            return str(value)

    def create_generic(self, model: T, exclude_fields: List[str] = None) -> Optional[str]:
        """
        Generic create method - works for any dataclass model.

        Eliminates need for custom create methods in every repository!

        Args:
            model: Dataclass model instance
            exclude_fields: Fields to exclude from INSERT (e.g., auto-generated)

        Returns:
            ID of created record, or None on error

        Example:
            deal = Deal(Id="123", Title="New Deal", ...)
            deal_id = repository.create_generic(deal)
        """
        exclude_fields = exclude_fields or []

        try:
            field_map = self._get_model_field_mapping(model)

            # Filter out excluded fields
            insert_fields = {
                k: v for k, v in field_map.items()
                if k not in exclude_fields
            }

            if not insert_fields:
                self.logger.error("No fields to insert")
                return None

            # Build INSERT query
            column_names = [v[0] for v in insert_fields.values()]
            placeholders = ['%s'] * len(column_names)
            values = [self._prepare_value_for_db(v[1]) for v in insert_fields.values()]

            query = f"""
                INSERT INTO {self.table_name}
                ({', '.join(column_names)})
                VALUES ({', '.join(placeholders)})
            """

            if self._execute_write(query, tuple(values), error_context=f"creating {self.table_name}"):
                # Return ID field value
                id_field = getattr(model, 'Id', None) or getattr(model, 'id', None)
                return str(id_field) if id_field else None

            return None

        except Exception as e:
            self.logger.error(f"Error in generic create: {e}")
            return None

    def update_generic(
        self,
        model: T,
        id_field: str = 'id',
        exclude_fields: List[str] = None
    ) -> bool:
        """
        Generic update method - works for any dataclass model.

        Args:
            model: Dataclass model instance with updated values
            id_field: Name of ID field (default: 'id')
            exclude_fields: Fields to exclude from UPDATE

        Returns:
            True on success, False on error

        Example:
            deal.Title = "Updated Title"
            success = repository.update_generic(deal, id_field='Id')
        """
        exclude_fields = exclude_fields or []
        exclude_fields.append(id_field)  # Never update ID field

        try:
            field_map = self._get_model_field_mapping(model)

            # Get ID value
            if id_field not in field_map:
                self.logger.error(f"ID field '{id_field}' not found in model")
                return False

            id_value = field_map[id_field][1]
            if id_value is None:
                self.logger.error("ID value is None, cannot update")
                return False

            # Filter fields to update
            update_fields = {
                k: v for k, v in field_map.items()
                if k not in exclude_fields
            }

            if not update_fields:
                self.logger.warning("No fields to update")
                return True

            # Build UPDATE query
            set_clauses = [f"{v[0]} = %s" for v in update_fields.values()]
            values = [self._prepare_value_for_db(v[1]) for v in update_fields.values()]
            values.append(id_value)  # Add ID for WHERE clause

            id_column = self._to_snake_case(id_field)
            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE {id_column} = %s
            """

            return self._execute_write(
                query,
                tuple(values),
                error_context=f"updating {self.table_name} {id_value}"
            )

        except Exception as e:
            self.logger.error(f"Error in generic update: {e}")
            return False