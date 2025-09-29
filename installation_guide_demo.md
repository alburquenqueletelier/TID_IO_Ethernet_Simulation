# Sistema de Control de Microcontroladores y Sensores

## Descripción General

Esta aplicación de escritorio en Python permite la comunicación entre una máquina host y microcontroladores equipados con diversos sensores (temperatura, gamma, PET). La aplicación proporciona una interfaz gráfica completa para monitorear, controlar y almacenar datos de sensores en tiempo real.

## Características Principales

### 🔐 Sistema de Autenticación
- Login seguro con credenciales hardcodeadas (admin/sensor123)
- Interfaz de autenticación moderna

### 📊 Dashboard Principal
- Estadísticas en tiempo real (tramas enviadas/recibidas)
- Identificación del tipo de evento más frecuente en 24h
- Gráficos de temperatura en tiempo real
- Lista de eventos recientes

### 🔧 Control de Comandos
- Envío de comandos predefinidos al microcontrolador
- Soporte para comandos personalizados
- Configuración flexible de puerto serial
- Área de respuestas en tiempo real

### 📈 Monitoreo de Tráfico
- Visualización detallada del tráfico de datos gamma/PET
- Sistema de filtros por tipo de sensor
- Calidad de datos y timestamps

### 🗄️ Base de Datos Integrada
- Almacenamiento automático en SQLite
- Exportación a CSV
- Estadísticas detalladas de almacenamiento
- Gestión completa de registros históricos

### ⚙️ Metadatos del Sistema
- Información detallada de microcontroladores conectados
- Estado y configuración de sensores
- Monitoreo del estado de conectividad

## Instalación
Se recomienda usar un entorno virtual.

### Requisitos del Sistema
- Python 3.7 o superior
- Windows 10/11, Linux Ubuntu 18.04+, o macOS 10.14+
- Puerto USB/Serial disponible

### Dependencias Requeridas

Instala las siguientes librerías usando pip:

```bash
pip install tkinter
pip install pyserial
pip install matplotlib
pip install sqlite3  # (incluido con Python)
```

O instala todas las dependencias de una vez:

```bash
pip install -r requirements.txt
```

### Contenido del archivo requirements.txt:
```
pyserial>=3.5
matplotlib>=3.5.0
```

## Configuración Inicial

### 1. Configuración del Puerto Serial

Antes de usar la aplicación, verifica:

- **Windows**: El puerto COM disponible (ej: COM3, COM4)
- **Linux**: El puerto tty disponible (ej: /dev/ttyUSB0, /dev/ttyACM0)
- **macOS**: El puerto disponible (ej: /dev/cu.usbmodem*)

### 2. Permisos (Linux/macOS)

En sistemas Linux/macOS, otorga permisos al puerto serial:

```bash
sudo chmod 666 /dev/ttyUSB0
# o agregar usuario al grupo dialout
sudo usermod -a -G dialout $USER
```

### 3. Base de Datos

La aplicación crea automáticamente una base de datos SQLite (`sensor_data.db`) en el directorio de ejecución.

## Uso de la Aplicación

### Inicio de Sesión
1. Ejecuta la aplicación: `python sensor_control_app.py`
2. Ingresa las credenciales:
   - **Usuario**: admin
   - **Contraseña**: sensor123

### Configuración de Conexión
1. Ve a la pestaña "Comandos"
2. Configura el puerto serial y velocidad (baudios)
3. Haz clic en "Conectar"

### Comandos Disponibles

La aplicación incluye comandos predefinidos para el microcontrolador:

| Comando | Descripción |
|---------|-------------|
| `GET_TEMP` | Obtener lectura de temperatura |
| `GET_GAMMA` | Obtener datos de sensores gamma/PET |
| `START_MONITOR` | Iniciar monitoreo continuo |
| `STOP_MONITOR` | Detener monitoreo |
| `GET_STATUS` | Obtener estado del sistema |
| `RESET` | Reiniciar microcontrolador |
| `CALIBRATE` | Calibrar sensores |

### Formato de Datos Esperado

El microcontrolador debe enviar datos en formato JSON:

```json
{
    "sensor_id": "TEMP_001",
    "type": "temperature",
    "value": 25.3,
    "unit": "°C",
    "timestamp": "2024-12-08T14:30:00"
}
```

```json
{
    "sensor_id": "GAMMA_001",
    "type": "gamma",
    "value": 0.125,
    "unit": "μSv/h",
    "timestamp": "2024-12-08T14:30:00"
}
```

## Protocolo de Comunicación

### Comandos del Host al Microcontrolador
- Formato: Texto plano terminado en `\n`
- Ejemplo: `GET_TEMP\n`

### Respuestas del Microcontrolador al Host
- Formato: JSON válido o texto plano
- Los datos JSON se procesan automáticamente
- El texto plano se muestra en el área de respuestas

## Estructura de Base de Datos

### Tabla: sensor_readings
```sql
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    sensor_type TEXT,
    sensor_id TEXT,
    value REAL,
    unit TEXT,
    metadata TEXT
);
```

### Tabla: communication_log
```sql
CREATE TABLE communication_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    direction TEXT,
    data TEXT,
    frame_type TEXT
);
```

## Funciones Avanzadas

### Exportación de Datos
- Formato CSV compatible con Excel
- Incluye todos los campos de sensores
- Timestamps en formato ISO 8601

### Monitoreo en Tiempo Real
- Gráficos actualizados automáticamente
- Detección de patrones en eventos
- Alertas de conectividad

### Modo Simulación
- Para desarrollo y pruebas
- Genera datos aleatorios cuando no hay conexión serial
- Permite probar todas las funcionalidades

## Troubleshooting

### Problemas Comunes

**Error de Conexión Serial**
```
Solución:
1. Verificar puerto COM/tty correcto
2. Comprobar que no esté en uso por otra aplicación
3. Verificar permisos (Linux/macOS)
4. Reiniciar la aplicación
```

**Base de Datos Bloqueada**
```
Solución:
1. Cerrar otras instancias de la aplicación
2. Verificar permisos de escritura en el directorio
3. Eliminar archivo .db-lock si existe
```

**Gráficos No Se Muestran**
```
Solución:
1. Verificar instalación de matplotlib
2. Reiniciar la aplicación
3. pip install matplotlib --upgrade
```

## Desarrollo y Personalización

### Agregar Nuevos Comandos
Modifica el diccionario `self.commands` en el método `create_commands_tab()`:

```python
self.commands = {
    "GET_TEMP": "Obtener temperatura",
    "NUEVO_COMANDO": "Descripción del comando",
    # ... más comandos
}
```

### Personalizar Tipos de Sensores
Modifica la función `process_sensor_data()` para manejar nuevos tipos:

```python
def process_sensor_data(self, data):
    event_type = data.get('type', 'unknown')
    if event_type == 'nuevo_sensor':
        # Lógica específica para el nuevo sensor
        pass
```

### Cambiar Credenciales
Modifica el método `login()` para cambiar usuario/contraseña:

```python
if username == "tu_usuario" and password == "tu_contraseña":
```

## Logs y Depuración

### Archivos Generados
- `sensor_data.db`: Base de datos principal
- Logs de consola para errores de comunicación

### Modo Debug
Descomenta las líneas de print para mayor información:

```python
# Agregar al inicio de métodos críticos
print(f"Debug: {mensaje_debug}")
```

## Contribución

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## Soporte

Para reportar bugs o solicitar nuevas funcionalidades, crea un issue en el repositorio del proyecto.

---

**Versión**: 1.0.0  
**Fecha**: Diciembre 2024  
**Autor**: Sistema de Control de Sensores Team