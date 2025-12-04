"""
User interface package.

This package provides the main UI components:
- app: Main application window
- widgets: Reusable UI widgets
- tabs: Tab components (Dashboard, Commands)
- dialogs: Dialog windows (future)
"""

from .app import McControlApp

__all__ = [
    'McControlApp',
]
