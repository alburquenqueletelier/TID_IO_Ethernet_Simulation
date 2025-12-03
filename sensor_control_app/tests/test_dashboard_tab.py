"""
Tests for the dashboard_tab module.

Tests DashboardTab component functionality including
initialization, UI structure, and basic interactions.
"""

import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

from sensor_control_app.ui.tabs import DashboardTab
from sensor_control_app.core import StateManager, MicroController
from sensor_control_app.network import InterfaceDiscovery, PacketSender
from sensor_control_app.storage import Database, MacroManager


class TestDashboardTab(unittest.TestCase):
    """Tests for DashboardTab component."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()

        # Create mock dependencies
        self.mock_db = MagicMock(spec=Database)
        self.mock_db.get.return_value = {}

        self.state_manager = StateManager(self.mock_db)
        self.interface_discovery = InterfaceDiscovery()
        self.packet_sender = PacketSender()
        self.macro_manager = MacroManager(self.mock_db)

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_initialization(self):
        """Test DashboardTab initialization."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        self.assertIsInstance(tab, ttk.Frame)
        self.assertIsNotNone(tab.state_manager)
        self.assertIsNotNone(tab.scrollable)

    def test_has_scrollable_frame(self):
        """Test that dashboard has scrollable frame."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        self.assertTrue(hasattr(tab, 'scrollable'))

    def test_has_pet_checkboxes(self):
        """Test that PET checkboxes are created."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        # Should have 10 PET checkboxes
        self.assertEqual(len(tab.pet_checkboxes), 10)

        # Check PET numbers 1-10
        for pet_num in range(1, 11):
            self.assertIn(pet_num, tab.pet_checkboxes)

    def test_has_pet_comboboxes(self):
        """Test that PET comboboxes are created."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        # Should have 10 PET comboboxes
        self.assertEqual(len(tab.pet_comboboxes), 10)

        # Check PET numbers 1-10
        for pet_num in range(1, 11):
            self.assertIn(pet_num, tab.pet_comboboxes)

    def test_refresh_interfaces(self):
        """Test refreshing network interfaces."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        # Should not raise exception
        tab.refresh_interfaces()
        self.assertTrue(True)

    def test_refresh_mc_table(self):
        """Test refreshing MC table."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        # Should not raise exception
        tab.refresh_mc_table()
        self.assertTrue(True)

    def test_load_data(self):
        """Test loading data from state manager."""
        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager
        )

        # Add test MC
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.state_manager.register_mc(mc)

        # Load data
        tab.load_data()

        # Should have loaded without error
        self.assertTrue(True)

    def test_with_callback(self):
        """Test initialization with callback."""
        callback_called = [False]

        def test_callback():
            callback_called[0] = True

        tab = DashboardTab(
            self.root,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager,
            on_refresh_callback=test_callback
        )

        # Refresh interfaces
        tab.refresh_interfaces()

        # Callback should have been called
        self.assertTrue(callback_called[0])


if __name__ == '__main__':
    unittest.main()
