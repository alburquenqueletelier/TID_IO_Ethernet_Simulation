# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PET scan control and data acquisition application that communicates with FPGAs (microcontrollers) via Ethernet using a custom Layer 2 protocol. The system handles up to 10 FPGAs, each connected via Ethernet at 1Gbit/s, used for configuring PET scans, debugging, and collecting sensor data.

**Architecture**: Modular design with clear separation of concerns
**Version**: 2.0 (Refactored from monolithic to modular)

## Development Setup

### Environment Setup
```bash
# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install tkinter globally (if not already installed)
sudo apt-get install python3-tk
```

### Configuration
Copy `.env.example` to `.env` and configure network interfaces:
```bash
cp .env.example .env
```

Use `ip a` on Linux to find interface names and MAC addresses.

## Running the Application

### Main Application (Recommended)
```bash
sudo $(which python) main.py
```

### Alternative Entry Points
```bash
# As a module
sudo $(which python) -m sensor_control_app.main

# Package style
sudo $(which python) sensor_control_app/main.py

# Legacy (deprecated, shows warning)
sudo $(which python) sensor_control_app.py
```

**Important:** The application requires sudo privileges because it uses raw sockets (Layer 2 Ethernet frames via Scapy). The `$(which python)` ensures sudo uses the virtual environment Python instead of the global one.

### Testing

The project uses **unittest** (Python standard library) for testing. Tests are located in `sensor_control_app/tests/` and are compatible with both unittest and pytest runners.

#### Running Tests Locally

**Option 1: Using the provided script (recommended)**
```bash
# Auto-detect environment (uses Xvfb if available, otherwise uses current display)
./run_tests.sh

# Force headless mode (requires Xvfb installed)
./run_tests.sh headless

# Force desktop mode (uses your current display)
./run_tests.sh desktop

# Using pytest (if installed)
./run_tests.sh pytest
```

**Option 2: Direct unittest execution**
```bash
# With current display (requires active desktop session)
python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v

# With Xvfb (headless, simulates CI/CD environment)
xvfb-run python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
```

**Option 3: Using pytest (if installed)**
```bash
# With current display
pytest sensor_control_app/tests/ -v

# With Xvfb (headless)
xvfb-run pytest sensor_control_app/tests/ -v
```

#### Installing Xvfb (for headless testing)

Xvfb is only required for running tests in headless mode (without a display), such as in CI/CD environments:

```bash
# On Ubuntu/Debian
sudo apt-get install xvfb
```

**Note:** You do NOT need Xvfb for local development if you have an active desktop session. It's primarily used in GitHub Actions CI/CD.

#### Test Configuration

- **Test location:** `sensor_control_app/tests/`
- **Test discovery:** Configured in `pytest.ini`
- **Shared setup:** `sensor_control_app/tests/conftest.py`
- **CI/CD:** Tests run automatically on push/PR to `main` branch via GitHub Actions with Xvfb
- **Total tests:** 268 (263 passing, 5 integration tests pending fixes)

Tests are configured to run in CI/CD via GitHub Actions using Xvfb for headless GUI testing.

### PoC (Proof of Concept) Scripts
Located in `poc/layer2_communitacion/`:
```bash
# Terminal 1: Start receiver
sudo $(which python) poc/layer2_communitacion/destination.py

# Terminal 2: Send frames
sudo $(which python) poc/layer2_communitacion/source.py
```

These scripts demonstrate raw Ethernet frame communication using Scapy.

## Architecture

### Modular Structure

The application follows a layered modular architecture:

```
sensor_control_app/
├── core/                      # Business logic & data models
│   ├── models.py              # MicroController, PETAssociation, Macro dataclasses
│   ├── state_manager.py       # Central state management
│   └── protocol.py            # Command protocol definitions
├── network/                   # Layer 2 networking
│   ├── interface_discovery.py # Ethernet interface discovery (psutil)
│   └── packet_sender.py       # Raw packet transmission (Scapy)
├── storage/                   # Data persistence
│   ├── database.py            # JSON database operations
│   └── macro_manager.py       # Macro CRUD operations
├── ui/                        # User interface
│   ├── app.py                 # Main application window (McControlApp)
│   ├── widgets/               # Reusable UI components
│   │   ├── scrollable_frame.py  # Canvas + Scrollbar wrapper
│   │   ├── drag_drop_list.py    # Drag & drop reorderable list
│   │   └── tooltip.py           # Hover tooltips
│   └── tabs/                  # Tab components
│       ├── dashboard_tab.py    # MC & PET management
│       └── commands_tab.py     # Command configuration & sending
└── tests/                     # Test suite
    ├── conftest.py            # Shared test fixtures
    ├── test_*.py              # Module-specific tests
    └── test_integration.py    # Integration tests
```

### Dependency Flow

