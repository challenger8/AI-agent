"""
utils/model_utils.py
--------------------
Utility functions for model object handling.
Centralizes common patterns like to_dict conversion.
"""

from typing import Any, Dict


def ensure_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert model object to dict if needed.

    Handles objects with to_dict() method and plain dicts uniformly.

    Args:
        obj: Model object or dict

    Returns:
        Dictionary representation

    Example:
        >>> deal = DealModel(id=1, title="Test")
        >>> deal_dict = ensure_dict(deal)  # Calls deal.to_dict()
        >>> deal_dict = ensure_dict({'id': 1})  # Returns as-is
    """
    if obj is None:
        return {}
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if isinstance(obj, dict):
        return obj
    return {}


def get_id_from_entity(entity: Any) -> str:
    """
    Extract ID from entity (model object or dict).

    Args:
        entity: Model object or dict with 'id' field

    Returns:
        String ID
    """
    entity_dict = ensure_dict(entity)
    return str(entity_dict.get('id', ''))
