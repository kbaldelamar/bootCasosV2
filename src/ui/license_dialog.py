"""
Diálogo para ingreso y activación de licencias con soporte para códigos encriptados.
"""
import logging
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QFormLayout, QProgressBar, QMessageBox, QTabWidget,
    QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from src.license.license_manager import LicenseManager, LicenseException


class LicenseActivationWorker(QThread):
    """Worker thread para activación de licencias."""
    
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, license_input: str, operation_type: str = 'validate'):
        super().__init__()
        self.license_input = license_input
        self.operation_type = operation_type  # 'validate', 'activate', 'process_encrypted'
        self.license_manager = LicenseManager()
    
    def run(self):
        """Ejecuta la operación de licencia correspondiente."""
        try:
            if self.operation_type == 'process_encrypted':
                self.progress.emit("Procesando código encriptado...")
                result = self.license_manager.process_encrypted_license_code(self.license_input)
                
            elif self.operation_type == 'activate':
                self.progress.emit("Activando licencia...")
                result = self.license_manager.activate_license(self.license_input)
                
            elif self.operation_type == 'validate':
                self.progress.emit("Validando licencia...")
                result = self.license_manager.validate_license(self.license_input)
                
            else:
                raise ValueError(f"Tipo de operación no válido: {self.operation_type}")
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class LicenseDialog(QDialog):
    """Diálogo para gestión de licencias con soporte para códigos encriptados."""
    
    def __init__(self, parent=None, reason="first_time"):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.reason = reason  # first_time, expired, invalid
        self.license_manager = LicenseManager()
        self.worker = None
        
        self.setup_ui()
        self.setup_content_by_reason()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Gestión de Licencias - BootCasosV2")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Título del diálogo
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Mensaje informativo
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666666; margin: 10px;")
        layout.addWidget(self.info_label)
        
        # Solo área para código encriptado
        self.encrypted_code_section = self.create_encrypted_code_section()
        layout.addWidget(self.encrypted_code_section)
        
        # Información del hardware
        hardware_group = QGroupBox("Información del Sistema")
        hardware_layout = QFormLayout(hardware_group)
        
        hardware_id = self.license_manager.get_hardware_id()
        self.hardware_label = QLabel(hardware_id)
        self.hardware_label.setStyleSheet("color: #888888; font-family: monospace;")
        hardware_layout.addRow("ID de Hardware:", self.hardware_label)
        
        layout.addWidget(hardware_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Área de resultados
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(100)
        self.result_text.setVisible(False)
        layout.addWidget(self.result_text)
        
        # Botón principal
        buttons_layout = QHBoxLayout()
        
        self.activate_button = QPushButton("� Activar Licencia y Entrar")
        self.activate_button.clicked.connect(self.activate_license_and_enter)
        self.activate_button.setEnabled(False)
        self.activate_button.setStyleSheet("""
            QPushButton { 
                background-color: #28A745; 
                color: white; 
                padding: 12px 24px; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6C757D;
            }
        """)
        buttons_layout.addWidget(self.activate_button)
        
        buttons_layout.addStretch()
        
        # Botón para validar licencia existente (solo si hay licencia guardada)
        self.validate_existing_button = QPushButton("✓ Validar Licencia Existente")
        self.validate_existing_button.clicked.connect(self.validate_existing_license)
        self.validate_existing_button.setStyleSheet("""
            QPushButton { 
                background-color: #007ACC; 
                color: white; 
                padding: 8px 16px; 
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        buttons_layout.addWidget(self.validate_existing_button)
        
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
        # Verificar si hay licencia existente para mostrar/ocultar botón de validación
        self.check_existing_license()
    
    def create_encrypted_code_section(self):
        """Crea la sección para códigos encriptados."""
        group = QGroupBox("Código de Licencia Encriptado")
        layout = QVBoxLayout(group)
        
        # Instrucciones
        instructions = QLabel(
            "Cargue el archivo de licencia generado (.txt) o pegue el código encriptado directamente."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Área de texto para código encriptado
        self.encrypted_input = QTextEdit()
        self.encrypted_input.setPlaceholderText(
            "Pegue aquí el código encriptado o use el botón 'Cargar Archivo' para seleccionar el archivo .txt"
        )
        self.encrypted_input.setMaximumHeight(120)
        self.encrypted_input.textChanged.connect(self.validate_encrypted_input)
        layout.addWidget(self.encrypted_input)
        
        # Botón para cargar desde archivo
        file_layout = QHBoxLayout()
        self.load_file_button = QPushButton("📁 Cargar Archivo .txt")
        self.load_file_button.clicked.connect(self.load_encrypted_from_file)
        self.load_file_button.setStyleSheet("QPushButton { padding: 6px 12px; }")
        file_layout.addWidget(self.load_file_button)
        file_layout.addStretch()
        layout.addLayout(file_layout)
        
        return group
    
    def setup_content_by_reason(self):
        """Configura el contenido según la razón del diálogo."""
        if self.reason == "first_time":
            self.title_label.setText("🔐 Activación de Licencia")
            self.info_label.setText(
                "Bienvenido a BootCasosV2. Para utilizar la aplicación, "
                "cargue su código de licencia encriptado (.txt) y haga clic en 'Activar Licencia y Entrar'.\\n\\n"
                "Una vez activada, tendrá acceso completo a todas las funcionalidades."
            )
            
        elif self.reason == "expired":
            self.title_label.setText("⚠️ Licencia Expirada")
            self.info_label.setText(
                "Su licencia ha expirado. Para continuar utilizando la aplicación, "
                "necesita cargar una nueva licencia.\\n\\n"
                "Contacte a su proveedor para obtener un nuevo código de licencia."
            )
            self.info_label.setStyleSheet("color: #FF6B35; margin: 10px;")
            
        elif self.reason == "invalid":
            self.title_label.setText("❌ Licencia Inválida")
            self.info_label.setText(
                "La licencia actual no es válida. Cargue un nuevo código de licencia encriptado para continuar."
            )
            self.info_label.setStyleSheet("color: #DC3545; margin: 10px;")
    
    def validate_encrypted_input(self):
        """Valida el código encriptado y habilita botones."""
        encrypted_code = self.encrypted_input.toPlainText().strip()
        is_valid = len(encrypted_code) > 50  # Códigos encriptados son largos
        
        self.activate_button.setEnabled(is_valid)
    
    def check_existing_license(self):
        """Verifica si hay licencia existente guardada."""
        try:
            # Verificar si hay licencia guardada localmente
            stored_license = self.license_manager._load_stored_license()
            self.validate_existing_button.setVisible(stored_license is not None)
        except:
            self.validate_existing_button.setVisible(False)
    
    def activate_license_and_enter(self):
        """Activa la licencia desde el código encriptado y permite entrar."""
        encrypted_code = self.encrypted_input.toPlainText().strip()
        if not encrypted_code:
            QMessageBox.warning(self, "Error", "Debe cargar un código de licencia encriptado.")
            return
        
        self.execute_license_operation(
            encrypted_code, 
            'process_encrypted', 
            "Activando licencia y preparando acceso..."
        )
    
    def validate_existing_license(self):
        """Valida la licencia existente sin procesar nueva."""
        try:
            # Verificar licencia existente
            if self.license_manager.is_valid(check_api=True):
                license_info = self.license_manager.get_license_info()
                client_name = license_info.get('client_name', 'Usuario')
                
                QMessageBox.information(
                    self,
                    "Licencia Válida",
                    f"La licencia para {client_name} es válida.\\n\\n"
                    "Puede acceder a la aplicación."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Licencia Inválida",
                    "La licencia existente no es válida o ha expirado.\\n"
                    "Debe cargar un nuevo código de licencia."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Validación",
                f"Error al validar licencia existente: {e}"
            )
    
    def load_encrypted_from_file(self):
        """Carga un código encriptado desde un archivo .txt"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar archivo de licencia",
            "",
            "Archivos de texto (*.txt);;Todos los archivos (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                self.encrypted_input.setPlainText(content)
                self.validate_encrypted_input()
                
                self.logger.info(f"Código cargado desde: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo cargar el archivo:\\n{e}"
                )
    
    def execute_license_operation(self, license_input: str, operation_type: str, progress_message: str = "Procesando..."):
        """Ejecuta la operación de licencia en un hilo separado."""
        # Configurar UI para operación en progreso
        self.activate_button.setEnabled(False)
        self.validate_existing_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.result_text.setVisible(True)
        self.result_text.clear()
        self.result_text.setPlainText(f"⏳ {progress_message}")
        self.result_text.setStyleSheet("color: #17A2B8;")
        
        # Crear y ejecutar worker
        self.worker = LicenseActivationWorker(license_input, operation_type)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.progress.connect(self.on_operation_progress)
        self.worker.start()
    
    def on_operation_finished(self, result: dict):
        """Maneja la finalización de la operación de licencia."""
        # Restaurar UI
        self.progress_bar.setVisible(False)
        self.validate_encrypted_input()  # Re-habilitar botones según input
        self.validate_existing_button.setEnabled(True)
        
        success_key = 'success' if 'success' in result else 'valid'
        
        if result.get(success_key, False):
            # Operación exitosa
            license_data = result.get('license_data', {})
            
            success_text = (
                f"✅ Licencia activada exitosamente\\n\\n"
                f"Cliente: {license_data.get('client_name', 'N/A')}\\n"
                f"Identificación: {license_data.get('client_identification', 'N/A')}\\n"
                f"Clave: {license_data.get('license_key', 'N/A')}\\n"
                f"Estado: {license_data.get('status', 'N/A')}\\n"
                f"Características: {', '.join(license_data.get('features', []))}"
            )
            
            self.result_text.setPlainText(success_text)
            self.result_text.setStyleSheet("color: #28A745;")
            
            # Cerrar automáticamente después de un breve delay para que el usuario vea el éxito
            self.logger.info("Licencia procesada exitosamente")
            
            # Cerrar el diálogo inmediatamente con éxito
            self.accept()
            
        else:
            # Error en la operación
            error_type = result.get('error_type', 'unknown')
            message = result.get('message', 'Error desconocido')
            
            error_text = f"❌ Error: {message}"
            
            if error_type == "license_expired":
                error_text += "\\n\\nLa licencia ha expirado. Contacte a su proveedor."
            elif error_type == "license_not_found":
                error_text += "\\n\\nLa clave de licencia no es válida."
            elif error_type == "already_activated":
                error_text += "\\n\\nLa licencia ya está activada en otro dispositivo."
            elif error_type == "connection_error":
                error_text += "\\n\\nVerifique su conexión a internet."
            
            self.result_text.setPlainText(error_text)
            self.result_text.setStyleSheet("color: #DC3545;")
            
            self.logger.error(f"Error en operación de licencia: {message}")
    
    def on_operation_error(self, error_message: str):
        """Maneja errores en la operación de licencia."""
        self.progress_bar.setVisible(False)
        self.validate_encrypted_input()
        self.validate_existing_button.setEnabled(True)
        
        error_text = f"❌ Error inesperado: {error_message}"
        self.result_text.setPlainText(error_text)
        self.result_text.setStyleSheet("color: #DC3545;")
        
        self.logger.error(f"Error inesperado en licencia: {error_message}")
    
    def on_operation_progress(self, message: str):
        """Actualiza el progreso de la operación."""
        self.result_text.setPlainText(f"⏳ {message}")
        self.result_text.setStyleSheet("color: #17A2B8;")
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()