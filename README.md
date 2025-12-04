# TID 

# Aplicación para comunicación entre Computadora y Micro Controlador

Aplicación de escritorio que permite la comunicación con FPGAs (Micro controladores) vía Ethernet usando protocolo personaliazdo para configurar PET SCAN, debuggin y recopilación de data de los sensores conectados a estas. 

El dispositivo contará con 10 FPGAs conectadas cada una con la computadora donde corre la aplicación vía Ethernet, recibiendo 1GBit/s por cada uno de los dispositivos cuando esté capturando datos. 

## Requerimientos

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

## Instalación
Con gestor de ambiente venv

1. Crear ambiente si no existe: `python3 -m venv .venv`
2. Levantar ambiente: `source .venv/bin/activate`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Instalar tkinter globalmente (no siempre viene) `sudo apt-get install python3-tk`

# Estado actual

## Estructura del proyecto
Modelo Vista Controlador

```
sensor_control_app
├── core
│   ├── __init__.py
│   ├── models.py
│   ├── protocol.py
│   └── state_manager.py
├── __init__.py
├── main.py
├── network
│   ├── __init__.py
│   ├── interface_discovery.py
│   └── packet_sender.py
├── storage
│   ├── database.py
│   ├── __init__.py
│   └── macro_manager.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── README.md
│   ├── test_app.py
│   ├── test_commands_tab.py
│   ├── test_dashboard_tab.py
│   ├── test_database.py
│   ├── test_drag_drop_list.py
│   ├── test_integration.py
│   ├── test_interface_discovery.py
│   ├── test_macro_manager.py
│   ├── test_models.py
│   ├── test_packet_sender.py
│   ├── test_protocol.py
│   ├── test_scrollable_frame.py
│   ├── test_state_manager.py
│   └── test_tooltip.py
├── ui
│   ├── app.py
│   ├── dialogs
│   │   └── __init__.py
│   ├── __init__.py
│   ├── tabs
│   │   ├── commands_tab.py
│   │   ├── dashboard_tab.py
│   │   └── __init__.py
│   └── widgets
│       ├── drag_drop_list.py
│       ├── __init__.py
│       ├── scrollable_frame.py
│       └── tooltip.py
└── utils
    └── __init__.py
```

## Separación de Responsabilidades

### 1. core/protocol.py
**Responsabilidad:** Definir el protocolo de comunicación

```python
# Comandos del protocolo
COMMANDS = {
    "X_00_CPU": b"\x00",
    "X_02_TestTrigger": b"\x02",
    # ... resto de comandos
}

# Configuraciones de comandos (HIGH/LOW, etc.)
COMMAND_CONFIGS = {
    "X_E1_FanSpeed0_High | X_E0_FanSpeed0_Low": {
        "HIGH": "X_E1_FanSpeed0_High",
        "LOW": "X_E0_FanSpeed0_Low"
    },
    # ... resto de configuraciones
}
```

### 2. core/models.py
**Responsabilidad:** Definir modelos de datos con dataclasses

```python
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class MicroController:
    mac_source: str
    mac_destiny: str
    interface_destiny: str
    label: str
    command_configs: Dict = field(default_factory=dict)
    last_state: Dict = field(default_factory=dict)
    macros: Dict = field(default_factory=dict)

@dataclass
class PETAssociation:
    pet_num: int
    mc_mac: Optional[str] = None
    enabled: bool = False

@dataclass
class Macro:
    name: str
    command_configs: Dict = field(default_factory=dict)
    last_state: Dict = field(default_factory=dict)
```

### 3. core/state_manager.py
**Responsabilidad:** Gestionar el estado de la aplicación

```python
class StateManager:
    def __init__(self, database):
        self.database = database
        self.mc_registered: Dict[str, MicroController] = {}
        self.mc_available: Dict[str, str] = {}
        self.pet_associations: Dict[int, PETAssociation] = {}
        self.macros: Dict[str, Macro] = {}

    def register_mc(self, mc: MicroController) -> None
    def unregister_mc(self, mac_source: str) -> None
    def get_mc(self, mac_source: str) -> Optional[MicroController]
    def associate_pet(self, pet_num: int, mc_mac: str) -> None
    def get_pet_mcs(self, enabled_only: bool = False) -> List[MicroController]
```

### 4. network/interface_discovery.py
**Responsabilidad:** Detectar interfaces de red

```python
import psutil

class InterfaceDiscovery:
    @staticmethod
    def get_ethernet_interfaces() -> Dict[str, str]:
        """Retorna {mac_address: interface_name}"""
        # Lógica actual de refresh_mc_list()

    @staticmethod
    def is_interface_up(interface_name: str) -> bool:
        """Verifica si una interfaz está activa"""
```

### 5. network/packet_sender.py
**Responsabilidad:** Enviar paquetes Ethernet

