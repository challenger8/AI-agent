"""
config/entity_types.py
----------------------
Centralized entity type constants for consistent usage across the codebase.
Eliminates magic strings and provides single source of truth.
"""

from typing import List


class EntityTypes:
    """
    Entity type constants for CRM entities.

    Usage:
        from config.entity_types import EntityTypes

        # Instead of: collection_names = ['deals', 'activities', 'agents']
        collection_names = EntityTypes.ALL

        # Instead of: if entity_type == 'deals':
        if entity_type == EntityTypes.DEALS:
    """
    DEALS = 'deals'
    ACTIVITIES = 'activities'
    AGENTS = 'agents'

    # All entity types (useful for iteration)
    ALL: List[str] = [DEALS, ACTIVITIES, AGENTS]

    # Singular forms (for result formatting)
    SINGULAR = {
        DEALS: 'deal',
        ACTIVITIES: 'activity',
        AGENTS: 'agent'
    }

    @classmethod
    def get_singular(cls, entity_type: str) -> str:
        """Get singular form of entity type."""
        return cls.SINGULAR.get(entity_type, entity_type.rstrip('s'))

    @classmethod
    def is_valid(cls, entity_type: str) -> bool:
        """Check if entity type is valid."""
        return entity_type in cls.ALL
