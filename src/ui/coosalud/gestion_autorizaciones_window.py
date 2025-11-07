"""
Ventana principal para automatización dual de Coosalud.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from src.core.config import config
from src.ui.automatizacion.interfaz_automatizacion_dual import InterfazAutomatizacionDual


class GestionAutorizacionesWindow(QWidget):
    """Ventana principal para automatización dual de Coosalud."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.interfaz_automatizacion = None
        
        self.setup_ui()
        self.logger.info("Ventana de automatización dual inicializada")
    
    def setup_ui(self):
        """Configura la interfaz de usuario responsiva."""
        self.setWindowTitle("🤖 Automatización Dual - Coosalud")
        self.setMinimumSize(1200, 600)
        
        # Maximizar ventana al abrir
        self.showMaximized()
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)  # Menos espacio sin header
        main_layout.setContentsMargins(10, 10, 10, 10)  # Márgenes más pequeños
        
        # Interfaz de automatización directamente SIN header
        self.interfaz_automatizacion = InterfazAutomatizacionDual()
        # Remover el header interno de la automatización
        self.interfaz_automatizacion.quitar_header_interno()
        main_layout.addWidget(self.interfaz_automatizacion)
        
        # Aplicar estilos
        self.aplicar_estilos()
    
    def aplicar_estilos(self):
        """Aplica estilos generales a la ventana."""
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                color: #2d3748;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin: 3px;
            }
            /* Estilo para la ventana principal */
            QMainWindow {
                background-color: #f5f7fa;
            }
        """)
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        # Si hay automatización activa, cerrarla apropiadamente
        if self.interfaz_automatizacion:
            self.interfaz_automatizacion.close()
        
        event.accept()