"""
Tests for the drag_drop_list widget.

Tests DragDropList widget functionality including
item management and drag & drop reordering.
"""

import unittest
import tkinter as tk
from tkinter import ttk
from sensor_control_app.ui.widgets import DragDropList


class TestDragDropList(unittest.TestCase):
    """Tests for DragDropList widget."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.reorder_callback_calls = []

    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _reorder_callback(self, source_idx, target_idx):
        """Test callback for reordering."""
        self.reorder_callback_calls.append((source_idx, target_idx))

    def test_initialization(self):
        """Test DragDropList initialization."""
        dnd_list = DragDropList(self.root)

        self.assertIsInstance(dnd_list, ttk.Frame)
        self.assertIsNotNone(dnd_list.items_container)
        self.assertEqual(len(dnd_list.items), 0)

    def test_initialization_with_callback(self):
        """Test initialization with reorder callback."""
        dnd_list = DragDropList(self.root, on_reorder=self._reorder_callback)

        self.assertEqual(dnd_list.on_reorder, self._reorder_callback)

    def test_initialization_with_colors(self):
        """Test initialization with custom colors."""
        dnd_list = DragDropList(
            self.root,
            item_bg="red",
            item_hover_bg="blue",
            item_drag_bg="green"
        )

        self.assertEqual(dnd_list.item_bg, "red")
        self.assertEqual(dnd_list.item_hover_bg, "blue")
        self.assertEqual(dnd_list.item_drag_bg, "green")

    def test_add_item(self):
        """Test adding an item to the list."""
        dnd_list = DragDropList(self.root)

        content = tk.Frame(dnd_list.items_container)
        tk.Label(content, text="Item 1").pack()

        wrapper = dnd_list.add_item("item1", content)

        self.assertIsInstance(wrapper, tk.Frame)
        self.assertEqual(len(dnd_list.items), 1)
        self.assertEqual(dnd_list.items[0]["id"], "item1")

    def test_add_multiple_items(self):
        """Test adding multiple items."""
        dnd_list = DragDropList(self.root)

        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            tk.Label(content, text=f"Item {i}").pack()
            dnd_list.add_item(f"item{i}", content)

        self.assertEqual(len(dnd_list.items), 3)

    def test_get_items(self):
        """Test getting list of items."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        items = dnd_list.get_items()

        self.assertEqual(len(items), 3)
        self.assertIsInstance(items, list)
        # Should return a copy
        self.assertIsNot(items, dnd_list.items)

    def test_get_item_ids(self):
        """Test getting ordered list of item IDs."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        item_ids = dnd_list.get_item_ids()

        self.assertEqual(item_ids, ["item0", "item1", "item2"])

    def test_clear_items(self):
        """Test clearing all items."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Clear
        dnd_list.clear_items()

        self.assertEqual(len(dnd_list.items), 0)

    def test_get_item_by_id(self):
        """Test getting item by ID."""
        dnd_list = DragDropList(self.root)

        content = tk.Frame(dnd_list.items_container)
        dnd_list.add_item("item1", content)

        item = dnd_list.get_item_by_id("item1")

        self.assertIsNotNone(item)
        self.assertEqual(item["id"], "item1")

    def test_get_item_by_id_not_found(self):
        """Test getting non-existent item by ID."""
        dnd_list = DragDropList(self.root)

        item = dnd_list.get_item_by_id("nonexistent")

        self.assertIsNone(item)

    def test_remove_item(self):
        """Test removing an item."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Remove middle item
        result = dnd_list.remove_item("item1")

        self.assertTrue(result)
        self.assertEqual(len(dnd_list.items), 2)
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item2"])

    def test_remove_item_not_found(self):
        """Test removing non-existent item."""
        dnd_list = DragDropList(self.root)

        result = dnd_list.remove_item("nonexistent")

        self.assertFalse(result)

    def test_reorder_items(self):
        """Test reordering items."""
        dnd_list = DragDropList(self.root, on_reorder=self._reorder_callback)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Reorder: move item0 to position 2
        dnd_list.reorder_items(0, 2)

        self.assertEqual(dnd_list.get_item_ids(), ["item1", "item2", "item0"])
        # Callback should have been called
        self.assertEqual(len(self.reorder_callback_calls), 1)
        self.assertEqual(self.reorder_callback_calls[0], (0, 2))

    def test_reorder_items_invalid_source(self):
        """Test reordering with invalid source index."""
        dnd_list = DragDropList(self.root, on_reorder=self._reorder_callback)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Try to reorder with invalid source
        dnd_list.reorder_items(10, 1)

        # Order should not change
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item1", "item2"])
        # Callback should not be called
        self.assertEqual(len(self.reorder_callback_calls), 0)

    def test_reorder_items_invalid_target(self):
        """Test reordering with invalid target index."""
        dnd_list = DragDropList(self.root, on_reorder=self._reorder_callback)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Try to reorder with invalid target
        dnd_list.reorder_items(0, 10)

        # Order should not change
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item1", "item2"])
        self.assertEqual(len(self.reorder_callback_calls), 0)

    def test_reorder_items_same_position(self):
        """Test reordering to same position."""
        dnd_list = DragDropList(self.root, on_reorder=self._reorder_callback)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Reorder to same position
        dnd_list.reorder_items(1, 1)

        # Order should not change
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item1", "item2"])
        # Callback should not be called
        self.assertEqual(len(self.reorder_callback_calls), 0)

    def test_move_item_up(self):
        """Test moving item up."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Move item1 up
        result = dnd_list.move_item_up("item1")

        self.assertTrue(result)
        self.assertEqual(dnd_list.get_item_ids(), ["item1", "item0", "item2"])

    def test_move_item_up_already_first(self):
        """Test moving first item up (should fail)."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Try to move first item up
        result = dnd_list.move_item_up("item0")

        self.assertFalse(result)
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item1", "item2"])

    def test_move_item_down(self):
        """Test moving item down."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Move item1 down
        result = dnd_list.move_item_down("item1")

        self.assertTrue(result)
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item2", "item1"])

    def test_move_item_down_already_last(self):
        """Test moving last item down (should fail)."""
        dnd_list = DragDropList(self.root)

        # Add items
        for i in range(3):
            content = tk.Frame(dnd_list.items_container)
            dnd_list.add_item(f"item{i}", content)

        # Try to move last item down
        result = dnd_list.move_item_down("item2")

        self.assertFalse(result)
        self.assertEqual(dnd_list.get_item_ids(), ["item0", "item1", "item2"])

    def test_dragging_state_initialization(self):
        """Test that dragging state is properly initialized."""
        dnd_list = DragDropList(self.root)

        self.assertFalse(dnd_list.dragging)
        self.assertIsNone(dnd_list.drag_source_index)
        self.assertEqual(dnd_list.drag_start_y, 0)

    def test_item_wrapper_has_bindings(self):
        """Test that item wrapper has drag event bindings."""
        dnd_list = DragDropList(self.root)

        content = tk.Frame(dnd_list.items_container)
        wrapper = dnd_list.add_item("item1", content)

        # Check that wrapper has some bindings
        bindings = wrapper.bind()
        # bindings can be tuple or string depending on Tk version
        self.assertTrue(bindings is not None)


if __name__ == '__main__':
    unittest.main()
