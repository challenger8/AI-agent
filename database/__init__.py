"""
Database package initialization
"""

# Simply re-export the original database module
from .database import DatabaseManager, create_database_manager

__all__ = ['DatabaseManager', 'create_database_manager']