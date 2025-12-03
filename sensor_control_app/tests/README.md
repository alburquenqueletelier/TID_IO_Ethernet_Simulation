# Tests - sensor_control_app

Este directorio contiene todos los tests del proyecto sensor_control_app.

## Estructura

```
sensor_control_app/tests/
├── __init__.py          # Marca el directorio como paquete Python
├── conftest.py          # Configuración compartida para tests (pytest fixtures)
├── test_app.py          # Tests de la aplicación principal (scroll, drag & drop)
└── README.md            # Este archivo
```

## Tecnologías de Testing

- **Framework principal:** `unittest` (incluido en Python, no requiere instalación)
- **Compatible con:** `pytest` (opcional, configurado en `pytest.ini`)
- **Display virtual:** `Xvfb` (solo necesario para CI/CD o testing headless)

## Ejecutar Tests

### Método 1: Script automatizado (recomendado)

Desde el directorio raíz del proyecto:

```bash
# Auto-detecta entorno (Xvfb si está disponible, sino display actual)
./run_tests.sh

# Fuerza modo headless (requiere Xvfb)
./run_tests.sh headless

# Fuerza modo desktop (usa tu pantalla)
./run_tests.sh desktop
```

### Método 2: unittest directo

```bash
# Con display (desde directorio raíz)
python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v

# Sin display (headless con Xvfb)
xvfb-run python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
```

### Método 3: pytest (si está instalado)

```bash
# Con display
pytest sensor_control_app/tests/ -v

# Sin display
xvfb-run pytest sensor_control_app/tests/ -v
```

### Método 4: Ejecutar un test específico

```bash
# Con unittest
python -m unittest sensor_control_app.tests.test_app.TestScrollAndDragDrop.test_dashboard_scroll_exists -v

# Con pytest
pytest sensor_control_app/tests/test_app.py::TestScrollAndDragDrop::test_dashboard_scroll_exists -v
```

## Escribir Nuevos Tests

### Convenciones

1. **Nombres de archivos:** `test_*.py` (ej: `test_protocol.py`, `test_network.py`)
2. **Nombres de clases:** `Test*` (ej: `TestProtocol`, `TestPacketSender`)
3. **Nombres de métodos:** `test_*` (ej: `test_send_command`, `test_validate_mac`)

### Plantilla de Test

```python
import unittest
import sys
import os

# Setup de path (necesario para importar desde raíz)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

# Imports de la aplicación
from sensor_control_app import McControlApp


class TestMyFeature(unittest.TestCase):
    """Descripción de lo que testea esta clase"""

    @classmethod
    def setUpClass(cls):
        """Ejecuta UNA VEZ antes de todos los tests de esta clase"""
        pass

    @classmethod
    def tearDownClass(cls):
        """Ejecuta UNA VEZ después de todos los tests de esta clase"""
        pass

    def setUp(self):
        """Ejecuta ANTES de cada test individual"""
        pass

    def tearDown(self):
        """Ejecuta DESPUÉS de cada test individual"""
        pass

    def test_something(self):
        """Test específico - debe comenzar con 'test_'"""
        self.assertTrue(True)
        self.assertEqual(1, 1)
        self.assertIsNotNone(object())


if __name__ == '__main__':
    unittest.main()
```

### Tests de GUI (Tkinter)

Para tests que involucran widgets de Tkinter:

```python
import tkinter as tk
from tkinter import ttk

class TestGUIFeature(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Crear root de Tkinter (una sola vez)"""
        cls.root = tk.Tk()
        cls.root.withdraw()  # Ocultar ventana

    @classmethod
    def tearDownClass(cls):
        """Destruir root de Tkinter"""
        cls.root.destroy()

    def setUp(self):
        """Instanciar aplicación antes de cada test"""
        self.app = McControlApp(self.root)
        self.root.update_idletasks()  # Forzar renderizado

    def tearDown(self):
        """Limpiar después de cada test"""
        if hasattr(self.app, 'some_data'):
            self.app.some_data.clear()
```

