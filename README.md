# TID Gamma Simulation

Este proyecto simula el envío y recepción de tramas de datos entre dispositivos usando Scapy en Python. El experimento consiste en conectar un cable de red desde una computadora hacia si misma. En este caso, se uso la entrada de red para conectar un RJ45 hacia un adaptador de Tipo C hacia ethernet.

## Requisitos
- Python 3.8+
- [Scapy](https://scapy.net/) 2.6.1+ (detalles de instalación a continuación)
- Wireshark 4.0.17

## Instalación
1. Clona el repositorio o descarga los archivos en tu máquina.
2. Crea un ambiente virtual (o no)

```bash
python3 -m venv .env # o el nombre que quieras
source .env/bin/activate
```

3. Instala las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

4. Crea un archivo .env y agregale el nombre de las interfaces con sus respectivas MAC.
```bash
cp .env.example .env
```

## Uso
El archivo principal es `simulation.py`. Para ejecutar la simulación:

```bash
sudo $(which python) simulation.py
```
Esto construirá y mostrará una trama de datos simulada usando Scapy.

**NOTA:** Scapy requiere privilegios root ya que interactua con raw socket a nivel de capa 2, el cual se logra mediante procesos reservados para el OS (systems calls). El `$(which python)` se usa para que sudo utilice el entorno virtual en lugar del global.

## Visualización 
1. Abre Wireshark con privilegios de admin
`sudo wireshark`

2. Seleccionar la interfaz que quieres monitorear (emisor o receptor)
3. Vuelve a ejecutar el script de python. Con esto se debería ver la trama.


## Estructura del proyecto
- `simulation.py`: Script principal de simulación.
- `requirements.txt`: Dependencias del proyecto.
- `docs/`: Documentación y recursos gráficos.

## Notas
- El script utiliza direcciones MAC ficticias. Modifícalas según tu entorno si deseas realizar pruebas reales.
- Se recomienda ejecutar con privilegios de administrador si se requiere acceso a la red física.

## Licencia
Este proyecto es solo para fines educativos.