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

## Ejecución
Ejecutar: `sudo $(which python) sensor_control_app.py`

## Release
Dado que el usuario final es versado en conocimientos de programación, solo se realizarán cambios en el código con notificación cuando la app reciba cambios. Se evaluará la opción de empaquetar todo más adelante ya que de empaquetar ahora podría truncar ciertas facilidades al usuario, como alterar directamente el archivo fuente de información de la app. Por tanto el usuario se hace responsable de lo que pueda ocurrir. 