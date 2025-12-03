"""
Core module for PET scan control application.

This module contains the business logic, protocol definitions,
data models, and state management.
"""

from .protocol import (
    COMMANDS,
    COMMAND_CONFIGS,
    get_command_byte,
    get_command_states,
    is_valid_command,
    is_valid_config,
    get_all_command_names,
    get_all_config_names,
)

from .models import (
    MicroController,
    PETAssociation,
    Macro,
    CommandInfo,
)

from .state_manager import StateManager

__all__ = [
    # Protocol
    'COMMANDS',
    'COMMAND_CONFIGS',
    'get_command_byte',
    'get_command_states',
    'is_valid_command',
    'is_valid_config',
    'get_all_command_names',
    'get_all_config_names',
    # Models
    'MicroController',
    'PETAssociation',
    'Macro',
    'CommandInfo',
    # State Management
    'StateManager',
]
