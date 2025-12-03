"""
Tooltip widget for displaying hover hints.

This module provides a simple tooltip implementation that shows
helpful text when hovering over widgets.
"""

import tkinter as tk
from typing import Optional


class ToolTip:
    """
    A simple tooltip that displays text when hovering over a widget.

    This class creates a small popup window that appears near the cursor
    when the user hovers over a widget for a brief moment.
    """

    def __init__(
        self,
        widget: tk.Widget,
        text: str,
        delay: int = 500,
        bg: str = "#ffffe0",
        fg: str = "black",
        font: tuple = ("Arial", 9, "normal"),
        padding: tuple = (5, 3)
    ):
        """
        Initialize the ToolTip.

        Args:
            widget: Widget to attach tooltip to
            text: Text to display in tooltip
            delay: Delay in milliseconds before showing tooltip
            bg: Background color of tooltip
            fg: Foreground (text) color of tooltip
            font: Font tuple (family, size, weight)
            padding: Padding tuple (x, y) in pixels
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.bg = bg
        self.fg = fg
        self.font = font
        self.padding = padding

        self.tooltip_window: Optional[tk.Toplevel] = None
        self.schedule_id: Optional[str] = None

        # Bind hover events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Button>", self._on_leave)  # Hide on click

    def _on_enter(self, event=None):
        """
        Handle mouse enter event.

        Schedules tooltip to appear after delay.

        Args:
            event: Mouse event
        """
        self._cancel_schedule()
        self.schedule_id = self.widget.after(self.delay, self._show_tooltip)

    def _on_leave(self, event=None):
        """
        Handle mouse leave event.

        Cancels scheduled tooltip and hides if visible.

        Args:
            event: Mouse event
        """
        self._cancel_schedule()
        self._hide_tooltip()

    def _cancel_schedule(self):
        """Cancel any scheduled tooltip display."""
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None

    def _show_tooltip(self):
        """Display the tooltip near the widget."""
        if self.tooltip_window:
            return  # Already showing

        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Create label with tooltip text
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background=self.bg,
            foreground=self.fg,
            font=self.font,
            relief="solid",
            borderwidth=1,
            padx=self.padding[0],
            pady=self.padding[1],
            justify="left"
        )
        label.pack()

    def _hide_tooltip(self):
        """Hide and destroy the tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, new_text: str):
        """
        Update the tooltip text.

        Args:
            new_text: New text to display
        """
        self.text = new_text
        # If tooltip is currently showing, hide and re-show with new text
        if self.tooltip_window:
            self._hide_tooltip()
            self._show_tooltip()

    def destroy(self):
        """Remove the tooltip and unbind events."""
        self._cancel_schedule()
        self._hide_tooltip()
        self.widget.unbind("<Enter>")
        self.widget.unbind("<Leave>")
        self.widget.unbind("<Button>")


def create_tooltip(widget: tk.Widget, text: str, **kwargs) -> ToolTip:
    """
    Convenience function to create a tooltip.

    Args:
        widget: Widget to attach tooltip to
        text: Tooltip text
        **kwargs: Additional ToolTip constructor arguments

    Returns:
        ToolTip: The created tooltip instance
    """
    return ToolTip(widget, text, **kwargs)


class BalloonTip(ToolTip):
    """
    Alternative name for ToolTip (for backwards compatibility).

    This is just an alias for the ToolTip class.
    """
    pass
