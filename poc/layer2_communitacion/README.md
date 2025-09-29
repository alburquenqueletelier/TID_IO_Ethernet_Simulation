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
python3 -m venv .venv # o el nombre que quieras
source .venv/bin/activate
```

3. Instala las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

4. Crea un archivo .env y agregale el nombre de las interfaces con sus respectivas MAC.
```bash
cp .env.example .env
```

**Nota:** para ver el nombre y mac de tus interfaces usa `ip a` en linux. Recuerda tener conectada tu computadora con un cable ethernet a sí misma.

## Uso
1. Ejecuta `destination.py` para monitorear el tráfico de la interfaz ethernet de destino
    ```bash
    sudo $(which python) destination.py
    ```
2. Abre otra terminal y ejecuta `source.py` para enviar una trama
    ```bash
    sudo $(which python) source.py
    ```

**NOTA:** La librería socket de python requiere de privilegios root para algunas características. El `$(which python)` se usa para que sudo utilice el entorno virtual en lugar del global.

## Visualización 
Adicional a los registros visibles en la terminal donde corre `destination.py` puedes usar `Wireshark` para monitorear las tramas enviadas o recibidas según la interfaz de red que sniffeas. 

1. Abre Wireshark con privilegios de admin
`sudo wireshark`

2. Seleccionar la interfaz que quieres monitorear (emisor o receptor)
3. Vuelve a ejecutar el script de python. Con esto se debería ver la trama.


## Estructura del proyecto
- `source.py`: Script que envía tramas desde la interfaz origen a la de destino.
- `destination.py`: Script que recibe tramas en bruto, las parsea e imprime en consola.
- `requirements.txt`: Dependencias del proyecto.
- `docs/`: Documentación y recursos gráficos.

## Notas
- El script utiliza direcciones MAC ficticias. Modifícalas según tu entorno si deseas realizar pruebas reales.
- Se recomienda ejecutar con privilegios de administrador si se requiere acceso a la red física.

## Licencia
Este proyecto es solo para fines educativos.