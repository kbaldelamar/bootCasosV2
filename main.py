"""
Módulo principal de la aplicación.
"""
import sys
import os
import logging

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.core.config import config


def setup_application():
    """Configura la aplicación antes de iniciarla."""
    # Configurar QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(config.get('app.name'))
    app.setApplicationVersion(config.get('app.version'))
    
    # Log de inicio
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando {config.get('app.name')} v{config.get('app.version')}")
    
    return app


def main():
    """Función principal de la aplicación."""
    try:
        # Configurar aplicación
        app = setup_application()
        
        # Crear y mostrar ventana principal
        window = MainWindow()
        window.show()
        
        # Ejecutar aplicación
        sys.exit(app.exec())
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error fatal en la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()