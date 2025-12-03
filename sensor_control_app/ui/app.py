"""
Main application window module.

This module provides the main application window that integrates
all components: Dashboard, Commands, and future tabs.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ..core import StateManager
from ..network import InterfaceDiscovery, PacketSender
from ..storage import Database, MacroManager
from .tabs import DashboardTab, CommandsTab


class McControlApp:
    """
    Main application window.

    This class coordinates all application components and provides
    the main window with notebook (tabs) interface.
    """

    def __init__(self, root: tk.Tk, db_path: str = "db.json"):
        """
        Initialize the application.

        Args:
            root: Root Tk window
            db_path: Path to database file
        """
        self.root = root
        self.db_path = db_path

        # Configure window
        self.root.title("PET Scanner Control - Microcontroller Management")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Initialize core components
        self.database = Database(db_path)
        self.state_manager = StateManager(self.database)
        self.interface_discovery = InterfaceDiscovery()
        self.packet_sender = PacketSender()
        self.macro_manager = MacroManager(self.database)

        # Load database
        self.database.load()
        self.state_manager.load_from_db()

        # Create UI
        self.create_ui()

        # Load initial data
        self.load_initial_data()

        # Setup close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_ui(self):
        """Create the main UI structure."""
        # Create menu bar
        self.create_menu()

        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.create_dashboard_tab()
        self.create_commands_tab()

    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_dashboard_tab(self):
        """Create Dashboard tab."""
        self.dashboard_tab = DashboardTab(
            self.notebook,
            self.state_manager,
            self.interface_discovery,
            self.packet_sender,
            self.macro_manager,
            on_refresh_callback=self.on_dashboard_refresh
        )
        self.notebook.add(self.dashboard_tab, text="Dashboard")

    def create_commands_tab(self):
        """Create Commands tab."""
        self.commands_tab = CommandsTab(
            self.notebook,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )
        self.notebook.add(self.commands_tab, text="Commands")

    def load_initial_data(self):
        """Load initial data into tabs."""
        # Load dashboard data
        self.dashboard_tab.load_data()
        self.dashboard_tab.refresh_interfaces()

        # Load commands tab data
        self.commands_tab.refresh_mc_list()

    def on_dashboard_refresh(self):
        """Handle dashboard refresh event."""
        # Update commands tab MC list when dashboard refreshes
        self.commands_tab.refresh_mc_list()

    def save_data(self):
        """Save application data to database."""
        try:
            self.state_manager._save_to_db()
            messagebox.showinfo("Success", "Data saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def show_about(self):
        """Show about dialog."""
        about_text = (
            "PET Scanner Control Application\n\n"
            "Version: 2.0 (Modular)\n\n"
            "A modular data acquisition system for PET scanners.\n\n"
            "Components:\n"
            "- Microcontroller Management\n"
            "- Command Configuration & Sending\n"
            "- Network Interface Discovery\n"
            "- PET Scanner Associations\n\n"
            "Built with:\n"
            "- Python 3.11+\n"
            "- Tkinter (GUI)\n"
            "- Scapy (Layer 2 Networking)\n"
            "- psutil (Network Interfaces)\n"
        )

        messagebox.showinfo("About", about_text)

    def on_closing(self):
        """Handle window close event."""
        # Ask for confirmation
        result = messagebox.askyesnocancel(
            "Exit",
            "Do you want to save changes before exiting?"
        )

        if result is None:  # Cancel
            return
        elif result:  # Yes - save and exit
            try:
                self.state_manager._save_to_db()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        # Stop any ongoing packet sending
        if self.packet_sender.is_sending():
            self.packet_sender.cancel()

        # Destroy window
        self.root.destroy()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()


def main():
    """
    Main entry point for the modular application.

    Creates the root window and starts the application.
    """
    root = tk.Tk()
    app = McControlApp(root)
    app.run()


if __name__ == "__main__":
    main()
