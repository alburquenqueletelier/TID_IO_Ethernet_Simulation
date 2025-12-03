"""
Drag and drop list widget for reorderable items.

This widget provides a reusable drag & drop list component that allows
users to reorder items by dragging them to new positions.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional, Any, Dict


class DragDropList(ttk.Frame):
    """
    A list widget with drag & drop reordering capability.

    This widget creates a vertically stacked list of items that can be
    reordered by dragging and dropping. Each item is represented as a frame
    that can contain any widgets.
    """

    def __init__(
        self,
        parent,
        on_reorder: Optional[Callable[[int, int], None]] = None,
        item_bg: str = "white",
        item_hover_bg: str = "#fff3e0",
        item_drag_bg: str = "#e3f2fd",
        **kwargs
    ):
        """
        Initialize the DragDropList.

        Args:
            parent: Parent widget
            on_reorder: Callback function called when items are reordered.
                       Receives (source_index, target_index)
            item_bg: Background color for items
            item_hover_bg: Background color when hovering over drop target
            item_drag_bg: Background color for item being dragged
            **kwargs: Additional arguments passed to ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Configuration
        self.on_reorder = on_reorder
        self.item_bg = item_bg
        self.item_hover_bg = item_hover_bg
        self.item_drag_bg = item_drag_bg

        # Container for items
        self.items_container = ttk.Frame(self)
        self.items_container.pack(fill="both", expand=True)

        # List to track item frames
        self.items: List[Dict[str, Any]] = []

        # Drag state
        self.dragging = False
        self.drag_source_index: Optional[int] = None
        self.drag_start_y = 0

    def add_item(self, item_id: Any, content_frame: tk.Frame) -> tk.Frame:
        """
        Add an item to the list.

        Args:
            item_id: Unique identifier for the item
            content_frame: Frame containing the item's content

        Returns:
            tk.Frame: The wrapper frame for the item
        """
        # Create wrapper frame for the item
        wrapper = tk.Frame(
            self.items_container,
            relief="ridge",
            borderwidth=1,
            bg=self.item_bg
        )
        wrapper.pack(fill="x", pady=2)

        # Pack the content frame inside the wrapper
        content_frame.pack(fill="both", expand=True)

        # Setup drag and drop
        self._setup_drag_and_drop(wrapper, item_id)

        # Store item info
        self.items.append({
            "id": item_id,
            "wrapper": wrapper,
            "content": content_frame
        })

        return wrapper

    def clear_items(self):
        """Remove all items from the list."""
        for item in self.items:
            item["wrapper"].destroy()
        self.items.clear()

    def get_items(self) -> List[Dict[str, Any]]:
        """
        Get list of all items.

        Returns:
            List[Dict]: List of item dictionaries with 'id', 'wrapper', 'content'
        """
        return self.items.copy()

    def get_item_ids(self) -> List[Any]:
        """
        Get ordered list of item IDs.

        Returns:
            List: Ordered list of item IDs
        """
        return [item["id"] for item in self.items]

    def reorder_items(self, source_index: int, target_index: int):
        """
        Reorder items in the list.

        Args:
            source_index: Index of item to move
            target_index: Index of position to move to
        """
        if source_index < 0 or source_index >= len(self.items):
            return
        if target_index < 0 or target_index >= len(self.items):
            return
        if source_index == target_index:
            return

        # Move item in list
        item = self.items.pop(source_index)
        self.items.insert(target_index, item)

        # Rebuild UI
        self._rebuild_ui()

        # Call callback if provided
        if self.on_reorder:
            self.on_reorder(source_index, target_index)

    def _setup_drag_and_drop(self, wrapper: tk.Frame, item_id: Any):
        """
        Setup drag and drop events for an item.

        Args:
            wrapper: Wrapper frame for the item
            item_id: Item identifier
        """
        # Bind hover cursor
        wrapper.bind("<Enter>", lambda e: wrapper.config(cursor="hand1"))
        wrapper.bind("<Leave>", lambda e: wrapper.config(cursor=""))

        # Bind drag events
        wrapper.bind("<Button-1>", lambda e: self._start_drag(e, wrapper))
        wrapper.bind("<B1-Motion>", lambda e: self._do_drag(e, wrapper))
        wrapper.bind("<ButtonRelease-1>", lambda e: self._end_drag(e, wrapper))

    def _start_drag(self, event, wrapper: tk.Frame):
        """
        Start dragging an item.

        Args:
            event: Mouse event
            wrapper: Item wrapper frame
        """
        # Don't start drag if clicked on a button or checkbox
        widget = event.widget
        if isinstance(widget, (tk.Button, tk.Checkbutton, ttk.Button, ttk.Checkbutton)):
            return

        # Find item index
        item_index = None
        for i, item in enumerate(self.items):
            if item["wrapper"] == wrapper:
                item_index = i
                break

        if item_index is None:
            return

        # Start dragging
        self.dragging = True
        self.drag_source_index = item_index
        self.drag_start_y = event.y_root

        # Change appearance
        wrapper.config(relief="raised", borderwidth=3, bg=self.item_drag_bg)

    def _do_drag(self, event, wrapper: tk.Frame):
        """
        Handle drag motion.

        Args:
            event: Mouse event
            wrapper: Item wrapper frame being dragged
        """
        if not self.dragging:
            return

        # Highlight item under cursor
        for item in self.items:
            item_wrapper = item["wrapper"]
            try:
                frame_y = item_wrapper.winfo_rooty()
                frame_height = item_wrapper.winfo_height()

                if frame_y <= event.y_root <= frame_y + frame_height:
                    # Highlight if not the dragged item
                    if item_wrapper != wrapper:
                        item_wrapper.config(bg=self.item_hover_bg)
                else:
                    # Restore original color
                    if item_wrapper != wrapper:
                        item_wrapper.config(bg=self.item_bg)
            except tk.TclError:
                # Widget might have been destroyed
                pass

    def _end_drag(self, event, wrapper: tk.Frame):
        """
        End dragging and perform reordering.

        Args:
            event: Mouse event
            wrapper: Item wrapper frame being dragged
        """
        if not self.dragging:
            return

        self.dragging = False

        # Restore appearance
        wrapper.config(relief="ridge", borderwidth=1, bg=self.item_bg)

        # Find target item
        target_index = None
        for i, item in enumerate(self.items):
            item_wrapper = item["wrapper"]
            item_wrapper.config(bg=self.item_bg)  # Restore all colors

            try:
                frame_y = item_wrapper.winfo_rooty()
                frame_height = item_wrapper.winfo_height()

                if frame_y <= event.y_root <= frame_y + frame_height:
                    target_index = i
                    break
            except tk.TclError:
                pass

        # Perform reordering if dropped on different item
        if target_index is not None and target_index != self.drag_source_index:
            self.reorder_items(self.drag_source_index, target_index)

        self.drag_source_index = None

    def _rebuild_ui(self):
        """Rebuild the UI to reflect current item order."""
        # Unpack all items
        for item in self.items:
            item["wrapper"].pack_forget()

        # Repack in new order
        for item in self.items:
            item["wrapper"].pack(fill="x", pady=2)

    def get_item_by_id(self, item_id: Any) -> Optional[Dict[str, Any]]:
        """
        Get item dictionary by ID.

        Args:
            item_id: Item identifier

        Returns:
            Optional[Dict]: Item dictionary or None if not found
        """
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None

    def remove_item(self, item_id: Any) -> bool:
        """
        Remove an item from the list.

        Args:
            item_id: Identifier of item to remove

        Returns:
            bool: True if item was removed, False if not found
        """
        item = self.get_item_by_id(item_id)
        if item:
            item["wrapper"].destroy()
            self.items.remove(item)
            return True
        return False

    def move_item_up(self, item_id: Any) -> bool:
        """
        Move an item up one position.

        Args:
            item_id: Identifier of item to move

        Returns:
            bool: True if item was moved, False otherwise
        """
        for i, item in enumerate(self.items):
            if item["id"] == item_id and i > 0:
                self.reorder_items(i, i - 1)
                return True
        return False

    def move_item_down(self, item_id: Any) -> bool:
        """
        Move an item down one position.

        Args:
            item_id: Identifier of item to move

        Returns:
            bool: True if item was moved, False otherwise
        """
        for i, item in enumerate(self.items):
            if item["id"] == item_id and i < len(self.items) - 1:
                self.reorder_items(i, i + 1)
                return True
        return False
