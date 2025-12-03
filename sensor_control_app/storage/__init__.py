"""
Storage package for PET scan control application.

This package handles all persistence-related functionality including:
- JSON database management
- Macro CRUD operations
"""

from .database import Database
from .macro_manager import MacroManager

__all__ = [
    'Database',
    'MacroManager',
]
