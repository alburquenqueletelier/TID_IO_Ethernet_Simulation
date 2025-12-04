# TID - PET Scanner Control Application

Application for communication between Computer and Microcontrollers (FPGAs)

Desktop application that enables communication with FPGAs (Microcontrollers) via Ethernet using a custom protocol for configuring PET scanners, debugging, and collecting sensor data.

The system supports up to 10 FPGAs, each connected to the computer via Ethernet, receiving 1Gbit/s from each device during data capture.

---

## Features

- **Microcontroller Management**: Register and manage up to 10 FPGAs via Ethernet
- **PET Scanner Association**: Associate microcontrollers with 10 PET scanner units
- **Command Configuration**: Configure and send custom Layer 2 Ethernet commands
- **Network Interface Discovery**: Automatic detection of available Ethernet interfaces
- **Macro System**: Save and load command configurations as reusable macros
- **Persistent Storage**: JSON-based database for configurations
- **Real-time Monitoring**: Dashboard with live status of microcontrollers and PET scanners

---

## Architecture

The application is built with a modular architecture:

```
sensor_control_app/
├── core/               # State management and data models
├── network/            # Layer 2 networking (Scapy-based)
├── storage/            # Database and macro management
├── ui/                 # User interface components
│   ├── app.py         # Main application window
│   ├── widgets/       # Reusable UI components
│   └── tabs/          # Dashboard and Commands tabs
└── tests/             # Comprehensive test suite
```

### Key Technologies

- **Python 3.11+**: Modern Python with type hints
- **Tkinter**: Native GUI framework
- **Scapy**: Layer 2 Ethernet packet manipulation
- **psutil**: Network interface discovery
- **unittest**: Testing framework

---

## Requirements

```bash
contourpy==1.3.3
cycler==0.12.1
fonttools==4.59.2
kiwisolver==1.4.9
matplotlib==3.10.6
numpy==2.3.2
packaging==25.0
pillow==11.3.0
psutil==7.1.0
pyparsing==3.2.3
pyserial==3.5
python-dateutil==2.9.0.post0
python-dotenv==1.1.1
scapy==2.6.1
six==1.17.0
```

---

## Installation

### Using venv (recommended)