```
main.py
  └─> McControlApp (ui/app.py)
        ├─> Database (storage/database.py)
        ├─> StateManager (core/state_manager.py)
        │     └─> uses Database
        ├─> InterfaceDiscovery (network/interface_discovery.py)
        ├─> PacketSender (network/packet_sender.py)
        ├─> MacroManager (storage/macro_manager.py)
        │     └─> uses Database
        ├─> DashboardTab (ui/tabs/dashboard_tab.py)
        │     ├─> uses StateManager
        │     ├─> uses InterfaceDiscovery
        │     ├─> uses PacketSender
        │     └─> uses MacroManager
        └─> CommandsTab (ui/tabs/commands_tab.py)
              ├─> uses StateManager
              ├─> uses PacketSender
              └─> uses MacroManager
```

**Design Pattern**: Dependency Injection - All dependencies are injected at initialization, making testing and maintenance easier.

### Core Module Details

#### 1. Models (core/models.py)

```python
@dataclass
class MicroController:
    """Represents a registered FPGA microcontroller."""
    mac_source: str                    # Source MAC address
    mac_destiny: str                   # Destination MAC address
    interface_destiny: str             # Network interface name
    label: str                         # User-friendly label
    command_configs: Dict = field(default_factory=dict)
    last_state: Dict = field(default_factory=dict)
    macros: Dict = field(default_factory=dict)

@dataclass
class PETAssociation:
    """Represents PET scanner to MC association."""
    pet_num: int                       # PET number (1-10)
    mc_mac: Optional[str] = None       # Associated MC MAC (or None)
    enabled: bool = False              # Enabled for commands

@dataclass
class Macro:
    """Reusable command configuration."""
    name: str
    command_configs: Dict = field(default_factory=dict)
    last_state: Dict = field(default_factory=dict)
```

#### 2. StateManager (core/state_manager.py)

Central state management for the entire application:

```python
class StateManager:
    def __init__(self, database: Optional[Database] = None):
        self.database = database
        self.mc_available: Dict[str, str] = {}     # Available MCs (discovered)
        self.mc_registered: Dict[str, MicroController] = {}  # Registered MCs
        self.pet_associations: Dict[int, PETAssociation] = {}  # 10 PET associations
        self.macros: Dict[str, Macro] = {}         # Universal macros

    # MC Management
    def register_mc(self, mc: MicroController) -> None
    def unregister_mc(self, mac_source: str) -> bool
    def get_mc(self, mac_source: str) -> Optional[MicroController]
    def get_all_registered_mcs(self) -> List[MicroController]

    # PET Management
    def associate_pet_with_mc(self, pet_num: int, mc_mac: str) -> None
    def get_pet_association(self, pet_num: int) -> PETAssociation
    def set_pet_enabled(self, pet_num: int, enabled: bool) -> None

    # Macro Management
    def save_universal_macro(self, name: str, macro: Macro) -> None
    def get_universal_macro(self, name: str) -> Optional[Macro]
    def list_universal_macros(self) -> List[str]

    # Persistence
    def load_from_db(self) -> None
    def _save_to_db(self) -> None
```

#### 3. Protocol (core/protocol.py)

Command protocol definitions:

```python
COMMAND_GROUPS = {
    "CPU & Diagnostics": ["X_00_CPU", "X_02_TestTrigger", "X_08_DIAG_", "X_09_DIAG_DIS"],
    "Readout": ["X_03_RO_Single", "X_04_RO_Continous", "X_05_RO_OFF"],
    "Trigger Modes": ["X_F9_TriggerExt", "X_FA_TriggerInt", "X_FB_TriggerOff", "X_FC_TriggerAutomatic"],
    "Power": ["X_20_PowerON_SIPM", ...],
    "Fan Speed": ["X_E0_FanSpeed0", "X_E1_FanSpeed1", "X_E2_FanSpeed2", "X_E3_FanSpeed3"],
    "Reset": ["X_FF_Reset"]
}

COMMAND_CONFIG = {
    "X_00_CPU": {
        "label": "CPU",
        "options": ["OFF", "ON"],
        "byte": b'\x00'
    },
    # ... more commands
}
```

### Network Module Details

#### 1. InterfaceDiscovery (network/interface_discovery.py)

Discovers Ethernet interfaces using psutil:

```python
class InterfaceDiscovery:
    def get_ethernet_interfaces(self) -> Dict[str, str]:
        """Returns {mac_address: interface_name}"""

    def is_interface_up(self, interface_name: str) -> bool:
        """Checks if interface is active"""
```

Filters out:
- Loopback interfaces
- Virtual interfaces (docker, veth, etc.)
- Wireless interfaces (wlan, wlp)

#### 2. PacketSender (network/packet_sender.py)

Sends Layer 2 Ethernet packets using Scapy:

