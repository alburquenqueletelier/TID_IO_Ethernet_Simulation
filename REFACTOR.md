# REFACTOR.md

## Objetivo

Este documento define la estructura modular propuesta para refactorizar `sensor_control_app.py` (~2944 líneas) en componentes desacoplados, facilitando el mantenimiento, testing y escalabilidad del sistema. El refactor debe ser usando las mismas tecnologías.


## Estado Actual

- **Archivo único:** `sensor_control_app.py`
- **Clase monolítica:** `McControlApp` con 37+ métodos
- **Responsabilidades mezcladas:**
  - Lógica de red (Scapy)
  - Persistencia de datos (JSON)
  - UI (Tkinter)
  - Gestión de estado (MCs, PETs, macros)
  - Protocolo de comunicación

## Estructura Propuesta

```
sensor_control_app/
├── __init__.py
├── main.py                      # Punto de entrada
│
├── core/                        # Lógica de negocio
│   ├── __init__.py
│   ├── protocol.py             # Definición del protocolo (appendix_dict)
│   ├── models.py               # Modelos de datos (dataclasses)
│   └── state_manager.py        # Gestión de estado de la aplicación
│
├── network/                     # Comunicación de red
│   ├── __init__.py
│   ├── interface_discovery.py  # Detección de interfaces (psutil)
│   ├── packet_sender.py        # Envío de paquetes Ethernet (Scapy)
│   └── packet_receiver.py      # Recepción de paquetes (futuro)
│
├── storage/                     # Persistencia
│   ├── __init__.py
│   ├── database.py             # Gestión de db.json
│   └── macro_manager.py        # CRUD de macros
│
├── ui/                          # Interfaz gráfica
│   ├── __init__.py
│   ├── app.py                  # Ventana principal y coordinación
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── scrollable_frame.py  # Widget reutilizable para scroll
│   │   ├── tooltip.py           # Tooltips reutilizables
│   │   └── drag_drop_list.py    # Lista con drag & drop
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── dashboard_tab.py     # Pestaña Dashboard
│   │   └── commands_tab.py      # Pestaña Comandos
│   └── dialogs/
│       ├── __init__.py
│       ├── add_command_dialog.py
│       ├── register_mc_dialog.py
│       └── macro_dialog.py
│
├── utils/                       # Utilidades
│   ├── __init__.py
│   ├── validators.py           # Validaciones (MAC, IPs, etc.)
│   └── formatting.py           # Formateo de strings, timestamps
│
└── tests/                       # Tests unitarios e integración
    ├── __init__.py
    ├── test_protocol.py
    ├── test_state_manager.py
    ├── test_packet_sender.py
    ├── test_database.py
    ├── test_macro_manager.py
    └── test_ui.py

# Archivos en raíz del proyecto (sin cambios)
sensor_control_app.py           # [DEPRECADO - mantener temporalmente]
test_app.py                     # [MIGRAR a tests/]
requirements.txt
db.json
.env
README.md
CLAUDE.md
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

## Estrategia de Migración

### Fase 1: Setup y Estructura Base
1. Crear estructura de carpetas
2. Mover tests existentes a `tests/`
3. Crear `__init__.py` en todos los paquetes
4. Configurar imports relativos

### Fase 2: Core y Models
1. Crear `core/protocol.py` con comandos
2. Crear `core/models.py` con dataclasses
3. Crear `core/state_manager.py`
4. Tests unitarios para cada módulo

### Fase 3: Network y Storage
1. Extraer `network/interface_discovery.py`
2. Extraer `network/packet_sender.py`
3. Extraer `storage/database.py`
4. Extraer `storage/macro_manager.py`
5. Tests de integración

### Fase 4: UI Base
1. Extraer widgets reutilizables:
   - `ui/widgets/scrollable_frame.py`
   - `ui/widgets/drag_drop_list.py`
   - `ui/widgets/tooltip.py`
2. Tests de widgets

### Fase 5: UI Tabs y Dialogs
1. Extraer `ui/tabs/dashboard_tab.py`
2. Extraer `ui/tabs/commands_tab.py`
3. Extraer dialogs
4. Tests de UI (con Xvfb)

### Fase 6: Integración
1. Crear `ui/app.py` con inyección de dependencias
2. Crear `main.py` punto de entrada
3. Tests de integración completos
4. Validar funcionalidad equivalente

### Fase 7: Limpieza
1. Deprecar `sensor_control_app.py`
2. Actualizar `README.md` con nueva estructura
3. Actualizar `CLAUDE.md`
4. Actualizar CI/CD (`.github/workflows/python-app.yml`)
5. Eliminar `REFACTOR.md`

## Ventajas de la Refactorización

### Mantenibilidad
- **Separación de responsabilidades:** Cada módulo tiene una única responsabilidad clara
- **Archivos pequeños:** Más fácil de navegar y entender
- **Reutilización:** Widgets y componentes pueden reutilizarse

### Testabilidad
- **Tests unitarios:** Cada módulo puede testearse aisladamente
- **Mocking:** Inyección de dependencias facilita mocking
- **Cobertura:** Más fácil alcanzar alta cobertura

### Escalabilidad
- **Nuevas features:** Fácil agregar nuevos comandos, tabs, o protocolos
- **Múltiples interfaces:** Potencial para CLI, web, o API REST
- **Paralelización:** Separar red y UI facilita concurrencia

### Colaboración
- **Merge conflicts:** Menos conflictos al trabajar en módulos separados
- **Onboarding:** Nuevos desarrolladores entienden el código más rápido
- **Code review:** Más fácil revisar cambios aislados

## Compatibilidad durante Migración

Durante la migración, mantener `sensor_control_app.py` funcional:

```python
# sensor_control_app.py (deprecado pero funcional)
import warnings
warnings.warn(
    "sensor_control_app.py está deprecado. "
    "Use 'python -m sensor_control_app.main' en su lugar.",
    DeprecationWarning,
    stacklevel=2
)

# Importar desde nueva estructura
from sensor_control_app.main import main

if __name__ == "__main__":
    main()
```

## Notas Importantes

1. **No romper funcionalidad existente:** La refactorización debe ser transparente para el usuario final
2. **Tests primero:** Escribir tests antes de migrar código garantiza equivalencia funcional
3. **Migración incremental:** Cada fase debe dejar el código en estado funcional
4. **Documentación continua:** Actualizar documentación en cada fase
5. **Backwards compatibility:** Mantener compatibilidad hasta completar migración

## Comandos Actualizados (Post-Refactorización)

### Ejecutar aplicación
```bash
# Opción 1: Como módulo
sudo $(which python) -m sensor_control_app.main

# Opción 2: Script directo
sudo $(which python) main.py
```

### Testing
```bash
# Todos los tests
xvfb-run pytest tests/

# Tests específicos
xvfb-run pytest tests/test_protocol.py
pytest tests/test_state_manager.py  # No requiere Xvfb
```

### Coverage
```bash
pytest --cov=sensor_control_app --cov-report=html tests/
```
