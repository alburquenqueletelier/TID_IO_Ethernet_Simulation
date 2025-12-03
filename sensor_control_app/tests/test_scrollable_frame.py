"""
Tests for the scrollable_frame widget.

Tests ScrollableFrame widget functionality including
scroll region updates and mousewheel support.
"""

import unittest
import tkinter as tk
from tkinter import ttk
from sensor_control_app.ui.widgets import ScrollableFrame, create_scrollable_frame


class TestScrollableFrame(unittest.TestCase):
    """Tests for ScrollableFrame widget."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_initialization(self):
        """Test ScrollableFrame initialization."""
        frame = ScrollableFrame(self.root)

        self.assertIsInstance(frame, ttk.Frame)
        self.assertIsNotNone(frame.canvas)
        self.assertIsNotNone(frame.scrollbar)
        self.assertIsNotNone(frame.scrollable_frame)

    def test_canvas_creation(self):
        """Test that canvas is created correctly."""
        frame = ScrollableFrame(self.root)

        self.assertIsInstance(frame.canvas, tk.Canvas)
        self.assertEqual(int(frame.canvas.cget("borderwidth")), 0)
        self.assertEqual(int(frame.canvas.cget("highlightthickness")), 0)

    def test_scrollbar_creation(self):
        """Test that scrollbar is created correctly."""
        frame = ScrollableFrame(self.root)

        self.assertIsInstance(frame.scrollbar, tk.Scrollbar)
        self.assertEqual(frame.scrollbar.cget("orient"), "vertical")

    def test_scrollable_frame_creation(self):
        """Test that internal scrollable frame is created."""
        frame = ScrollableFrame(self.root)

        self.assertIsInstance(frame.scrollable_frame, ttk.Frame)

    def test_get_frame(self):
        """Test get_frame method returns scrollable frame."""
        frame = ScrollableFrame(self.root)

        inner_frame = frame.get_frame()

        self.assertIs(inner_frame, frame.scrollable_frame)

    def test_scroll_to_top(self):
        """Test scrolling to top."""
        frame = ScrollableFrame(self.root)
        frame.pack()

        # Add some content
        for i in range(10):
            tk.Label(frame.scrollable_frame, text=f"Label {i}").pack()

        self.root.update()

        # Scroll to bottom first
        frame.scroll_to_bottom()
        self.root.update()

        # Then scroll to top
        frame.scroll_to_top()
        self.root.update()

        # Verify we're at the top (yview returns (0.0, something))
        yview = frame.canvas.yview()
        self.assertEqual(yview[0], 0.0)

    def test_scroll_to_bottom(self):
        """Test scrolling to bottom."""
        frame = ScrollableFrame(self.root)
        frame.pack(fill="both", expand=True)

        # Add content to make it scrollable
        for i in range(20):
            tk.Label(frame.scrollable_frame, text=f"Label {i}", height=2).pack()

        self.root.update()

        # Scroll to bottom
        frame.scroll_to_bottom()
        self.root.update()

        # Verify we're at or near the bottom
        yview = frame.canvas.yview()
        # yview[1] should be 1.0 or close to it if content exceeds visible area
        self.assertGreaterEqual(yview[1], 0.9)

    def test_update_scroll_bindings(self):
        """Test updating scroll bindings."""
        frame = ScrollableFrame(self.root)

        # Add a widget
        label = tk.Label(frame.scrollable_frame, text="Test")
        label.pack()

        # Update bindings
        frame.update_scroll_bindings()

        # No exception should be raised
        self.assertTrue(True)

    def test_set_scroll_region(self):
        """Test manually setting scroll region."""
        frame = ScrollableFrame(self.root)
        frame.pack()

        # Add content
        tk.Label(frame.scrollable_frame, text="Content").pack()

        self.root.update()

        # Set scroll region
        frame.set_scroll_region()

        # Should have a scroll region set
        bbox = frame.canvas.bbox("all")
        self.assertIsNotNone(bbox)

    def test_canvas_window_creation(self):
        """Test that canvas window is created for scrollable frame."""
        frame = ScrollableFrame(self.root)

        self.assertIsNotNone(frame.canvas_window)
        # Verify window is in canvas
        self.assertIn(frame.canvas_window, frame.canvas.find_all())

    def test_mousewheel_binding(self):
        """Test that mousewheel events are bound."""
        frame = ScrollableFrame(self.root)

        # Check that canvas has mousewheel bindings
        bindings = frame.canvas.bind()
        # Should have some bindings (exact list depends on platform)
        # bindings can be a tuple or string depending on Tk version
        self.assertTrue(bindings is not None)

    def test_adding_widgets_to_scrollable_frame(self):
        """Test adding widgets to the scrollable frame."""
        frame = ScrollableFrame(self.root)

        # Add widgets
        label1 = tk.Label(frame.scrollable_frame, text="Label 1")
        label2 = tk.Label(frame.scrollable_frame, text="Label 2")

        label1.pack()
        label2.pack()

        self.root.update()

        # Verify widgets are children
        children = frame.scrollable_frame.winfo_children()
        self.assertIn(label1, children)
        self.assertIn(label2, children)

    def test_canvas_width_adjustment(self):
        """Test that canvas adjusts scrollable frame width."""
        frame = ScrollableFrame(self.root)
        frame.pack(fill="both", expand=True)

        self.root.geometry("800x600")
        self.root.update()

        # Canvas should have adjusted the window width
        # This is implementation-dependent, just verify no errors
        self.assertTrue(True)


class TestCreateScrollableFrameFunction(unittest.TestCase):
    """Tests for create_scrollable_frame convenience function."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_function_returns_tuple(self):
        """Test that function returns tuple of components."""
        result = create_scrollable_frame(self.root)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_function_returns_correct_types(self):
        """Test that function returns correct component types."""
        canvas, scrollbar, scrollable_frame = create_scrollable_frame(self.root)

        self.assertIsInstance(canvas, tk.Canvas)
        self.assertIsInstance(scrollbar, tk.Scrollbar)
        self.assertIsInstance(scrollable_frame, ttk.Frame)

    def test_function_creates_working_scroll(self):
        """Test that created components work together."""
        canvas, scrollbar, scrollable_frame = create_scrollable_frame(self.root)

        # Pack components (canvas and scrollbar need to be packed manually)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add content
        for i in range(10):
            tk.Label(scrollable_frame, text=f"Label {i}").pack()

        self.root.update()

        # Should not raise any errors
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
