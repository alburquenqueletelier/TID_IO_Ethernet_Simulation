"""
Database module for JSON-based persistence.

This module handles loading and saving application data to a JSON file,
including microcontroller registrations, macros, and PET associations.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Database:
    """
    Manages JSON-based database for application persistence.

    This class handles reading from and writing to a JSON file that stores
    all application state including microcontrollers, macros, and PET associations.
    """

    DEFAULT_DB_FILE = "db.json"

    def __init__(self, db_path: str = None):
        """
        Initialize the Database.

        Args:
            db_path: Path to the database JSON file. If None, uses DEFAULT_DB_FILE
        """
        self.db_path = Path(db_path if db_path else self.DEFAULT_DB_FILE)
        self.data: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Load data from the JSON database file.

        If the file doesn't exist or is empty/corrupted, returns an empty dictionary.
        The loaded data is stored in self.data and also returned.

        Returns:
            Dict[str, Any]: The loaded database contents

        Structure of returned data:
            {
                "mc_registered": {
                    "mac_source": {
                        "mac_destiny": str,
                        "interface_destiny": str,
                        "label": str,
                        "command_configs": {},
                        "last_state": {},
                        "macros": {}
                    }
                },
                "macros": {
                    "macro_name": {
                        "command_configs": {},
                        "last_state": {}
                    }
                },
                "pet_associations": {
                    "1": {"mc": "mac_address", "enabled": bool},
                    ...
                    "10": {"mc": "mac_address", "enabled": bool}
                },
                "selected_pet_macros": {
                    "1": ["macro1", "macro2"],
                    ...
                }
            }
        """
        if not self.db_path.exists():
            print(f"Database file '{self.db_path}' does not exist. Starting with empty database.")
            self.data = {}
            return self.data

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                print(f"Database file '{self.db_path}' loaded successfully.")
                return self.data

        except json.JSONDecodeError:
            print(f"Warning: '{self.db_path}' is empty or corrupted. Starting with empty database.")
            self.data = {}
            return self.data

        except Exception as e:
            print(f"Error loading database from '{self.db_path}': {e}")
            self.data = {}
            return self.data

    def save(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save data to the JSON database file.

        Args:
            data: Data to save. If None, saves self.data

        Returns:
            bool: True if save was successful, False otherwise
        """
        if data is not None:
            self.data = data

        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            return True

        except Exception as e:
            print(f"Error saving database to '{self.db_path}': {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the database.

        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """
        Set a value in the database.

        Args:
            key: Key to set
            value: Value to store
            auto_save: If True, automatically save to disk after setting

        Returns:
            bool: True if successful (and saved if auto_save=True), False otherwise
        """
        self.data[key] = value

        if auto_save:
            return self.save()

        return True

    def delete(self, key: str, auto_save: bool = True) -> bool:
        """
        Delete a key from the database.

        Args:
            key: Key to delete
            auto_save: If True, automatically save to disk after deleting

        Returns:
            bool: True if key existed and was deleted, False otherwise
        """
        if key in self.data:
            del self.data[key]
            if auto_save:
                return self.save()
            return True

        return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the database.

        Args:
            key: Key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        return key in self.data

    def clear(self, auto_save: bool = True) -> bool:
        """
        Clear all data from the database.

        Args:
            auto_save: If True, automatically save to disk after clearing

        Returns:
            bool: True if successful, False otherwise
        """
        self.data = {}

        if auto_save:
            return self.save()

        return True

    def get_all(self) -> Dict[str, Any]:
        """
        Get all data from the database.

        Returns:
            Dict[str, Any]: Complete database contents
        """
        return self.data.copy()

    def update(self, updates: Dict[str, Any], auto_save: bool = True) -> bool:
        """
        Update multiple keys at once.

        Args:
            updates: Dictionary of key-value pairs to update
            auto_save: If True, automatically save to disk after updating

        Returns:
            bool: True if successful, False otherwise
        """
        self.data.update(updates)

        if auto_save:
            return self.save()

        return True

    def backup(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the database file.

        Args:
            backup_path: Path for the backup file. If None, appends .backup to db_path

        Returns:
            bool: True if backup was successful, False otherwise
        """
        if backup_path is None:
            backup_path = str(self.db_path) + ".backup"

        try:
            if self.db_path.exists():
                import shutil
                shutil.copy2(self.db_path, backup_path)
                print(f"Database backed up to '{backup_path}'")
                return True
            else:
                print(f"Cannot backup: database file '{self.db_path}' does not exist")
                return False

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def __repr__(self) -> str:
        """String representation of the Database."""
        return f"Database(path='{self.db_path}', keys={list(self.data.keys())})"
