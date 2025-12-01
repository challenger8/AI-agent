"""
tests/unit/test_base_model.py
-----------------------------
Tests for base model serialization mixin
"""

import pytest
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

from models.base_model import SerializableMixin


@dataclass
class SampleModel(SerializableMixin):
    """Test model using the mixin"""
    id: str
    name: str
    created_at: datetime
    price: Decimal
    is_active: bool
    optional_field: str = None


class TestSerializableMixin:
    """Test SerializableMixin functionality"""
    
    def test_to_dict_basic(self):
        """Test basic to_dict conversion"""
        model = SampleModel(
            id='test-123',
            name='Test Item',
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            price=Decimal('99.99'),
            is_active=True
        )
        
        result = model.to_dict()
        
        assert isinstance(result, dict)
        assert result['id'] == 'test-123'
        assert result['name'] == 'Test Item'
        assert result['created_at'] == '2024-01-15T10:30:00'
        assert result['price'] == 99.99
        assert result['is_active'] is True
    
    def test_to_dict_with_none(self):
        """Test to_dict handles None values"""
        model = SampleModel(
            id='test-123',
            name='Test',
            created_at=datetime.now(),
            price=Decimal('10.00'),
            is_active=False,
            optional_field=None
        )
        
        result = model.to_dict()
        
        assert result['optional_field'] is None
    
    def test_from_dict_basic(self):
        """Test basic from_dict conversion"""
        data = {
            'id': 'test-456',
            'name': 'Test Item',
            'created_at': '2024-01-15T10:30:00',
            'price': '149.99',
            'is_active': True
        }
        
        model = SampleModel.from_dict(data)
        
        assert model.id == 'test-456'
        assert model.name == 'Test Item'
        assert isinstance(model.created_at, datetime)
        assert model.created_at.year == 2024
        assert isinstance(model.price, Decimal)
        assert model.price == Decimal('149.99')
        assert model.is_active is True
    
    def test_from_dict_boolean_string(self):
        """Test from_dict converts boolean strings"""
        data = {
            'id': 'test',
            'name': 'Test',
            'created_at': '2024-01-01T00:00:00',
            'price': '10.00',
            'is_active': 'true'  # String boolean
        }
        
        model = SampleModel.from_dict(data)
        
        assert model.is_active is True
    
    def test_round_trip(self):
        """Test to_dict → from_dict round trip"""
        original = SampleModel(
            id='test-789',
            name='Round Trip Test',
            created_at=datetime(2024, 6, 1, 14, 30, 0),
            price=Decimal('299.99'),
            is_active=False,
            optional_field='extra'
        )
        
        # Convert to dict
        data = original.to_dict()
        
        # Convert back to model
        restored = SampleModel.from_dict(data)
        
        # Should match original
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.created_at == original.created_at
        assert restored.price == original.price
        assert restored.is_active == original.is_active
        assert restored.optional_field == original.optional_field
    
    def test_from_dict_ignores_extra_fields(self):
        """Test from_dict ignores fields not in model"""
        data = {
            'id': 'test',
            'name': 'Test',
            'created_at': '2024-01-01T00:00:00',
            'price': '10.00',
            'is_active': True,
            'extra_field': 'should be ignored'  # Not in model
        }
        
        # Should not raise error
        model = SampleModel.from_dict(data)
        
        assert model.id == 'test'
        assert not hasattr(model, 'extra_field')
    
    def test_from_dict_handles_invalid_datetime(self):
        """Test from_dict handles invalid datetime gracefully"""
        data = {
            'id': 'test',
            'name': 'Test',
            'created_at': 'invalid-date',  # Invalid
            'price': '10.00',
            'is_active': True
        }
        
        model = SampleModel.from_dict(data)
        
        assert model.created_at is None  # Should be None on error