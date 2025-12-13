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

## Ejecución
### Levantar Aplicación
1. Activar ambiente virtual de python: `source .venv/bin/activate`
2. Ejecutar app con: `sudo $(which python) main.py`

### Correr Test
Realizar cada vez que se realizan cambios para validar que no se ha roto nada.
1. `./run_test.sh` o `python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v`

**Nota:** otorgue permisos de modificación al script run_test `chmod +x run_test.sh` o ejecutelo con `bash run_test.sh`

### Generar documentación
1. `make <formato>` ejemplo: `make man`

La documentación se genera en build. Ej: `man build/man/tidgammacf001.1`. Se recomienda luego de generar un build de man copiarlo a la raiz para simplificar su ejecución.

**Nota**: para ver todos los formatos que soporta sphinx ejecute `make --help`

# Deprecado
Versión anterior monolítica contenida en el archivo `sensor_control_app.py` con funcionalidades para:
1. Emparejar FPGA con Interfaz de computadora
2. Gestionar Macros de FGPA con sus comandos (no incluye comandos de CPU)
3. Enviar Macro a todos los PET Scan conectados a las FPGA

## Ejecución
Ejecutar: `sudo $(which python) sensor_control_app.py`
