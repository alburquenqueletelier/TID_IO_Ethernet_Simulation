"""
Tests for the packet_sender module.

Tests packet transmission functionality including single packets,
batch sending, and cancellation.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import time
from sensor_control_app.network.packet_sender import PacketSender, PacketInfo


class TestPacketInfo(unittest.TestCase):
    """Tests for PacketInfo dataclass."""

    def test_packet_info_creation(self):
        """Test creating a PacketInfo object."""
        packet = PacketInfo(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff",
            command_name="X_FF_Reset",
            repetitions=5,
            delay_ms=100
        )

        self.assertEqual(packet.mac_source, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(packet.mac_destiny, "11:22:33:44:55:66")
        self.assertEqual(packet.interface, "eth0")
        self.assertEqual(packet.command_byte, b"\xff")
        self.assertEqual(packet.command_name, "X_FF_Reset")
        self.assertEqual(packet.repetitions, 5)
        self.assertEqual(packet.delay_ms, 100)

    def test_packet_info_defaults(self):
        """Test PacketInfo with default values."""
        packet = PacketInfo(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\x00"
        )

        self.assertEqual(packet.command_name, "")
        self.assertEqual(packet.repetitions, 1)
        self.assertEqual(packet.delay_ms, 0)


class TestPacketSender(unittest.TestCase):
    """Tests for PacketSender class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sender = PacketSender()

    def test_initialization(self):
        """Test PacketSender initialization."""
        self.assertFalse(self.sender.sending)
        self.assertFalse(self.sender.cancel_flag)

    def test_protocol_constants(self):
        """Test that protocol constants are defined."""
        self.assertEqual(PacketSender.PAYLOAD_LENGTH, 7)
        self.assertEqual(PacketSender.PADDING_BYTES, b"\x00\x00\x00\x00")
        self.assertEqual(PacketSender.CONSTANT_BYTES, b"\x02\x03")

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packet_success(self, mock_sendp):
        """Test sending a single packet successfully."""
        result = self.sender.send_packet(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff"
        )

        self.assertTrue(result)
        mock_sendp.assert_called_once()

        # Verify packet construction
        call_args = mock_sendp.call_args
        self.assertEqual(call_args[1]["iface"], "eth0")
        self.assertEqual(call_args[1]["verbose"], False)

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packet_constructs_correct_packet(self, mock_sendp):
        """Test that packet is constructed correctly."""
        self.sender.send_packet(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff"
        )

        # Get the packet that was sent
        packet_raw = mock_sendp.call_args[0][0]

        # Verify packet structure
        packet_bytes = bytes(packet_raw)

        # Destination MAC (6 bytes)
        self.assertEqual(packet_bytes[0:6], bytes.fromhex("112233445566"))

        # Source MAC (6 bytes)
        self.assertEqual(packet_bytes[6:12], bytes.fromhex("aabbccddeeff"))

        # Length (2 bytes) - should be 7
        self.assertEqual(packet_bytes[12:14], b"\x00\x07")

        # Padding (4 bytes)
        self.assertEqual(packet_bytes[14:18], b"\x00\x00\x00\x00")

        # Constants (2 bytes)
        self.assertEqual(packet_bytes[18:20], b"\x02\x03")

        # Command byte (1 byte)
        self.assertEqual(packet_bytes[20:21], b"\xff")

    def test_send_packet_invalid_mac_short(self):
        """Test send_packet with invalid (short) MAC address."""
        with self.assertRaises(ValueError) as context:
            self.sender.send_packet(
                mac_source="aa:bb:cc",
                mac_destiny="11:22:33:44:55:66",
                interface="eth0",
                command_byte=b"\xff"
            )

        self.assertIn("MAC address", str(context.exception))

    def test_send_packet_invalid_mac_format(self):
        """Test send_packet with invalid MAC format."""
        with self.assertRaises(ValueError):
            self.sender.send_packet(
                mac_source="invalid_mac",
                mac_destiny="11:22:33:44:55:66",
                interface="eth0",
                command_byte=b"\xff"
            )

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packet_with_verbose(self, mock_sendp):
        """Test sending packet with verbose mode."""
        self.sender.send_packet(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff",
            verbose=True
        )

        call_args = mock_sendp.call_args
        self.assertEqual(call_args[1]["verbose"], True)

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packet_with_repetitions(self, mock_sendp):
        """Test sending packet with repetitions."""
        packet_info = PacketInfo(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff",
            command_name="Reset",
            repetitions=3,
            delay_ms=0
        )

        result = self.sender.send_packet_with_repetitions(packet_info)

        self.assertTrue(result)
        self.assertEqual(mock_sendp.call_count, 3)

    @patch('sensor_control_app.network.packet_sender.sendp')
    @patch('sensor_control_app.network.packet_sender.time.sleep')
    def test_send_packet_with_delay(self, mock_sleep, mock_sendp):
        """Test sending packet with delay."""
        packet_info = PacketInfo(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff",
            repetitions=2,
            delay_ms=100
        )

        self.sender.send_packet_with_repetitions(packet_info)

        # Should sleep in 100ms intervals (delay_ms / 1000 * 10 times)
        self.assertTrue(mock_sleep.called)

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packet_with_callback(self, mock_sendp):
        """Test sending packet with callback."""
        callback_calls = []

        def callback(curr, total, msg):
            callback_calls.append((curr, total, msg))

        packet_info = PacketInfo(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff",
            command_name="Reset",
            repetitions=3,
            delay_ms=0
        )

        self.sender.send_packet_with_repetitions(packet_info, callback)

        self.assertEqual(len(callback_calls), 3)
        self.assertEqual(callback_calls[0][0], 1)  # First rep
        self.assertEqual(callback_calls[2][0], 3)  # Last rep

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packet_with_repetitions_cancellation(self, mock_sendp):
        """Test cancelling packet repetitions."""
        packet_info = PacketInfo(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="11:22:33:44:55:66",
            interface="eth0",
            command_byte=b"\xff",
            repetitions=10,
            delay_ms=0
        )

        # Cancel after first send
        def side_effect(*args, **kwargs):
            self.sender.cancel_flag = True

        mock_sendp.side_effect = side_effect

        result = self.sender.send_packet_with_repetitions(packet_info)

        self.assertFalse(result)
        self.assertEqual(mock_sendp.call_count, 1)

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packets_batch(self, mock_sendp):
        """Test sending multiple packets in batch."""
        packets = [
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\x00", repetitions=2),
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\xff", repetitions=1),
        ]

        result = self.sender.send_packets_batch(packets)

        self.assertTrue(result)
        self.assertEqual(mock_sendp.call_count, 3)  # 2 + 1 repetitions
        self.assertFalse(self.sender.sending)  # Should be reset after

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packets_batch_already_sending(self, mock_sendp):
        """Test that batch sending fails if already sending."""
        self.sender.sending = True

        packets = [
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\x00"),
        ]

        result = self.sender.send_packets_batch(packets)

        self.assertFalse(result)
        mock_sendp.assert_not_called()

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packets_batch_with_callback(self, mock_sendp):
        """Test batch sending with progress callback."""
        callback_calls = []

        def callback(curr, total, msg):
            callback_calls.append((curr, total, msg))

        packets = [
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\x00", "CMD1", repetitions=2),
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\xff", "CMD2", repetitions=1),
        ]

        result = self.sender.send_packets_batch(packets, callback)

        self.assertTrue(result)
        # Should have callbacks for each repetition + completion message
        self.assertGreater(len(callback_calls), 0)

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_cancel_sending(self, mock_sendp):
        """Test cancelling batch sending."""
        packets = [
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\x00", repetitions=10),
        ]

        # Cancel after first send
        def side_effect(*args, **kwargs):
            self.sender.cancel()

        mock_sendp.side_effect = side_effect

        result = self.sender.send_packets_batch(packets)

        self.assertFalse(result)
        # cancel_flag is reset after batch completes, so we just verify result is False

    def test_is_sending(self):
        """Test is_sending method."""
        self.assertFalse(self.sender.is_sending())

        self.sender.sending = True
        self.assertTrue(self.sender.is_sending())

    def test_validate_mac_address_valid(self):
        """Test MAC address validation with valid addresses."""
        valid_macs = [
            "aa:bb:cc:dd:ee:ff",
            "AA:BB:CC:DD:EE:FF",
            "00:11:22:33:44:55",
            "aa-bb-cc-dd-ee-ff",
            "AA-BB-CC-DD-EE-FF",
        ]

        for mac in valid_macs:
            with self.subTest(mac=mac):
                self.assertTrue(PacketSender.validate_mac_address(mac))

    def test_validate_mac_address_invalid(self):
        """Test MAC address validation with invalid addresses."""
        invalid_macs = [
            "aa:bb:cc:dd:ee",      # Too short
            "aa:bb:cc:dd:ee:ff:gg", # Too long
            "invalid",             # Not hex
            "aa:bb:cc:dd:ee:gg",   # Invalid hex
            "aabbccddeeff",        # No separators
        ]

        for mac in invalid_macs:
            with self.subTest(mac=mac):
                self.assertFalse(PacketSender.validate_mac_address(mac))

    @patch('sensor_control_app.network.packet_sender.sendp')
    def test_send_packets_batch_async(self, mock_sendp):
        """Test asynchronous batch sending."""
        packets = [
            PacketInfo("aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66", "eth0", b"\x00"),
        ]

        thread = self.sender.send_packets_batch_async(packets)

        self.assertIsNotNone(thread)
        thread.join(timeout=1)  # Wait for thread to complete

        self.assertEqual(mock_sendp.call_count, 1)


if __name__ == '__main__':
    unittest.main()