**Importante:** Los tests de GUI requieren:
- `root.withdraw()` para ocultar la ventana
- `root.update_idletasks()` para forzar renderizado de widgets
- Xvfb cuando se ejecutan sin display (CI/CD)

## Configuración de conftest.py

El archivo `conftest.py` contiene funciones de setup/teardown compartidas:

```python
from conftest import setup_test_environment, teardown_test_environment

# Llamar en setUpClass si es necesario
setup_test_environment()
```

Esto asegura que:
- El path de imports esté configurado correctamente
- Variables de entorno de test estén activas
- El ambiente esté listo para tests

## CI/CD (GitHub Actions)

Los tests se ejecutan automáticamente en GitHub Actions cuando:
- Se hace push a `main`
- Se crea un Pull Request hacia `main`

Configuración en `.github/workflows/python-app.yml`:

```yaml
- name: Test with pytest/unittest (using Xvfb)
  run: |
    xvfb-run pytest sensor_control_app/tests/
```

El workflow instala Xvfb automáticamente y ejecuta los tests en modo headless.

## Debugging de Tests

### Ver output detallado

```bash
# unittest con verbosidad máxima
python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v

# pytest con output detallado
pytest sensor_control_app/tests/ -vv -s
```

### Ejecutar un solo test para debugging

```bash
# unittest
python -m unittest sensor_control_app.tests.test_app.TestScrollAndDragDrop.test_dashboard_scroll_exists -v

# pytest con debugging
pytest sensor_control_app/tests/test_app.py::TestScrollAndDragDrop::test_dashboard_scroll_exists -vv -s
```

### Debugging con pdb

```python
def test_something(self):
    import pdb; pdb.set_trace()  # Breakpoint
    # Tu código aquí
```

## Buenas Prácticas

1. **Tests aislados:** Cada test debe ser independiente y no depender del estado de otros tests
2. **Setup/Teardown:** Usar setUp/tearDown para preparar y limpiar el ambiente
3. **Nombres descriptivos:** Los nombres de tests deben describir QUÉ están testeando
4. **Un concepto por test:** Cada test debe verificar una sola cosa
5. **Assertions claras:** Usar mensajes descriptivos en assertions

```python
# Mal
self.assertTrue(x)

# Bien
self.assertTrue(x, "El valor de x debería ser True después de inicializar")
```

## Troubleshooting

### Error: "No module named 'sensor_control_app'"

Asegúrate de ejecutar desde el directorio raíz del proyecto, no desde `sensor_control_app/tests/`.

### Error: "Couldn't connect to display"

Necesitas Xvfb para tests headless:

```bash
sudo apt-get install xvfb
xvfb-run python -m unittest discover -s sensor_control_app/tests
```

O ejecuta con display:

```bash
python -m unittest discover -s sensor_control_app/tests
```

### Error: "Test discovery failed"

Verifica que:
- Estás en el directorio raíz del proyecto
- Todos los archivos de test comienzan con `test_`
- Todos los `__init__.py` existen en los directorios necesarios

## Cobertura de Código

Para medir cobertura (requiere `pytest-cov`):

```bash
pip install pytest-cov
pytest sensor_control_app/tests/ --cov=sensor_control_app --cov-report=html
```

Esto genera un reporte HTML en `htmlcov/index.html`.

## Próximos Tests a Implementar (Fase 2+)

- `test_protocol.py` - Tests del protocolo de comunicación
- `test_state_manager.py` - Tests de gestión de estado
- `test_packet_sender.py` - Tests de envío de paquetes
- `test_database.py` - Tests de persistencia
- `test_macro_manager.py` - Tests de gestión de macros
- `test_widgets.py` - Tests de widgets reutilizables
- `test_tabs.py` - Tests de pestañas (Dashboard, Commands)
