"""
Ejemplo de ejecución de la interfaz de automatización dual.
"""
import sys
import asyncio
import logging
from PySide6.QtWidgets import QApplication
from src.ui.coosalud.gestion_autorizaciones_window import GestionAutorizacionesWindow


def configurar_logging():
    """Configura el sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('automatizacion.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """Función principal."""
    try:
        # Configurar logging
        configurar_logging()
        
        # Crear aplicación
        app = QApplication(sys.argv)
        app.setApplicationName("Sistema de Automatización Dual - Coosalud")
        app.setApplicationVersion("2.0")
        
        # Crear y mostrar ventana principal
        ventana = GestionAutorizacionesWindow()
        ventana.show()
        
        # Log inicial
        logging.info("🚀 Sistema de automatización dual iniciado")
        logging.info("📋 Vista tradicional disponible en la primera pestaña")
        logging.info("🤖 Automatización dual disponible en la segunda pestaña")
        
        # Ejecutar aplicación
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"❌ Error crítico en la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()