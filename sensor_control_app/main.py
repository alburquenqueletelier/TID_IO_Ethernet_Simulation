"""
Main entry point for the PET Scanner Control Application.

This module provides the main entry point for the modular version
of the application. It can be run as:

    python -m sensor_control_app.main

Or directly:

    python sensor_control_app/main.py

For root privileges (required for raw sockets):

    sudo $(which python) -m sensor_control_app.main
"""

import sys
import os

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_control_app.ui.app import main

if __name__ == "__main__":
    main()
