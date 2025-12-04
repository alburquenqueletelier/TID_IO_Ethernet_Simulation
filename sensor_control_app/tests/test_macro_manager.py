"""
Tests for the macro_manager module.

Tests macro management functionality including saving, loading,
and deleting both universal and microcontroller-specific macros.
"""

import unittest
from unittest.mock import MagicMock
from sensor_control_app.storage.macro_manager import MacroManager
from sensor_control_app.storage.database import Database
from sensor_control_app.core.models import Macro


class TestMacroManager(unittest.TestCase):
    """Tests for MacroManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock database
        self.mock_db = MagicMock(spec=Database)
        self.mock_db.get.return_value = {}
        self.mock_db.set.return_value = True

        self.manager = MacroManager(self.mock_db)

    def test_initialization(self):
        """Test MacroManager initialization."""
        self.assertIsNotNone(self.manager.database)

    def test_save_universal_macro(self):
        """Test saving a universal macro."""
        macro = Macro(
            name="test_macro",
            command_configs={"cmd1": {"enabled": True}},
            last_state={"cmd1": "ON"}
        )

        self.mock_db.get.return_value = {}

        result = self.manager.save_universal_macro(macro)

        self.assertTrue(result)
        self.mock_db.set.assert_called_once()

        # Verify the data structure
        call_args = self.mock_db.set.call_args
        self.assertEqual(call_args[0][0], "macros")
        self.assertIn("test_macro", call_args[0][1])

    def test_save_universal_macro_overwrites_existing(self):
        """Test that saving overwrites existing macro."""
        existing_macros = {
            "test_macro": {
                "command_configs": {"old": True},
                "last_state": {}
            }
        }
        self.mock_db.get.return_value = existing_macros

        new_macro = Macro(
            name="test_macro",
            command_configs={"new": True},
            last_state={}
        )

        result = self.manager.save_universal_macro(new_macro)

        self.assertTrue(result)

        # Verify new data overwrites old
        call_args = self.mock_db.set.call_args[0][1]
        self.assertEqual(call_args["test_macro"]["command_configs"], {"new": True})

    def test_save_mc_macro(self):
        """Test saving a microcontroller-specific macro."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "mac_destiny": "11:22:33:44:55:66",
                "interface_destiny": "eth0",
                "label": "MC1",
                "macros": {}
            }
        }
        self.mock_db.get.return_value = mc_registered

        macro = Macro(
            name="mc_macro",
            command_configs={"cmd1": {"enabled": True}},
            last_state={}
        )

        result = self.manager.save_mc_macro(macro, mc_mac)

        self.assertTrue(result)
        self.mock_db.set.assert_called_once_with("mc_registered", mc_registered, auto_save=True)

    def test_save_mc_macro_nonexistent_mc(self):
        """Test saving macro for non-existent MC returns False."""
        self.mock_db.get.return_value = {}

        macro = Macro(name="test", command_configs={}, last_state={})

        result = self.manager.save_mc_macro(macro, "nonexistent:mac")

        self.assertFalse(result)

    def test_save_mc_macro_initializes_macros_dict(self):
        """Test that saving MC macro initializes macros dict if missing."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "mac_destiny": "11:22:33:44:55:66",
                "label": "MC1"
                # No "macros" key
            }
        }
        self.mock_db.get.return_value = mc_registered

        macro = Macro(name="test", command_configs={}, last_state={})

        result = self.manager.save_mc_macro(macro, mc_mac)

        self.assertTrue(result)

        # Verify macros dict was created
        saved_data = self.mock_db.set.call_args[0][1]
        self.assertIn("macros", saved_data[mc_mac])

    def test_load_universal_macro(self):
        """Test loading a universal macro."""
        macros = {
            "test_macro": {
                "command_configs": {"cmd1": {"enabled": True}},
                "last_state": {"cmd1": "ON"}
            }
        }
        self.mock_db.get.return_value = macros

        result = self.manager.load_universal_macro("test_macro")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test_macro")
        self.assertEqual(result.command_configs, {"cmd1": {"enabled": True}})
        self.assertEqual(result.last_state, {"cmd1": "ON"})

    def test_load_universal_macro_not_found(self):
        """Test loading non-existent universal macro."""
        self.mock_db.get.return_value = {}

        result = self.manager.load_universal_macro("nonexistent")

        self.assertIsNone(result)

    def test_load_mc_macro(self):
        """Test loading a microcontroller-specific macro."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "macros": {
                    "mc_macro": {
                        "command_configs": {"cmd": True},
                        "last_state": {}
                    }
                }
            }
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.load_mc_macro("mc_macro", mc_mac)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "mc_macro")
        self.assertEqual(result.command_configs, {"cmd": True})

    def test_load_mc_macro_mc_not_found(self):
        """Test loading macro for non-existent MC."""
        self.mock_db.get.return_value = {}

        result = self.manager.load_mc_macro("test", "nonexistent:mac")

        self.assertIsNone(result)

    def test_load_mc_macro_not_found(self):
        """Test loading non-existent MC macro."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "macros": {}
            }
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.load_mc_macro("nonexistent", mc_mac)

        self.assertIsNone(result)

    def test_delete_universal_macro(self):
        """Test deleting a universal macro."""
        macros = {
            "macro1": {"command_configs": {}, "last_state": {}},
            "macro2": {"command_configs": {}, "last_state": {}}
        }
        self.mock_db.get.return_value = macros

        result = self.manager.delete_universal_macro("macro1")

        self.assertTrue(result)

        # Verify macro1 was removed
        saved_macros = self.mock_db.set.call_args[0][1]
        self.assertNotIn("macro1", saved_macros)
        self.assertIn("macro2", saved_macros)

    def test_delete_universal_macro_not_found(self):
        """Test deleting non-existent universal macro."""
        self.mock_db.get.return_value = {}

        result = self.manager.delete_universal_macro("nonexistent")

        self.assertFalse(result)

    def test_delete_mc_macro(self):
        """Test deleting a microcontroller-specific macro."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "macros": {
                    "macro1": {"command_configs": {}},
                    "macro2": {"command_configs": {}}
                }
            }
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.delete_mc_macro("macro1", mc_mac)

        self.assertTrue(result)

        # Verify macro1 was removed
        saved_data = self.mock_db.set.call_args[0][1]
        self.assertNotIn("macro1", saved_data[mc_mac]["macros"])
        self.assertIn("macro2", saved_data[mc_mac]["macros"])

    def test_delete_mc_macro_mc_not_found(self):
        """Test deleting macro for non-existent MC."""
        self.mock_db.get.return_value = {}

        result = self.manager.delete_mc_macro("test", "nonexistent:mac")

        self.assertFalse(result)

    def test_delete_mc_macro_not_found(self):
        """Test deleting non-existent MC macro."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {"macros": {}}
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.delete_mc_macro("nonexistent", mc_mac)

        self.assertFalse(result)

    def test_list_universal_macros(self):
        """Test listing all universal macros."""
        macros = {
            "macro1": {},
            "macro2": {},
            "macro3": {}
        }
        self.mock_db.get.return_value = macros

        result = self.manager.list_universal_macros()

        self.assertEqual(set(result), {"macro1", "macro2", "macro3"})

    def test_list_universal_macros_empty(self):
        """Test listing universal macros when none exist."""
        self.mock_db.get.return_value = {}

        result = self.manager.list_universal_macros()

        self.assertEqual(result, [])

    def test_list_mc_macros(self):
        """Test listing microcontroller-specific macros."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "macros": {
                    "mc_macro1": {},
                    "mc_macro2": {}
                }
            }
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.list_mc_macros(mc_mac)

        self.assertEqual(set(result), {"mc_macro1", "mc_macro2"})

    def test_list_mc_macros_mc_not_found(self):
        """Test listing macros for non-existent MC."""
        self.mock_db.get.return_value = {}

        result = self.manager.list_mc_macros("nonexistent:mac")

        self.assertEqual(result, [])

    def test_get_all_universal_macros(self):
        """Test getting all universal macros as objects."""
        macros_data = {
            "macro1": {"command_configs": {"cmd1": True}, "last_state": {}},
            "macro2": {"command_configs": {"cmd2": True}, "last_state": {}}
        }
        self.mock_db.get.return_value = macros_data

        result = self.manager.get_all_universal_macros()

        self.assertEqual(len(result), 2)
        self.assertIn("macro1", result)
        self.assertIn("macro2", result)
        self.assertIsInstance(result["macro1"], Macro)
        self.assertEqual(result["macro1"].name, "macro1")

    def test_get_all_mc_macros(self):
        """Test getting all MC-specific macros as objects."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {
                "macros": {
                    "mc_macro1": {"command_configs": {}, "last_state": {}},
                    "mc_macro2": {"command_configs": {}, "last_state": {}}
                }
            }
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.get_all_mc_macros(mc_mac)

        self.assertEqual(len(result), 2)
        self.assertIn("mc_macro1", result)
        self.assertIsInstance(result["mc_macro1"], Macro)

    def test_get_all_mc_macros_mc_not_found(self):
        """Test getting macros for non-existent MC."""
        self.mock_db.get.return_value = {}

        result = self.manager.get_all_mc_macros("nonexistent:mac")

        self.assertEqual(result, {})

    def test_macro_exists_universal_true(self):
        """Test checking if universal macro exists (True)."""
        macros = {"test_macro": {}}
        self.mock_db.get.return_value = macros

        result = self.manager.macro_exists("test_macro", mc_mac_source=None)

        self.assertTrue(result)

    def test_macro_exists_universal_false(self):
        """Test checking if universal macro exists (False)."""
        self.mock_db.get.return_value = {}

        result = self.manager.macro_exists("nonexistent", mc_mac_source=None)

        self.assertFalse(result)

    def test_macro_exists_mc_true(self):
        """Test checking if MC macro exists (True)."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {"macros": {"test_macro": {}}}
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.macro_exists("test_macro", mc_mac_source=mc_mac)

        self.assertTrue(result)

    def test_macro_exists_mc_false(self):
        """Test checking if MC macro exists (False)."""
        mc_mac = "aa:bb:cc:dd:ee:ff"
        mc_registered = {
            mc_mac: {"macros": {}}
        }
        self.mock_db.get.return_value = mc_registered

        result = self.manager.macro_exists("nonexistent", mc_mac_source=mc_mac)

        self.assertFalse(result)

    def test_rename_universal_macro(self):
        """Test renaming a universal macro."""
        macros = {
            "old_name": {"command_configs": {"cmd": True}, "last_state": {}}
        }

        # Setup mock to return different values for different calls
        call_count = [0]

        def get_side_effect(key, default=None):
            if key == "macros":
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call: load existing macros
                    return macros.copy()
                else:
                    # Subsequent calls for existence checks
                    return macros
            return default

        self.mock_db.get.side_effect = get_side_effect

        result = self.manager.rename_macro("old_name", "new_name", mc_mac_source=None)

        self.assertTrue(result)

    def test_rename_macro_new_name_exists(self):
        """Test renaming macro when new name already exists."""
        macros = {
            "old_name": {},
            "new_name": {}
        }
        self.mock_db.get.return_value = macros

        result = self.manager.rename_macro("old_name", "new_name", mc_mac_source=None)

        self.assertFalse(result)

    def test_rename_macro_old_not_found(self):
        """Test renaming non-existent macro."""
        self.mock_db.get.return_value = {}

        result = self.manager.rename_macro("nonexistent", "new_name", mc_mac_source=None)

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
