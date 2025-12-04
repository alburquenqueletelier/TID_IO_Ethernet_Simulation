"""
Tests for the interface_discovery module.

Tests network interface discovery functionality including
Ethernet interface detection and filtering.
"""

import unittest
from unittest.mock import patch, MagicMock
from sensor_control_app.network.interface_discovery import InterfaceDiscovery


class TestInterfaceDiscovery(unittest.TestCase):
    """Tests for InterfaceDiscovery class."""

    def test_excluded_prefixes_defined(self):
        """Test that excluded prefixes are properly defined."""
        self.assertIsInstance(InterfaceDiscovery.EXCLUDED_PREFIXES, list)
        self.assertIn("docker", InterfaceDiscovery.EXCLUDED_PREFIXES)
        self.assertIn("veth", InterfaceDiscovery.EXCLUDED_PREFIXES)

    def test_wifi_keywords_defined(self):
        """Test that WiFi keywords are properly defined."""
        self.assertIsInstance(InterfaceDiscovery.WIFI_KEYWORDS, list)
        self.assertIn("wl", InterfaceDiscovery.WIFI_KEYWORDS)
        self.assertIn("wifi", InterfaceDiscovery.WIFI_KEYWORDS)

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_empty(self, mock_psutil):
        """Test get_ethernet_interfaces with no interfaces."""
        mock_psutil.net_if_addrs.return_value = {}
        mock_psutil.net_if_stats.return_value = {}

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {})

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_filters_loopback(self, mock_psutil):
        """Test that loopback interface is filtered out."""
        # Mock address object
        addr = MagicMock()
        addr.family = 17  # AF_PACKET
        addr.address = "00:11:22:33:44:55"

        mock_psutil.net_if_addrs.return_value = {
            "lo": [addr]
        }
        mock_psutil.net_if_stats.return_value = {
            "lo": MagicMock(isup=True)
        }
        mock_psutil.AF_LINK = -1

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {})

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_filters_virtual(self, mock_psutil):
        """Test that virtual interfaces are filtered out."""
        addr = MagicMock()
        addr.family = 17
        addr.address = "aa:bb:cc:dd:ee:ff"

        mock_psutil.net_if_addrs.return_value = {
            "docker0": [addr],
            "veth123": [addr],
            "vmnet8": [addr],
        }
        mock_psutil.net_if_stats.return_value = {
            "docker0": MagicMock(isup=True),
            "veth123": MagicMock(isup=True),
            "vmnet8": MagicMock(isup=True),
        }
        mock_psutil.AF_LINK = -1

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {})

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_filters_wifi(self, mock_psutil):
        """Test that WiFi interfaces are filtered out."""
        addr = MagicMock()
        addr.family = 17
        addr.address = "11:22:33:44:55:66"

        mock_psutil.net_if_addrs.return_value = {
            "wlan0": [addr],
            "wlp3s0": [addr],
        }
        mock_psutil.net_if_stats.return_value = {
            "wlan0": MagicMock(isup=True),
            "wlp3s0": MagicMock(isup=True),
        }
        mock_psutil.AF_LINK = -1

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {})

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_filters_down(self, mock_psutil):
        """Test that interfaces that are down are filtered out."""
        addr = MagicMock()
        addr.family = 17
        addr.address = "aa:bb:cc:dd:ee:ff"

        mock_psutil.net_if_addrs.return_value = {
            "eth0": [addr]
        }
        mock_psutil.net_if_stats.return_value = {
            "eth0": MagicMock(isup=False)
        }
        mock_psutil.AF_LINK = -1

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {})

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_filters_null_mac(self, mock_psutil):
        """Test that null MAC addresses are filtered out."""
        addr = MagicMock()
        addr.family = 17
        addr.address = "00:00:00:00:00:00"

        mock_psutil.net_if_addrs.return_value = {
            "eth0": [addr]
        }
        mock_psutil.net_if_stats.return_value = {
            "eth0": MagicMock(isup=True)
        }
        mock_psutil.AF_LINK = -1

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {})

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_get_ethernet_interfaces_valid(self, mock_psutil):
        """Test get_ethernet_interfaces with valid interfaces."""
        addr1 = MagicMock()
        addr1.family = 17
        addr1.address = "aa:bb:cc:dd:ee:ff"

        addr2 = MagicMock()
        addr2.family = 17
        addr2.address = "11:22:33:44:55:66"

        mock_psutil.net_if_addrs.return_value = {
            "eth0": [addr1],
            "eth1": [addr2]
        }
        mock_psutil.net_if_stats.return_value = {
            "eth0": MagicMock(isup=True),
            "eth1": MagicMock(isup=True)
        }
        mock_psutil.AF_LINK = -1

        result = InterfaceDiscovery.get_ethernet_interfaces()

        self.assertEqual(result, {
            "aa:bb:cc:dd:ee:ff": "eth0",
            "11:22:33:44:55:66": "eth1"
        })

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_is_interface_up_true(self, mock_psutil):
        """Test is_interface_up returns True for up interface."""
        mock_psutil.net_if_stats.return_value = {
            "eth0": MagicMock(isup=True)
        }

        result = InterfaceDiscovery.is_interface_up("eth0")

        self.assertTrue(result)

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_is_interface_up_false(self, mock_psutil):
        """Test is_interface_up returns False for down interface."""
        mock_psutil.net_if_stats.return_value = {
            "eth0": MagicMock(isup=False)
        }

        result = InterfaceDiscovery.is_interface_up("eth0")

        self.assertFalse(result)

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_is_interface_up_not_found(self, mock_psutil):
        """Test is_interface_up returns False for non-existent interface."""
        mock_psutil.net_if_stats.return_value = {}

        result = InterfaceDiscovery.is_interface_up("eth999")

        self.assertFalse(result)

    @patch('sensor_control_app.network.interface_discovery.psutil')
    def test_is_interface_up_exception(self, mock_psutil):
        """Test is_interface_up handles exceptions gracefully."""
        mock_psutil.net_if_stats.side_effect = Exception("Network error")

        result = InterfaceDiscovery.is_interface_up("eth0")

        self.assertFalse(result)

    @patch('sensor_control_app.network.interface_discovery.InterfaceDiscovery.get_ethernet_interfaces')
    def test_get_interface_by_mac_found(self, mock_get_interfaces):
        """Test get_interface_by_mac when MAC is found."""
        mock_get_interfaces.return_value = {
            "aa:bb:cc:dd:ee:ff": "eth0",
            "11:22:33:44:55:66": "eth1"
        }

        result = InterfaceDiscovery.get_interface_by_mac("aa:bb:cc:dd:ee:ff")

        self.assertEqual(result, "eth0")

    @patch('sensor_control_app.network.interface_discovery.InterfaceDiscovery.get_ethernet_interfaces')
    def test_get_interface_by_mac_not_found(self, mock_get_interfaces):
        """Test get_interface_by_mac when MAC is not found."""
        mock_get_interfaces.return_value = {
            "aa:bb:cc:dd:ee:ff": "eth0"
        }

        result = InterfaceDiscovery.get_interface_by_mac("99:99:99:99:99:99")

        self.assertIsNone(result)

    @patch('sensor_control_app.network.interface_discovery.InterfaceDiscovery.is_interface_up')
    @patch('sensor_control_app.network.interface_discovery.InterfaceDiscovery.get_ethernet_interfaces')
    def test_get_all_interfaces_info(self, mock_get_interfaces, mock_is_up):
        """Test get_all_interfaces_info returns complete information."""
        mock_get_interfaces.return_value = {
            "aa:bb:cc:dd:ee:ff": "eth0",
            "11:22:33:44:55:66": "eth1"
        }
        mock_is_up.side_effect = [True, False]

        result = InterfaceDiscovery.get_all_interfaces_info()

        self.assertEqual(result, {
            "eth0": {"mac": "aa:bb:cc:dd:ee:ff", "status": "up"},
            "eth1": {"mac": "11:22:33:44:55:66", "status": "down"}
        })

    def test_get_mac_address_with_af_link(self):
        """Test _get_mac_address with AF_LINK family."""
        addr = MagicMock()
        addr.family = -1  # Simulating psutil.AF_LINK
        addr.address = "aa:bb:cc:dd:ee:ff"

        with patch('sensor_control_app.network.interface_discovery.psutil') as mock_psutil:
            mock_psutil.AF_LINK = -1

            result = InterfaceDiscovery._get_mac_address([addr])

            self.assertEqual(result, "aa:bb:cc:dd:ee:ff")

    def test_get_mac_address_with_af_packet(self):
        """Test _get_mac_address with AF_PACKET (Linux)."""
        addr = MagicMock()
        addr.family = 17  # AF_PACKET on Linux
        addr.address = "11:22:33:44:55:66"

        result = InterfaceDiscovery._get_mac_address([addr])

        self.assertEqual(result, "11:22:33:44:55:66")

    def test_get_mac_address_no_mac(self):
        """Test _get_mac_address with no MAC address."""
        addr = MagicMock()
        addr.family = 2  # AF_INET (IP address, not MAC)
        addr.address = "192.168.1.1"

        result = InterfaceDiscovery._get_mac_address([addr])

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
