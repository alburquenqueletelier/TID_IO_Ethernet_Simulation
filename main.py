#!/usr/bin/env python3
"""
Main entry point for PET Scanner Control Application (Modular Version).

This is the recommended entry point for the refactored modular application.

Usage:
    python main.py

With sudo (required for raw sockets):
    sudo $(which python) main.py

Or as a module:
    python -m sensor_control_app.main
"""

from sensor_control_app.ui.app import main

if __name__ == "__main__":
    main()