```python
@dataclass
class PacketInfo:
    """Information for a packet to be sent."""
    mac_source: str
    mac_destiny: str
    interface: str
    command_byte: bytes
    command_name: str = ""
    repetitions: int = 1
    delay_ms: int = 0

class PacketSender:
    def send_packet(self, packet_info: PacketInfo) -> bool:
        """Send a single packet"""

    def send_packet_with_repetitions(self, packet_info: PacketInfo,
                                     progress_callback: Optional[Callable] = None) -> bool:
        """Send packet multiple times with delay"""

    def send_packets_batch_async(self, packets: List[PacketInfo],
                                 progress_callback: Optional[Callable] = None,
                                 completion_callback: Optional[Callable] = None) -> None:
        """Send multiple packets asynchronously"""
```

Packet structure:
```python
packet = Ether(dst=mac_destiny, src=mac_source) / Raw(load=command_bytes)
```

Command bytes format: 7 bytes total
- Byte 0-3: Constant bytes (0x48, 0x00, 0x00, 0x00)
- Byte 4-5: Padding (0x00, 0x00)
- Byte 6: Command byte

### Storage Module Details

#### 1. Database (storage/database.py)

JSON-based persistence with error handling:

```python
class Database:
    def __init__(self, file_path: str = "db.json"):
        self.file_path = file_path
        self.data: dict = {}

    def load(self) -> dict:
        """Load database from file, handle corruption"""

    def save(self, data: dict) -> None:
        """Save data to file atomically"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key"""

    def set(self, key: str, value: Any) -> None:
        """Set value and auto-save"""

    def backup(self, backup_path: Optional[str] = None) -> str:
        """Create backup of database"""
```

Database structure:
```json
{
    "mc_registered": {
        "mac_source": { "mac_destiny": "...", "label": "...", ... }
    },
    "macros": {
        "macro_name": { "command_configs": {...}, "last_state": {...} }
    },
    "pet_associations": {
        "1": { "mc": "mac_address", "enabled": true }
    }
}
```

#### 2. MacroManager (storage/macro_manager.py)

Macro CRUD operations:

```python
class MacroManager:
    def __init__(self, database: Database):
        self.database = database

    # Universal Macros
    def save_universal_macro(self, name: str, macro_data: dict) -> None
    def load_universal_macro(self, name: str) -> Optional[dict]
    def delete_universal_macro(self, name: str) -> bool
    def list_universal_macros(self) -> List[str]

    # MC-Specific Macros
    def save_mc_macro(self, mc_mac: str, name: str, macro_data: dict) -> None
    def load_mc_macro(self, mc_mac: str, name: str) -> Optional[dict]
    def delete_mc_macro(self, mc_mac: str, name: str) -> bool
    def list_mc_macros(self, mc_mac: str) -> List[str]
```

### UI Module Details

#### 1. Main Application (ui/app.py)

```python
class McControlApp:
    def __init__(self, root: tk.Tk, db_path: str = "db.json"):
        # Initialize all dependencies
        self.database = Database(db_path)
        self.state_manager = StateManager(self.database)
        self.interface_discovery = InterfaceDiscovery()
        self.packet_sender = PacketSender()
        self.macro_manager = MacroManager(self.database)

        # Load data
        self.database.load()
        self.state_manager.load_from_db()

        # Create UI
        self.create_menu()
        self.notebook = ttk.Notebook(root)
        self.dashboard_tab = DashboardTab(self.notebook, ...)
        self.commands_tab = CommandsTab(self.notebook, ...)

    def save_data(self):
        """Save all state to database"""

    def on_closing(self):
        """Handle window close with save prompt"""
```

#### 2. Widgets

**ScrollableFrame** (ui/widgets/scrollable_frame.py):
- Canvas + Scrollbar encapsulation
- Mousewheel support (cross-platform)
- Auto-updating scroll region

**DragDropList** (ui/widgets/drag_drop_list.py):
- Reorderable list items
- Drag & drop with visual feedback
- Callback on reorder

**Tooltip** (ui/widgets/tooltip.py):
- Hover tooltips
- Configurable delay, colors, fonts

#### 3. Tabs

**DashboardTab** (ui/tabs/dashboard_tab.py):
- Network interface list with refresh
- MC registration table
- PET-to-MC association matrix (10 PETs)
- Universal macro selection for PET commands

**CommandsTab** (ui/tabs/commands_tab.py):
- MC selection dropdown
- Command configuration UI (checkboxes, radio buttons)
- Command sending with progress
- Macro save/load per MC

### Key Data Flows

#### Registering a Microcontroller

1. User clicks "➕ Register New MC" in Dashboard
2. Dialog collects MAC addresses and interface
3. DashboardTab creates MicroController instance
4. StateManager.register_mc(mc) called
5. StateManager saves to Database
6. Dashboard refreshes MC table
7. CommandsTab is notified to refresh MC list

