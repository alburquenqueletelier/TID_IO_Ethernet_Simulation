# TID 

# Aplicación para comunicación entre Computadora y Micro Controlador

## Etapa Actual

Aplicación de escritorio que permite vía formulario enviar un comando al microcontrolador. 

En desarrollo...

## Requerimientos

Linux Debian 12 (rellenar con lo del otro doc)

```bash
contourpy==1.3.3
cycler==0.12.1
fonttools==4.59.2
kiwisolver==1.4.9
matplotlib==3.10.6
numpy==2.3.2
packaging==25.0
pillow==11.3.0
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

## Ejecución
Ejecutar: `python3 sensor_control_app.py`