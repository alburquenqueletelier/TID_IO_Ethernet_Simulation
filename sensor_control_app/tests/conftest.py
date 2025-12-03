"""
Configuración compartida para tests.

Este archivo se carga automáticamente por pytest antes de ejecutar tests.
Para unittest, las funciones están disponibles pero deben ser llamadas manualmente.
"""

import sys
import os

# Agregar el directorio raíz al path para permitir imports absolutos
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


def setup_test_environment():
    """
    Configuración inicial del ambiente de testing.

    Esta función debe ser llamada antes de cualquier test que requiera
    importar módulos de la aplicación principal.
    """
    # Asegurar que el directorio raíz está en el path
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # Configurar variables de entorno si es necesario
    # Por ejemplo, para tests, podríamos querer usar una base de datos diferente
    os.environ.setdefault('TEST_MODE', 'true')


def teardown_test_environment():
    """
    Limpieza del ambiente de testing.
    """
    # Limpiar variables de entorno de test
    if 'TEST_MODE' in os.environ:
        del os.environ['TEST_MODE']