#### Sending Commands

1. User configures commands in CommandsTab
2. User clicks "📡 Send Commands"
3. CommandsTab calls get_command_configs() to build command list
4. Creates PacketInfo list for each enabled command
5. Calls PacketSender.send_packets_batch_async()
6. PacketSender creates background thread
7. Each packet is sent via Scapy's sendp()
8. Progress callbacks update UI
9. Completion callback re-enables UI

#### PET Scanner Broadcasting

1. User selects universal macro in Dashboard
2. User clicks "Send to Selected PETs"
3. Dashboard identifies all enabled PETs
4. For each enabled PET:
   - Get associated MC
   - Load macro commands
   - Build PacketInfo list
5. Send to all MCs concurrently
6. Update progress for each MC

## Testing Guidelines

### Test Structure

**Core Tests:**
- `test_models.py`: Data model creation, serialization
- `test_state_manager.py`: State operations, persistence
- `test_protocol.py`: Command definitions

**Network Tests:**
- `test_interface_discovery.py`: Interface detection (mocked psutil)
- `test_packet_sender.py`: Packet creation, sending (mocked Scapy)

**Storage Tests:**
- `test_database.py`: JSON operations, error handling
- `test_macro_manager.py`: Macro CRUD operations

**UI Tests:**
- `test_scrollable_frame.py`: Scrolling, bindings
- `test_drag_drop_list.py`: Drag & drop, reordering
- `test_tooltip.py`: Tooltip display, timing
- `test_dashboard_tab.py`: Tab initialization, data loading
- `test_commands_tab.py`: Command configuration, MC selection

**Integration Tests:**
- `test_integration.py`: End-to-end workflows (5 tests pending fixes)

### Running Tests in CI/CD

Configured in `.github/workflows/python-app.yml`:
- Runs on push/PR to `main` branch
- Uses Python 3.11
- Linting with flake8 (max line length: 127)
- Tests run with `xvfb-run python -m unittest`

## Important Development Notes

### Network Permissions

All network communication requires root privileges due to raw socket usage. Always use:
```bash
sudo $(which python) <script>
```

### Database File

`db.json` is the persistent storage. It's created automatically on first run and updated on:
- Microcontroller registration/unregistration
- Command configuration changes
- Macro save operations
- PET association changes

**Location**: Project root (configurable)

### State Management Best Practices

1. **Always use StateManager**: Don't modify data structures directly
2. **Use dependency injection**: Pass StateManager to components
3. **Auto-save on changes**: StateManager saves to DB automatically
4. **Use typed models**: MicroController, PETAssociation, Macro

### Threading Considerations

Command sending runs in background threads:
- Use `daemon=True` for auto-cleanup
- Provide cancel flags for user interruption
- Use callbacks for progress updates
- Update UI from main thread only (use `after()`)

Example:
```python
def send_in_background():
    threading.Thread(
        target=self._send_task,
        args=(packets, callback),
        daemon=True
    ).start()
```

### UI Update Pattern

When updating UI from callbacks:
```python
def progress_callback(current, total):
    root.after(0, lambda: update_ui(current, total))
```

This ensures UI updates happen in the main thread.

## Legacy Code

### Monolithic Version (Deprecated)

The file `sensor_control_app.py` (~2944 lines) is the original monolithic version. It's deprecated but maintained for backwards compatibility.

**DO NOT:**
- Add new features to sensor_control_app.py
- Refactor sensor_control_app.py
- Fix bugs in sensor_control_app.py (unless critical)

**DO:**
- Implement new features in modular codebase
- Guide users toward `main.py` entry point
- Keep deprecation warning prominent

## Project Context

This is a university research project (TID - Taller de Investigación y Desarrollo) focused on:
- Building an open-source data acquisition system
- Characterizing particle detectors (SiPMs)
- Custom Ethernet protocol implementation
- Real-time sensor data visualization

The project emphasizes accessibility and modularity as an alternative to expensive proprietary DAQ systems.

## Development Roadmap

- [x] Phase 1: Monolithic prototype
- [x] Phase 2: Core models and state management
- [x] Phase 3: Network and storage modules
- [x] Phase 4: UI widgets
- [x] Phase 5: UI tabs
- [x] Phase 6: Integration and entry points
- [ ] Phase 7: Cleanup and final documentation (in progress)
- [ ] Future: Data visualization and analysis tools

## Additional Resources

- **README.md**: User-facing documentation
- **REFACTOR.md**: Refactoring plan and progress
- **PHASE*_SUMMARY.md**: Detailed summaries of each refactoring phase
- **tests/**: Comprehensive test suite with examples

---

**Last Updated**: December 2, 2025
**Architecture Version**: 2.0 (Modular)
