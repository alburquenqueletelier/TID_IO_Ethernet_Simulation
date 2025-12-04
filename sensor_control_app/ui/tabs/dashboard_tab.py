"""
Dashboard tab module.

This module provides the Dashboard tab component which displays:
- Registered microcontrollers table
- Network interface monitoring
- PET scanner associations
- Command macro management for PET scanners
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any

from ..widgets import ScrollableFrame
from ...core import StateManager
from ...network import InterfaceDiscovery, PacketSender
from ...storage import MacroManager


class DashboardTab(ttk.Frame):
    """
    Dashboard tab component.

    This tab provides the main overview of the system including:
    - Microcontroller registration and management
    - Network interface status
    - PET scanner configuration
    - Macro management for PET scanners
    """

    def __init__(
        self,
        parent,
        state_manager: StateManager,
        interface_discovery: InterfaceDiscovery,
        packet_sender: PacketSender,
        macro_manager: MacroManager,
        on_refresh_callback: Optional[Callable] = None
    ):
        """
        Initialize the DashboardTab.

        Args:
            parent: Parent widget (typically a Notebook)
            state_manager: StateManager instance for managing application state
            interface_discovery: InterfaceDiscovery for detecting network interfaces
            packet_sender: PacketSender for sending commands
            macro_manager: MacroManager for managing macros
            on_refresh_callback: Optional callback when refresh is triggered
        """
        super().__init__(parent)

        # Dependencies
        self.state_manager = state_manager
        self.interface_discovery = interface_discovery
        self.packet_sender = packet_sender
        self.macro_manager = macro_manager
        self.on_refresh_callback = on_refresh_callback

        # UI state
        self.mc_table_rows = []
        self.selected_pet_macros = {}  # {pet_num: [macro_names]}

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the dashboard UI components."""
        # Create scrollable container
        self.scrollable = ScrollableFrame(self)
        self.scrollable.pack(fill="both", expand=True)

        # Get inner frame
        container = self.scrollable.get_frame()

        # Title
        title_frame = ttk.Frame(container)
        title_frame.pack(fill="x", pady=10, padx=10)

        title_label = tk.Label(
            title_frame,
            text="Dashboard - Microcontrollers & PET Management",
            font=("Arial", 16, "bold")
        )
        title_label.pack()

        # Network Interfaces Section
        self.create_network_section(container)

        # Microcontrollers Table
        self.create_mc_table_section(container)

        # Registration Form and PET Associations (side by side)
        self.create_registration_and_pet_section(container)

        # Update scroll bindings
        self.scrollable.update_scroll_bindings()

    def create_network_section(self, parent):
        """Create network interfaces section."""
        section_frame = ttk.LabelFrame(parent, text="Network Interfaces", padding=10)
        section_frame.pack(fill="x", padx=10, pady=5)

        # Refresh button
        btn_frame = ttk.Frame(section_frame)
        btn_frame.pack(fill="x", pady=5)

        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh Interfaces",
            command=self.refresh_interfaces,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        refresh_btn.pack(side="left", padx=5)

        # Interface count label
        self.interface_count_label = tk.Label(
            btn_frame,
            text="Available interfaces: 0",
            font=("Arial", 10)
        )
        self.interface_count_label.pack(side="left", padx=10)

    def create_mc_table_section(self, parent):
        """Create microcontrollers table section."""
        section_frame = ttk.LabelFrame(
            parent,
            text="Registered Microcontrollers",
            padding=10
        )
        section_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Table header
        header_frame = ttk.Frame(section_frame)
        header_frame.pack(fill="x", pady=5)

        headers = ["Interface Network", "MAC Source", "MAC Destiny", "Interface Destiny", "Label"]
        widths = [24, 28, 20, 20, 20]

        for header, width in zip(headers, widths):
            label = tk.Label(
                header_frame,
                text=header,
                font=("Arial", 10, "bold"),
                width=width,
                relief="ridge",
                bg="#e0e0e0"
            )
            label.pack(side="left", padx=1)

        # Table container
        self.mc_table_container = ttk.Frame(section_frame)
        self.mc_table_container.pack(fill="both", expand=True)

    def create_registration_and_pet_section(self, parent):
        """Create registration form and PET associations side by side."""
        # Main container (divided in 2 columns)
        main_container = ttk.Frame(parent)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT COLUMN: Registration Form (50%)
        self.create_registration_form(main_container)

        # RIGHT COLUMN: PET Associations (50%)
        self.create_pet_section(main_container)

    def create_registration_form(self, parent):
        """Create MC registration form."""
        register_frame = ttk.LabelFrame(
            parent,
            text="Register Microcontroller",
            padding=10
        )
        register_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        form_container = ttk.Frame(register_frame)
        form_container.pack(fill="x", padx=10, pady=10)

        # MAC Source
        mac_source_row = ttk.Frame(form_container)
        mac_source_row.pack(fill="x", pady=5)

        tk.Label(
            mac_source_row,
            text="MAC Source:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w"
        ).pack(side="left")

        self.mac_source_var = tk.StringVar()
        self.mac_source_combo = ttk.Combobox(
            mac_source_row,
            textvariable=self.mac_source_var,
            values=list(self.state_manager.mc_available.keys()),
            state="readonly",
            width=30
        )
        self.mac_source_combo.pack(side="left", padx=(10, 0))
        self.mac_source_combo.set("Select MAC source...")

        # MAC Destiny
        mac_destiny_row = ttk.Frame(form_container)
        mac_destiny_row.pack(fill="x", pady=5)

        tk.Label(
            mac_destiny_row,
            text="MAC Destiny:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w"
        ).pack(side="left")

        self.mac_destiny_var = tk.StringVar()
        self.mac_destiny_entry = tk.Entry(
            mac_destiny_row,
            textvariable=self.mac_destiny_var,
            width=32
        )
        self.mac_destiny_entry.pack(side="left", padx=(10, 5))

        tk.Label(
            mac_destiny_row,
            text="(e.g., fe:80:ab:cd:12:34)",
            fg="gray",
            font=("Arial", 8)
        ).pack(side="left")

        # Interface Destiny
        interface_destiny_row = ttk.Frame(form_container)
        interface_destiny_row.pack(fill="x", pady=5)

        tk.Label(
            interface_destiny_row,
            text="Interface Destiny:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w"
        ).pack(side="left")

        self.interface_destiny_var = tk.StringVar()
        self.interface_destiny_entry = tk.Entry(
            interface_destiny_row,
            textvariable=self.interface_destiny_var,
            width=32
        )
        self.interface_destiny_entry.pack(side="left", padx=(10, 5))

        tk.Label(
            interface_destiny_row,
            text="(e.g., eth0)",
            fg="gray",
            font=("Arial", 8)
        ).pack(side="left")

        # Label
        label_row = ttk.Frame(form_container)
        label_row.pack(fill="x", pady=5)

        tk.Label(
            label_row,
            text="Label:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w"
        ).pack(side="left")

        self.label_var = tk.StringVar()
        label_entry = tk.Entry(
            label_row,
            textvariable=self.label_var,
            width=32
        )
        label_entry.pack(side="left", padx=(10, 5))

        tk.Label(
            label_row,
            text="(optional)",
            fg="gray",
            font=("Arial", 8)
        ).pack(side="left")

        # Register button
        register_btn_frame = ttk.Frame(form_container)
        register_btn_frame.pack(fill="x", pady=15)

        register_btn = tk.Button(
            register_btn_frame,
            text="Register Microcontroller",
            command=self.register_mc,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=30
        )
        register_btn.pack()

    def create_pet_section(self, parent):
        """Create PET scanner associations section."""
        import math

        section_frame = ttk.LabelFrame(
            parent,
            text="PET Scan",
            padding=10
        )
        section_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # Macro selection frame
        macro_select_frame = ttk.LabelFrame(
            section_frame,
            text="Select Macro",
            padding=10
        )
        macro_select_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Macro selector row
        macro_row = ttk.Frame(macro_select_frame)
        macro_row.pack(fill="x", pady=5)

        tk.Label(
            macro_row,
            text="Macro:",
            font=("Arial", 9)
        ).pack(side="left", padx=(0, 8))

        # Variable for selected macro
        self.selected_macro_var = tk.StringVar()

        # Create combobox
        self.macro_combo_dashboard = ttk.Combobox(
            macro_row,
            textvariable=self.selected_macro_var,
            state="readonly",
            width=30
        )
        self.macro_combo_dashboard.pack(side="left", fill="x", expand=True)

        # Refresh button
        refresh_macros_btn = tk.Button(
            macro_row,
            text="🔄",
            font=("Arial", 9, "bold"),
            bg="#3498db",
            fg="white",
            width=3,
            command=self.update_macro_options,
            cursor="hand2"
        )
        refresh_macros_btn.pack(side="left", padx=(8, 0))

        # Select all checkbox
        select_all_frame = ttk.Frame(macro_select_frame)
        select_all_frame.pack(fill="x", pady=(5, 0))

        self.select_all_pets_var = tk.BooleanVar(value=False)
        select_all_cb = tk.Checkbutton(
            select_all_frame,
            text="Select all",
            variable=self.select_all_pets_var,
            command=self.toggle_all_pets,
            font=("Arial", 10, "bold")
        )
        select_all_cb.pack(anchor="w")

        # Canvas for circular PET layout
        pet_canvas = tk.Canvas(section_frame, width=450, height=450, bg="white")
        pet_canvas.pack(padx=20, pady=(10, 20))

        # Draw 10 PET buttons in a circle
        center_x = 225
        center_y = 225
        radius = 150
        num_pets = 10

        self.pet_buttons = []
        self.pet_tooltips = []
        self.pet_checkbox_vars = {}
        self.pet_checkboxes_widgets = {}  # Track checkbox widgets

        for i in range(num_pets):
            angle = (2 * math.pi / num_pets) * i - (math.pi / 2)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Checkbox position (above the button)
            checkbox_offset = 30
            cb_x = x
            cb_y = y - checkbox_offset

            # Create checkbox variable
            pet_num = i + 1
            assoc = self.state_manager.get_pet_association(pet_num)
            pet_enabled_var = tk.BooleanVar(value=assoc.enabled if assoc else False)
            self.pet_checkbox_vars[pet_num] = pet_enabled_var

            # Determine if checkbox should be enabled
            has_mc = assoc and assoc.mc_mac is not None
            checkbox_state = "normal" if has_mc else "disabled"

            # Create checkbox
            pet_checkbox = tk.Checkbutton(
                pet_canvas,
                variable=pet_enabled_var,
                bg="white",
                activebackground="white",
                state=checkbox_state,
                command=lambda num=pet_num, v=pet_enabled_var: self.update_pet_enabled(num, v)
            )
            pet_canvas.create_window(cb_x, cb_y, window=pet_checkbox)
            self.pet_checkboxes_widgets[pet_num] = pet_checkbox

            # Determine button color
            btn_bg = "#3498db" if has_mc else "#e67e22"  # Blue if has MC, orange if not

            # Create PET button
            pet_btn = tk.Button(
                pet_canvas,
                text=f"PET {pet_num}",
                font=("Arial", 9, "bold"),
                bg=btn_bg,
                fg="white",
                width=8,
                height=2,
                relief="flat",
                borderwidth=0,
                highlightthickness=2,
                highlightbackground="#2980b9",
                cursor="hand2",
                command=lambda num=pet_num: self.on_pet_click(num)
            )

            # Place button on canvas
            pet_canvas.create_window(x, y, window=pet_btn)
            self.pet_buttons.append(pet_btn)

            # Setup tooltip
            self.setup_pet_tooltip(pet_btn, pet_num)

        # Send button in the center
        self.send_pet_btn = tk.Button(
            pet_canvas,
            text="Send",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=10,
            height=2,
            relief="raised",
            borderwidth=3,
            cursor="hand2",
            command=self.send_pet_commands
        )

        # Place send button in center
        pet_canvas.create_window(center_x, center_y, window=self.send_pet_btn)

    def refresh_interfaces(self):
        """Refresh available network interfaces."""
        interfaces = self.interface_discovery.get_ethernet_interfaces()

        # Update state
        self.state_manager.update_mc_available(interfaces)

        # Update UI
        self.interface_count_label.config(
            text=f"Available interfaces: {len(interfaces)}"
        )

        # Update MAC source combobox in registration form
        if hasattr(self, 'mac_source_combo'):
            self.mac_source_combo['values'] = list(interfaces.keys())

        # Refresh MC table to show updated interface info
        self.refresh_mc_table()

        # Refresh PET buttons to update associations
        if hasattr(self, 'refresh_pet_buttons'):
            self.refresh_pet_buttons()

        # Call callback if provided
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def refresh_mc_table(self):
        """Refresh the microcontrollers table."""
        # Clear existing rows
        for row in self.mc_table_rows:
            row.destroy()
        self.mc_table_rows.clear()

        # Iterate over all available MCs (detected interfaces)
        for mac_source, interface_network in self.state_manager.mc_available.items():
            # Check if this MC is registered
            mc = self.state_manager.get_mc(mac_source)

            if mc:
                # MC is registered - show full info
                self.create_mc_table_row_registered(mc, interface_network)
            else:
                # MC is available but not registered
                self.create_mc_table_row_unregistered(mac_source, interface_network)

    def create_mc_table_row_registered(self, mc, interface_network: str):
        """
        Create a table row for a registered microcontroller.

        Args:
            mc: MicroController object
            interface_network: Network interface name
        """
        row_frame = ttk.Frame(self.mc_table_container)
        row_frame.pack(fill="x", pady=1)

        widths = [20, 20, 20, 20, 20]
        values = [
            interface_network,
            mc.mac_source,
            mc.mac_destiny,
            mc.interface_destiny,
            mc.label
        ]

        for value, width in zip(values, widths):
            label = tk.Label(
                row_frame,
                text=value,
                width=width,
                relief="ridge",
                bg="white"
            )
            label.pack(side="left", padx=1)

        self.mc_table_rows.append(row_frame)

    def create_mc_table_row_unregistered(self, mac_source: str, interface_network: str):
        """
        Create a table row for an unregistered (available) microcontroller.

        Args:
            mac_source: Source MAC address
            interface_network: Network interface name
        """
        row_frame = ttk.Frame(self.mc_table_container)
        row_frame.pack(fill="x", pady=1)

        widths = [20, 20, 20, 20, 20]
        values = [
            interface_network,
            mac_source,
            "Not registered",
            "N/A",
            "N/A"
        ]

        for value, width in zip(values, widths):
            label = tk.Label(
                row_frame,
                text=value,
                width=width,
                relief="ridge",
                bg="#ffe0e0"  # Light red background for unregistered
            )
            label.pack(side="left", padx=1)

        self.mc_table_rows.append(row_frame)


    def setup_pet_tooltip(self, button, pet_num: int):
        """Setup hover tooltip for a PET button."""
        tooltip = None

        def show_tooltip(event):
            nonlocal tooltip

            # Get association info
            assoc = self.state_manager.get_pet_association(pet_num)
            mc_label = "No MC"

            if assoc and assoc.mc_mac:
                # Find MC by destiny MAC
                mc = self.state_manager.get_mc_by_destiny(assoc.mc_mac)
                if mc:
                    mc_label = mc.label

            # Create tooltip
            x = button.winfo_rootx() + button.winfo_width() // 2
            y = button.winfo_rooty() - 10

            tooltip = tk.Toplevel(button)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")

            # Frame with border
            frame = tk.Frame(
                tooltip,
                background="#2c3e50",
                relief="solid",
                borderwidth=1
            )
            frame.pack(fill="both", expand=True)

            # Tooltip content
            tk.Label(
                frame,
                text=f"PET {pet_num}",
                font=("Arial", 9, "bold"),
                bg="#2c3e50",
                fg="white",
                padx=10,
                pady=2
            ).pack()

            tk.Label(
                frame,
                text=f"MC: {mc_label}",
                font=("Arial", 8),
                bg="#2c3e50",
                fg="#ecf0f1",
                padx=10,
                pady=2
            ).pack()

            # Adjust position to appear above button
            tooltip.update_idletasks()
            tooltip_height = tooltip.winfo_height()
            tooltip.wm_geometry(f"+{x - tooltip.winfo_width()//2}+{y - tooltip_height - 5}")

        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        button.bind("<Enter>", show_tooltip)
        button.bind("<Leave>", hide_tooltip)

    def update_macro_options(self):
        """Update macro combobox options."""
        macro_names = self.macro_manager.list_universal_macros()
        macro_options = ["No Macro"] + macro_names
        self.macro_combo_dashboard["values"] = macro_options

        # If no selection or selection no longer exists, set to "No Macro"
        current = self.selected_macro_var.get()
        if not current or (current != "No Macro" and current not in macro_names):
            self.selected_macro_var.set("No Macro")

    def toggle_all_pets(self):
        """Toggle all PET checkboxes (only those with MC assigned)."""
        value = self.select_all_pets_var.get()
        for pet_num in range(1, 11):
            assoc = self.state_manager.get_pet_association(pet_num)
            # Only update if has MC assigned
            if assoc and assoc.mc_mac is not None:
                self.state_manager.set_pet_enabled(pet_num, value)
                # Update checkbox variable
                if pet_num in self.pet_checkbox_vars:
                    self.pet_checkbox_vars[pet_num].set(value)

    def update_pet_enabled(self, pet_num: int, var: tk.BooleanVar):
        """Update PET enabled state."""
        assoc = self.state_manager.get_pet_association(pet_num)
        # Only allow change if has MC assigned
        if not assoc or assoc.mc_mac is None:
            var.set(False)  # Force to False
            return

        self.state_manager.set_pet_enabled(pet_num, var.get())

        # Update "Select all" checkbox if necessary
        all_selected = all(
            self.state_manager.get_pet_association(j).enabled
            for j in range(1, 11)
            if self.state_manager.get_pet_association(j).mc_mac is not None
        )
        self.select_all_pets_var.set(all_selected)

    def on_pet_click(self, pet_num: int):
        """Handle PET button click - show association dialog."""
        self.show_pet_association_dialog(pet_num)

    def show_pet_association_dialog(self, pet_num: int):
        """Show dialog to associate a MC with a PET."""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"Associate PET {pet_num}")
        dialog.geometry("400x200")
        dialog.configure(bg="#f0f0f0")
        dialog.transient(self)
        dialog.grab_set()

        # Main container
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text=f"Associate PET {pet_num} with Microcontroller",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=(0, 20))

        # MC selection
        mc_frame = ttk.Frame(main_frame)
        mc_frame.pack(fill="x", pady=10)

        tk.Label(
            mc_frame,
            text="Select MC:",
            font=("Arial", 10, "bold"),
            width=12,
            anchor="w"
        ).pack(side="left")

        # Get registered MCs that are currently connected (available)
        all_mcs = self.state_manager.get_all_registered_mcs()
        # Filter only MCs that are currently connected
        connected_mcs = [
            mc for mc in all_mcs
            if mc.mac_source in self.state_manager.mc_available
        ]

        # Get all MCs already associated with other PETs
        associated_macs = set()
        for i in range(1, 11):
            if i != pet_num:  # Exclude current PET
                other_assoc = self.state_manager.get_pet_association(i)
                if other_assoc and other_assoc.mc_mac:
                    associated_macs.add(other_assoc.mc_mac)

        # Build options with visual indicator for already associated MCs
        mc_options = ["None"]
        for mc in connected_mcs:
            if mc.mac_destiny in associated_macs:
                # Add blue indicator for already associated MCs
                mc_options.append(f"🔗 {mc.label} ({mc.mac_destiny})")
            else:
                mc_options.append(f"{mc.label} ({mc.mac_destiny})")

        # Get current association
        assoc = self.state_manager.get_pet_association(pet_num)
        current_value = "None"
        if assoc and assoc.mc_mac:
            mc = self.state_manager.get_mc_by_destiny(assoc.mc_mac)
            if mc:
                # Check if this MC is also associated with others
                if mc.mac_destiny in associated_macs:
                    current_value = f"🔗 {mc.label} ({mc.mac_destiny})"
                else:
                    current_value = f"{mc.label} ({mc.mac_destiny})"

        mc_var = tk.StringVar(value=current_value)
        mc_combo = ttk.Combobox(
            mc_frame,
            textvariable=mc_var,
            values=mc_options,
            state="readonly",
            width=30
        )
        mc_combo.pack(side="left", padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        def save_association():
            """Save the association."""
            selection = mc_var.get()

            if selection == "None":
                mc_mac = None
            else:
                # Extract MAC from "Label (MAC)" or "🔗 Label (MAC)" format
                try:
                    # Remove the emoji indicator if present
                    clean_selection = selection.replace("🔗 ", "")
                    mc_mac = clean_selection.split("(")[1].rstrip(")")
                except (IndexError, AttributeError):
                    mc_mac = None

            # Update state
            self.state_manager.associate_pet(pet_num, mc_mac, False)

            # Refresh PET buttons
            self.refresh_pet_buttons()

            # Close dialog
            dialog.destroy()

        save_btn = tk.Button(
            button_frame,
            text="Save",
            command=save_association,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        )
        save_btn.pack(side="left", padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            bg="#f44336",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        )
        cancel_btn.pack(side="left", padx=5)

    def refresh_pet_buttons(self):
        """Refresh PET button colors and checkbox states based on associations."""
        for i, button in enumerate(self.pet_buttons):
            pet_num = i + 1
            assoc = self.state_manager.get_pet_association(pet_num)
            has_mc = assoc and assoc.mc_mac is not None

            # Update button color
            btn_bg = "#3498db" if has_mc else "#e67e22"
            button.config(bg=btn_bg)

            # Update checkbox state
            if pet_num in self.pet_checkboxes_widgets:
                checkbox_state = "normal" if has_mc else "disabled"
                self.pet_checkboxes_widgets[pet_num].config(state=checkbox_state)
                if not has_mc:
                    self.pet_checkbox_vars[pet_num].set(False)

    def send_pet_commands(self):
        """Send commands to all enabled PETs."""
        messagebox.showinfo(
            "Send Commands",
            "PET command sending not yet implemented.\n"
            "This will send the selected macro to all enabled PETs."
        )


    def register_mc(self):
        """Process MC registration from the form."""
        import re
        from ...core.models import MicroController

        mac_src = self.mac_source_var.get()
        mac_dst = self.mac_destiny_var.get().strip().lower()
        interface_dst = self.interface_destiny_var.get().strip()
        label = self.label_var.get().strip()

        # Validations
        if not mac_src or mac_src == "Select MAC source...":
            messagebox.showwarning("Validation", "Please select a MAC source")
            return

        if not mac_dst:
            messagebox.showwarning("Validation", "Please enter a MAC destiny")
            return

        if not interface_dst:
            messagebox.showwarning("Validation", "Please enter an interface destiny")
            return

        # Validate MAC format
        mac_pattern = r"^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$"
        if not re.match(mac_pattern, mac_dst):
            messagebox.showerror(
                "Validation",
                "Invalid MAC format\nUse format: fe:80:ab:cd:12:34"
            )
            return

        # Normalize format (use : as separator)
        mac_dst = mac_dst.replace("-", ":")

        # Create MicroController instance
        mc = MicroController(
            mac_source=mac_src,
            mac_destiny=mac_dst,
            interface_destiny=interface_dst,
            label=label if label else "No Label"
        )

        # Register in state manager
        self.state_manager.register_mc(mc)

        # Clear form
        self.mac_source_var.set("Select MAC source...")
        self.mac_destiny_var.set("")
        self.interface_destiny_var.set("")
        self.label_var.set("")

        # Refresh table and comboboxes
        self.refresh_mc_table()
        self.refresh_pet_buttons()

        # Show success message
        messagebox.showinfo(
            "Success",
            f"Microcontroller registered:\n{mac_src} → {mac_dst} ({interface_dst})"
        )

    def delete_mc(self, mac_source: str):
        """
        Delete a microcontroller.

        Args:
            mac_source: Source MAC address of MC to delete
        """
        # Confirm deletion
        mc = self.state_manager.get_mc(mac_source)
        if not mc:
            return

        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete microcontroller '{mc.label}'?\n"
            f"MAC: {mc.mac_source} → {mc.mac_destiny}"
        )

        if result:
            self.state_manager.unregister_mc(mac_source)
            self.refresh_mc_table()
            if hasattr(self, 'refresh_pet_buttons'):
                self.refresh_pet_buttons()
            messagebox.showinfo("Success", "Microcontroller deleted successfully")

    def load_data(self):
        """Load and display data from state manager."""
        # Refresh tables
        self.refresh_mc_table()

        # Update macro options
        if hasattr(self, 'macro_combo_dashboard'):
            self.update_macro_options()

        # Refresh PET buttons to show current associations
        if hasattr(self, 'pet_buttons'):
            self.refresh_pet_buttons()

        # Load PET checkbox states
        if hasattr(self, 'pet_checkbox_vars'):
            for pet_num in range(1, 11):
                assoc = self.state_manager.get_pet_association(pet_num)
                if assoc and pet_num in self.pet_checkbox_vars:
                    self.pet_checkbox_vars[pet_num].set(assoc.enabled)
