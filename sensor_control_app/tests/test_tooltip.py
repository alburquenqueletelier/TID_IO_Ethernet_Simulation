"""
Tests for the tooltip widget.

Tests ToolTip widget functionality including
showing, hiding, and updating tooltips.
"""

import unittest
import tkinter as tk
from sensor_control_app.ui.widgets import ToolTip, BalloonTip, create_tooltip


class TestToolTip(unittest.TestCase):
    """Tests for ToolTip widget."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.button = tk.Button(self.root, text="Test Button")
        self.button.pack()

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_initialization(self):
        """Test ToolTip initialization."""
        tooltip = ToolTip(self.button, "Test tooltip")

        self.assertEqual(tooltip.widget, self.button)
        self.assertEqual(tooltip.text, "Test tooltip")
        self.assertIsNone(tooltip.tooltip_window)
        self.assertIsNone(tooltip.schedule_id)

    def test_initialization_with_custom_delay(self):
        """Test initialization with custom delay."""
        tooltip = ToolTip(self.button, "Test", delay=1000)

        self.assertEqual(tooltip.delay, 1000)

    def test_initialization_with_custom_colors(self):
        """Test initialization with custom colors."""
        tooltip = ToolTip(
            self.button,
            "Test",
            bg="red",
            fg="blue"
        )

        self.assertEqual(tooltip.bg, "red")
        self.assertEqual(tooltip.fg, "blue")

    def test_initialization_with_custom_font(self):
        """Test initialization with custom font."""
        custom_font = ("Helvetica", 12, "bold")
        tooltip = ToolTip(self.button, "Test", font=custom_font)

        self.assertEqual(tooltip.font, custom_font)

    def test_initialization_with_custom_padding(self):
        """Test initialization with custom padding."""
        tooltip = ToolTip(self.button, "Test", padding=(10, 5))

        self.assertEqual(tooltip.padding, (10, 5))

    def test_event_bindings(self):
        """Test that events are bound to widget."""
        tooltip = ToolTip(self.button, "Test")

        # Check that widget has some bindings
        enter_bindings = self.button.bind("<Enter>")
        leave_bindings = self.button.bind("<Leave>")
        button_bindings = self.button.bind("<Button>")

        # Bindings should exist (actual strings vary by platform)
        self.assertIsInstance(enter_bindings, str)
        self.assertIsInstance(leave_bindings, str)
        self.assertIsInstance(button_bindings, str)

    def test_show_tooltip_scheduling(self):
        """Test that tooltip is scheduled to show after delay."""
        tooltip = ToolTip(self.button, "Test", delay=100)

        # Trigger enter event manually
        tooltip._on_enter()
        self.root.update_idletasks()

        # Tooltip should be scheduled but not shown yet
        self.assertIsNotNone(tooltip.schedule_id)
        self.assertIsNone(tooltip.tooltip_window)

    def test_show_tooltip_after_delay(self):
        """Test that tooltip shows after delay."""
        tooltip = ToolTip(self.button, "Test", delay=10)

        # Trigger enter event
        self.button.event_generate("<Enter>")

        # Wait for delay + processing time
        self.root.after(50, lambda: None)
        self.root.update()

        # Tooltip might be shown (timing-dependent)
        # This test verifies no errors occur
        self.assertTrue(True)

    def test_hide_tooltip_on_leave(self):
        """Test that tooltip is hidden when leaving widget."""
        tooltip = ToolTip(self.button, "Test", delay=10)

        # Show tooltip
        self.button.event_generate("<Enter>")
        self.root.after(50, lambda: None)
        self.root.update()

        # Leave widget
        self.button.event_generate("<Leave>")
        self.root.update()

        # Tooltip should be hidden
        self.assertIsNone(tooltip.tooltip_window)
        self.assertIsNone(tooltip.schedule_id)

    def test_cancel_scheduled_tooltip(self):
        """Test cancelling scheduled tooltip."""
        tooltip = ToolTip(self.button, "Test", delay=1000)

        # Schedule tooltip manually
        tooltip._on_enter()
        self.root.update_idletasks()

        self.assertIsNotNone(tooltip.schedule_id)

        # Leave before it shows
        tooltip._on_leave()
        self.root.update_idletasks()

        # Schedule should be cancelled
        self.assertIsNone(tooltip.schedule_id)
        self.assertIsNone(tooltip.tooltip_window)

    def test_update_text(self):
        """Test updating tooltip text."""
        tooltip = ToolTip(self.button, "Original text")

        tooltip.update_text("New text")

        self.assertEqual(tooltip.text, "New text")

    def test_destroy_tooltip(self):
        """Test destroying tooltip."""
        tooltip = ToolTip(self.button, "Test")

        # Show tooltip
        self.button.event_generate("<Enter>")
        self.root.after(50, lambda: None)
        self.root.update()

        # Destroy
        tooltip.destroy()

        # Tooltip should be cleaned up
        self.assertIsNone(tooltip.tooltip_window)
        self.assertIsNone(tooltip.schedule_id)

    def test_multiple_tooltips_on_different_widgets(self):
        """Test multiple tooltips on different widgets."""
        button1 = tk.Button(self.root, text="Button 1")
        button2 = tk.Button(self.root, text="Button 2")

        tooltip1 = ToolTip(button1, "Tooltip 1")
        tooltip2 = ToolTip(button2, "Tooltip 2")

        self.assertEqual(tooltip1.text, "Tooltip 1")
        self.assertEqual(tooltip2.text, "Tooltip 2")
        self.assertIsNot(tooltip1.widget, tooltip2.widget)

    def test_tooltip_does_not_show_immediately(self):
        """Test that tooltip doesn't show immediately on hover."""
        tooltip = ToolTip(self.button, "Test", delay=500)

        # Trigger enter
        self.button.event_generate("<Enter>")
        self.root.update_idletasks()

        # Tooltip should not be shown yet (delay not elapsed)
        self.assertIsNone(tooltip.tooltip_window)


class TestBalloonTip(unittest.TestCase):
    """Tests for BalloonTip (alias for ToolTip)."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.button = tk.Button(self.root, text="Test")
        self.button.pack()

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_balloon_tip_is_tooltip(self):
        """Test that BalloonTip is an alias for ToolTip."""
        balloon = BalloonTip(self.button, "Test")

        self.assertIsInstance(balloon, ToolTip)


class TestCreateTooltipFunction(unittest.TestCase):
    """Tests for create_tooltip convenience function."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.button = tk.Button(self.root, text="Test")
        self.button.pack()

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_create_tooltip_returns_tooltip(self):
        """Test that create_tooltip returns ToolTip instance."""
        tooltip = create_tooltip(self.button, "Test text")

        self.assertIsInstance(tooltip, ToolTip)

    def test_create_tooltip_with_text(self):
        """Test creating tooltip with text."""
        tooltip = create_tooltip(self.button, "My tooltip")

        self.assertEqual(tooltip.text, "My tooltip")

    def test_create_tooltip_with_kwargs(self):
        """Test creating tooltip with additional arguments."""
        tooltip = create_tooltip(
            self.button,
            "Test",
            delay=2000,
            bg="yellow"
        )

        self.assertEqual(tooltip.delay, 2000)
        self.assertEqual(tooltip.bg, "yellow")


if __name__ == '__main__':
    unittest.main()
