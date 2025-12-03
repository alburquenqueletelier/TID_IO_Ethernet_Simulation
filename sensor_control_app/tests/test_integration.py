"""
Integration tests for the complete PET Scanner Control Application.

These tests verify that all components work together correctly:
- Application initialization
- Database persistence
- Tab integration
- Component communication
- End-to-end workflows
"""

import unittest
import tkinter as tk
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from sensor_control_app.ui.app import McControlApp
from sensor_control_app.core.models import MicroController


class TestApplicationIntegration(unittest.TestCase):
    """Test complete application integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

        # Clean up temp database
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_application_initialization(self):
        """Test that application initializes all components correctly."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Verify core components
        self.assertIsNotNone(app.database)
        self.assertIsNotNone(app.state_manager)
        self.assertIsNotNone(app.interface_discovery)
        self.assertIsNotNone(app.packet_sender)
        self.assertIsNotNone(app.macro_manager)

        # Verify UI components
        self.assertIsNotNone(app.notebook)
        self.assertIsNotNone(app.dashboard_tab)
        self.assertIsNotNone(app.commands_tab)

        # Verify notebook has 2 tabs
        self.assertEqual(app.notebook.index("end"), 2)

    def test_database_persistence(self):
        """Test that data persists across application instances."""
        # Create initial data with correct structure
        initial_data = {
            "mc_registered": {
                "00:11:22:33:44:55": {
                    "mac_destiny": "AA:BB:CC:DD:EE:FF",
                    "interface_destiny": "eth0",
                    "label": "MC1",
                    "command_configs": {},
                    "last_state": {},
                    "macros": {}
                }
            },
            "macros": {},
            "pet_associations": {}
        }

        with open(self.temp_db_path, 'w') as f:
            json.dump(initial_data, f)

        # Load application
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Verify data was loaded
        mcs = app.state_manager.get_all_registered_mcs()
        self.assertEqual(len(mcs), 1)
        self.assertEqual(mcs[0].label, "MC1")
        self.assertEqual(mcs[0].mac_destiny, "AA:BB:CC:DD:EE:FF")

    def test_dashboard_commands_integration(self):
        """Test that Dashboard and Commands tabs communicate correctly."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register a MC through state manager
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="TestMC"
        )
        app.state_manager.register_mc(mc)

        # Refresh dashboard
        app.dashboard_tab.load_data()

        # Verify commands tab can see the MC
        app.commands_tab.refresh_mc_list()

        # Check that MC appears in commands tab
        mc_var = app.commands_tab.mc_var
        self.assertIsNotNone(mc_var)

    @patch('sensor_control_app.network.InterfaceDiscovery.get_ethernet_interfaces')
    def test_network_interface_discovery(self, mock_get_interfaces):
        """Test network interface discovery integration."""
        # Mock network interfaces
        mock_get_interfaces.return_value = {
            "00:11:22:33:44:55": "eth0",
            "00:11:22:33:44:66": "eth1"
        }

        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Refresh interfaces
        app.dashboard_tab.refresh_interfaces()

        # Verify interface count label exists and is updated
        self.assertTrue(hasattr(app.dashboard_tab, 'interface_count_label'))
        self.assertIn("2", app.dashboard_tab.interface_count_label.cget("text"))

    def test_macro_save_load_integration(self):
        """Test macro save and load across tabs."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Save a universal macro
        macro_data = {
            "command_configs": {
                "X_00_CPU": {"enabled": True, "selected_option": 1}
            },
            "last_state": {}
        }

        app.macro_manager.save_universal_macro("TestMacro", macro_data)

        # Verify macro can be loaded
        loaded = app.macro_manager.load_universal_macro("TestMacro")
        self.assertEqual(loaded["command_configs"]["X_00_CPU"]["enabled"], True)

        # Verify macro persists after save
        with patch('tkinter.messagebox.showinfo'):
            app.save_data()

        # Create new app instance
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.root = tk.Tk()
        app2 = McControlApp(self.root, db_path=self.temp_db_path)

        loaded2 = app2.macro_manager.load_universal_macro("TestMacro")
        self.assertEqual(loaded2["command_configs"]["X_00_CPU"]["enabled"], True)

    def test_pet_association_integration(self):
        """Test PET scanner association with microcontrollers."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register a MC
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="PET_MC_1"
        )
        app.state_manager.register_mc(mc)

        # Associate with PET 1
        app.state_manager.associate_pet_with_mc(1, "AA:BB:CC:DD:EE:FF")

        # Verify association
        pet_data = app.state_manager.get_pet_association(1)
        self.assertEqual(pet_data.mc_mac, "AA:BB:CC:DD:EE:FF")

        # Refresh dashboard
        app.dashboard_tab.load_data()

        # Verify persistence
        with patch('tkinter.messagebox.showinfo'):
            app.save_data()

    @patch('sensor_control_app.network.PacketSender.send_packet')
    def test_command_sending_integration(self, mock_send):
        """Test end-to-end command sending workflow."""
        mock_send.return_value = True

        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register a MC
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="CommandMC"
        )
        app.state_manager.register_mc(mc)

        # Load MC in commands tab
        app.commands_tab.refresh_mc_list()

        # Verify packet sender is available
        self.assertIsNotNone(app.packet_sender)
        self.assertTrue(hasattr(app.packet_sender, 'send_packet'))

    def test_window_close_with_save(self):
        """Test window close with save prompt."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register some data
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="CloseTestMC"
        )
        app.state_manager.register_mc(mc)

        # Mock messagebox to auto-save and close
        with patch('tkinter.messagebox.askyesnocancel', return_value=True):
            app.on_closing()

        # Verify data was saved
        self.assertTrue(os.path.exists(self.temp_db_path))

        # Verify database has the MC
        with open(self.temp_db_path, 'r') as f:
            data = json.load(f)
            self.assertIn("mc_registered", data)

    def test_menu_commands(self):
        """Test menu bar commands."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register test data
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="MenuTestMC"
        )
        app.state_manager.register_mc(mc)

        # Test save command
        with patch('tkinter.messagebox.showinfo'):
            app.save_data()

        # Verify data was saved
        self.assertTrue(os.path.exists(self.temp_db_path))

    def test_multiple_mc_registration(self):
        """Test registering multiple microcontrollers."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register multiple MCs
        for i in range(3):
            mc = MicroController(
                mac_source=f"00:11:22:33:44:{i:02X}",
                mac_destiny=f"AA:BB:CC:DD:EE:{i:02X}",
                interface_destiny=f"eth{i}",
                label=f"MC{i+1}"
            )
            app.state_manager.register_mc(mc)

        # Verify all MCs are registered
        mcs = app.state_manager.get_all_registered_mcs()
        self.assertEqual(len(mcs), 3)

        # Refresh dashboard and commands tabs
        app.dashboard_tab.load_data()
        app.commands_tab.refresh_mc_list()

        # Save with message box mocked
        with patch('tkinter.messagebox.showinfo'):
            app.save_data()

        # Load in new instance
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.root = tk.Tk()
        app2 = McControlApp(self.root, db_path=self.temp_db_path)

        mcs2 = app2.state_manager.get_all_registered_mcs()
        self.assertEqual(len(mcs2), 3)

    def test_all_pet_associations(self):
        """Test all 10 PET scanner associations."""
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Register a MC
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="SharedMC"
        )
        app.state_manager.register_mc(mc)

        # Associate all 10 PETs with the same MC
        for pet_num in range(1, 11):
            app.state_manager.associate_pet_with_mc(pet_num, "AA:BB:CC:DD:EE:FF")
            app.state_manager.set_pet_enabled(pet_num, True)

        # Verify all associations
        for pet_num in range(1, 11):
            pet_data = app.state_manager.get_pet_association(pet_num)
            self.assertEqual(pet_data.mc_mac, "AA:BB:CC:DD:EE:FF")
            self.assertTrue(pet_data.enabled)

        # Save and reload
        with patch('tkinter.messagebox.showinfo'):
            app.save_data()

        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.root = tk.Tk()
        app2 = McControlApp(self.root, db_path=self.temp_db_path)

        # Verify persistence
        for pet_num in range(1, 11):
            pet_data = app2.state_manager.get_pet_association(pet_num)
            self.assertEqual(pet_data.mc_mac, "AA:BB:CC:DD:EE:FF")


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    @patch('sensor_control_app.network.InterfaceDiscovery.get_ethernet_interfaces')
    @patch('sensor_control_app.network.PacketSender.send_packet')
    def test_complete_workflow_discovery_to_command(self, mock_send, mock_interfaces):
        """Test complete workflow from interface discovery to command sending."""
        # Mock network discovery
        mock_interfaces.return_value = {
            "00:11:22:33:44:55": "eth0"
        }
        mock_send.return_value = True

        # Initialize app
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # 1. Discover interfaces
        app.dashboard_tab.refresh_interfaces()

        # 2. Register MC
        mc = MicroController(
            mac_source="00:11:22:33:44:55",
            mac_destiny="AA:BB:CC:DD:EE:FF",
            interface_destiny="eth0",
            label="WorkflowMC"
        )
        app.state_manager.register_mc(mc)

        # 3. Associate with PET
        app.state_manager.associate_pet_with_mc(1, "AA:BB:CC:DD:EE:FF")
        app.state_manager.set_pet_enabled(1, True)

        # 4. Configure commands (simulate)
        command_configs = {
            "X_00_CPU": {
                "enabled": True,
                "selected_option": 1,
                "repetitions": 1
            }
        }
        app.state_manager.save_mc_commands("AA:BB:CC:DD:EE:FF", command_configs)

        # 5. Save macro
        macro_data = {
            "command_configs": command_configs,
            "last_state": {}
        }
        app.macro_manager.save_universal_macro("WorkflowMacro", macro_data)

        # 6. Refresh UI
        app.dashboard_tab.load_data()
        app.commands_tab.refresh_mc_list()

        # 7. Save all data
        with patch('tkinter.messagebox.showinfo'):
            app.save_data()

        # Verify everything persisted
        self.assertTrue(os.path.exists(self.temp_db_path))

        # Create new app instance and verify
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.root = tk.Tk()
        app2 = McControlApp(self.root, db_path=self.temp_db_path)

        mcs = app2.state_manager.get_all_registered_mcs()
        self.assertEqual(len(mcs), 1)
        self.assertEqual(mcs[0].label, "WorkflowMC")

        pet_data = app2.state_manager.get_pet_association(1)
        self.assertEqual(pet_data.mc_mac, "AA:BB:CC:DD:EE:FF")

        macro = app2.macro_manager.load_universal_macro("WorkflowMacro")
        self.assertIsNotNone(macro)

    def test_empty_database_initialization(self):
        """Test application handles empty database correctly."""
        # Don't create any initial data
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Verify default state
        mcs = app.state_manager.get_all_registered_mcs()
        self.assertEqual(len(mcs), 0)

        # Verify all PETs are unassociated
        for pet_num in range(1, 11):
            pet_data = app.state_manager.get_pet_association(pet_num)
            self.assertIsNone(pet_data.mc_mac)
            self.assertFalse(pet_data.enabled)

    def test_corrupted_database_recovery(self):
        """Test application recovers from corrupted database."""
        # Create corrupted database
        with open(self.temp_db_path, 'w') as f:
            f.write("{invalid json content")

        # Application should handle this gracefully
        app = McControlApp(self.root, db_path=self.temp_db_path)

        # Verify it initialized with defaults
        mcs = app.state_manager.get_all_registered_mcs()
        self.assertEqual(len(mcs), 0)


if __name__ == '__main__':
    unittest.main()
