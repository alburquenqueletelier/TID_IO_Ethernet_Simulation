"""
Commands tab module.

This module provides the Commands tab component which handles:
- Command configuration interface
- Command sending with repetitions
- Command management (add/remove command instances)
- Macro save/load functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict

from ..widgets import ScrollableFrame
from ...core import StateManager, COMMAND_CONFIGS, get_command_byte
from ...network import PacketSender, PacketInfo
from ...storage import MacroManager


class CommandsTab(ttk.Frame):
    """
    Commands tab component.

    This tab provides the command configuration and sending interface:
    - MC selection
    - Command list with drag & drop reordering
    - Command configuration (enable/disable, state selection)
    - Batch command sending with repetitions
    - Macro management
    """

    def __init__(
        self,
        parent,
        state_manager: StateManager,
        packet_sender: PacketSender,
        macro_manager: MacroManager,
        parent_window=None
    ):
        """
        Initialize the CommandsTab.

        Args:
            parent: Parent widget (typically a Notebook)
            state_manager: StateManager instance
            packet_sender: PacketSender for sending commands
            macro_manager: MacroManager for managing macros
            parent_window: Main window for centering modals
        """
        super().__init__(parent)

        # Dependencies
        self.state_manager = state_manager
        self.packet_sender = packet_sender
        self.macro_manager = macro_manager
        self.parent_window = parent_window or parent.winfo_toplevel()

        # UI state
        self.selected_mc_mac = None
        self.commands_state = {}  # {cmd_name: {"enabled": BooleanVar, "state": state_value, "on_btn": btn, "off_btn": btn}}
        self.command_rows = []  # List of row frames
        self.sending_commands = False

        # Drag and drop state
        self.dragging = False
        self.drag_source = None
        self.drag_start_y = 0

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the commands tab UI."""
        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill="both", expand=True)

        # Header section
        self.create_header_section(main_container)

        # Commands section (scrollable)
        self.create_commands_section(main_container)

        # Control section
        self.create_control_section(main_container)

    def create_header_section(self, parent):
        """Create header with MC selection."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", padx=10, pady=10)

        # Title
        title_label = tk.Label(
            header_frame,
            text="Command Configuration",
            font=("Arial", 16, "bold")
        )
        title_label.pack()

        # MC Selection
        mc_select_frame = ttk.Frame(header_frame)
        mc_select_frame.pack(fill="x", pady=10)

        mc_label = tk.Label(
            mc_select_frame,
            text="Select Microcontroller:",
            font=("Arial", 11)
        )
        mc_label.pack(side="left", padx=5)

        self.mc_combo = ttk.Combobox(
            mc_select_frame,
            width=40,
            state="readonly"
        )
        self.mc_combo.pack(side="left", padx=5)
        self.mc_combo.bind("<<ComboboxSelected>>", self.on_mc_selected)

        # Refresh MC list button
        refresh_btn = tk.Button(
            mc_select_frame,
            text="🔄",
            command=self.refresh_mc_list,
            font=("Arial", 10)
        )
        refresh_btn.pack(side="left", padx=2)

        # Action buttons frame (below MC selection)
        action_buttons_frame = ttk.Frame(header_frame)
        action_buttons_frame.pack(fill="x", pady=5)

        # Manage Commands button
        manage_commands_btn = tk.Button(
            action_buttons_frame,
            text="Manage Commands",
            command=self.manage_commands,
            bg="#f1c40f",
            fg="black",
            font=("Arial", 10, "bold"),
            width=20
        )
        manage_commands_btn.pack(side="left", padx=5)

        # Save Macro button
        save_macro_btn = tk.Button(
            action_buttons_frame,
            text="💾 Save Macro",
            command=self.save_macro,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=20
        )
        save_macro_btn.pack(side="left", padx=5)

        # Load Macro button
        load_macro_btn = tk.Button(
            action_buttons_frame,
            text="📂 Load Macro",
            command=self.load_macro,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=20
        )
        load_macro_btn.pack(side="left", padx=5)

    def create_commands_section(self, parent):
        """Create scrollable commands table section."""
        commands_frame = ttk.LabelFrame(
            parent,
            text="Commands Configuration",
            padding=10
        )
        commands_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Table container
        table_container = tk.Frame(commands_frame)
        table_container.pack(fill="both", expand=True)

        # Headers (fixed at top)
        header_frame = tk.Frame(table_container, relief="ridge", borderwidth=1)
        header_frame.pack(fill="x")

        # Checkbox "Select All"
        def toggle_all_commands():
            value = self.select_all_cb_var.get()
            for cmd_state in self.commands_state.values():
                cmd_state["enabled"].set(value)

        self.select_all_cb_var = tk.BooleanVar(value=False)
        select_all_cb = tk.Checkbutton(
            header_frame,
            variable=self.select_all_cb_var,
            command=toggle_all_commands,
            width=2
        )
        select_all_cb.grid(row=0, column=0, padx=1, pady=2)

        tk.Label(
            header_frame, text="Comando", width=58, font=("Arial", 8, "bold")
        ).grid(row=0, column=1)
        tk.Label(
            header_frame, text="ON/HIGH/GLOBAL", width=15, font=("Arial", 8, "bold"), padx=10
        ).grid(row=0, column=2)
        tk.Label(header_frame, text="OFF/LOW/LOCAL", width=16, font=("Arial", 8, "bold")).grid(
            row=0, column=3
        )

        # Scrollable canvas for commands table
        canvas_container = tk.Frame(table_container)
        canvas_container.pack(fill="both", expand=True)

        self.commands_canvas = tk.Canvas(canvas_container, borderwidth=0, highlightthickness=0)
        commands_scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=self.commands_canvas.yview)
        self.commands_table_frame = tk.Frame(self.commands_canvas)

        self.commands_table_frame.bind(
            "<Configure>", lambda e: self.commands_canvas.configure(scrollregion=self.commands_canvas.bbox("all"))
        )

        self.canvas_window = self.commands_canvas.create_window((0, 0), window=self.commands_table_frame, anchor="nw")
        self.commands_canvas.configure(yscrollcommand=commands_scrollbar.set)

        self.commands_canvas.pack(side="left", fill="both", expand=True)
        commands_scrollbar.pack(side="right", fill="y")

        # Adjust canvas width when resized
        def configure_canvas_width(event):
            self.commands_canvas.itemconfig(self.canvas_window, width=event.width)

        self.commands_canvas.bind("<Configure>", configure_canvas_width)

        # Bind mousewheel scrolling
        def on_mousewheel(event):
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                self.commands_canvas.yview_scroll(1, "units")
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                self.commands_canvas.yview_scroll(-1, "units")
            return "break"

        self.commands_canvas.bind("<MouseWheel>", on_mousewheel)
        self.commands_canvas.bind("<Button-4>", on_mousewheel)
        self.commands_canvas.bind("<Button-5>", on_mousewheel)

        # Store mousewheel callback for later binding to children
        self.table_mousewheel_callback = on_mousewheel

        # Initially empty - will be populated when MC is selected
        self.rebuild_command_table()

    def create_control_section(self, parent):
        """Create control buttons section."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Container for send button and review checkbox
        send_container = tk.Frame(control_frame)
        send_container.pack(pady=5)

        # Send commands button
        self.send_btn = tk.Button(
            send_container,
            text="Send Commands",
            command=self.send_commands,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=20
        )
        self.send_btn.pack(side="left", padx=(0, 10))

        # Review checkbox
        self.show_review_var = tk.BooleanVar(value=False)
        review_checkbox = tk.Checkbutton(
            send_container,
            text="Review",
            variable=self.show_review_var,
            font=("Arial", 10)
        )
        review_checkbox.pack(side="left")

    def refresh_mc_list(self):
        """Refresh the list of available microcontrollers."""
        mcs = self.state_manager.get_all_registered_mcs()
        mc_options = [f"{mc.label} ({mc.mac_destiny})" for mc in mcs]

        current_value = self.mc_combo.get()
        self.mc_combo['values'] = mc_options

        # Restore selection if still valid
        if current_value in mc_options:
            self.mc_combo.set(current_value)
        elif mc_options:
            self.mc_combo.set(mc_options[0])
            self.on_mc_selected(None)

    def on_mc_selected(self, event):
        """Handle MC selection change."""
        selection = self.mc_combo.get()

        if not selection:
            self.selected_mc_mac = None
            return

        # Extract MAC from "Label (MAC)" format
        try:
            mac_destiny = selection.split("(")[1].rstrip(")")
            mc = self.state_manager.get_mc_by_destiny(mac_destiny)

            if mc:
                self.selected_mc_mac = mc.mac_source
                self.load_mc_commands(mc.mac_source)
        except (IndexError, AttributeError):
            self.selected_mc_mac = None

    def load_mc_commands(self, mac_source: str):
        """
        Load command configuration for a microcontroller.

        Args:
            mac_source: Source MAC address of MC
        """
        self.rebuild_command_table()

    def rebuild_command_table(self):
        """Rebuild command table based on selected MC's command_configs and last_state."""
        # Clear existing rows
        for row_data in self.command_rows:
            row_data["frame"].destroy()
        self.command_rows.clear()
        self.commands_state.clear()

        # Get selected MC
        if not self.selected_mc_mac:
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            return

        command_configs = mc.command_configs if hasattr(mc, 'command_configs') else {}
        last_state = mc.last_state if hasattr(mc, 'last_state') else {}

        # If no commands configured, show empty table
        if not command_configs:
            return

        # Create rows for each command
        for cmd_name, cmd_config in command_configs.items():
            self.create_command_table_row(cmd_name, cmd_config, last_state.get(cmd_name, ""))

        # Bind mousewheel scrolling to all new widgets
        self.bind_mousewheel_to_table_widgets()

    def bind_mousewheel_to_table_widgets(self):
        """Recursively bind mousewheel scrolling to all table widgets."""
        if not hasattr(self, 'table_mousewheel_callback'):
            return

        def bind_recursive(widget):
            try:
                # Skip spinbox widgets to preserve their own scrolling
                if not isinstance(widget, (tk.Spinbox, ttk.Combobox)):
                    widget.bind("<MouseWheel>", self.table_mousewheel_callback)
                    widget.bind("<Button-4>", self.table_mousewheel_callback)
                    widget.bind("<Button-5>", self.table_mousewheel_callback)

                for child in widget.winfo_children():
                    bind_recursive(child)
            except:
                pass

        bind_recursive(self.commands_table_frame)

    def create_command_table_row(self, cmd_name: str, cmd_config: Dict, last_state_value: str):
        """Create a table row for a command."""
        bg_color = "#f7f7f7"
        row_frame = tk.Frame(self.commands_table_frame, relief="ridge", borderwidth=1, bg=bg_color, height=35)
        row_frame.pack(fill="x")
        row_frame.pack_propagate(False)
        row_frame.grid_propagate(False)
        row_frame.grid_rowconfigure(0, weight=1)

        # Extract base command (without #N)
        base_cmd = cmd_name.split('#')[0] if '#' in cmd_name else cmd_name

        # Commands that don't have buttons (automatic)
        auto_commands = ["X_FF_Reset", "X_02_TestTrigger", "X_03_RO_Single"]
        repeatable_commands = ["X_02_TestTrigger", "X_03_RO_Single"]

        # Determine if command checkbox is enabled (check for saved enabled state)
        mc = self.state_manager.get_mc(self.selected_mc_mac)
        saved_enabled = False
        if mc and hasattr(mc, 'last_state'):
            saved_enabled = mc.last_state.get(f"{cmd_name}_enabled", False)

        self.commands_state[cmd_name] = {
            "enabled": tk.BooleanVar(value=saved_enabled),
            "state": last_state_value if last_state_value else None,
        }

        # Checkbox
        checkbox = tk.Checkbutton(
            row_frame, variable=self.commands_state[cmd_name]["enabled"], bg=bg_color
        )
        checkbox.grid(row=0, column=0, padx=5, sticky="")

        # Command name
        tk.Label(
            row_frame, text=cmd_name, width=50, font=("Arial", 9), bg=bg_color
        ).grid(row=0, column=1, sticky="w")

        col_offset = 2

        # Check if this is an auto command
        if base_cmd in auto_commands:
            # No buttons for auto commands
            self.commands_state[cmd_name]["on_btn"] = None
            self.commands_state[cmd_name]["off_btn"] = None

            # Auto commands are always "ON" when enabled
            if not last_state_value:
                self.commands_state[cmd_name]["state"] = "ON"

            # For auto commands, Repit and Delay start at col_offset (where buttons would be)
            # Repit field (only for repeatable commands, NOT for Reset)
            if base_cmd in repeatable_commands:
                # Get saved repetitions from MC's last_state
                mc = self.state_manager.get_mc(self.selected_mc_mac)
                saved_reps = 1
                if mc and hasattr(mc, 'last_state'):
                    saved_reps = mc.last_state.get(f"{cmd_name}_reps", 1)

                repit_var = tk.IntVar(value=saved_reps)
                self.commands_state[cmd_name]["repetitions"] = repit_var

                # Label
                tk.Label(
                    row_frame,
                    text="Repit:",
                    font=("Arial", 8),
                    bg=bg_color
                ).grid(row=0, column=col_offset, padx=(5, 2), sticky="e")
                col_offset += 1

                # Spinbox
                spinbox = tk.Spinbox(
                    row_frame,
                    from_=1,
                    to=1000,
                    textvariable=repit_var,
                    width=5,
                    justify="center"
                )
                spinbox.grid(row=0, column=col_offset, padx=2)
                col_offset += 1
            elif base_cmd == "X_FF_Reset":
                # Reset always has 1 repetition (implicit) - no UI shown
                self.commands_state[cmd_name]["repetitions"] = tk.IntVar(value=1)

            # Delay (s) field for auto commands
            mc = self.state_manager.get_mc(self.selected_mc_mac)
            saved_delay = 1.0
            if mc and hasattr(mc, 'last_state'):
                saved_delay = mc.last_state.get(f"{cmd_name}_delta", 1.0)

            delay_var = tk.DoubleVar(value=saved_delay)
            self.commands_state[cmd_name]["delta_time"] = delay_var

            # Label
            tk.Label(
                row_frame,
                text="Delay (s):",
                font=("Arial", 8),
                bg=bg_color
            ).grid(row=0, column=col_offset, padx=(5, 2), sticky="e")
            col_offset += 1

            # Spinbox
            delay_spinbox = tk.Spinbox(
                row_frame,
                from_=0.1,
                to=60.0,
                increment=0.1,
                textvariable=delay_var,
                width=6,
                justify="center",
                format="%.1f"
            )
            delay_spinbox.grid(row=0, column=col_offset, padx=2)

        else:
            # Regular commands with buttons
            # Get button keys
            btn_keys = list(cmd_config.keys())
            btn1_text = btn_keys[0] if len(btn_keys) > 0 else "ON"
            btn2_text = btn_keys[1] if len(btn_keys) > 1 else "OFF"

            # ON button
            on_btn = tk.Button(
                row_frame,
                text=btn1_text,
                width=8,
                height=1,
                bg="#e0e0e0",
                command=lambda cmd=cmd_name, state=btn1_text: self.toggle_command_state(cmd, state),
            )
            on_btn.grid(row=0, column=col_offset, padx=2, pady=2)
            col_offset += 1
            self.commands_state[cmd_name]["on_btn"] = on_btn

            # OFF button if has two options
            if len(btn_keys) > 1:
                off_btn = tk.Button(
                    row_frame,
                    text=btn2_text,
                    width=8,
                    height=1,
                    bg="#e0e0e0",
                    command=lambda cmd=cmd_name, state=btn2_text: self.toggle_command_state(cmd, state),
                )
                off_btn.grid(row=0, column=col_offset, padx=2, pady=2)
                self.commands_state[cmd_name]["off_btn"] = off_btn
                col_offset += 1
            else:
                self.commands_state[cmd_name]["off_btn"] = None
                # Empty space for alignment
                tk.Label(row_frame, text="", width=12, bg=bg_color).grid(row=0, column=col_offset)
                col_offset += 1

            # Load saved state if exists
            if last_state_value == btn1_text:
                on_btn.config(bg="#27ae60", relief="sunken")
                if self.commands_state[cmd_name].get("off_btn"):
                    self.commands_state[cmd_name]["off_btn"].config(bg="#e0e0e0", relief="raised")
            elif last_state_value == btn2_text:
                if self.commands_state[cmd_name].get("off_btn"):
                    self.commands_state[cmd_name]["off_btn"].config(bg="#e74c3c", relief="sunken")
                on_btn.config(bg="#e0e0e0", relief="raised")
            else:
                on_btn.config(bg="#e0e0e0", relief="raised")
                if self.commands_state[cmd_name].get("off_btn"):
                    self.commands_state[cmd_name]["off_btn"].config(bg="#e0e0e0", relief="raised")

            # For regular commands, repetitions are always 1
            self.commands_state[cmd_name]["repetitions"] = tk.IntVar(value=1)

            # Delay (s) field for regular commands
            mc = self.state_manager.get_mc(self.selected_mc_mac)
            saved_delay = 1.0
            if mc and hasattr(mc, 'last_state'):
                saved_delay = mc.last_state.get(f"{cmd_name}_delta", 1.0)

            delay_var = tk.DoubleVar(value=saved_delay)
            self.commands_state[cmd_name]["delta_time"] = delay_var

            # Label
            tk.Label(
                row_frame,
                text="Delay (s):",
                font=("Arial", 8),
                bg=bg_color
            ).grid(row=0, column=col_offset, padx=(10, 2), sticky="e")
            col_offset += 1

            # Spinbox
            delay_spinbox = tk.Spinbox(
                row_frame,
                from_=0.1,
                to=60.0,
                increment=0.1,
                textvariable=delay_var,
                width=6,
                justify="center",
                format="%.1f"
            )
            delay_spinbox.grid(row=0, column=col_offset, padx=2)

        self.command_rows.append({"frame": row_frame, "cmd_name": cmd_name})

        # Setup drag and drop for this row
        self.setup_drag_and_drop(row_frame, cmd_name)

    def setup_drag_and_drop(self, row_frame, cmd_name):
        """Configure drag and drop for a command row."""
        # Bind events only to the frame (not to buttons or checkboxes)
        row_frame.bind("<Enter>", lambda e: row_frame.config(cursor="hand1"))
        row_frame.bind("<Leave>", lambda e: row_frame.config(cursor=""))
        row_frame.bind("<Button-1>", lambda e: self.start_drag(e, row_frame, cmd_name))
        row_frame.bind("<B1-Motion>", lambda e: self.do_drag(e, row_frame))
        row_frame.bind("<ButtonRelease-1>", lambda e: self.end_drag(e, row_frame))

    def start_drag(self, event, row_frame, cmd_name):
        """Start dragging a command row."""
        # Only start if not clicking on a button or checkbox
        widget = event.widget
        if isinstance(widget, (tk.Button, tk.Checkbutton)):
            return

        self.dragging = True
        self.drag_source = (row_frame, cmd_name)
        self.drag_start_y = event.y_root

        # Change appearance of dragging row
        row_frame.config(relief="raised", borderwidth=3, bg="#e3f2fd")

    def do_drag(self, event, row_frame):
        """Handle movement during drag."""
        if not self.dragging:
            return

        # Calculate which row is under the cursor
        for frame_data in self.command_rows:
            frame = frame_data["frame"]
            frame_y = frame.winfo_rooty()
            frame_height = frame.winfo_height()

            if frame_y <= event.y_root <= frame_y + frame_height:
                # Highlight the row being hovered
                if frame != row_frame:
                    frame.config(bg="#fff3e0")
            else:
                # Restore original color
                if frame != row_frame:
                    frame.config(bg="#f7f7f7")

    def end_drag(self, event, row_frame):
        """Finish drag and reorder commands."""
        if not self.dragging:
            return

        self.dragging = False

        # Restore appearance
        row_frame.config(relief="ridge", borderwidth=1, bg="#f7f7f7")

        # Find which row was dropped on
        target_row = None
        target_index = None

        for i, frame_data in enumerate(self.command_rows):
            frame = frame_data["frame"]
            frame.config(bg="#f7f7f7")  # Restore all

            frame_y = frame.winfo_rooty()
            frame_height = frame.winfo_height()

            if frame_y <= event.y_root <= frame_y + frame_height:
                target_row = frame_data
                target_index = i
                break

        # If dropped on another row, reorder
        if target_row and target_row["cmd_name"] != self.drag_source[1]:
            self.reorder_commands(self.drag_source[1], target_row["cmd_name"])

        self.drag_source = None

    def reorder_commands(self, source_cmd, target_cmd):
        """Reorder commands in the list and update the UI."""
        if not self.selected_mc_mac:
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            return

        # Find source and target indices
        source_idx = None
        target_idx = None
        for i, row_data in enumerate(self.command_rows):
            if row_data["cmd_name"] == source_cmd:
                source_idx = i
            if row_data["cmd_name"] == target_cmd:
                target_idx = i

        if source_idx is None or target_idx is None:
            return

        # Save current UI state temporarily (before rebuild)
        temp_state = {}
        for cmd_name, cmd_state in self.commands_state.items():
            temp_state[cmd_name] = {
                "enabled": cmd_state["enabled"].get(),
                "state": cmd_state.get("state"),
            }
            if "repetitions" in cmd_state:
                temp_state[cmd_name]["repetitions"] = cmd_state["repetitions"].get()
            if "delta_time" in cmd_state:
                temp_state[cmd_name]["delta_time"] = cmd_state["delta_time"].get()

        # Reorder in visual list
        item = self.command_rows.pop(source_idx)
        self.command_rows.insert(target_idx, item)

        # Reorder in MC's command_configs
        if hasattr(mc, 'command_configs'):
            configs_list = list(mc.command_configs.items())
            config_item = configs_list.pop(source_idx)
            configs_list.insert(target_idx, config_item)
            mc.command_configs = dict(configs_list)

            # Save to database
            self.state_manager._save_to_db()

        # Rebuild UI
        self.rebuild_command_table()

        # Restore temporary state
        for cmd_name, saved_state in temp_state.items():
            if cmd_name in self.commands_state:
                # Restore enabled
                self.commands_state[cmd_name]["enabled"].set(saved_state["enabled"])

                # Restore state
                if saved_state["state"]:
                    self.commands_state[cmd_name]["state"] = saved_state["state"]

                    # Restore button visuals
                    self.update_button_visuals(cmd_name, saved_state["state"])

                # Restore repetitions
                if "repetitions" in saved_state and "repetitions" in self.commands_state[cmd_name]:
                    self.commands_state[cmd_name]["repetitions"].set(saved_state["repetitions"])

                # Restore delta_time
                if "delta_time" in saved_state and "delta_time" in self.commands_state[cmd_name]:
                    self.commands_state[cmd_name]["delta_time"].set(saved_state["delta_time"])

    def update_button_visuals(self, cmd_name: str, state: str):
        """Update button visual state without triggering callbacks."""
        if cmd_name not in self.commands_state:
            return

        cmd_state = self.commands_state[cmd_name]
        on_btn = cmd_state.get("on_btn")
        off_btn = cmd_state.get("off_btn")

        if not on_btn:
            return

        # Reset both buttons
        on_btn.config(bg="#e0e0e0", relief="raised")
        if off_btn:
            off_btn.config(bg="#e0e0e0", relief="raised")

        # Highlight selected button
        cmd_config = self.get_mc_command_config(cmd_name)
        if cmd_config:
            btn_keys = list(cmd_config.keys())
            if state == btn_keys[0]:
                on_btn.config(bg="#27ae60", relief="sunken")
            elif len(btn_keys) > 1 and state == btn_keys[1]:
                if off_btn:
                    off_btn.config(bg="#e74c3c", relief="sunken")

    def toggle_command_state(self, cmd_name: str, state: str):
        """Toggle command state button."""
        if cmd_name not in self.commands_state:
            return

        cmd_state = self.commands_state[cmd_name]
        cmd_state["state"] = state
        cmd_state["enabled"].set(True)

        # Update button visuals
        self.update_button_visuals(cmd_name, state)

    def get_mc_command_config(self, cmd_name: str) -> Dict:
        """Get command config for selected MC."""
        if not self.selected_mc_mac:
            return {}
        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc or not hasattr(mc, 'command_configs'):
            return {}
        return mc.command_configs.get(cmd_name, {})

    def send_commands(self):
        """Send configured commands to selected MC or cancel sending."""
        # If currently sending, cancel the operation
        if hasattr(self, 'sending_commands') and self.sending_commands:
            self.packet_sender.cancel()
            return

        if not self.selected_mc_mac:
            messagebox.showwarning(
                "No MC Selected",
                "Please select a microcontroller first."
            )
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            messagebox.showerror("Error", "Selected MC not found.")
            return

        # Collect enabled commands
        packets = []
        for cmd_name, cmd_state in self.commands_state.items():
            if not cmd_state["enabled"].get():
                continue  # Skip disabled commands

            state = cmd_state.get("state")
            if not state:
                continue

            # Get command config
            cmd_config = self.get_mc_command_config(cmd_name)
            if not cmd_config:
                continue

            # Get the actual command name from config
            command_name = cmd_config.get(state)
            if not command_name:
                continue

            # Get repetitions (default 1)
            repetitions = cmd_state.get("repetitions", tk.IntVar(value=1)).get()

            # Get delay in seconds and convert to milliseconds
            delay_seconds = cmd_state.get("delta_time", tk.DoubleVar(value=1.0)).get()
            delay_ms = int(delay_seconds * 1000)

            # Get command byte
            try:
                command_byte = get_command_byte(command_name)

                packet = PacketInfo(
                    mac_source=mc.mac_source,
                    mac_destiny=mc.mac_destiny,
                    interface=mc.interface_destiny,
                    command_byte=command_byte,
                    command_name=command_name,
                    repetitions=repetitions,
                    delay_ms=delay_ms
                )
                packets.append(packet)
            except KeyError:
                continue

        if not packets:
            messagebox.showwarning(
                "No Commands",
                "No commands are enabled. Enable commands first."
            )
            return

        # Show review modal if checkbox is checked
        if self.show_review_var.get():
            cmd_list = "\n".join([f"  • {p.command_name}" for p in packets])
            info_msg = f"""{len(packets)} commands will be sent:
{cmd_list}

MC Destiny: {mc.label}
Interface: {mc.interface_destiny}"""

            if not messagebox.askyesno("Summary Window", info_msg):
                return

        # Save current state to database before sending
        self.save_current_state_to_db()

        # Send packets
        self.sending_commands = True
        self.send_btn.config(text="⏹ Cancel", bg="#e74c3c")

        def on_complete(success):
            self.sending_commands = False
            self.send_btn.config(text="Send Commands", bg="#4CAF50")

            if success:
                messagebox.showinfo("Success", "Commands sent successfully!")
            else:
                messagebox.showwarning("Cancelled", "Command sending was cancelled.")

        # Send asynchronously
        self.packet_sender.send_packets_batch_async(packets, on_complete=on_complete)

    def save_current_state_to_db(self):
        """Save current command states, repetitions, and delays to database."""
        if not self.selected_mc_mac:
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            return

        # Update last_state with current values
        if not hasattr(mc, 'last_state'):
            mc.last_state = {}

        for cmd_name, cmd_state in self.commands_state.items():
            # Save state
            state = cmd_state.get("state")
            if state:
                mc.last_state[cmd_name] = state

            # Save checkbox enabled state
            if "enabled" in cmd_state:
                mc.last_state[f"{cmd_name}_enabled"] = cmd_state["enabled"].get()

            # Save repetitions
            if "repetitions" in cmd_state:
                mc.last_state[f"{cmd_name}_reps"] = cmd_state["repetitions"].get()

            # Save delay
            if "delta_time" in cmd_state:
                mc.last_state[f"{cmd_name}_delta"] = cmd_state["delta_time"].get()

        # Save to database
        self.state_manager._save_to_db()

    def manage_commands(self):
        """Open modal to manage commands (add/remove command instances)."""
        if not self.selected_mc_mac:
            messagebox.showwarning("Validation", "Must select a Microcontroller to manage commands.")
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            messagebox.showwarning("Validation", "Microcontroller not found.")
            return

        # Universe of available commands from COMMAND_CONFIGS
        from ...core import COMMAND_CONFIGS
        all_commands = list(COMMAND_CONFIGS.keys())

        # Count current instances of each command
        current_commands = list(mc.command_configs.keys()) if hasattr(mc, 'command_configs') else []
        command_counts = {}
        for cmd in all_commands:
            count = 0
            for key in current_commands:
                base_cmd = key.split('#')[0] if '#' in key else key
                if base_cmd == cmd:
                    count += 1
            command_counts[cmd] = count

        # Create modal
        modal = tk.Toplevel(self.parent_window)
        modal.title("Manage Commands")
        modal.transient(self.parent_window)
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")

        # Center modal (wider to show full command text)
        self.center_modal_on_parent(modal, 550, 520)

        tk.Label(modal, text="Manage microcontroller commands", font=("Arial", 12, "bold"), bg="#f7f7f7").pack(pady=(20, 10))

        # Frame with scroll for command list
        canvas_frame = tk.Frame(modal, bg="#f7f7f7")
        canvas_frame.pack(fill="both", expand=True, padx=4, pady=10)

        canvas = tk.Canvas(canvas_frame, bg="#f7f7f7", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        cb_frame = tk.Frame(canvas, bg="#f7f7f7")

        cb_frame.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        modal_canvas_window = canvas.create_window((0, 0), window=cb_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Adjust canvas width when resized
        def configure_modal_canvas_width(event):
            canvas.itemconfig(modal_canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_modal_canvas_width)

        # Bind mousewheel scrolling to modal canvas
        def on_modal_mousewheel(event):
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                canvas.yview_scroll(-1, "units")
            return "break"

        canvas.bind("<MouseWheel>", on_modal_mousewheel)
        canvas.bind("<Button-4>", on_modal_mousewheel)
        canvas.bind("<Button-5>", on_modal_mousewheel)

        # Also bind to the frame for better scroll coverage
        def bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", on_modal_mousewheel)
            widget.bind("<Button-4>", on_modal_mousewheel)
            widget.bind("<Button-5>", on_modal_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child)

        # Bind after widgets are created
        modal.after(100, lambda: bind_mousewheel_recursive(cb_frame))

        # Variables for checkboxes and instances
        command_vars = {}
        instance_vars = {}

        # Checkbox select/deselect all
        select_all_var = tk.BooleanVar(value=False)
        def toggle_all():
            value = select_all_var.get()
            for var in command_vars.values():
                var.set(value)

        header_frame = tk.Frame(cb_frame, bg="#f7f7f7")
        header_frame.pack(fill="x", pady=(0, 8))

        select_all_cb = tk.Checkbutton(
            header_frame,
            text="Select/Deselect all",
            variable=select_all_var,
            command=toggle_all,
            anchor="w",
            bg="#f7f7f7",
            font=("Arial", 10, "bold"),
            width=50
        )
        select_all_cb.grid(row=0, column=0, sticky="w")

        tk.Label(header_frame, text="Instances", font=("Arial", 10, "bold"), bg="#f7f7f7").grid(row=0, column=1, padx=(10, 0))

        # List commands with checkboxes and instance inputs
        for cmd_name in all_commands:
            var = tk.BooleanVar(value=command_counts[cmd_name] > 0)
            command_vars[cmd_name] = var

            instance_var = tk.IntVar(value=max(1, command_counts[cmd_name]))
            instance_vars[cmd_name] = instance_var

            row_frame = tk.Frame(cb_frame, bg="#f7f7f7")
            row_frame.pack(fill="x", pady=2)

            cb = tk.Checkbutton(row_frame, text=cmd_name, variable=var, anchor="w", bg="#f7f7f7", width=50)
            cb.grid(row=0, column=0, sticky="w")

            spinbox = tk.Spinbox(
                row_frame,
                from_=1,
                to=100,
                textvariable=instance_var,
                width=5,
                justify="center"
            )
            spinbox.grid(row=0, column=1, padx=(10, 0))

        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(fill="x", pady=(20, 20))

        def accept():
            # Save current UI state (including unsaved changes)
            current_ui_state = {}
            for cmd_name, cmd_state in self.commands_state.items():
                current_ui_state[cmd_name] = {
                    "enabled": cmd_state["enabled"].get(),
                    "state": cmd_state.get("state"),
                }
                if "repetitions" in cmd_state:
                    current_ui_state[cmd_name]["repetitions"] = cmd_state["repetitions"].get()
                if "delta_time" in cmd_state:
                    current_ui_state[cmd_name]["delta_time"] = cmd_state["delta_time"].get()

            # Get current command_configs to preserve order
            current_configs = mc.command_configs if hasattr(mc, 'command_configs') else {}
            current_order = list(current_configs.keys())

            # Determine desired instances for each command
            desired_instances = {}
            for cmd in all_commands:
                if command_vars[cmd].get():
                    desired_instances[cmd] = instance_vars[cmd].get()
                else:
                    desired_instances[cmd] = 0

            # Build new command list preserving order
            new_command_configs = {}
            used_commands = {cmd: 0 for cmd in all_commands}  # Track how many instances we've added

            # First, keep existing commands in their current order
            for key in current_order:
                base_cmd = key.split('#')[0] if '#' in key else key

                if base_cmd in desired_instances and used_commands[base_cmd] < desired_instances[base_cmd]:
                    # Keep this instance
                    used_commands[base_cmd] += 1

                    # Generate new key
                    if desired_instances[base_cmd] > 1:
                        new_key = f"{base_cmd}#{used_commands[base_cmd]}"
                    else:
                        new_key = base_cmd

                    new_command_configs[new_key] = COMMAND_CONFIGS[base_cmd]

            # Add new instances at the end (for commands that need more instances)
            for cmd in all_commands:
                if cmd in desired_instances:
                    while used_commands[cmd] < desired_instances[cmd]:
                        used_commands[cmd] += 1

                        if desired_instances[cmd] > 1:
                            new_key = f"{cmd}#{used_commands[cmd]}"
                        else:
                            new_key = cmd

                        new_command_configs[new_key] = COMMAND_CONFIGS[cmd]

            mc.command_configs = new_command_configs

            # Update last_state from both saved state and current UI state
            last_state = mc.last_state if hasattr(mc, 'last_state') else {}
            new_last_state = {}

            # Map old keys to new keys
            old_to_new_map = {}
            old_keys = list(current_order)
            new_keys = list(new_command_configs.keys())

            # Create mapping for existing commands
            cmd_counters = {}
            for old_key in old_keys:
                base_cmd = old_key.split('#')[0] if '#' in old_key else old_key
                if base_cmd not in cmd_counters:
                    cmd_counters[base_cmd] = 0
                cmd_counters[base_cmd] += 1

                # Find corresponding new key
                new_key_index = None
                temp_counter = 0
                for i, new_key in enumerate(new_keys):
                    new_base = new_key.split('#')[0] if '#' in new_key else new_key
                    if new_base == base_cmd:
                        temp_counter += 1
                        if temp_counter == cmd_counters[base_cmd]:
                            new_key_index = i
                            break

                if new_key_index is not None:
                    old_to_new_map[old_key] = new_keys[new_key_index]

            # Copy states using the mapping
            for old_key, new_key in old_to_new_map.items():
                # Copy from UI state first (has priority)
                if old_key in current_ui_state:
                    ui_state = current_ui_state[old_key]
                    if ui_state["state"]:
                        new_last_state[new_key] = ui_state["state"]
                    new_last_state[f"{new_key}_enabled"] = ui_state["enabled"]
                    if "repetitions" in ui_state:
                        new_last_state[f"{new_key}_reps"] = ui_state["repetitions"]
                    if "delta_time" in ui_state:
                        new_last_state[f"{new_key}_delta"] = ui_state["delta_time"]
                # Otherwise copy from saved state
                else:
                    if old_key in last_state:
                        new_last_state[new_key] = last_state[old_key]
                    if f"{old_key}_enabled" in last_state:
                        new_last_state[f"{new_key}_enabled"] = last_state[f"{old_key}_enabled"]
                    if f"{old_key}_reps" in last_state:
                        new_last_state[f"{new_key}_reps"] = last_state[f"{old_key}_reps"]
                    if f"{old_key}_delta" in last_state:
                        new_last_state[f"{new_key}_delta"] = last_state[f"{old_key}_delta"]

            mc.last_state = new_last_state

            # Save to database
            self.state_manager._save_to_db()

            # Rebuild table
            self.rebuild_command_table()
            modal.destroy()

        add_btn = tk.Button(btn_frame, text="Add", font=("Arial", 10, "bold"), bg="#27ae60", fg="white", command=accept)
        add_btn.pack(side="left", padx=(40, 10), ipadx=10)

        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Arial", 10, "bold"), bg="#e74c3c", fg="white", command=modal.destroy)
        cancel_btn.pack(side="right", padx=(10, 40), ipadx=10)

    def center_modal_on_parent(self, modal, width, height):
        """Center a modal over the main window.

        Args:
            modal: Toplevel window to center
            width: Modal width
            height: Modal height
        """
        modal.update_idletasks()

        # Get position and size of main window
        parent_x = self.parent_window.winfo_x()
        parent_y = self.parent_window.winfo_y()
        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()

        # Calculate centered position over parent
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        modal.geometry(f"{width}x{height}+{x}+{y}")

    def save_macro(self):
        """Save current command configuration as a macro."""
        if not self.selected_mc_mac:
            messagebox.showwarning("Validation", "Must select a Microcontroller first.")
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            messagebox.showwarning("Validation", "Microcontroller not found.")
            return

        # Verify there are configured commands
        command_configs = mc.command_configs if hasattr(mc, 'command_configs') else {}
        if not command_configs:
            messagebox.showwarning("Validation", "No commands configured to save.")
            return

        # Get universal macros
        existing_macros = self.state_manager.list_macros()

        # Calculate modal height based on number of macros
        base_height = 250  # Base height (title, input, buttons)
        if existing_macros:
            macros_section_height = min(250, len(existing_macros) * 35 + 60)  # Max 250px for list
        else:
            macros_section_height = 0

        modal_height = base_height + macros_section_height

        # Modal to request macro name
        modal = tk.Toplevel(self.parent_window)
        modal.title("Save Macro")
        modal.transient(self.parent_window)
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")

        # Center modal
        self.center_modal_on_parent(modal, 500, modal_height)

        tk.Label(
            modal,
            text="Save Macro",
            font=("Arial", 12, "bold"),
            bg="#f7f7f7"
        ).pack(pady=(20, 10))

        # Frame for name input
        name_frame = tk.Frame(modal, bg="#f7f7f7")
        name_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            name_frame,
            text="Macro name:",
            font=("Arial", 10),
            bg="#f7f7f7"
        ).pack(anchor="w")

        name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=name_var, font=("Arial", 10))
        name_entry.pack(fill="x", pady=(5, 0))
        name_entry.focus()

        # Existing macros section (if any)
        if existing_macros:
            tk.Label(
                modal,
                text="Saved macros (click to select):",
                font=("Arial", 10, "bold"),
                bg="#f7f7f7"
            ).pack(anchor="w", padx=20, pady=(10, 5))

            # Frame with scroll for macros - dynamic height based on quantity
            max_height = min(250, len(existing_macros) * 35 + 10)  # Max 250px
            macros_canvas_frame = tk.Frame(modal, bg="#f7f7f7", height=max_height)
            macros_canvas_frame.pack(fill="x", padx=20, pady=(0, 10))
            macros_canvas_frame.pack_propagate(False)

            macros_canvas = tk.Canvas(
                macros_canvas_frame,
                bg="#f7f7f7",
                highlightthickness=1,
                highlightbackground="#ccc"
            )
            macros_scrollbar = tk.Scrollbar(macros_canvas_frame, orient="vertical", command=macros_canvas.yview)
            macros_list_frame = tk.Frame(macros_canvas, bg="#f7f7f7")

            macros_list_frame.bind("<Configure>", lambda e: macros_canvas.configure(scrollregion=macros_canvas.bbox("all")))
            canvas_window = macros_canvas.create_window((0, 0), window=macros_list_frame, anchor="nw")

            # Adjust width of inner frame to canvas
            def on_canvas_configure(event):
                macros_canvas.itemconfig(canvas_window, width=event.width)

            macros_canvas.bind("<Configure>", on_canvas_configure)
            macros_canvas.configure(yscrollcommand=macros_scrollbar.set)

            macros_canvas.pack(side="left", fill="both", expand=True)
            macros_scrollbar.pack(side="right", fill="y")

            # Add each macro with delete button
            for macro_name in existing_macros:
                macro_row = tk.Frame(macros_list_frame, bg="white", relief="ridge", borderwidth=1)
                macro_row.pack(fill="x", pady=2, padx=2)

                # Frame for text (expands)
                text_frame = tk.Frame(macro_row, bg="white")
                text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=2)

                # Label with macro name (truncated)
                macro_label = tk.Label(
                    text_frame,
                    text=macro_name if len(macro_name) <= 30 else macro_name[:27] + "...",
                    font=("Arial", 9),
                    bg="white",
                    anchor="w",
                    cursor="hand2"
                )
                macro_label.pack(fill="x", expand=True)

                # Tooltip to show full name on hover
                def create_tooltip(widget, text):
                    tooltip = None

                    def on_enter(event):
                        nonlocal tooltip
                        if len(text) > 30:  # Only show if truncated
                            x, y, _, _ = widget.bbox("insert")
                            x += widget.winfo_rootx() + 25
                            y += widget.winfo_rooty() + 25

                            tooltip = tk.Toplevel(widget)
                            tooltip.wm_overrideredirect(True)
                            tooltip.wm_geometry(f"+{x}+{y}")

                            label = tk.Label(
                                tooltip,
                                text=text,
                                background="lightyellow",
                                relief="solid",
                                borderwidth=1,
                                font=("Arial", 9)
                            )
                            label.pack()

                    def on_leave(event):
                        nonlocal tooltip
                        if tooltip:
                            tooltip.destroy()
                            tooltip = None

                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)

                create_tooltip(macro_label, macro_name)

                # Click to select
                def select_macro(name):
                    name_var.set(name)

                macro_label.bind("<Button-1>", lambda e, name=macro_name: select_macro(name))

                # Delete button (aligned right)
                def on_delete(m_name):
                    if messagebox.askyesno("Confirm deletion", f"Delete macro '{m_name}'?"):
                        self.state_manager.delete_macro(m_name)
                        messagebox.showinfo("Success", f"Macro '{m_name}' deleted successfully.")
                        modal.destroy()
                        self.save_macro()

                delete_btn = tk.Button(
                    macro_row,
                    text="🗑️",
                    font=("Arial", 10),
                    bg="#e74c3c",
                    fg="white",
                    width=3,
                    command=lambda m_name=macro_name: on_delete(m_name)
                )
                delete_btn.pack(side="right", padx=5, pady=2)

        # Frame for buttons
        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(fill="x", pady=(10, 20), side="bottom")

        def guardar():
            macro_name = name_var.get().strip()
            if not macro_name:
                messagebox.showwarning("Validation", "Must enter a name for the macro.")
                return

            # Check if already exists in universal macros (get fresh list)
            current_macros = self.state_manager.list_macros()
            if macro_name in current_macros:
                if not messagebox.askyesno("Confirm overwrite", f"Macro '{macro_name}' already exists.\nDo you want to overwrite it?"):
                    return

            # Build current last_state
            current_last_state = {}
            for cmd_name in command_configs.keys():
                cmd_state = self.commands_state.get(cmd_name, {})
                state = cmd_state.get("state")
                if state:
                    current_last_state[cmd_name] = state

                # Save checkbox enabled state
                if "enabled" in cmd_state:
                    current_last_state[f"{cmd_name}_enabled"] = cmd_state["enabled"].get()

                # Save repetitions if applicable
                if "repetitions" in cmd_state:
                    current_last_state[f"{cmd_name}_reps"] = cmd_state["repetitions"].get()

                # Save individual delta_time
                if "delta_time" in cmd_state:
                    current_last_state[f"{cmd_name}_delta"] = cmd_state["delta_time"].get()

            # Build macro object
            from ...core.models import Macro
            macro = Macro(
                name=macro_name,
                command_configs=dict(command_configs),
                last_state=current_last_state
            )

            # Save to universal macros using StateManager
            self.state_manager.save_macro(macro)

            messagebox.showinfo("Success", f"Macro '{macro_name}' saved successfully.")
            modal.destroy()

        guardar_btn = tk.Button(
            btn_frame,
            text="Save",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=guardar,
            width=10
        )
        guardar_btn.pack(side="left", padx=(40, 10))

        cancelar_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=modal.destroy,
            width=10
        )
        cancelar_btn.pack(side="right", padx=(10, 40))

    def load_macro(self):
        """Load a saved macro."""
        if not self.selected_mc_mac:
            messagebox.showwarning("Validation", "Must select a Microcontroller first.")
            return

        mc = self.state_manager.get_mc(self.selected_mc_mac)
        if not mc:
            messagebox.showwarning("Validation", "Microcontroller not found.")
            return

        macros = self.state_manager.list_macros()
        if not macros:
            messagebox.showinfo("Information", "No saved macros found.")
            return

        # Modal to select macro
        modal = tk.Toplevel(self.parent_window)
        modal.title("Load Macro")
        modal.transient(self.parent_window)
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")

        # Center modal
        self.center_modal_on_parent(modal, 500, 400)

        tk.Label(
            modal,
            text="Select a macro to load:",
            font=("Arial", 11, "bold"),
            bg="#f7f7f7"
        ).pack(pady=(20, 10))

        # Frame with scroll for macros
        macros_canvas_frame = tk.Frame(modal, bg="#f7f7f7")
        macros_canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        macros_canvas = tk.Canvas(
            macros_canvas_frame,
            bg="#f7f7f7",
            highlightthickness=1,
            highlightbackground="#ccc"
        )
        macros_scrollbar = tk.Scrollbar(macros_canvas_frame, orient="vertical", command=macros_canvas.yview)
        macros_list_frame = tk.Frame(macros_canvas, bg="#f7f7f7")

        macros_list_frame.bind("<Configure>", lambda e: macros_canvas.configure(scrollregion=macros_canvas.bbox("all")))
        canvas_window = macros_canvas.create_window((0, 0), window=macros_list_frame, anchor="nw")

        # Adjust width of inner frame to canvas
        def on_canvas_configure(event):
            macros_canvas.itemconfig(canvas_window, width=event.width)

        macros_canvas.bind("<Configure>", on_canvas_configure)
        macros_canvas.configure(yscrollcommand=macros_scrollbar.set)

        macros_canvas.pack(side="left", fill="both", expand=True)
        macros_scrollbar.pack(side="right", fill="y")

        # Variable to store selected macro
        selected_macro = tk.StringVar()

        # List to maintain references of all rows
        macro_rows_widgets = []

        # Add each macro with delete button
        for macro_name in macros:
            macro_row = tk.Frame(macros_list_frame, bg="white", relief="ridge", borderwidth=1)
            macro_row.pack(fill="x", pady=2, padx=2)

            # Frame for text (expands)
            text_frame = tk.Frame(macro_row, bg="white")
            text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=2)

            # Label with macro name (truncated)
            macro_label = tk.Label(
                text_frame,
                text=macro_name if len(macro_name) <= 30 else macro_name[:27] + "...",
                font=("Arial", 9),
                bg="white",
                anchor="w",
                cursor="hand2"
            )
            macro_label.pack(fill="x", expand=True)

            # Save widget references for this row
            macro_rows_widgets.append({
                "row": macro_row,
                "frame": text_frame,
                "label": macro_label
            })

            # Tooltip to show full name on hover
            def create_tooltip(widget, text):
                tooltip = None

                def on_enter(event):
                    nonlocal tooltip
                    if len(text) > 30:
                        x, y, _, _ = widget.bbox("insert")
                        x += widget.winfo_rootx() + 25
                        y += widget.winfo_rooty() + 25

                        tooltip = tk.Toplevel(widget)
                        tooltip.wm_overrideredirect(True)
                        tooltip.wm_geometry(f"+{x}+{y}")

                        label = tk.Label(
                            tooltip,
                            text=text,
                            background="lightyellow",
                            relief="solid",
                            borderwidth=1,
                            font=("Arial", 9)
                        )
                        label.pack()

                def on_leave(event):
                    nonlocal tooltip
                    if tooltip:
                        tooltip.destroy()
                        tooltip = None

                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

            create_tooltip(macro_label, macro_name)

            # Click to select
            def select_macro_fn(name, current_row, current_frame, current_label):
                selected_macro.set(name)

                # Restore color of ALL rows
                for widgets in macro_rows_widgets:
                    widgets["row"].config(bg="white")
                    widgets["frame"].config(bg="white")
                    widgets["label"].config(bg="white")

                # Apply selection color to current row
                current_row.config(bg="#e3f2fd")
                current_frame.config(bg="#e3f2fd")
                current_label.config(bg="#e3f2fd")

            # Bind with correct arguments using current loop values
            macro_label.bind("<Button-1>", lambda e, n=macro_name, r=macro_row, f=text_frame, l=macro_label: select_macro_fn(n, r, f, l))
            text_frame.bind("<Button-1>", lambda e, n=macro_name, r=macro_row, f=text_frame, l=macro_label: select_macro_fn(n, r, f, l))
            macro_row.bind("<Button-1>", lambda e, n=macro_name, r=macro_row, f=text_frame, l=macro_label: select_macro_fn(n, r, f, l))

            # Delete button
            def on_delete(name):
                if messagebox.askyesno("Confirm deletion", f"Delete macro '{name}'?"):
                    self.state_manager.delete_macro(name)
                    messagebox.showinfo("Success", f"Macro '{name}' deleted successfully.")
                    modal.destroy()
                    self.load_macro()

            delete_btn = tk.Button(
                macro_row,
                text="🗑️",
                font=("Arial", 10),
                bg="#e74c3c",
                fg="white",
                width=3,
                command=lambda name=macro_name: on_delete(name)
            )
            delete_btn.pack(side="right", padx=5, pady=2)

        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(pady=(10, 20))

        def cargar():
            macro_name = selected_macro.get()
            if not macro_name:
                messagebox.showwarning("Validation", "Must select a macro.")
                return

            # Load macro object
            macro = self.state_manager.load_macro(macro_name)
            if not macro:
                messagebox.showerror("Error", "Selected macro no longer exists.")
                return

            # Load macro configuration into MC
            mc.command_configs = dict(macro.command_configs)
            mc.last_state = dict(macro.last_state)

            # Save to database
            self.state_manager._save_to_db()

            # Rebuild command table
            self.rebuild_command_table()
            modal.destroy()

            messagebox.showinfo("Success", f"Macro '{macro_name}' loaded successfully.")

        cargar_btn = tk.Button(
            btn_frame,
            text="Load",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=cargar,
            width=10
        )
        cargar_btn.pack(side="left", padx=10)

        cancelar_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=modal.destroy,
            width=10
        )
        cancelar_btn.pack(side="right", padx=10)

    def get_command_configs(self) -> Dict:
        """
        Get current command configurations.

        Returns:
            Dict: Command configurations {cmd_name: {"enabled": bool, "state": str}}
        """
        configs = {}

        for cmd_name, cmd_state in self.commands_state.items():
            enabled = cmd_state["enabled"].get()

            if enabled:
                state = cmd_state.get("state")
                configs[cmd_name] = {
                    "enabled": True,
                    "state": state
                }

        return configs
