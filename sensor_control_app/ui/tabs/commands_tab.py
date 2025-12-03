"""
Commands tab module.

This module provides the Commands tab component which handles:
- Command configuration interface
- Command sending with repetitions
- Drag & drop command reordering
- Macro save/load functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, List

from ..widgets import ScrollableFrame, DragDropList
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
        macro_manager: MacroManager
    ):
        """
        Initialize the CommandsTab.

        Args:
            parent: Parent widget (typically a Notebook)
            state_manager: StateManager instance
            packet_sender: PacketSender for sending commands
            macro_manager: MacroManager for managing macros
        """
        super().__init__(parent)

        # Dependencies
        self.state_manager = state_manager
        self.packet_sender = packet_sender
        self.macro_manager = macro_manager

        # UI state
        self.selected_mc_mac = None
        self.command_widgets = {}  # {config_name: {"enabled_var": var, "state_var": var, ...}}
        self.sending_commands = False

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

    def create_commands_section(self, parent):
        """Create scrollable commands configuration section."""
        commands_frame = ttk.LabelFrame(
            parent,
            text="Commands Configuration",
            padding=10
        )
        commands_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollable container
        self.scrollable = ScrollableFrame(commands_frame)
        self.scrollable.pack(fill="both", expand=True)

        # Commands container (inside scrollable frame)
        self.commands_container = self.scrollable.get_frame()

        # Create command rows
        self.create_command_rows()

    def create_command_rows(self):
        """Create rows for each command configuration."""
        for config_name, config_data in COMMAND_CONFIGS.items():
            self.create_command_row(config_name, config_data)

        # Update scroll bindings
        self.scrollable.update_scroll_bindings()

    def create_command_row(self, config_name: str, config_data: Dict):
        """
        Create a row for a command configuration.

        Args:
            config_name: Command configuration name
            config_data: Configuration data with states
        """
        row_frame = ttk.Frame(self.commands_container)
        row_frame.pack(fill="x", pady=2)

        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=False)
        enabled_check = tk.Checkbutton(
            row_frame,
            text="",
            variable=enabled_var
        )
        enabled_check.pack(side="left", padx=2)

        # Command name label
        name_label = tk.Label(
            row_frame,
            text=config_name,
            width=40,
            anchor="w",
            font=("Arial", 9)
        )
        name_label.pack(side="left", padx=5)

        # State selection (if applicable)
        state_var = tk.StringVar()
        if len(config_data) > 0:
            # Create radio buttons for states
            state_frame = ttk.Frame(row_frame)
            state_frame.pack(side="left", padx=5)

            for state_name in config_data.keys():
                radio = tk.Radiobutton(
                    state_frame,
                    text=state_name,
                    variable=state_var,
                    value=state_name,
                    font=("Arial", 9)
                )
                radio.pack(side="left", padx=5)

            # Set default value
            state_var.set(list(config_data.keys())[0])

        # Store widget references
        self.command_widgets[config_name] = {
            "enabled_var": enabled_var,
            "state_var": state_var,
            "config_data": config_data
        }

    def create_control_section(self, parent):
        """Create control buttons section."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Send commands button
        self.send_btn = tk.Button(
            control_frame,
            text="Send Commands",
            command=self.send_commands,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=20
        )
        self.send_btn.pack(pady=5)

        # Macro buttons
        macro_frame = ttk.Frame(control_frame)
        macro_frame.pack(fill="x", pady=5)

        save_macro_btn = tk.Button(
            macro_frame,
            text="Save as Macro",
            command=self.save_macro,
            font=("Arial", 10)
        )
        save_macro_btn.pack(side="left", padx=5)

        load_macro_btn = tk.Button(
            macro_frame,
            text="Load Macro",
            command=self.load_macro,
            font=("Arial", 10)
        )
        load_macro_btn.pack(side="left", padx=5)

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
        mc = self.state_manager.get_mc(mac_source)
        if not mc:
            return

        # Load command configs
        for config_name, widget_data in self.command_widgets.items():
            if config_name in mc.command_configs:
                cmd_config = mc.command_configs[config_name]

                # Set enabled state
                widget_data["enabled_var"].set(cmd_config.get("enabled", False))

                # Set state if applicable
                if "state" in cmd_config and cmd_config["state"]:
                    widget_data["state_var"].set(cmd_config["state"])

    def send_commands(self):
        """Send configured commands to selected MC."""
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
        for config_name, widget_data in self.command_widgets.items():
            if not widget_data["enabled_var"].get():
                continue  # Skip disabled commands

            # Get selected state
            config_data = widget_data["config_data"]
            if config_data:
                state = widget_data["state_var"].get()
                command_name = config_data.get(state)
            else:
                command_name = config_name

            if not command_name:
                continue

            # Get command byte
            try:
                command_byte = get_command_byte(command_name)

                packet = PacketInfo(
                    mac_source=mc.mac_source,
                    mac_destiny=mc.mac_destiny,
                    interface=mc.interface_destiny,
                    command_byte=command_byte,
                    command_name=command_name,
                    repetitions=1,
                    delay_ms=100
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

        # Confirm sending
        result = messagebox.askyesno(
            "Confirm Send",
            f"Send {len(packets)} command(s) to {mc.label}?"
        )

        if not result:
            return

        # Send packets
        self.sending_commands = True
        self.send_btn.config(text="Sending...", state="disabled")

        def on_complete(success):
            self.sending_commands = False
            self.send_btn.config(text="Send Commands", state="normal")

            if success:
                messagebox.showinfo("Success", "Commands sent successfully!")
            else:
                messagebox.showwarning("Cancelled", "Command sending was cancelled.")

        # Send asynchronously
        self.packet_sender.send_packets_batch_async(packets, on_complete=on_complete)

    def save_macro(self):
        """Save current command configuration as a macro."""
        messagebox.showinfo(
            "Save Macro",
            "Macro save dialog not yet implemented in modular version.\n"
            "This will be implemented in later phases."
        )

    def load_macro(self):
        """Load a saved macro."""
        messagebox.showinfo(
            "Load Macro",
            "Macro load dialog not yet implemented in modular version.\n"
            "This will be implemented in later phases."
        )

    def get_command_configs(self) -> Dict:
        """
        Get current command configurations.

        Returns:
            Dict: Command configurations
        """
        configs = {}

        for config_name, widget_data in self.command_widgets.items():
            enabled = widget_data["enabled_var"].get()

            if enabled:
                config_data = widget_data["config_data"]
                if config_data:
                    state = widget_data["state_var"].get()
                    configs[config_name] = {
                        "enabled": True,
                        "state": state
                    }
                else:
                    configs[config_name] = {
                        "enabled": True,
                        "state": None
                    }

        return configs
