"""
Network package for PET scan control application.

This package handles all network-related functionality including:
- Ethernet interface discovery
- Raw packet transmission (Layer 2)
"""

from .interface_discovery import InterfaceDiscovery
from .packet_sender import PacketSender, PacketInfo

__all__ = [
    'InterfaceDiscovery',
    'PacketSender',
    'PacketInfo',
]
