"""
Scrollable frame widget with integrated vertical scrollbar.

This widget provides a reusable scrollable frame component with
automatic scroll region updates and mousewheel support.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class ScrollableFrame(ttk.Frame):
    """
    A frame with integrated vertical scrollbar and mousewheel support.

    This widget creates a canvas-based scrollable frame that automatically
    adjusts its scroll region when content changes. It includes:
    - Vertical scrollbar
    - Mousewheel support (cross-platform)
    - Automatic width adjustment
    - Recursive mousewheel binding to all child widgets
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize the ScrollableFrame.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments passed to ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Bind frame configuration to update scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window in canvas for the scrollable frame
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        # Configure canvas scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind canvas width changes to adjust internal frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Setup mousewheel scrolling
        self._setup_mousewheel()

    def _on_canvas_configure(self, event):
        """
        Handle canvas resize events.

        Adjusts the width of the internal frame to match the canvas width.

        Args:
            event: Configure event
        """
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _setup_mousewheel(self):
        """Setup mousewheel scrolling for the canvas and all children."""
        # Bind mousewheel to canvas
        self._bind_mousewheel(self.canvas)

        # Bind to scrollable frame and all its children
        self._bind_to_all_children(self.scrollable_frame)

    def _bind_mousewheel(self, widget):
        """
        Bind mousewheel events to a widget.

        Supports both Windows/MacOS (MouseWheel) and Linux (Button-4/5).

        Args:
            widget: Widget to bind mousewheel events to
        """
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows/MacOS
        widget.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up
        widget.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down

    def _on_mousewheel(self, event):
        """
        Handle mousewheel scroll events.

        Args:
            event: Mouse event

        Returns:
            str: "break" to prevent event propagation
        """
        # Determine scroll direction
        if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
            # Scroll down
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            # Scroll up
            self.canvas.yview_scroll(-1, "units")

        return "break"  # Prevent event propagation

    def _bind_to_all_children(self, parent):
        """
        Recursively bind mousewheel events to all child widgets.

        Skips widgets that have their own scrolling mechanisms.

        Args:
            parent: Parent widget to start recursive binding from
        """
        try:
            self._bind_mousewheel(parent)

            for child in parent.winfo_children():
                # Skip widgets with their own scroll mechanisms
                if not isinstance(child, (
                    scrolledtext.ScrolledText,
                    tk.Listbox,
                    tk.Text,
                    ttk.Combobox,
                    tk.Spinbox
                )):
                    self._bind_to_all_children(child)

        except Exception:
            # Silently handle widgets that don't support binding
            pass

    def update_scroll_bindings(self):
        """
        Update mousewheel bindings for all children.

        Call this method after adding new widgets to the scrollable_frame
        to ensure they have mousewheel scrolling enabled.
        """
        self._bind_to_all_children(self.scrollable_frame)

    def scroll_to_top(self):
        """Scroll to the top of the frame."""
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the frame."""
        self.canvas.yview_moveto(1)

    def get_frame(self):
        """
        Get the inner scrollable frame.

        Use this frame to add child widgets.

        Returns:
            ttk.Frame: The scrollable frame to add widgets to
        """
        return self.scrollable_frame

    def set_scroll_region(self):
        """Manually update the scroll region (useful after dynamic content changes)."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


# Convenience function for backwards compatibility
def create_scrollable_frame(parent):
    """
    Create a scrollable frame (backwards compatible function).

    Args:
        parent: Parent widget

    Returns:
        tuple: (canvas, scrollbar, scrollable_frame) for manual setup
    """
    canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Bind canvas width changes
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

    return canvas, scrollbar, scrollable_frame
