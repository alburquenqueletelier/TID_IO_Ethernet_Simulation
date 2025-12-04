"""
Tests for the database module.

Tests JSON-based database functionality including
loading, saving, and CRUD operations.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from sensor_control_app.storage.database import Database


class TestDatabase(unittest.TestCase):
    """Tests for Database class."""

    def setUp(self):
        """Set up test fixtures with temporary database file."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.db_path = self.temp_file.name
        self.db = Database(self.db_path)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_initialization(self):
        """Test Database initialization."""
        self.assertEqual(str(self.db.db_path), self.db_path)
        self.assertEqual(self.db.data, {})

    def test_initialization_default_path(self):
        """Test Database initialization with default path."""
        db = Database()
        self.assertEqual(str(db.db_path), Database.DEFAULT_DB_FILE)

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        # Remove the temp file to simulate non-existent
        os.unlink(self.db_path)

        data = self.db.load()

        self.assertEqual(data, {})
        self.assertEqual(self.db.data, {})

    def test_load_empty_file(self):
        """Test loading from empty file."""
        # Create empty file
        with open(self.db_path, 'w') as f:
            f.write('')

        data = self.db.load()

        self.assertEqual(data, {})

    def test_load_corrupted_file(self):
        """Test loading from corrupted JSON file."""
        with open(self.db_path, 'w') as f:
            f.write('{ invalid json }')

        data = self.db.load()

        self.assertEqual(data, {})

    def test_load_valid_file(self):
        """Test loading from valid JSON file."""
        test_data = {
            "mc_registered": {"aa:bb:cc:dd:ee:ff": {"label": "MC1"}},
            "macros": {"macro1": {"commands": []}}
        }

        with open(self.db_path, 'w') as f:
            json.dump(test_data, f)

        data = self.db.load()

        self.assertEqual(data, test_data)
        self.assertEqual(self.db.data, test_data)

    def test_save_new_file(self):
        """Test saving to new file."""
        test_data = {"key1": "value1", "key2": 123}
        self.db.data = test_data

        result = self.db.save()

        self.assertTrue(result)

        # Verify file contents
        with open(self.db_path, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded, test_data)

    def test_save_with_data_parameter(self):
        """Test saving with explicit data parameter."""
        test_data = {"key": "value"}

        result = self.db.save(test_data)

        self.assertTrue(result)
        self.assertEqual(self.db.data, test_data)

        # Verify file contents
        with open(self.db_path, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded, test_data)

    def test_save_unicode(self):
        """Test saving with Unicode characters."""
        test_data = {"label": "Señal española", "emoji": "🔥"}

        result = self.db.save(test_data)

        self.assertTrue(result)

        # Verify file contents preserve Unicode
        with open(self.db_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["label"], "Señal española")
        self.assertEqual(loaded["emoji"], "🔥")

    def test_get_existing_key(self):
        """Test getting existing key."""
        self.db.data = {"key1": "value1"}

        result = self.db.get("key1")

        self.assertEqual(result, "value1")

    def test_get_nonexistent_key(self):
        """Test getting non-existent key with default."""
        result = self.db.get("nonexistent", default="default_value")

        self.assertEqual(result, "default_value")

    def test_get_nonexistent_key_no_default(self):
        """Test getting non-existent key without default."""
        result = self.db.get("nonexistent")

        self.assertIsNone(result)

    def test_set_with_auto_save(self):
        """Test setting value with auto-save."""
        result = self.db.set("key1", "value1", auto_save=True)

        self.assertTrue(result)
        self.assertEqual(self.db.data["key1"], "value1")

        # Verify it was saved to file
        with open(self.db_path, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["key1"], "value1")

    def test_set_without_auto_save(self):
        """Test setting value without auto-save."""
        result = self.db.set("key1", "value1", auto_save=False)

        self.assertTrue(result)
        self.assertEqual(self.db.data["key1"], "value1")

        # Verify it was NOT saved to file
        with open(self.db_path, 'r') as f:
            content = f.read()

        # File should be empty or not contain the key
        self.assertEqual(content, "")

    def test_delete_existing_key(self):
        """Test deleting existing key."""
        self.db.data = {"key1": "value1", "key2": "value2"}
        self.db.save()

        result = self.db.delete("key1", auto_save=True)

        self.assertTrue(result)
        self.assertNotIn("key1", self.db.data)
        self.assertIn("key2", self.db.data)

        # Verify deletion was saved
        with open(self.db_path, 'r') as f:
            loaded = json.load(f)

        self.assertNotIn("key1", loaded)

    def test_delete_nonexistent_key(self):
        """Test deleting non-existent key."""
        result = self.db.delete("nonexistent")

        self.assertFalse(result)

    def test_exists_true(self):
        """Test exists returns True for existing key."""
        self.db.data = {"key1": "value1"}

        self.assertTrue(self.db.exists("key1"))

    def test_exists_false(self):
        """Test exists returns False for non-existent key."""
        self.assertFalse(self.db.exists("nonexistent"))

    def test_clear_with_auto_save(self):
        """Test clearing database with auto-save."""
        self.db.data = {"key1": "value1", "key2": "value2"}
        self.db.save()

        result = self.db.clear(auto_save=True)

        self.assertTrue(result)
        self.assertEqual(self.db.data, {})

        # Verify cleared data was saved
        with open(self.db_path, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded, {})

    def test_get_all(self):
        """Test getting all data."""
        test_data = {"key1": "value1", "key2": "value2"}
        self.db.data = test_data

        result = self.db.get_all()

        self.assertEqual(result, test_data)
        # Should return a copy, not the original
        self.assertIsNot(result, self.db.data)

    def test_update_single_key(self):
        """Test updating single key."""
        self.db.data = {"key1": "value1"}

        result = self.db.update({"key2": "value2"}, auto_save=False)

        self.assertTrue(result)
        self.assertEqual(self.db.data, {"key1": "value1", "key2": "value2"})

    def test_update_multiple_keys(self):
        """Test updating multiple keys."""
        updates = {"key1": "new_value1", "key2": "value2", "key3": "value3"}

        result = self.db.update(updates, auto_save=False)

        self.assertTrue(result)
        self.assertEqual(self.db.data, updates)

    def test_update_with_auto_save(self):
        """Test updating with auto-save."""
        result = self.db.update({"key1": "value1"}, auto_save=True)

        self.assertTrue(result)

        # Verify saved to file
        with open(self.db_path, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["key1"], "value1")

    def test_backup_existing_file(self):
        """Test backing up existing database."""
        test_data = {"key": "value"}
        self.db.save(test_data)

        backup_path = self.db_path + ".test_backup"

        try:
            result = self.db.backup(backup_path)

            self.assertTrue(result)
            self.assertTrue(os.path.exists(backup_path))

            # Verify backup contents
            with open(backup_path, 'r') as f:
                loaded = json.load(f)

            self.assertEqual(loaded, test_data)

        finally:
            if os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_backup_default_path(self):
        """Test backup with default path."""
        test_data = {"key": "value"}
        self.db.save(test_data)

        default_backup = self.db_path + ".backup"

        try:
            result = self.db.backup()

            self.assertTrue(result)
            self.assertTrue(os.path.exists(default_backup))

        finally:
            if os.path.exists(default_backup):
                os.unlink(default_backup)

    def test_backup_nonexistent_file(self):
        """Test backing up non-existent database."""
        os.unlink(self.db_path)

        result = self.db.backup()

        self.assertFalse(result)

    def test_repr(self):
        """Test string representation."""
        self.db.data = {"key1": "value1", "key2": "value2"}

        repr_str = repr(self.db)

        self.assertIn("Database", repr_str)
        self.assertIn(self.db_path, repr_str)
        self.assertIn("key1", repr_str)
        self.assertIn("key2", repr_str)

    def test_complex_data_structure(self):
        """Test saving and loading complex nested structures."""
        complex_data = {
            "mc_registered": {
                "aa:bb:cc:dd:ee:ff": {
                    "mac_destiny": "11:22:33:44:55:66",
                    "interface_destiny": "eth0",
                    "label": "MC1",
                    "command_configs": {
                        "cmd1": {"enabled": True, "state": "ON"}
                    },
                    "last_state": {},
                    "macros": {
                        "macro1": {
                            "command_configs": {},
                            "last_state": {}
                        }
                    }
                }
            },
            "macros": {},
            "pet_associations": {
                "1": {"mc": None, "enabled": False}
            }
        }

        self.db.save(complex_data)

        # Create new DB instance and load
        new_db = Database(self.db_path)
        loaded = new_db.load()

        self.assertEqual(loaded, complex_data)


if __name__ == '__main__':
    unittest.main()
