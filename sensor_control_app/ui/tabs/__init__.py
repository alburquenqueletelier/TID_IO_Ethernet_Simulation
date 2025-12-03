"""
UI tabs package.

This package provides the main tab components for the application:
- DashboardTab: Main dashboard with MC registration and PET management
- CommandsTab: Command configuration and sending interface
"""

from .dashboard_tab import DashboardTab
from .commands_tab import CommandsTab

__all__ = [
    'DashboardTab',
    'CommandsTab',
]
