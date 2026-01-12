"""
Packet sender module for transmitting raw Ethernet frames.

This module handles the transmission of Layer 2 Ethernet packets using Scapy.
It supports single packet transmission and batch sending with repetitions and delays.
"""

import threading
import time
from typing import List, Optional, Callable
from dataclasses import dataclass

from scapy.all import Ether, Raw, sendp


@dataclass
class PacketInfo:
    """Information about a packet to send."""
    mac_source: str
    mac_destiny: str
    interface: str
    command_byte: bytes
    command_name: str = ""
    repetitions: int = 1
    delay_ms: int = 0
    extra_payload: bytes = b''  # Additional bytes after command_byte for composite commands


class PacketSender:
    """
    Handles sending raw Ethernet packets using Scapy.

    This class provides methods to send individual packets or batches of packets
    with support for repetitions, delays, and cancellation.
    """

    # Protocol constants
    PAYLOAD_LENGTH = 7
    PADDING_BYTES = b"\x00\x00\x00\x00"
    CONSTANT_BYTES = b"\x02\x03"

    def __init__(self):
        """Initialize the PacketSender."""
        self.sending = False
        self.cancel_flag = False
        self._lock = threading.Lock()

    def send_packet(
        self,
        mac_source: str,
        mac_destiny: str,
        interface: str,
        command_byte: bytes,
        extra_payload: bytes = b'',
        verbose: bool = False
    ) -> bool:
        """
        Send a single raw Ethernet packet.

        Constructs and sends a Layer 2 Ethernet frame with the following structure:
        - Destination MAC (6 bytes)
        - Source MAC (6 bytes)
        - Length (2 bytes)
        - Padding (4 bytes)
        - Constants (2 bytes)
        - Command byte (1 byte)

        Args:
            mac_source: Source MAC address (e.g., "aa:bb:cc:dd:ee:ff")
            mac_destiny: Destination MAC address
            interface: Network interface name (e.g., "eth0")
            command_byte: Command byte to send (e.g., b"\\xff")
            verbose: If True, print Scapy transmission details

        Returns:
            bool: True if packet was sent successfully, False otherwise

        Raises:
            ValueError: If MAC addresses are invalid
            Exception: If packet transmission fails
        """
        try:
            # Validate and convert MAC addresses
            mac_source_bytes = bytes.fromhex(mac_source.replace(":", ""))
            mac_destiny_bytes = bytes.fromhex(mac_destiny.replace(":", ""))

            if len(mac_source_bytes) != 6 or len(mac_destiny_bytes) != 6:
                raise ValueError("MAC addresses must be 6 bytes")

            # Construct packet
            # Calculate payload length: base 7 bytes + extra_payload length
            payload_length = self.PAYLOAD_LENGTH + len(extra_payload)
            length_bytes = payload_length.to_bytes(2, byteorder="big")

            packet = (
                mac_destiny_bytes
                + mac_source_bytes
                + length_bytes
                + self.PADDING_BYTES
                + self.CONSTANT_BYTES
                + command_byte
                + extra_payload  # Additional bytes for composite commands
            )

            # Send packet using Scapy
            scapy_packet = Raw(load=packet)
            sendp(scapy_packet, iface=interface, verbose=verbose)

            return True

        except ValueError as e:
            raise ValueError(f"Invalid MAC address format: {e}")
        except Exception as e:
            raise Exception(f"Failed to send packet: {e}")

    def send_packet_with_repetitions(
        self,
        packet_info: PacketInfo,
        callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """
        Send a packet multiple times with optional delay.

        Args:
            packet_info: PacketInfo object containing packet details
            callback: Optional callback function called after each send.
                     Signature: callback(current_rep, total_reps, message)

        Returns:
            bool: True if all packets were sent, False if cancelled
        """
        for rep in range(packet_info.repetitions):
            # Check for cancellation
            if self.cancel_flag:
                if callback:
                    callback(rep, packet_info.repetitions,
                            f"Cancelled after {rep}/{packet_info.repetitions} repetitions")
                return False

            try:
                # Send packet
                self.send_packet(
                    packet_info.mac_source,
                    packet_info.mac_destiny,
                    packet_info.interface,
                    packet_info.command_byte,
                    extra_payload=packet_info.extra_payload,
                    verbose=False
                )

                # Call callback if provided
                if callback:
                    rep_info = f" (rep {rep + 1}/{packet_info.repetitions})" if packet_info.repetitions > 1 else ""
                    callback(rep + 1, packet_info.repetitions,
                            f"Sent {packet_info.command_name}{rep_info}")

                # Delay if specified (after each send, including between repetitions)
                if packet_info.delay_ms > 0:
                    delay_seconds = packet_info.delay_ms / 1000.0
                    # Check cancellation during delay (in 100ms intervals)
                    for _ in range(int(delay_seconds * 10)):
                        if self.cancel_flag:
                            return False
                        time.sleep(0.1)

            except Exception as e:
                if callback:
                    callback(rep + 1, packet_info.repetitions,
                            f"Error: {str(e)}")
                return False

        return True

    def send_packets_batch(
        self,
        packets: List[PacketInfo],
        callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """
        Send multiple packets in sequence.

        Args:
            packets: List of PacketInfo objects to send
            callback: Optional callback function called for progress updates.
                     Signature: callback(current_packet, total_packets, message)

        Returns:
            bool: True if all packets were sent, False if cancelled
        """
        with self._lock:
            if self.sending:
                return False
            self.sending = True
            self.cancel_flag = False

        try:
            total_packets = sum(p.repetitions for p in packets)
            packet_count = 0

            for packet_idx, packet_info in enumerate(packets):
                if self.cancel_flag:
                    if callback:
                        callback(packet_count, total_packets,
                                f"Cancelled after {packet_count}/{total_packets} packets")
                    return False

                # Send with repetitions
                success = self.send_packet_with_repetitions(
                    packet_info,
                    lambda curr, total, msg: callback(
                        packet_count + curr, total_packets, msg
                    ) if callback else None
                )

                if not success:
                    return False

                packet_count += packet_info.repetitions

            if callback:
                callback(total_packets, total_packets, "All packets sent successfully")

            return True

        finally:
            with self._lock:
                self.sending = False
                self.cancel_flag = False

    def send_packets_batch_async(
        self,
        packets: List[PacketInfo],
        callback: Optional[Callable[[int, int, str], None]] = None,
        on_complete: Optional[Callable[[bool], None]] = None
    ) -> threading.Thread:
        """
        Send multiple packets asynchronously in a background thread.

        Args:
            packets: List of PacketInfo objects to send
            callback: Optional callback for progress updates
            on_complete: Optional callback when sending completes.
                        Receives True if all sent, False if cancelled

        Returns:
            threading.Thread: The thread handling the transmission
        """
        def send_thread():
            success = self.send_packets_batch(packets, callback)
            if on_complete:
                on_complete(success)

        thread = threading.Thread(target=send_thread, daemon=True)
        thread.start()
        return thread

    def cancel(self) -> None:
        """
        Cancel ongoing packet transmission.

        Sets the cancel flag which will stop the current batch transmission
        at the next check point (between packets or during delays).
        """
        self.cancel_flag = True

    def is_sending(self) -> bool:
        """
        Check if currently sending packets.

        Returns:
            bool: True if sending is in progress, False otherwise
        """
        with self._lock:
            return self.sending

    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """
        Validate MAC address format.

        Args:
            mac: MAC address string (e.g., "aa:bb:cc:dd:ee:ff")

        Returns:
            bool: True if valid, False otherwise
        """
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac))
