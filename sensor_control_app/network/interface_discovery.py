"""
Interface discovery module for detecting Ethernet interfaces.

This module provides functionality to discover available Ethernet interfaces
on the system, excluding virtual interfaces, loopback, WiFi, and other
non-physical interfaces.
"""

import psutil
from typing import Dict, Optional


class InterfaceDiscovery:
    """
    Handles discovery of Ethernet network interfaces.

    This class provides methods to detect available Ethernet interfaces
    on the system and retrieve their MAC addresses.
    """

    # Prefixes to exclude from interface discovery
    EXCLUDED_PREFIXES = [
        "vir",      # Virtual interfaces
        "docker",   # Docker interfaces
        "br-",      # Bridge interfaces
        "veth",     # Virtual Ethernet
        "vmnet",    # VMware interfaces
        "vboxnet",  # VirtualBox interfaces
    ]

    # Keywords to exclude WiFi interfaces
    WIFI_KEYWORDS = ["wl", "wifi"]

    @staticmethod
    def get_ethernet_interfaces() -> Dict[str, str]:
        """
        Discover all available Ethernet interfaces.

        Returns a dictionary mapping MAC addresses to interface names.
        Filters out:
        - Loopback interface (lo)
        - Virtual interfaces (docker, veth, vmnet, etc.)
        - WiFi interfaces
        - Interfaces that are down
        - Interfaces with null MAC addresses

        Returns:
            Dict[str, str]: Dictionary with MAC addresses as keys and
                           interface names as values.
                           Example: {"aa:bb:cc:dd:ee:ff": "eth0"}
        """
        available_interfaces = {}

        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface_name, addrs in interfaces.items():
            # Skip loopback interface
            if iface_name == "lo":
                continue

            # Skip virtual interfaces
            if any(iface_name.startswith(prefix)
                   for prefix in InterfaceDiscovery.EXCLUDED_PREFIXES):
                continue

            # Skip WiFi interfaces
            if any(keyword in iface_name.lower()
                   for keyword in InterfaceDiscovery.WIFI_KEYWORDS):
                continue

            # Check if interface is up
            if iface_name in stats and not stats[iface_name].isup:
                continue

            # Find MAC address
            mac = InterfaceDiscovery._get_mac_address(addrs)

            # Only add if MAC is valid
            if mac and mac != "00:00:00:00:00:00":
                available_interfaces[mac] = iface_name

        return available_interfaces

    @staticmethod
    def _get_mac_address(addrs) -> Optional[str]:
        """
        Extract MAC address from interface address list.

        Args:
            addrs: List of network addresses from psutil.net_if_addrs()

        Returns:
            Optional[str]: MAC address if found, None otherwise
        """
        for addr in addrs:
            # Check if this is a link-layer address (MAC)
            if (getattr(addr, "family", None) == psutil.AF_LINK or
                getattr(addr, "family", None) == 17):  # 17 is AF_PACKET on Linux
                return addr.address

        return None

    @staticmethod
    def is_interface_up(interface_name: str) -> bool:
        """
        Check if a network interface is up.

        Args:
            interface_name: Name of the interface (e.g., "eth0")

        Returns:
            bool: True if interface exists and is up, False otherwise
        """
        try:
            stats = psutil.net_if_stats()
            if interface_name in stats:
                return stats[interface_name].isup
            return False
        except Exception:
            return False

    @staticmethod
    def get_interface_by_mac(mac_address: str) -> Optional[str]:
        """
        Get interface name by MAC address.

        Args:
            mac_address: MAC address to search for (e.g., "aa:bb:cc:dd:ee:ff")

        Returns:
            Optional[str]: Interface name if found, None otherwise
        """
        interfaces = InterfaceDiscovery.get_ethernet_interfaces()
        return interfaces.get(mac_address)

    @staticmethod
    def get_all_interfaces_info() -> Dict[str, Dict[str, str]]:
        """
        Get detailed information about all Ethernet interfaces.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary with interface names as keys
                                       and info dictionaries as values.
                                       Example: {
                                           "eth0": {
                                               "mac": "aa:bb:cc:dd:ee:ff",
                                               "status": "up"
                                           }
                                       }
        """
        interfaces_info = {}
        interfaces = InterfaceDiscovery.get_ethernet_interfaces()

        for mac, iface_name in interfaces.items():
            interfaces_info[iface_name] = {
                "mac": mac,
                "status": "up" if InterfaceDiscovery.is_interface_up(iface_name) else "down"
            }

        return interfaces_info
