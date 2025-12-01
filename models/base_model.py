"""
models/base_model.py
--------------------
Base model mixins for common functionality (DRY principle)
"""

from dataclasses import fields
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, TypeVar, Type

T = TypeVar('T')


class SerializableMixin:
    """
    Mixin for automatic serialization/deserialization.
    
    Works with dataclasses to provide to_dict() and from_dict()
    Handles common type conversions:
    - datetime → ISO string
    - Decimal → float
    - None → None (preserved)
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary with type conversion.
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        
        for field in fields(self):
            value = getattr(self, field.name)
            
            # Handle datetime conversion
            if isinstance(value, datetime):
                result[field.name] = value.isoformat()
            # Handle Decimal conversion
            elif isinstance(value, Decimal):
                result[field.name] = float(value)
            # Handle None
            elif value is None:
                result[field.name] = None
            # Everything else as-is
            else:
                result[field.name] = value
        
        return result
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from dictionary with type conversion.
        
        Args:
            data: Dictionary with model data
            
        Returns:
            Model instance
        """
        # Get field information from dataclass
        field_types = {f.name: f.type for f in fields(cls)}
        converted_data = {}
        
        for key, value in data.items():
            # Skip if field doesn't exist in model
            if key not in field_types:
                continue
            
            # Skip None values
            if value is None:
                converted_data[key] = None
                continue
            
            field_type = field_types[key]
            
            # Handle datetime fields
            if field_type == datetime or 'datetime' in str(field_type).lower():
                if isinstance(value, str):
                    try:
                        converted_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        converted_data[key] = None
                else:
                    converted_data[key] = value
            
            # Handle Decimal fields
            elif field_type == Decimal or 'Decimal' in str(field_type):
                try:
                    converted_data[key] = Decimal(str(value))
                except (ValueError, TypeError):
                    converted_data[key] = None
            
            # Handle boolean fields
            elif field_type == bool or 'bool' in str(field_type).lower():
                if isinstance(value, str):
                    converted_data[key] = value.lower() in ['true', '1', 'yes']
                else:
                    converted_data[key] = bool(value)
            
            # Everything else as-is
            else:
                converted_data[key] = value
        
        return cls(**converted_data)