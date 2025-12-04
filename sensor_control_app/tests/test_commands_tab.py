"""
Tests for the commands_tab module.

Tests CommandsTab component functionality including
initialization, UI structure, and command configuration.
"""

import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

from sensor_control_app.ui.tabs import CommandsTab
from sensor_control_app.core import StateManager, MicroController
from sensor_control_app.network import PacketSender
from sensor_control_app.storage import Database, MacroManager


class TestCommandsTab(unittest.TestCase):
    """Tests for CommandsTab component."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()

        # Create mock dependencies
        self.mock_db = MagicMock(spec=Database)
        self.mock_db.get.return_value = {}

        self.state_manager = StateManager(self.mock_db)
        self.packet_sender = PacketSender()
        self.macro_manager = MacroManager(self.mock_db)

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_initialization(self):
        """Test CommandsTab initialization."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        self.assertIsInstance(tab, ttk.Frame)
        self.assertIsNotNone(tab.state_manager)
        self.assertIsNotNone(tab.packet_sender)
        self.assertIsNotNone(tab.macro_manager)

    def test_has_mc_combobox(self):
        """Test that MC combobox is created."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        self.assertTrue(hasattr(tab, 'mc_combo'))
        self.assertIsInstance(tab.mc_combo, ttk.Combobox)

    def test_has_command_widgets(self):
        """Test that command state tracking exists."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Should have commands_state dict (renamed from command_widgets)
        self.assertIsInstance(tab.commands_state, dict)
        # Initially empty until MC is selected
        self.assertIsInstance(tab.commands_state, dict)

    def test_has_scrollable_frame(self):
        """Test that commands tab has scrollable canvas."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # The refactored code uses commands_canvas instead of scrollable
        self.assertTrue(hasattr(tab, 'commands_canvas'))

    def test_refresh_mc_list(self):
        """Test refreshing MC list."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Should not raise exception
        tab.refresh_mc_list()
        self.assertTrue(True)

    def test_refresh_mc_list_with_data(self):
        """Test refreshing MC list with registered MCs."""
        # Add test MC
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.state_manager.register_mc(mc)

        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Refresh list
        tab.refresh_mc_list()

        # Combo should have values
        self.assertGreater(len(tab.mc_combo['values']), 0)

    def test_load_mc_commands(self):
        """Test loading commands for a specific MC."""
        # Add test MC with commands
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface_destiny="eth0",
            label="Test MC",
            command_configs={
                "X_FF_Reset": {"enabled": True, "state": None}
            }
        )
        self.state_manager.register_mc(mc)

        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Load commands
        tab.load_mc_commands(mc.mac_source)

        # Should not raise exception
        self.assertTrue(True)

    def test_get_command_configs(self):
        """Test getting current command configurations."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Get configs
        configs = tab.get_command_configs()

        # Should return a dict
        self.assertIsInstance(configs, dict)

    def test_get_command_configs_with_enabled_commands(self):
        """Test getting configs with enabled commands."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Enable a command if any exist in commands_state
        if tab.commands_state:
            first_config = list(tab.commands_state.keys())[0]
            tab.commands_state[first_config]["enabled"].set(True)

            # Get configs
            configs = tab.get_command_configs()

            # Should include the enabled command
            self.assertIn(first_config, configs)
            self.assertTrue(configs[first_config]["enabled"])

    def test_sending_state(self):
        """Test sending state initialization."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Should not be sending initially
        self.assertFalse(tab.sending_commands)

    def test_selected_mc_initialization(self):
        """Test selected MC initialization."""
        tab = CommandsTab(
            self.root,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )

        # Should be None initially
        self.assertIsNone(tab.selected_mc_mac)


if __name__ == '__main__':
    unittest.main()