1. **Create virtual environment** (if it doesn't exist):
   ```bash
   python3 -m venv .venv
   ```

2. **Activate environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install tkinter globally** (if not already installed):
   ```bash
   sudo apt-get install python3-tk
   ```

---

## Running the Application

The application requires **root privileges** because it uses raw sockets for Layer 2 Ethernet communication.

### Recommended Method

```bash
sudo $(which python) main.py
```

The `$(which python)` ensures sudo uses the virtual environment Python instead of the global one.

### Alternative Methods

**As a module:**
```bash
sudo $(which python) -m sensor_control_app.main
```

**Legacy method** (deprecated, shows warning):
```bash
sudo $(which python) sensor_control_app.py
```

---

## Testing

The project includes comprehensive tests for all modules:

### Running Tests Locally

**Option 1: Using the test script (recommended)**
```bash
# Auto-detect environment (uses Xvfb if available)
./run_tests.sh

# Force headless mode (requires Xvfb)
./run_tests.sh headless

# Force desktop mode (uses current display)
./run_tests.sh desktop
```

**Option 2: Direct unittest execution**
```bash
# With current display
python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v

# With Xvfb (headless, for CI/CD)
xvfb-run python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
```

**Option 3: Using pytest** (if installed)
```bash
pytest sensor_control_app/tests/ -v
```

### Test Coverage

- **Core modules**: State management, data models
- **Network**: Interface discovery, packet sending
- **Storage**: Database, macro management
- **UI Widgets**: Scrollable frames, drag & drop, tooltips
- **UI Tabs**: Dashboard, Commands
- **Integration**: End-to-end workflows

**Total tests**: 268 (263 passing, 5 pending fixes)

---

## Configuration

### Network Interfaces

Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Use `ip a` on Linux to find interface names and MAC addresses.

### Database

Default location: `db.json` in project root

The database stores:
- Registered microcontrollers
- Command configurations per MC
- Universal and per-MC macros
- PET-to-MC associations

---

## Proof of Concept Scripts

Layer 2 communication examples in `poc/layer2_communitacion/`:

**Terminal 1** (receiver):
```bash
sudo $(which python) poc/layer2_communitacion/destination.py
```

**Terminal 2** (sender):
```bash
sudo $(which python) poc/layer2_communitacion/source.py
```

These demonstrate raw Ethernet frame communication using Scapy.

---

## Project Structure

```
.
├── main.py                       # Main entry point ⭐
├── sensor_control_app.py         # Legacy entry point (deprecated)
├── README.md                     # This file
├── CLAUDE.md                     # Development guidelines for Claude Code
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment configuration template
├── pytest.ini                    # Test configuration
├── run_tests.sh                  # Test runner script
├── sensor_control_app/           # Main package
│   ├── __init__.py
│   ├── main.py                   # Package entry point
│   ├── core/                     # State & models
│   │   ├── __init__.py
│   │   ├── models.py             # Data models
│   │   ├── state_manager.py     # State management
│   │   └── protocol.py          # Command protocol
│   ├── network/                  # Networking
│   │   ├── __init__.py
│   │   ├── interface_discovery.py
│   │   └── packet_sender.py
│   ├── storage/                  # Persistence
│   │   ├── __init__.py
│   │   ├── database.py          # JSON database
│   │   └── macro_manager.py     # Macro CRUD
│   ├── ui/                       # User interface
│   │   ├── __init__.py
│   │   ├── app.py               # Main window
│   │   ├── widgets/             # Reusable components
│   │   │   ├── __init__.py
│   │   │   ├── scrollable_frame.py
│   │   │   ├── drag_drop_list.py
│   │   │   └── tooltip.py
│   │   └── tabs/                # Tab components
│   │       ├── __init__.py
│   │       ├── dashboard_tab.py
│   │       └── commands_tab.py
│   └── tests/                    # Test suite
│       ├── conftest.py           # Shared test fixtures
│       ├── test_*.py             # Module tests
│       └── test_integration.py   # Integration tests
├── poc/                          # Proof of concept scripts
│   └── layer2_communitacion/
└── .github/
    └── workflows/
        └── python-app.yml        # CI/CD configuration
```

---

## Development

### Development Setup

1. Clone the repository
2. Set up virtual environment (see Installation)
3. Install dependencies
4. Run tests to verify setup

### Code Style

- Type hints for all functions
- Docstrings for all public APIs
- Maximum line length: 127 characters
- Linting: flake8

### Testing Guidelines

- Write tests for all new features
- Run tests before committing
- Maintain test coverage above 95%
- Use mocks for external dependencies

### CI/CD

Tests run automatically on push/PR to `main` branch via GitHub Actions.

---

## Usage Guide

### 1. Register Microcontrollers

1. Launch the application
2. Go to **Dashboard** tab
3. Click "🔄 Refresh Interfaces" to discover network interfaces
4. Click "➕ Register New MC" to add microcontrollers
5. Enter MAC addresses and interface names

### 2. Associate PET Scanners

1. In **Dashboard** tab, scroll to "PET Scanner Associations"
2. For each PET (1-10), select the associated microcontroller from dropdown
3. Enable the checkbox to activate the PET
4. Click "Save" from menu

### 3. Configure Commands

1. Go to **Commands** tab
2. Select a microcontroller from dropdown
3. Configure commands using checkboxes and radio buttons
4. Set repetitions and delays as needed
5. Click "💾 Save Current MC Config" to save

### 4. Send Commands

1. In **Commands** tab, configure desired commands
2. Click "📡 Send Commands to Selected MC" to send to one MC
3. Or use PET scanner macros to broadcast to multiple MCs
4. Monitor progress in status label

### 5. Use Macros

**Save a macro:**
1. Configure commands in Commands tab
2. Click "💾 Save as Macro"
3. Enter macro name

**Load a macro:**
1. Select macro from dropdown
2. Click "📂 Load Macro"
3. Commands are restored

---

## Troubleshooting

### "Permission denied" errors

The application requires root privileges for raw sockets. Always use:
```bash
sudo $(which python) main.py
```

### Virtual environment not used with sudo

Make sure to use `$(which python)` instead of just `python`:
```bash
# ✅ Correct
sudo $(which python) main.py

# ❌ Wrong (uses system Python)
sudo python main.py
```

### Tkinter not found

Install tkinter globally:
```bash
sudo apt-get install python3-tk
```

### Network interface not showing

1. Check interface is up: `ip link show`
2. Verify you're running with sudo
3. Check .env configuration

### Database errors

If `db.json` becomes corrupted:
1. Stop the application
2. Backup current db: `cp db.json db.json.backup`
3. Delete db.json
4. Restart application (creates new empty db)

---

## Contributing

This is a university research project (TID - Taller de Investigación y Desarrollo) focusing on:
- Building an open-source data acquisition system
- Characterizing particle detectors (SiPMs)
- Custom Ethernet protocol implementation
- Real-time sensor data visualization

### Development Roadmap

- [x] Phase 1: Project setup and monolithic prototype
- [x] Phase 2: Core models and state management
- [x] Phase 3: Network and storage modules
- [x] Phase 4: UI widgets
- [x] Phase 5: UI tabs
- [x] Phase 6: Integration and entry points
- [ ] Phase 7: Cleanup and final documentation
- [ ] Future: Data visualization and analysis tools

---

## License

This project is part of university research and is provided as-is for educational purposes.

---

## Release Notes

Given that end users are experienced in programming, releases will be made through code updates with notifications. Packaging into a standalone executable may be considered later, but for now users are responsible for managing their own installations.

This approach allows users to:
- Modify source code as needed
- Directly edit the database file
- Customize network configurations
- Extend functionality

---

## Support

For issues, questions, or contributions:
1. Check this README and CLAUDE.md
2. Review test files for usage examples
3. Examine the code documentation
4. Contact the development team

---

## Acknowledgments

- Universidad Adolfo Ibáñez (UAI)
- TID Research Program
- Contributors and testers

---

**Last Updated**: December 2, 2025
**Version**: 2.0 (Modular Architecture)
