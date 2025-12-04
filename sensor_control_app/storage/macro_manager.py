"""
Macro manager module for handling command macros.

This module provides functionality to create, save, load, and delete
command macros (both universal and per-microcontroller).
"""

from typing import Dict, List, Optional
from ..core.models import Macro, MicroController
from .database import Database


class MacroManager:
    """
    Manages command macros for the application.

    Handles both universal macros (shared across all microcontrollers)
    and microcontroller-specific macros.
    """

    def __init__(self, database: Database):
        """
        Initialize the MacroManager.

        Args:
            database: Database instance for persistence
        """
        self.database = database

    def save_universal_macro(self, macro: Macro) -> bool:
        """
        Save a universal macro (shared across all microcontrollers).

        Args:
            macro: Macro object to save

        Returns:
            bool: True if save was successful, False otherwise
        """
        # Get existing macros
        macros = self.database.get("macros", {})

        # Add or update macro
        macros[macro.name] = macro.to_dict()

        # Save back to database
        return self.database.set("macros", macros, auto_save=True)

    def save_mc_macro(self, macro: Macro, mc_mac_source: str) -> bool:
        """
        Save a microcontroller-specific macro.

        Args:
            macro: Macro object to save
            mc_mac_source: Source MAC address of the microcontroller

        Returns:
            bool: True if save was successful, False otherwise
        """
        # Get registered microcontrollers
        mc_registered = self.database.get("mc_registered", {})

        if mc_mac_source not in mc_registered:
            return False

        # Get MC data
        mc_data = mc_registered[mc_mac_source]

        # Initialize macros dict if it doesn't exist
        if "macros" not in mc_data:
            mc_data["macros"] = {}

        # Add or update macro
        mc_data["macros"][macro.name] = macro.to_dict()

        # Save back to database
        mc_registered[mc_mac_source] = mc_data
        return self.database.set("mc_registered", mc_registered, auto_save=True)

    def load_universal_macro(self, name: str) -> Optional[Macro]:
        """
        Load a universal macro by name.

        Args:
            name: Name of the macro to load

        Returns:
            Optional[Macro]: Macro object if found, None otherwise
        """
        macros = self.database.get("macros", {})

        if name not in macros:
            return None

        macro_dict = macros[name]
        return Macro(
            name=name,
            command_configs=macro_dict.get("command_configs", {}),
            last_state=macro_dict.get("last_state", {})
        )

    def load_mc_macro(self, name: str, mc_mac_source: str) -> Optional[Macro]:
        """
        Load a microcontroller-specific macro.

        Args:
            name: Name of the macro to load
            mc_mac_source: Source MAC address of the microcontroller

        Returns:
            Optional[Macro]: Macro object if found, None otherwise
        """
        mc_registered = self.database.get("mc_registered", {})

        if mc_mac_source not in mc_registered:
            return None

        mc_data = mc_registered[mc_mac_source]
        macros = mc_data.get("macros", {})

        if name not in macros:
            return None

        macro_dict = macros[name]
        return Macro(
            name=name,
            command_configs=macro_dict.get("command_configs", {}),
            last_state=macro_dict.get("last_state", {})
        )

    def delete_universal_macro(self, name: str) -> bool:
        """
        Delete a universal macro.

        Args:
            name: Name of the macro to delete

        Returns:
            bool: True if macro was deleted, False if not found
        """
        macros = self.database.get("macros", {})

        if name not in macros:
            return False

        del macros[name]
        return self.database.set("macros", macros, auto_save=True)

    def delete_mc_macro(self, name: str, mc_mac_source: str) -> bool:
        """
        Delete a microcontroller-specific macro.

        Args:
            name: Name of the macro to delete
            mc_mac_source: Source MAC address of the microcontroller

        Returns:
            bool: True if macro was deleted, False if not found
        """
        mc_registered = self.database.get("mc_registered", {})

        if mc_mac_source not in mc_registered:
            return False

        mc_data = mc_registered[mc_mac_source]
        macros = mc_data.get("macros", {})

        if name not in macros:
            return False

        del macros[name]
        mc_data["macros"] = macros
        mc_registered[mc_mac_source] = mc_data

        return self.database.set("mc_registered", mc_registered, auto_save=True)

    def list_universal_macros(self) -> List[str]:
        """
        List all universal macro names.

        Returns:
            List[str]: List of macro names
        """
        macros = self.database.get("macros", {})
        return list(macros.keys())

    def list_mc_macros(self, mc_mac_source: str) -> List[str]:
        """
        List all microcontroller-specific macro names.

        Args:
            mc_mac_source: Source MAC address of the microcontroller

        Returns:
            List[str]: List of macro names, empty list if MC not found
        """
        mc_registered = self.database.get("mc_registered", {})

        if mc_mac_source not in mc_registered:
            return []

        mc_data = mc_registered[mc_mac_source]
        macros = mc_data.get("macros", {})
        return list(macros.keys())

    def get_all_universal_macros(self) -> Dict[str, Macro]:
        """
        Get all universal macros.

        Returns:
            Dict[str, Macro]: Dictionary of macro name to Macro object
        """
        macros_dict = self.database.get("macros", {})
        result = {}

        for name, macro_data in macros_dict.items():
            result[name] = Macro(
                name=name,
                command_configs=macro_data.get("command_configs", {}),
                last_state=macro_data.get("last_state", {})
            )

        return result

    def get_all_mc_macros(self, mc_mac_source: str) -> Dict[str, Macro]:
        """
        Get all microcontroller-specific macros.

        Args:
            mc_mac_source: Source MAC address of the microcontroller

        Returns:
            Dict[str, Macro]: Dictionary of macro name to Macro object
        """
        mc_registered = self.database.get("mc_registered", {})

        if mc_mac_source not in mc_registered:
            return {}

        mc_data = mc_registered[mc_mac_source]
        macros_dict = mc_data.get("macros", {})
        result = {}

        for name, macro_data in macros_dict.items():
            result[name] = Macro(
                name=name,
                command_configs=macro_data.get("command_configs", {}),
                last_state=macro_data.get("last_state", {})
            )

        return result

    def macro_exists(self, name: str, mc_mac_source: Optional[str] = None) -> bool:
        """
        Check if a macro exists.

        Args:
            name: Name of the macro
            mc_mac_source: If provided, checks MC-specific macros.
                          If None, checks universal macros.

        Returns:
            bool: True if macro exists, False otherwise
        """
        if mc_mac_source is None:
            # Check universal macros
            macros = self.database.get("macros", {})
            return name in macros
        else:
            # Check MC-specific macros
            mc_registered = self.database.get("mc_registered", {})
            if mc_mac_source not in mc_registered:
                return False

            mc_data = mc_registered[mc_mac_source]
            macros = mc_data.get("macros", {})
            return name in macros

    def rename_macro(
        self,
        old_name: str,
        new_name: str,
        mc_mac_source: Optional[str] = None
    ) -> bool:
        """
        Rename a macro.

        Args:
            old_name: Current name of the macro
            new_name: New name for the macro
            mc_mac_source: If provided, renames MC-specific macro.
                          If None, renames universal macro.

        Returns:
            bool: True if rename was successful, False otherwise
        """
        # Check if new name already exists
        if self.macro_exists(new_name, mc_mac_source):
            return False

        # Load the macro
        if mc_mac_source is None:
            macro = self.load_universal_macro(old_name)
            if not macro:
                return False

            # Save with new name
            macro.name = new_name
            self.save_universal_macro(macro)

            # Delete old macro
            self.delete_universal_macro(old_name)

        else:
            macro = self.load_mc_macro(old_name, mc_mac_source)
            if not macro:
                return False

            # Save with new name
            macro.name = new_name
            self.save_mc_macro(macro, mc_mac_source)

            # Delete old macro
            self.delete_mc_macro(old_name, mc_mac_source)

        return True