```python
from scapy.all import Ether, Raw, sendp
import threading

class PacketSender:
    def __init__(self):
        self.sending = False
        self.cancel_flag = False

    def send_command(self,
                    mac_source: str,
                    mac_destiny: str,
                    interface: str,
                    command: bytes,
                    repetitions: int = 1,
                    delay_ms: int = 0) -> bool:
        """Envía un comando via Ethernet"""
        # Lógica extraída de send_command_packet()

    def send_commands_batch(self, commands: List[CommandInfo],
                           callback=None) -> None:
        """Envía múltiples comandos en thread separado"""
        # Lógica de send_all() en thread

    def cancel(self) -> None:
        """Cancela envío en progreso"""
        self.cancel_flag = True
```

### 6. storage/database.py
**Responsabilidad:** Persistencia en JSON

```python
import json
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "db.json"):
        self.db_path = Path(db_path)
        self.data = {}

    def load(self) -> dict:
        """Carga datos desde JSON"""
        # Lógica de init_database()

    def save(self, data: dict) -> None:
        """Guarda datos en JSON"""
        # Lógica de update_db_stats()

    def get(self, key: str, default=None):
        """Obtiene un valor"""

    def set(self, key: str, value) -> None:
        """Establece un valor y guarda"""
```

### 7. storage/macro_manager.py
**Responsabilidad:** Gestión de macros

```python
class MacroManager:
    def __init__(self, database: Database):
        self.database = database

    def save_macro(self, name: str, macro: Macro,
                   mc_mac: Optional[str] = None) -> None:
        """Guarda macro universal o por MC"""

    def load_macro(self, name: str,
                   mc_mac: Optional[str] = None) -> Optional[Macro]:
        """Carga macro"""

    def delete_macro(self, name: str,
                    mc_mac: Optional[str] = None) -> bool:
        """Elimina macro"""

    def list_macros(self, mc_mac: Optional[str] = None) -> List[str]:
        """Lista macros disponibles"""
```

### 8. ui/app.py
**Responsabilidad:** Coordinación de la UI

```python
import tkinter as tk
from tkinter import ttk

class McControlApp:
    def __init__(self, root: tk.Tk):
        self.root = root

        # Inyección de dependencias
        self.database = Database()
        self.state_manager = StateManager(self.database)
        self.packet_sender = PacketSender()
        self.macro_manager = MacroManager(self.database)
        self.interface_discovery = InterfaceDiscovery()

        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz principal"""
        self.notebook = ttk.Notebook(self.root)

        # Crear pestañas con inyección de dependencias
        self.dashboard_tab = DashboardTab(
            self.notebook,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )
        self.commands_tab = CommandsTab(
            self.notebook,
            self.state_manager,
            self.packet_sender,
            self.macro_manager
        )
```

### 9. ui/widgets/scrollable_frame.py
**Responsabilidad:** Widget reutilizable para scroll

```python
class ScrollableFrame(ttk.Frame):
    """Frame con scroll integrado"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical",
                                     command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Setup similar al patrón actual
        # Extraído de create_dashboard_tab() y create_commands_tab()
```

### 10. ui/widgets/drag_drop_list.py
**Responsabilidad:** Lista con drag & drop

```python
class DragDropList(ttk.Frame):
    """Lista con reordenamiento drag & drop"""
    def __init__(self, parent, items=None, **kwargs):
        super().__init__(parent, **kwargs)
        # Lógica de setup_drag_and_drop(), start_drag(),
        # do_drag(), end_drag(), reorder_commands()
```

### 11. ui/tabs/dashboard_tab.py
**Responsabilidad:** Pestaña Dashboard

```python
class DashboardTab(ttk.Frame):
    def __init__(self, parent, state_manager, packet_sender, macro_manager):
        super().__init__(parent)
        self.state_manager = state_manager
        self.packet_sender = packet_sender
        self.macro_manager = macro_manager

        self.setup_ui()

    def setup_ui(self):
        """Construye la UI del dashboard"""
        # Lógica extraída de create_dashboard_tab()
        self.create_mc_table()
        self.create_pet_section()
        self.create_macro_section()
```

### 12. ui/tabs/commands_tab.py
**Responsabilidad:** Pestaña Comandos

```python
class CommandsTab(ttk.Frame):
    def __init__(self, parent, state_manager, packet_sender, macro_manager):
        super().__init__(parent)
        self.state_manager = state_manager
        self.packet_sender = packet_sender
        self.macro_manager = macro_manager

        self.setup_ui()

    def setup_ui(self):
        """Construye la UI de comandos"""
        # Lógica extraída de create_commands_tab()
        self.create_mc_selector()
        self.create_command_list()
        self.create_control_buttons()
```

## Ejecución
1. Activar ambiente virtual de python: `source .venv/bin/activate`
2. Ejecutar app con: `sudo $(which python) main.py`

### Correr Test
1. `./run_test.sh` o `python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v`

**Nota:** otorgue permisos de modificación al script run_test `chmod +x run_test.sh` o ejecutelo con `bash run_test.sh`

# Deprecado
Versión anterior monolítica contenida en el archivo `sensor_control_app.py` con funcionalidades para:
1. Emparejar FPGA con Interfaz de computadora
2. Gestionar Macros de FGPA con sus comandos (no incluye comandos de CPU)
3. Enviar Macro a todos los PET Scan conectados a las FPGA

## Ejecución
Ejecutar: `sudo $(which python) sensor_control_app.py`
