#!/bin/bash

# Script para ejecutar tests de la aplicación sensor_control_app
# Soporta ejecución en ambiente con escritorio y sin escritorio (CI/CD)

set -e  # Salir si algún comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_msg() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "sensor_control_app.py" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    print_msg "Activando entorno virtual..."
    source .venv/bin/activate
else
    print_warning "No se encontró entorno virtual en .venv/"
fi

# Detectar modo de ejecución
MODE="${1:-auto}"

print_msg "=== Ejecutando tests de sensor_control_app ==="
echo ""

case "$MODE" in
    auto)
        # Detectar automáticamente si Xvfb está disponible
        if command -v xvfb-run &> /dev/null; then
            print_msg "Modo: AUTO - Xvfb detectado, ejecutando en modo headless"
            xvfb-run python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
        else
            print_msg "Modo: AUTO - Sin Xvfb, ejecutando con display actual"
            python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
        fi
        ;;

    headless)
        # Forzar modo sin escritorio (requiere Xvfb)
        if ! command -v xvfb-run &> /dev/null; then
            print_error "Modo headless requiere Xvfb instalado"
            print_msg "Instalar con: sudo apt-get install xvfb"
            exit 1
        fi
        print_msg "Modo: HEADLESS - Usando Xvfb"
        xvfb-run python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
        ;;

    desktop)
        # Forzar modo con escritorio
        print_msg "Modo: DESKTOP - Usando display actual"
        python -m unittest discover -s sensor_control_app/tests -p "test_*.py" -v
        ;;

    pytest)
        # Usar pytest si está disponible
        if ! command -v pytest &> /dev/null; then
            print_error "pytest no está instalado"
            print_msg "Instalar con: pip install pytest"
            exit 1
        fi

        if command -v xvfb-run &> /dev/null; then
            print_msg "Modo: PYTEST - Con Xvfb"
            xvfb-run pytest sensor_control_app/tests/ -v
        else
            print_msg "Modo: PYTEST - Sin Xvfb"
            pytest sensor_control_app/tests/ -v
        fi
        ;;

    help|--help|-h)
        echo "Uso: $0 [modo]"
        echo ""
        echo "Modos disponibles:"
        echo "  auto     - Detecta automáticamente si usar Xvfb (default)"
        echo "  headless - Fuerza ejecución sin UI usando Xvfb"
        echo "  desktop  - Fuerza ejecución con display actual"
        echo "  pytest   - Ejecuta tests usando pytest"
        echo "  help     - Muestra esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  $0              # Modo automático"
        echo "  $0 headless     # Simula ambiente CI/CD"
        echo "  $0 desktop      # Ejecuta con tu escritorio"
        exit 0
        ;;

    *)
        print_error "Modo desconocido: $MODE"
        print_msg "Usa '$0 help' para ver opciones disponibles"
        exit 1
        ;;
esac

# Capturar código de salida
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_msg "=== ✓ Tests completados exitosamente ==="
else
    print_error "=== ✗ Tests fallaron ==="
fi

exit $EXIT_CODE
